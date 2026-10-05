"""Province-year fire outcomes and equally weighted station climate summaries."""

from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd

from wildfire_lab.nfdb import numeric, records

FEATURES = (
    'annual_mean_temp_c', 'summer_mean_temp_c', 'annual_precip_mm',
    'summer_precip_mm', 'spring_precip_mm', 'annual_snowfall_cm',
    'annual_highest_max_temp_c', 'annual_lowest_min_temp_c',
    'annual_heating_degree_days', 'annual_cooling_degree_days',
)


def fire_years(rows, start=1988, end=2018):
    """Do not require a daily date, coordinate or weather match for annual labels."""
    rows = [row for row in rows if row['SRC_AGENCY'] == 'ON']
    ids = Counter(row['NFDBFIREID'].strip() for row in rows)
    annual = defaultdict(list)
    counts = defaultdict(Counter)
    exclusions = Counter()
    for row in rows:
        try:
            year = int(row['YEAR'])
        except ValueError:
            exclusions['invalid_year'] += 1
            continue
        if not start <= year <= end:
            continue
        identity = row['NFDBFIREID'].strip()
        if not identity or ids[identity] != 1:
            exclusions['blank_or_duplicate_identity'] += 1
            counts[year]['identity_exclusions'] += 1
            continue
        if row['PRESCRIBED'].strip() or row['FIRE_TYPE'].strip() == 'PB':
            exclusions['prescribed_code'] += 1
            counts[year]['prescribed_exclusions'] += 1
            continue
        counts[year]['recorded_incidents'] += 1
        size = numeric(row['SIZE_HA'])
        if size is None or size < 0:
            counts[year]['unknown_size_incidents'] += 1
        else:
            annual[year].append(size)
    output = []
    for year in range(start, end + 1):
        sizes = annual[year]
        year_counts = {name: counts[year][name] for name in (
            'recorded_incidents', 'unknown_size_incidents',
            'identity_exclusions', 'prescribed_exclusions')}
        output.append(dict(year=year, **year_counts, size_observed_incidents=len(sizes),
                           mean_reported_size_ha=np.mean(sizes) if sizes else np.nan,
                           total_observed_size_ha=sum(sizes) if sizes else np.nan))
    return pd.DataFrame(output), dict(exclusions)


def climate_years(frame, start=1988, end=2018):
    """Compute station-year summaries, then give eligible stations equal weight."""
    frame = frame.copy()
    dates = pd.to_datetime(frame['month'])
    frame['year'], frame['calendar_month'] = dates.dt.year, dates.dt.month
    frame = frame[frame['year'].between(start, end)]
    if frame.duplicated(['climate_id', 'month']).any():
        raise ValueError('Duplicate station-month observations')
    specs = [
        ('annual_mean_temp_c', 'mean_temp_c', None, 'mean', 9),
        ('summer_mean_temp_c', 'mean_temp_c', [6, 7, 8], 'mean', 3),
        ('annual_precip_mm', 'total_precip_mm', None, 'sum', 12),
        ('summer_precip_mm', 'total_precip_mm', [6, 7, 8], 'sum', 3),
        ('spring_precip_mm', 'total_precip_mm', [3, 4, 5], 'sum', 3),
        ('annual_snowfall_cm', 'snowfall_cm', None, 'sum', 12),
        ('annual_highest_max_temp_c', 'highest_max_temp_c', None, 'max', 12),
        ('annual_lowest_min_temp_c', 'lowest_min_temp_c', None, 'min', 12),
        ('annual_heating_degree_days', 'heating_degree_days', None, 'sum', 12),
        ('annual_cooling_degree_days', 'cooling_degree_days', None, 'sum', 12),
    ]
    output = pd.DataFrame(index=pd.Index(range(start, end + 1), name='year'))
    for name, source, months, operation, minimum in specs:
        selected = frame if months is None else frame[frame.calendar_month.isin(months)]
        station = selected.groupby(['year', 'climate_id'])[source].agg(
            value=operation, measured_months='count')
        station = station[station.measured_months >= minimum]
        summary = station.groupby('year').value.agg(['mean', 'count'])
        output[name] = summary['mean']
        output[name + '_stations'] = summary['count'].fillna(0)
    return output.reset_index()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(archive, weather, plan_path, output, start=1988, end=2018):
    """Create a separate immutable annual dataset; old incident caches are untouched."""
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    fires, excluded = fire_years(records(archive), start, end)
    climate = climate_years(pd.read_csv(weather, dtype={'climate_id': str}), start, end)
    table = fires.merge(climate, on='year', validate='one_to_one')
    if table.mean_reported_size_ha.isna().any():
        raise ValueError('A requested year has no observed eligible fire sizes')
    output.mkdir(parents=True)
    table.to_csv(output / 'annual.csv', index=False)
    manifest = dict(unit='Ontario province-year', years=[start, end], rows=len(table),
                    primary_target='mean_reported_size_ha', fire_exclusions=excluded,
                    source_sha256={'nfdb': digest(archive), 'weather': digest(weather)},
                    recipe_sha256=digest(__file__), plan_sha256=digest(plan_path),
                    table_sha256=digest(output / 'annual.csv'),
                    information='Same-year climate; retrospective annual estimation',
                    weather_policy='Equal eligible station weight; thresholds in frozen plan',
                    limitations=['Station network varies; equal station weight is not area weight',
                                 'Reported fires and sizes are not a complete final-area census',
                                 'Monthly measurements can contain partial-day coverage'])
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return table, manifest
