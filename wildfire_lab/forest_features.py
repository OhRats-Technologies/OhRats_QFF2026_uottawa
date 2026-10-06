"""Strict prior-year/epoch joins and matched fixed feature panels."""
import numpy as np
import pandas as pd

WEATHER=['annual_mean_temp_c','summer_mean_temp_c','annual_precip_mm','summer_precip_mm']
STRUCTURE=['forest_closure','forest_biomass','forest_age','spruce_pine_share_of_three_species']
MEMORY=['lag_reported_fire_area_ha','prior_epoch_biomass_change_per_year']
POOL=WEATHER+STRUCTURE+MEMORY


def join(table, rows):
    """No future-epoch interpolation and no positional shift across year gaps."""
    table=table.sort_values('year').copy()
    context=pd.DataFrame(rows).set_index('epoch')
    epochs=sorted(context.index)
    table['forest_epoch']=[max(e for e in epochs if e<year) for year in table.year]
    for column in STRUCTURE+['prior_epoch_biomass_change_per_year']:
        table[column]=table.forest_epoch.map(context[column])
    table['forest_age_epoch']=table.forest_epoch.map(context['forest_age_epoch'])
    table['forest_age_staleness_years']=table.year-table.forest_age_epoch
    areas=table.set_index('year').total_observed_size_ha
    table['lag_fire_year']=table.year-1
    table['lag_reported_fire_area_ha']=table.lag_fire_year.map(areas)
    table['zero']=0.
    table['calendar_linear']=table.year-1988
    table['calendar_square']=table.calendar_linear**2
    table['calendar_cube']=table.calendar_linear**3
    table['calendar_epoch']=table.forest_epoch
    return table


def panels(choices):
    pool=lambda name:[POOL[i] for i in choices[name]]
    interleaved=[column for pair in zip(WEATHER,STRUCTURE) for column in pair]
    return dict(weather=WEATHER,structure=STRUCTURE,
        weather_structure=WEATHER+STRUCTURE,zero8=WEATHER+['zero']*4,
        calendar8=WEATHER+['calendar_linear','calendar_square','calendar_cube','calendar_epoch'],
        interleaved8=interleaved,all10=POOL,zero10=WEATHER+['zero']*6,
        mi4=pool('mi'),exact4=pool('exact'),sqd4=pool('sqd'),uniform4=pool('uniform'))
