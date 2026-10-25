import asyncio
from datetime import date, datetime, time, timedelta, timezone
import httpx

BASE = 'https://data.elexon.co.uk/bmrs/api/v1'

class UpstreamError(RuntimeError):
    pass

async def _get(client, dataset, start, end):
    url=f'{BASE}/datasets/{dataset}/stream'
    try:
        response=await client.get(url,params={'from':start.isoformat().replace('+00:00','Z'),
                                              'to':end.isoformat().replace('+00:00','Z')})
        response.raise_for_status()
        data=response.json()
        if isinstance(data,dict): data=data.get('data',[])
        if not isinstance(data,list): raise ValueError('Unexpected Elexon response')
        return data
    except (httpx.HTTPError,ValueError) as exc:
        raise UpstreamError(f'Elexon {dataset} fetch failed: {exc}') from exc

async def retrieve_month():
    # Query in small chunks to avoid server query-size limits; wind forecast
    # publication windows extend into Dec 2025 for Jan 1 deliveries.
    start=datetime(2025,12,29,tzinfo=timezone.utc)
    end=datetime(2026,2,2,tzinfo=timezone.utc)
    windows=[]
    cursor=start
    while cursor<end:
        nxt=min(cursor+timedelta(days=1),end)
        windows.append((cursor,nxt));cursor=nxt
    async with httpx.AsyncClient(timeout=35.0,follow_redirects=True,
                                 limits=httpx.Limits(max_connections=5)) as client:
        semaphore=asyncio.Semaphore(4)
        async def guarded(dataset,s,e):
            async with semaphore:
                return await _get(client,dataset,s,e)
        actual_groups=await asyncio.gather(*(guarded('FUELHH',s,e) for s,e in windows))
        forecast_groups=await asyncio.gather(*(guarded('WINDFOR',s,e) for s,e in windows))
    return ([r for group in actual_groups for r in group],
            [r for group in forecast_groups for r in group])
