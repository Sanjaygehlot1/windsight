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


def test_january_means_decision_dates_not_delivery_dates():
    result = analyze([], [])
    assert len(result['periods']) == 31 * 48
    assert result['periods'][0]['decisionDate'] == '2026-01-01'
    assert result['periods'][0]['startTime'] == '2026-01-02T00:00:00Z'
    assert result['periods'][-1]['decisionDate'] == '2026-01-31'
    assert result['periods'][-1]['startTime'] == '2026-02-01T23:30:00Z'


def test_exact_cutoff_and_minute_selection():
    t = '2026-01-02T00:00:00Z'
    forecasts = [
        {'startTime': t, 'publishTime': '2026-01-01T11:59:00Z', 'generation': 80},
        {'startTime': t, 'publishTime': '2026-01-01T12:30:00Z', 'generation': 90},
        {'startTime': t, 'publishTime': '2026-01-01T12:30:01Z', 'generation': 120},
    ]
    result = analyze([], forecasts, cutoff_hour=12, cutoff_minute=30)
    assert result['periods'][0]['forecastMW'] == 90
    assert result['periods'][0]['cutoff'] == '2026-01-01T12:30:00Z'


def test_metrics_matched_only_and_partial_energy_is_not_a_day_total():
    actual = [{'startTime': f'2026-01-02T{t}Z', 'fuelType': 'WIND', 'generation': v} for t, v in [('00:00', 100), ('00:30', 100), ('01:00', 999)]]
    forecasts = [{'startTime': f'2026-01-02T{t}Z', 'publishTime': '2026-01-01T10:00Z', 'generation': v} for t, v in [('00:00', 110), ('00:30', 80)]]
    stats = analyze(actual, forecasts)['metrics']
    assert stats['maeMW'] == 15
    assert stats['rmseMW'] == 15.81
    assert stats['biasMW'] == -5
    assert stats['p90AbsErrorMW'] == 19
    assert stats['matchedMeanActualMW'] == 100
    assert stats['matchedPeriods'] == 2
    assert stats['actualEnergyMWh'] is None
    assert stats['forecastEnergyMWh'] is None


def test_hourly_forecasts_do_not_fill_missing_half_hours():
    fc = [{'startTime': f'2026-01-02T{h:02d}:00Z', 'publishTime': '2026-01-01T10:00Z', 'generation': 120} for h in range(24)]
    actual = [{'startTime': f'2026-01-02T{h:02d}:{m:02d}Z', 'fuelType': 'WIND', 'generation': 100} for h in range(24) for m in [0, 30]]
    result = analyze(actual, fc, start_day=date(2026, 1, 2), end_day=date(2026, 1, 2))
    assert result['forecastResolutionMinutes'] == 60
    assert result['metrics']['coveragePct'] == 50
    assert result['metrics']['matchedPeriods'] == 24
    assert result['periods'][1]['forecastMW'] is None
    assert result['metrics']['actualEnergyMWh'] == 2400


def test_latest_actual_revision_and_duplicate_order_independence():
    t = '2026-01-02T00:00Z'
    actual = [{'startTime': t, 'publishTime': '2026-01-02T00:30Z', 'fuelType': 'WIND', 'generation': 100}, {'startTime': t, 'publishTime': '2026-01-05T00:00Z', 'fuelType': 'WIND', 'generation': 110}]
    fc = [{'startTime': t, 'publishTime': '2026-01-01T10:00Z', 'generation': 120}]
    a = analyze(actual, fc + fc)
    b = analyze(list(reversed(actual)), fc)
    assert a == b
    assert a['periods'][0]['actualMW'] == 110
    assert a['metrics']['maeMW'] == 10


def test_conflicting_equal_publications_are_excluded():
    fc = [{'startTime': '2026-01-02T00:00Z', 'publishTime': '2026-01-01T10:00Z', 'generation': v} for v in [100, 200]]
    result = analyze([], fc)
    assert result['periods'][0]['forecastMW'] is None
    assert result['quality']['conflictingPeriodsExcluded'] == 1


def test_nonfinite_negative_and_naive_values_are_rejected_but_zero_is_valid():
    values = [float('nan'), float('inf'), -10, None, 'bad', 0]
    actual = [{'startTime': f'2026-01-02T0{i}:00Z', 'fuelType': 'WIND', 'generation': v} for i, v in enumerate(values)]
    actual += [{'startTime': '2026-01-02T06:00', 'fuelType': 'WIND', 'generation': 10}]
    result = analyze(actual, [])
    assert result['metrics']['actualPeriods'] == 1
    assert result['periods'][10]['actualMW'] == 0
    assert result['quality']['invalidRowsSkipped'] == 6


def test_invalid_cutoff_rejected():
    import pytest
    with pytest.raises(ValueError):
        analyze([], [], cutoff_hour=24)
    with pytest.raises(ValueError):
        analyze([], [], cutoff_minute=60)
