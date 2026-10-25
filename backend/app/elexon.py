import asyncio
from datetime import datetime, timedelta, timezone
import httpx
from .analytics import DELIVERY_START, DELIVERY_END

BASE = 'https://data.elexon.co.uk/bmrs/api/v1'


class UpstreamError(RuntimeError):
    pass


async def _get(client, dataset, params):
    for attempt in range(3):
        try:
            response = await client.get(f'{BASE}/datasets/{dataset}/stream', params=params)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and 'data' in data:
                data = data['data']
            if not isinstance(data, list) or any(not isinstance(r, dict) for r in data):
                raise ValueError('Unexpected response shape')
            return data
        except (httpx.HTTPError, ValueError) as exc:
            retryable = isinstance(exc, httpx.TransportError) or (
                isinstance(exc, httpx.HTTPStatusError) and (exc.response.status_code == 429 or exc.response.status_code >= 500)
            )
            if not retryable or attempt == 2:
                raise UpstreamError(f'Elexon {dataset} could not be loaded. Please retry.') from exc
            await asyncio.sleep(2 ** attempt)


async def retrieve_month():
    jobs = []
    day = DELIVERY_START
    while day <= DELIVERY_END:
        jobs.append(('FUELHH', {'settlementDateFrom': day.isoformat(), 'settlementDateTo': day.isoformat(), 'fuelType': 'WIND'}))
        day += timedelta(days=1)
    cursor = datetime(2025, 12, 29, tzinfo=timezone.utc)
    end = datetime(2026, 2, 1, tzinfo=timezone.utc)
    while cursor < end:
        nxt = cursor + timedelta(days=1)
        jobs.append(('WINDFOR', {'publishDateTimeFrom': cursor.isoformat(), 'publishDateTimeTo': nxt.isoformat()}))
        cursor = nxt
    async with httpx.AsyncClient(timeout=45, follow_redirects=True, limits=httpx.Limits(max_connections=4)) as client:
        semaphore = asyncio.Semaphore(4)
        async def load(dataset, params):
            async with semaphore:
                return dataset, await _get(client, dataset, params)
        groups = await asyncio.gather(*(load(dataset, params) for dataset, params in jobs))
    actuals, forecasts = [], []
    actual_seen, forecast_seen = set(), set()
    for dataset, rows in groups:
        for row in rows:
            if dataset == 'FUELHH' and row.get('fuelType') != 'WIND':
                continue
            fields = ['startTime', 'publishTime', 'generation'] + (['fuelType'] if dataset == 'FUELHH' else [])
            reduced = {k: row[k] for k in fields if k in row}
            key = tuple(str(reduced.get(k)) for k in fields)
            seen = actual_seen if dataset == 'FUELHH' else forecast_seen
            if key not in seen:
                seen.add(key)
                (actuals if dataset == 'FUELHH' else forecasts).append(reduced)
    return actuals, forecasts
