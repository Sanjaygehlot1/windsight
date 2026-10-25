import asyncio
import httpx
import pytest
import app.elexon as elexon


def test_ingestion_queries_dates_filters_wind_and_deduplicates(monkeypatch):
    calls = []
    async def fake_get(client, dataset, params):
        calls.append((dataset, params))
        if dataset == 'FUELHH':
            assert 'publishDateTimeFrom' not in params
            return [{'startTime': '2026-01-02T00:00Z', 'publishTime': '2026-01-02T00:30Z', 'generation': 100, 'fuelType': 'WIND'}, {'fuelType': 'CCGT', 'generation': 900}]
        return [{'startTime': '2026-01-02T00:00Z', 'publishTime': '2026-01-01T10:00Z', 'generation': 120}]
    monkeypatch.setattr(elexon, '_get', fake_get)
    actual, forecast = asyncio.run(elexon.retrieve_month())
    assert len(actual) == len(forecast) == 1
    actual_calls = [p for d, p in calls if d == 'FUELHH']
    assert len(actual_calls) == 31
    assert actual_calls[0]['settlementDateFrom'] == '2026-01-02'
    assert actual_calls[-1]['settlementDateTo'] == '2026-02-01'
    assert all(p['fuelType'] == 'WIND' for p in actual_calls)
    assert any(p.get('publishDateTimeFrom', '').startswith('2025-12-29') for _, p in calls)


def test_transient_error_retries_and_invalid_payload_does_not(monkeypatch):
    waits = []
    async def no_wait(delay):
        waits.append(delay)
    monkeypatch.setattr(elexon.asyncio, 'sleep', no_wait)
    count = 0
    def response(request):
        nonlocal count
        count += 1
        return httpx.Response(503) if count == 1 else httpx.Response(200, json=[{'generation': 100}])
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(response)) as client:
            return await elexon._get(client, 'FUELHH', {})
    assert asyncio.run(run()) == [{'generation': 100}]
    assert waits == [1]
    async def invalid():
        async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={'error': 'bad'}))) as client:
            await elexon._get(client, 'WINDFOR', {})
    with pytest.raises(elexon.UpstreamError):
        asyncio.run(invalid())
