from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from math import isfinite, sqrt
from zoneinfo import ZoneInfo

LONDON = ZoneInfo('Europe/London')
DECISION_START = date(2026, 1, 1)
DECISION_END = date(2026, 1, 31)
DELIVERY_START = DECISION_START + timedelta(days=1)
DELIVERY_END = DECISION_END + timedelta(days=1)


def parse_time(value):
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('Timestamp must include timezone')
    return dt.astimezone(timezone.utc)


def iso(dt):
    return dt.isoformat().replace('+00:00', 'Z')


def cutoff_for(delivery_day, hour, minute=0):
    return datetime.combine(delivery_day - timedelta(days=1), time(hour, minute), LONDON).astimezone(timezone.utc)


def summarize(points):
    errors = [p['errorMW'] for p in points if p['errorMW'] is not None]
    absolute = sorted(abs(e) for e in errors)
    count = len(points)
    forecasts = [p['forecastMW'] for p in points if p['forecastMW'] is not None]
    actuals = [p['actualMW'] for p in points if p['actualMW'] is not None]
    def avg(values):
        return round(sum(values) / len(values), 2) if values else None
    p90 = None
    if absolute:
        pos = (len(absolute) - 1) * .9
        lo = int(pos)
        hi = min(lo + 1, len(absolute) - 1)
        p90 = round(absolute[lo] + (absolute[hi] - absolute[lo]) * (pos - lo), 2)
    return {
        'matchedPeriods': len(errors), 'totalPeriods': count,
        'forecastPeriods': len(forecasts), 'actualPeriods': len(actuals),
        'coveragePct': round(100 * len(errors) / count, 2) if count else 0,
        'maeMW': avg(absolute),
        'rmseMW': round(sqrt(sum(e * e for e in errors) / len(errors)), 2) if errors else None,
        'biasMW': avg(errors), 'p90AbsErrorMW': p90,
        'meanForecastMW': avg(forecasts), 'meanActualMW': avg(actuals),
        'matchedMeanActualMW': avg([p['actualMW'] for p in points if p['errorMW'] is not None]),
        'forecastEnergyMWh': round(sum(forecasts) * .5, 2) if len(forecasts) == count and count else None,
        'actualEnergyMWh': round(sum(actuals) * .5, 2) if len(actuals) == count and count else None,
    }


def analyze(actual_rows, forecast_rows, cutoff_hour=12, start_day=DELIVERY_START,
            end_day=DELIVERY_END, cutoff_minute=0):
    if not 0 <= cutoff_hour <= 23 or not 0 <= cutoff_minute <= 59:
        raise ValueError('Invalid decision cutoff')
    if start_day > end_day:
        raise ValueError('Invalid delivery date range')
    actual_versions = defaultdict(lambda: defaultdict(set))
    forecast_versions = defaultdict(lambda: defaultdict(set))
    invalid = 0
    for rows, target, actual in [(actual_rows, actual_versions, True), (forecast_rows, forecast_versions, False)]:
        for row in rows:
            if not isinstance(row, dict):
                invalid += 1
                continue
            if actual and row.get('fuelType') != 'WIND':
                continue
            try:
                stamp = parse_time(row['startTime'])
                value = float(row['generation'])
                if not isfinite(value) or value < 0:
                    raise ValueError('Invalid generation')
                pub = parse_time(row['publishTime']) if row.get('publishTime') else (
                    datetime.min.replace(tzinfo=timezone.utc) if actual else None
                )
                if pub is None:
                    raise ValueError('Forecast requires publication time')
                target[stamp][pub].add(value)
            except (ValueError, TypeError, KeyError, OverflowError):
                invalid += 1
    points, daily = [], []
    conflicts = 0
    day = start_day
    while day <= end_day:
        cutoff = cutoff_for(day, cutoff_hour, cutoff_minute)
        period = datetime.combine(day, time(0), LONDON).astimezone(timezone.utc)
        end = datetime.combine(day + timedelta(days=1), time(0), LONDON).astimezone(timezone.utc)
        day_points = []
        while period < end:
            candidates = forecast_versions.get(period, {})
            eligible = [pub for pub in candidates if pub <= cutoff]
            publication = max(eligible) if eligible else None
            forecast_values = candidates[publication] if publication is not None else set()
            versions = actual_versions.get(period, {})
            actual_publication = max(versions) if versions else None
            actual_values = versions[actual_publication] if actual_publication is not None else set()
            conflicts += int(len(forecast_values) > 1) + int(len(actual_values) > 1)
            forecast = next(iter(forecast_values)) if len(forecast_values) == 1 else None
            actual = next(iter(actual_values)) if len(actual_values) == 1 else None
            point = {
                'startTime': iso(period), 'deliveryDate': day.isoformat(),
                'decisionDate': (day - timedelta(days=1)).isoformat(), 'cutoff': iso(cutoff),
                'forecastMW': forecast, 'actualMW': actual,
                'publishTime': iso(publication) if publication is not None else None,
                'actualPublishTime': iso(actual_publication) if actual_publication and actual_publication.year > 1 else None,
                'errorMW': round(forecast - actual, 6) if forecast is not None and actual is not None else None,
            }
            day_points.append(point)
            period += timedelta(minutes=30)
        points.extend(day_points)
        daily.append({'date': day.isoformat(), 'decisionDate': (day - timedelta(days=1)).isoformat(), **summarize(day_points)})
        day += timedelta(days=1)
    return {
        'periods': points, 'daily': daily, 'metrics': summarize(points),
        'cutoffHourUK': cutoff_hour, 'cutoffMinuteUK': cutoff_minute,
        'decisionStart': (start_day - timedelta(days=1)).isoformat(),
        'decisionEnd': (end_day - timedelta(days=1)).isoformat(),
        'deliveryStart': start_day.isoformat(), 'deliveryEnd': end_day.isoformat(),
        'quality': {'invalidRowsSkipped': invalid, 'conflictingPeriodsExcluded': conflicts},
        'forecastResolutionMinutes': min((int((b-a).total_seconds() / 60) for a, b in zip(sorted(forecast_versions), sorted(forecast_versions)[1:])), default=None),
        'methodology': 'For each delivery half-hour, select the latest WINDFOR publication at or before the configured cutoff on the previous UK calendar day. Error = forecast minus actual. Metrics use matched half-hours only.',
    }
