import asyncio
import gzip
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .analytics import analyze
from .elexon import retrieve_month, UpstreamError

app = FastAPI(title='WindSight API', version='2.0.0')
app.add_middleware(CORSMiddleware, allow_origins=[s.strip() for s in os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')], allow_methods=['GET'], allow_headers=['*'])
SNAPSHOT = Path(__file__).resolve().parents[1] / 'data' / 'january-2026.json.gz'
_cache = None
_lock = asyncio.Lock()


def read_snapshot():
    if not SNAPSHOT.exists():
        return None
    try:
        with gzip.open(SNAPSHOT, 'rt', encoding='utf-8') as f:
            saved = json.load(f)
        if not saved['actuals'] or not saved['forecasts']:
            return None
        return saved['actuals'], saved['forecasts'], saved['loadedAt'], 'snapshot'
    except (OSError, ValueError, KeyError):
        logging.exception('Unable to read historical snapshot; attempting live ingestion')
        return None


@app.get('/api/health')
def health():
    return {'status': 'ok', 'decisionPeriod': '2026-01-01/2026-01-31', 'snapshotAvailable': SNAPSHOT.exists()}


@app.get('/api/dashboard')
async def dashboard(cutoff_hour: int = Query(12, ge=0, le=23), cutoff_minute: int = Query(0, ge=0, le=59)):
    global _cache
    async with _lock:
        if _cache is None:
            _cache = read_snapshot()
        if _cache is None:
            try:
                actuals, forecasts = await retrieve_month()
            except UpstreamError as exc:
                raise HTTPException(status_code=502, detail=str(exc)) from exc
            if not actuals or not forecasts:
                raise HTTPException(status_code=502, detail='Elexon returned no wind actuals or forecasts for the pilot period. Please retry.')
            _cache = (actuals, forecasts, datetime.now(timezone.utc).isoformat(), 'live')
        actuals, forecasts, loaded_at, mode = _cache
    result = analyze(actuals, forecasts, cutoff_hour=cutoff_hour, cutoff_minute=cutoff_minute)
    result.update(sourceRecordCounts={'FUELHH': len(actuals), 'WINDFOR': len(forecasts)}, loadedAt=loaded_at, dataMode=mode, source='Elexon BMRS: FUELHH (WIND) + WINDFOR')
    return result


static_dir = Path(os.getenv('STATIC_DIR', str(Path(__file__).resolve().parents[2] / 'frontend' / 'dist')))
if static_dir.is_dir():
    app.mount('/', StaticFiles(directory=static_dir, html=True), name='frontend')
