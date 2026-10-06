"""Nested measured-feature pools; strict dated joins from published source summaries."""
import pandas as pd
from wildfire_lab.forest_features import POOL

EXTRA_WEATHER = ['spring_precip_mm', 'annual_snowfall_cm', 'annual_highest_max_temp_c',
                 'annual_lowest_min_temp_c', 'annual_heating_degree_days',
                 'annual_cooling_degree_days']
SPECIES = ['broadleaf_crown_closure', 'black_spruce_crown_closure', 'jack_pine_crown_closure']
FEATURES = POOL + EXTRA_WEATHER + SPECIES + ['lag_recorded_incidents']


def expand(table, summary):
    table = table.copy()
    for column, layer in zip(SPECIES, ['broadleaf', 'black_spruce', 'jack_pine']):
        rows = [r for r in summary['rows'] if r['layer'] == layer and r['model_eligible']]
        values = {r['epoch']: r['mean'] for r in rows}
        epochs = [max(e for e in values if e < year) for year in table.year]
        table[column] = [values[e] for e in epochs]
        assert epochs == table.forest_epoch.tolist()
    counts = table.set_index('year').recorded_incidents
    table['lag_recorded_incidents'] = (table.year-1).map(counts)
    return table
