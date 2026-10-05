"""Annual climate coverage and lag sensitivities with fixed predictors."""

import numpy as np
import pandas as pd

from wildfire_lab.annual_classical import errors, fit_predict
from wildfire_lab.annual_data import climate_years
from wildfire_lab.annual_quantum import kernel_fold, predict_cached


def complete_days(weather):
    """Unknown missing-day counts are excluded, not assumed to be complete."""
    clean = weather.copy()
    sources = {
        'missing_mean_temp_days': ['mean_temp_c', 'heating_degree_days', 'cooling_degree_days'],
        'missing_precip_days': ['total_precip_mm'],
        'missing_snowfall_days': ['snowfall_cm'],
        'missing_max_temp_days': ['highest_max_temp_c'],
        'missing_min_temp_days': ['lowest_min_temp_c'],
    }
    counts = {}
    for field, columns in sources.items():
        for column in columns:
            mask = clean[column].notna() & ~clean[field].eq(0)
            counts[column] = int(mask.sum())
            clean.loc[mask, column] = np.nan
    return clean, counts


def training_roster(weather, first, last, fraction=.8):
    """Four-feature eligibility over training years; validation never selects IDs."""
    years = pd.to_datetime(weather.month).dt.year
    frame = weather[years.between(first, last)].copy()
    frame['year'] = years.loc[frame.index]
    frame['calendar_month'] = pd.to_datetime(frame.month).dt.month
    all_months = frame.groupby(['climate_id', 'year'])[['mean_temp_c', 'total_precip_mm']].count()
    summer = frame[frame.calendar_month.isin([6, 7, 8])].groupby(
        ['climate_id', 'year'])[['mean_temp_c', 'total_precip_mm']].count()
    counts = all_months.join(summer, rsuffix='_summer').fillna(0)
    eligible = ((counts.mean_temp_c >= 9) & (counts.total_precip_mm == 12)
                & (counts.mean_temp_c_summer == 3) & (counts.total_precip_mm_summer == 3))
    frequency = eligible.groupby('climate_id').sum() / (last - first + 1)
    return sorted(frequency[frequency >= fraction].index.tolist())


def context_table(labels, weather, condition, first, last):
    metadata = {}
    if condition == 'same_year_zero_missing_days':
        weather, metadata['excluded_partial_or_unknown_day_measurements'] = complete_days(weather)
    elif condition == 'same_year_training_roster':
        roster = training_roster(weather, first, last)
        if not roster:
            raise ValueError('No station qualifies for the training-only roster')
        weather = weather[weather.climate_id.isin(roster)]
        metadata.update(roster=roster, roster_count=len(roster), roster_years=[first, last])
    climate = climate_years(weather, 1987, 2018)
    if condition == 'previous_year_original':
        climate['year'] += 1
    label_columns = ['year', 'mean_reported_size_ha']
    table = labels[label_columns].merge(climate, on='year', validate='one_to_one')
    return table, metadata


def screen(labels, weather, parent, plan, output):
    output.mkdir(parents=True)
    results, datasets, resources = [], [], []
    features = parent['four_feature_subset']
    for condition in plan['conditions']:
        for outer, fold in enumerate(parent['development_folds']):
            first, last, valid_first, valid_last = fold
            table, metadata = context_table(labels, weather, condition, first, last)
            directory = output / condition / f'fold-{outer}'
            directory.mkdir(parents=True)
            table.to_csv(directory / 'annual.csv', index=False)
            datasets.append(dict(condition=condition, fold=fold, metadata=metadata,
                                 missing_predictors=int(table[features].isna().sum().sum()),
                                 station_counts={name: table[name + '_stations'].astype(int).tolist()
                                                 for name in features},
                                 years=table.year.tolist()))
            train = table[table.year.between(first, last)]
            valid = table[table.year.between(valid_first, valid_last)]
            x, cross = train[features].to_numpy(), valid[features].to_numpy()
            y, actual = train.mean_reported_size_ha.to_numpy(), valid.mean_reported_size_ha.to_numpy()
            kernel = kernel_fold(x, cross, y, directory / 'kernel', reps=1, amplitude=np.pi / 2)
            resources.append(dict(condition=condition, fold=fold, **kernel[-1]))
            predictions = {
                'fixed_ridge': fit_predict('ridge', x, cross, y, dict(alpha=1.)),
                'fixed_rbf': fit_predict('rbf', x, cross, y, dict(C=1., epsilon=.2)),
                'fixed_qsvr': predict_cached(*kernel[:4], dict(C=1., epsilon=.2)),
            }
            for model, prediction in predictions.items():
                results.append(dict(condition=condition, model=model, features=features,
                                    fold=fold, years=valid.year.tolist(), actual_ha=actual.tolist(),
                                    predicted_ha=prediction.tolist(), **errors(actual, prediction)))
    return results, datasets, resources
