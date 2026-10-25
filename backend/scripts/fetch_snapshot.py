"""Create a reproducible, real-data pilot snapshot: python -m scripts.fetch_snapshot."""
import asyncio
import gzip
import json
from datetime import datetime, timezone
from pathlib import Path
from app.elexon import retrieve_month
from app.analytics import analyze


async def main():
    actuals, forecasts = await retrieve_month()
    result = analyze(actuals, forecasts)
    if result['metrics']['matchedPeriods'] == 0:
        raise RuntimeError('No matched observations; refusing to save an empty snapshot')
    snapshot = {'loadedAt': datetime.now(timezone.utc).isoformat(), 'actuals': actuals, 'forecasts': forecasts}
    dest = Path(__file__).resolve().parents[1] / 'data' / 'january-2026.json.gz'
    dest.parent.mkdir(exist_ok=True)
    with gzip.open(dest, 'wt', encoding='utf-8') as f:
        json.dump(snapshot, f, separators=(',', ':'), allow_nan=False)
    print(json.dumps({'path': str(dest), 'sourceRecords': {'actual': len(actuals), 'forecast': len(forecasts)}, 'metrics': result['metrics'], 'quality': result['quality'], 'loadedAt': snapshot['loadedAt']}, indent=2))


if __name__ == '__main__':
    asyncio.run(main())
