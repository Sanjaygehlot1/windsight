from datetime import datetime, date, time, timedelta, timezone
from zoneinfo import ZoneInfo
from collections import defaultdict
from math import sqrt

LONDON = ZoneInfo('Europe/London')

def parse_time(value):
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('Timestamp must include timezone')
    return dt.astimezone(timezone.utc)

def cutoff_for(delivery_day: date, hour: int):
    decision_day = delivery_day - timedelta(days=1)
    return datetime.combine(decision_day, time(hour, 0), LONDON).astimezone(timezone.utc)

def analyze(actual_rows, forecast_rows, cutoff_hour=12, start_day=date(2026,1,1), end_day=date(2026,1,31)):
    actuals = {}
    for row in actual_rows:
        if row.get('fuelType') != 'WIND':
            continue
        try:
            stamp = parse_time(row['startTime'])
            value = float(row['generation'])
            if value < 0: continue
            actuals[stamp] = value
        except (ValueError, TypeError, KeyError):
            continue
    forecasts = defaultdict(list)
    for row in forecast_rows:
        try:
            stamp = parse_time(row['startTime'])
            pub = parse_time(row['publishTime'])
            value = float(row['generation'])
            if value < 0: continue
            forecasts[stamp].append((pub, value))
        except (ValueError, TypeError, KeyError):
            continue
    points = []
    day = start_day
    while day <= end_day:
        cutoff = cutoff_for(day, cutoff_hour)
        # UTC half-hours are aligned in January; UK local delivery day determines membership.
        period = datetime.combine(day, time(0), LONDON).astimezone(timezone.utc)
        end = datetime.combine(day + timedelta(days=1), time(0), LONDON).astimezone(timezone.utc)
        while period < end:
            eligible = [(pub, val) for pub, val in forecasts.get(period, []) if pub <= cutoff]
            selected = max(eligible, key=lambda p: p[0]) if eligible else None
            actual = actuals.get(period)
            points.append({
                'startTime': period.isoformat().replace('+00:00','Z'),
                'deliveryDate': day.isoformat(),
                'cutoff': cutoff.isoformat().replace('+00:00','Z'),
                'forecastMW': selected[1] if selected else None,
                'actualMW': actual,
                'publishTime': selected[0].isoformat().replace('+00:00','Z') if selected else None,
                'errorMW': (selected[1]-actual) if selected and actual is not None else None,
            })
            period += timedelta(minutes=30)
        day += timedelta(days=1)
    matched = [p for p in points if p['errorMW'] is not None]
    errors = [p['errorMW'] for p in matched]
    abs_errors = sorted(abs(e) for e in errors)
    def quantile(q):
        if not abs_errors: return None
        pos = (len(abs_errors)-1)*q
        lower = int(pos)
        upper = min(lower+1,len(abs_errors)-1)
        return abs_errors[lower] + (abs_errors[upper]-abs_errors[lower])*(pos-lower)
    def avg(xs): return sum(xs)/len(xs) if xs else None
    stats = {
        'matchedPeriods': len(matched),
        'totalPeriods': len(points),
        'forecastPeriods': sum(p['forecastMW'] is not None for p in points),
        'actualPeriods': sum(p['actualMW'] is not None for p in points),
        'coveragePct': round(100*len(matched)/len(points),2) if points else 0,
        'maeMW': round(avg(abs_errors),2) if errors else None,
        'rmseMW': round(sqrt(avg([e*e for e in errors])),2) if errors else None,
        'biasMW': round(avg(errors),2) if errors else None,
        'p90AbsErrorMW': round(quantile(.9),2) if errors else None,
        'meanShortfallMW': round(avg([max(0,e) for e in errors]),2) if errors else None,
        'forecastEnergyMWh': round(sum(p['forecastMW']*.5 for p in points if p['forecastMW'] is not None),2),
        'actualEnergyMWh': round(sum(p['actualMW']*.5 for p in points if p['actualMW'] is not None),2),
    }
    byday=[]
    for index in range((end_day-start_day).days+1):
        d=(start_day+timedelta(days=index)).isoformat()
        ps=[p for p in points if p['deliveryDate']==d]
        es=[p['errorMW'] for p in ps if p['errorMW'] is not None]
        byday.append({'date':d,'maeMW':round(avg([abs(e) for e in es]),2) if es else None,
                      'biasMW':round(avg(es),2) if es else None,'matched':len(es),
                      'actualMWh':round(sum(p['actualMW']*.5 for p in ps if p['actualMW'] is not None),2),
                      'forecastMWh':round(sum(p['forecastMW']*.5 for p in ps if p['forecastMW'] is not None),2)})
    return {'periods':points,'daily':byday,'metrics':stats,'cutoffHourUK':cutoff_hour,
            'methodology':'For each half-hour delivery start, use the latest forecast published no later than 12:00 (or configured hour) UK time on the previous calendar day. Error = forecast - actual, positive means forecast overestimated wind.'}
