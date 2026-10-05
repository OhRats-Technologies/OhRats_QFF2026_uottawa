"""Shared incident covariate joins; callers control the permitted year window."""
import math
from collections import Counter


def weather_rows(incidents,index,lags,max_distance_km=150):
    joined=[];drops=Counter()
    for incident in incidents:
        context=[(lag,index.query(incident,lag,max_distance_km)) for lag in lags]
        if any(result is None for _,result in context):
            drops['weather_outside_150km_or_missing_month']+=1
            continue
        month=int(incident['date'][5:7])
        row=dict(incident,month_sin=math.sin(2*math.pi*month/12),month_cos=math.cos(2*math.pi*month/12))
        for lag,(values,metadata) in context:
            row.update(values,**{f'station_lag{lag}':metadata['climate_id'],f'weather_distance_lag{lag}':metadata['distance_km']})
        joined.append(row)
    return joined,dict(drops)
