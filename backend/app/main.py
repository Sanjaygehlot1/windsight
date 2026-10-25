from datetime import date, datetime, timezone
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from .analytics import analyze
from .elexon import retrieve_month, UpstreamError
import asyncio
import os

app=FastAPI(title='WindSight API',version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=[s.strip() for s in os.getenv('CORS_ORIGINS','http://localhost:5173').split(',')],allow_methods=['GET'],allow_headers=['*'])
_cache=None
_lock=asyncio.Lock()

@app.get('/api/health')
def health(): return {'status':'ok','dataset':'January 2026'}

@app.get('/api/dashboard')
async def dashboard(cutoff_hour:int=Query(12,ge=0,le=23),refresh:bool=False):
    global _cache
    async with _lock:
        if _cache is None or refresh:
            try: actuals, forecasts=await retrieve_month()
            except UpstreamError as e: raise HTTPException(status_code=502,detail=str(e))
            _cache=(actuals,forecasts,datetime.now(timezone.utc).isoformat())
        actuals,forecasts,last_updated=_cache
    result=analyze(actuals,forecasts,cutoff_hour)
    result['loadedAt']=last_updated
    result['source']='Elexon BMRS: FUELHH + WINDFOR'
    return result
