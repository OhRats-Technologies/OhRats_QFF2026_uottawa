"""Audit reported-size boundaries without changing the frozen incident target."""
from collections import Counter
from decimal import Decimal
from math import isfinite
from statistics import median

from wildfire_lab.nfdb import incidents,records


def training_sizes(archive,plan):
    start,end=plan['years']
    if end>2018:raise ValueError('Training-period audit only')
    threshold=Decimal(plan['target_threshold_ha'])
    accepted,excluded=incidents(archive,plan['agency'],start,end,float(threshold))
    lookup={r['incident_id']:r for r in accepted};sizes={}
    for row in records(archive):
        if row['SRC_AGENCY']!=plan['agency'] or not start<=int(row['YEAR'])<=end:continue
        key=row['NFDBFIREID']
        if key not in lookup:continue
        value=Decimal(row['SIZE_HA'])
        if not value.is_finite() or value<0:raise ValueError('Invalid accepted size')
        assert key not in sizes and int(value>=threshold)==lookup[key]['target']
        sizes[key]=dict(year=int(row['YEAR']),size=value,target=lookup[key]['target'])
    assert sizes.keys()==lookup.keys()
    return sizes,excluded


def select_cohort(source,rows,years):
    selected={}
    for row in rows:
        key=row['incident_id'];year=int(row['year'])
        if not years[0]<=year<=years[1]:raise ValueError('Cohort includes non-training years')
        if key in selected or key not in source:raise ValueError('Duplicate or unknown incident')
        record=source[key]
        if year!=record['year'] or int(row['target'])!=record['target']:raise ValueError('Changed frozen label')
        selected[key]=record
    return selected


def summarize(source,plan):
    values=[r['size'] for r in source.values()]
    if not values:raise ValueError('Empty label cohort')
    threshold=Decimal(plan['target_threshold_ha']);positive=[v for v in values if v>0]
    counts=Counter(values);annual=[]
    for year in range(plan['years'][0],plan['years'][1]+1):
        ys=[r['size'] for r in source.values() if r['year']==year]
        n=len(ys);above=sum(v>=threshold for v in ys)
        annual.append(dict(year=year,rows=n,positive_rows=above,positive_fraction=above/n if n else None,
                           zero_size_rows=sum(v==0 for v in ys),exact_threshold_rows=sum(v==threshold for v in ys)))
    bands=[]
    for raw in plan['boundary_half_widths_ha']:
        width=Decimal(raw);lower,upper=threshold-width,threshold+width
        near=[v for v in values if lower<=v<upper]
        bands.append(dict(half_width_ha=raw,lower_inclusive_ha=str(lower),upper_exclusive_ha=str(upper),
                          rows=len(near),negative_rows=sum(v<threshold for v in near),positive_rows=sum(v>=threshold for v in near)))
    return dict(rows=len(values),positive_rows=sum(v>=threshold for v in values),
        positive_fraction=sum(v>=threshold for v in values)/len(values),zero_size_rows=counts[Decimal(0)],
        exact_threshold_rows=counts[threshold],strictly_above_threshold_rows=sum(v>threshold for v in values),
        median_size_ha=float(median(values)),
        thresholds=[dict(threshold_ha=raw,rows_ge=sum(v>=Decimal(raw) for v in values)) for raw in plan['descriptive_thresholds_ha']],
        boundary_bands=bands,positive_size_rows=len(positive),
        positive_size_numeric_multiples=[dict(step_ha=raw,rows=sum(v%Decimal(raw)==0 for v in positive)) for raw in plan['numeric_steps_ha']],
        most_common_recorded_sizes=[dict(size_ha=format(v,'f'),rows=n) for v,n in sorted(counts.items(),key=lambda p:(-p[1],p[0]))[:plan['top_recorded_sizes']]],
        annual=annual)


def retention(before,after):
    if not after.keys()<=before.keys():raise ValueError('Cohort is not a subset')
    return {str(label):dict(before_rows=sum(r['target']==label for r in before.values()),
        retained_rows=sum(r['target']==label for r in after.values()),
        excluded_rows=sum(r['target']==label for k,r in before.items() if k not in after)) for label in [0,1]}


def geographic_retention(before,after,edges):
    """Describe a fixed cohort's latitude-associated exclusions, not their cause."""
    if len(edges)<2 or any(a>=b for a,b in zip(edges,edges[1:])):
        raise ValueError('Latitude edges must increase')
    if not after.keys()<=before.keys():raise ValueError('Cohort is not a subset')
    for key,row in before.items():
        if row['target'] not in [0,1] or not isfinite(row['latitude']) or not edges[0]<=row['latitude']<=edges[-1]:
            raise ValueError('Invalid label or latitude')
        if key in after and any(after[key][field]!=row[field] for field in ['target','latitude']):
            raise ValueError('Changed cohort record')
    def summary(rows):
        latitudes=[row['latitude'] for row in rows.values()]
        return dict(rows=len(rows),positive_rows=sum(row['target'] for row in rows.values()),
            median_latitude=median(latitudes) if latitudes else None,
            minimum_latitude=min(latitudes) if latitudes else None,
            maximum_latitude=max(latitudes) if latitudes else None)
    def counts(first,second):
        result=retention(first,second)
        for row in result.values():
            row['excluded_fraction']=row['excluded_rows']/row['before_rows'] if row['before_rows'] else None
        return result
    bins=[]
    for i,(lower,upper) in enumerate(zip(edges,edges[1:])):
        last=i==len(edges)-2
        selected={key:row for key,row in before.items() if lower<=row['latitude'] and
                  (row['latitude']<upper or last and row['latitude']==upper)}
        retained={key:row for key,row in selected.items() if key in after}
        bins.append(dict(lower_inclusive=lower,upper=upper,upper_inclusive=last,by_target=counts(selected,retained)))
    excluded={key:row for key,row in before.items() if key not in after}
    assert sum(sum(c['before_rows'] for c in b['by_target'].values()) for b in bins)==len(before)
    return dict(before=summary(before),retained=summary(after),excluded=summary(excluded),
                by_target=counts(before,after),latitude_bins=bins)
