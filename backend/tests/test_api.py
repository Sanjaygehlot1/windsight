from fastapi.testclient import TestClient
import app.main as api


def test_validations_health_and_cutoff_response(monkeypatch):
    monkeypatch.setattr(api, '_cache', ([{'startTime': '2026-01-02T00:00Z', 'fuelType': 'WIND', 'generation': 100}], [{'startTime': '2026-01-02T00:00Z', 'publishTime': '2026-01-01T12:30Z', 'generation': 120}], '2026-10-25T00:00:00Z', 'snapshot'))
    client = TestClient(api.app)
    assert client.get('/api/health').status_code == 200
    assert client.get('/api/dashboard?cutoff_hour=24').status_code == 422
    assert client.get('/api/dashboard?cutoff_minute=-1').status_code == 422
    assert client.get('/api/dashboard?cutoff_hour=12').json()['periods'][0]['forecastMW'] is None
    data = client.get('/api/dashboard?cutoff_hour=12&cutoff_minute=30').json()
    assert data['periods'][0]['forecastMW'] == 120
    assert data['dataMode'] == 'snapshot'
    assert data['decisionEnd'] == '2026-01-31'


def test_upstream_error_is_not_replaced_with_sample_values(monkeypatch):
    monkeypatch.setattr(api, '_cache', None)
    monkeypatch.setattr(api, 'read_snapshot', lambda: None)
    async def fail():
        raise api.UpstreamError('Elexon is unavailable')
    monkeypatch.setattr(api, 'retrieve_month', fail)
    response = TestClient(api.app).get('/api/dashboard')
    assert response.status_code == 502
    assert response.json() == {'detail': 'Elexon is unavailable'}


def test_empty_upstream_response_is_an_error(monkeypatch):
    monkeypatch.setattr(api, '_cache', None)
    monkeypatch.setattr(api, 'read_snapshot', lambda: None)
    async def empty():
        return [], []
    monkeypatch.setattr(api, 'retrieve_month', empty)
    assert TestClient(api.app).get('/api/dashboard').status_code == 502


def test_real_snapshot_has_only_eligible_forecasts():
    snapshot = api.read_snapshot()
    assert snapshot is not None, 'Generate the documented Elexon snapshot before shipping'
    actuals, forecasts, _, _ = snapshot
    from app.analytics import analyze, parse_time
    result = analyze(actuals, forecasts)
    assert len(actuals) == 1488
    assert result['metrics']['matchedPeriods'] > 0
    assert result['metrics']['actualPeriods'] == 1488
    assert all(p['publishTime'] is None or parse_time(p['publishTime']) <= parse_time(p['cutoff']) for p in result['periods'])
    assert all(r['fuelType'] == 'WIND' for r in actuals)
