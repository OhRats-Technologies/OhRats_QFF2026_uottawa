"""Training-only station/month weather baselines; not official climate normals."""
import numpy as np
import pandas as pd
from wildfire_lab.weather import month_lag


class MonthlyBaseline:
    def __init__(self,path,train_end_year,min_samples=5):
        if train_end_year>2018:
            raise ValueError('Baseline fitting cannot consume final-test years')
        frame=pd.read_csv(path,dtype={'climate_id':str})
        dates=pd.to_datetime(frame.month)
        frame=frame.loc[dates.dt.year.between(1987,train_end_year)].copy()
        frame['calendar_month']=pd.to_datetime(frame.month).dt.month
        frame['log_precip']=np.log1p(frame.total_precip_mm.where(frame.total_precip_mm>=0))
        self.fields=['mean_temp_c','log_precip']
        group=frame.groupby(['climate_id','calendar_month'])[self.fields]
        self.means,self.counts=group.mean(),group.count()
        self.fallback=frame.groupby('calendar_month')[self.fields].mean()
        self.min_samples=min_samples
        self.metadata=dict(fit_latest_year=int(pd.to_datetime(frame.month).dt.year.max()),weather_rows=len(frame),
                           min_station_month_samples=min_samples,semantics='Estimated training-only station/month baseline, not official ECCC normals.')

    def attach(self,frame,lags=(1,2,3)):
        result=frame.copy();fallback_counts={}
        for lag in lags:
            months=frame.date.map(lambda day:int(month_lag(day,lag)[5:7]))
            keys=pd.MultiIndex.from_arrays([frame[f'station_lag{lag}'].astype(str),months])
            for field,suffix in [('mean_temp_c','temp_anomaly_c'),('log_precip','log_precip_anomaly')]:
                baseline=self.means[field].reindex(keys).to_numpy()
                count=self.counts[field].reindex(keys).fillna(0).to_numpy()
                use=(count>=self.min_samples)&np.isfinite(baseline)
                global_mean=months.map(self.fallback[field]).to_numpy()
                baseline=np.where(use,baseline,global_mean)
                observed=frame[f'lag{lag}_mean_temp_c'].to_numpy() if field=='mean_temp_c' else np.log1p(frame[f'lag{lag}_total_precip_mm'].where(frame[f'lag{lag}_total_precip_mm']>=0)).to_numpy()
                result[f'lag{lag}_{suffix}']=observed-baseline
                fallback_counts[f'lag{lag}_{suffix}']=int((~use).sum())
        return result,dict(self.metadata,fallback_counts=fallback_counts,rows=len(frame))
