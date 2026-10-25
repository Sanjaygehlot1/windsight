from datetime import date
from app.analytics import analyze

def test_no_future_forecast_leakage():
    t='2026-01-02T00:00:00Z'
    rows=[{'startTime':t,'publishTime':'2026-01-01T10:00:00Z','generation':100},
          {'startTime':t,'publishTime':'2026-01-01T13:00:00Z','generation':190}]
    actual=[{'startTime':t,'fuelType':'WIND','generation':80}]
    result=analyze(actual,rows,start_day=date(2026,1,2),end_day=date(2026,1,2))
    point=result['periods'][0]
    assert point['forecastMW']==100
    assert point['errorMW']==20
    assert result['metrics']['matchedPeriods']==1
    assert result['metrics']['coveragePct']==round(100/48,2)

def test_missing_forecast_is_not_zero():
    result=analyze([{'startTime':'2026-01-01T00:00Z','fuelType':'WIND','generation':100}],[],start_day=date(2026,1,1),end_day=date(2026,1,1))
    assert result['metrics']['maeMW'] is None
    assert result['metrics']['matchedPeriods']==0

def test_only_wind_actuals():
    rows=[{'startTime':'2026-01-02T00:00Z','fuelType':'CCGT','generation':1000},
          {'startTime':'2026-01-02T00:00Z','fuelType':'WIND','generation':80}]
    fc=[{'startTime':'2026-01-02T00:00Z','publishTime':'2026-01-01T11:00Z','generation':100}]
    result=analyze(rows,fc,start_day=date(2026,1,2),end_day=date(2026,1,2))
    assert result['metrics']['maeMW']==20
