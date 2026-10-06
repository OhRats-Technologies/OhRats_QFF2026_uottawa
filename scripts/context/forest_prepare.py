"""Audit derived Ontario arrays and assemble training-only forest/memory inputs."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from wildfire_lab.forest_features import join


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def derive(root):
    source=json.loads((root/'docs/data/forest_feature_sources.json').read_text())
    summary=json.loads((root/'docs/data/forest_feature_summary.json').read_text())
    for name,expected in source['derived_arrays_sha256'].items():
        if digest(root/name)!=expected:
            raise ValueError('Derived numerical source array changed')
    records={(r['epoch'],r['layer']):r for r in source['records']}
    stats={(r['epoch'],r['layer']):r for r in summary['rows']}
    paths={Path(name).parent.name:root/name for name in source['derived_arrays_sha256']}
    def load(epoch,layer):
        with np.load(paths[records[(epoch,layer)]['name']]) as f:
            return f['values'],f['valid']
    epochs=sorted({epoch for epoch,_ in records})
    rows=[]
    for epoch in epochs:
        species=[load(epoch,layer) for layer in ['broadleaf','black_spruce','jack_pine']]
        common=np.logical_and.reduce([valid for _,valid in species])
        amounts=np.array([values[common].sum(dtype=np.float64) for values,_ in species])
        share=float(amounts[1:].sum()/amounts.sum()) if amounts.sum()>0 else None
        age_epoch=max(e for e in epochs if e<=epoch and stats[(e,'age')]['model_eligible'])
        row=dict(epoch=epoch,forest_closure=stats[(epoch,'closure')]['mean'],
            forest_biomass=stats[(epoch,'biomass')]['mean'],
            forest_age=stats[(age_epoch,'age')]['mean'],forest_age_epoch=age_epoch,
            spruce_pine_share_of_three_species=share,species_common_samples=int(common.sum()),
            prior_epoch_biomass_change_per_year=None,biomass_pair_samples=None)
        previous=[e for e in epochs if e<epoch]
        if previous:
            a,av=load(epoch,'biomass');b,bv=load(previous[-1],'biomass')
            valid=av & bv
            change=a[valid].astype(float)-b[valid].astype(float)
            row.update(prior_epoch_biomass_change_per_year=float(change.mean()/(epoch-previous[-1])),
                       biomass_pair_samples=int(valid.sum()),previous_biomass_epoch=previous[-1])
        rows.append(row)
    return dict(rows=rows,source_sha256=digest(root/'docs/data/forest_feature_sources.json'),
        summary_sha256=digest(root/'docs/data/forest_feature_summary.json'),
        interpretation='Selected-species share is spruce+pine/(broadleaf+spruce+pine), not all-conifer fraction, tree density, FBP fuel class or hazard. Biomass change uses the pairwise common footprint of two earlier epochs, not future-mask intersection or eventual recovery. Age uses only advertised-NEAREST epochs; latest eligible2000 remains stale thereafter.')


if __name__=='__main__':
    derived=derive(ROOT)
    annual=ROOT/'docs/data/annual_training.csv'
    table=pd.read_csv(annual)
    if table.year.tolist()!=list(range(1988,2019)):
        raise ValueError('Training-year boundary changed')
    table=join(table,derived['rows'])
    derived['annual_source_sha256']=digest(annual)
    derived['code_sha256']={name:digest(ROOT/name) for name in
                           ['scripts/context/forest_prepare.py','wildfire_lab/forest_features.py']}
    (ROOT/'docs/data/forest_feature_derived.json').write_text(json.dumps(derived,indent=2)+'\n')
    table.to_csv(ROOT/'docs/data/forest_expansion_training.csv',index=False)
    print(json.dumps(dict(rows=len(table),epoch_max=int(table.forest_epoch.max()),
        age_epoch_max=int(table.forest_age_epoch.max()),first_lag_missing=bool(pd.isna(table.lag_reported_fire_area_ha.iloc[0])),
        final_test_accessed=False),indent=2))
