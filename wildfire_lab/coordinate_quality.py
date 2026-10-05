"""Reported-coordinate concentration and chronological interpolation geometry."""
from collections import Counter
import hashlib
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
from wildfire_lab.evaluation import split
from wildfire_lab.spatial import coordinates

GRID_STEPS=(.1,.01,.001)
GRID_ATOL_DEGREES=1e-8


def coordinate_keys(frame):return list(zip(frame.latitude,frame.longitude))


def datum_check(frame,archive,expected_sha256):
    """Metadata interpretation and local-operation sensitivity, not a correction."""
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=expected_sha256:
        raise ValueError('Changed NFDB source archive')
    with zipfile.ZipFile(archive) as z:
        name,=[n for n in z.namelist() if n.endswith('.txt.xml')]
        raw=z.read(name)
    tree=ET.fromstring(raw)
    fields={node.findtext('attrlabl'):dict(description=node.findtext('attrdef'),source=node.findtext('attrdefs'))
        for node in tree.findall('.//attr') if node.findtext('attrlabl') in ('LATITUDE','LONGITUDE')}
    from rasterio.warp import transform
    import rasterio
    x,y=transform('EPSG:4269','EPSG:3978',frame.longitude.to_numpy(),frame.latitude.to_numpy())
    alternative=np.column_stack((x,y));difference=np.linalg.norm(coordinates(frame)-alternative,axis=1)
    return dict(archive_sha256=expected_sha256,xml_sha256=hashlib.sha256(raw).hexdigest(),
        stored_geometry_reference_codes=[node.attrib.get('code') for node in tree.findall('.//refSysInfo/RefSystem/refSysID/identCode')],
        stored_geometry_geographic_system=tree.findtext('.//geogcsn'),field_definitions=fields,
        pipeline_assumed_latlon_crs='EPSG:4326',alternative_latlon_crs='EPSG:4269',output_crs='EPSG:3978',
        projected_difference_m={str(q):float(np.quantile(difference,q)) for q in [0,.5,.99,1]},
        rasterio_version=rasterio.__version__,gdal_version=rasterio.__gdal_version__,
        limitations='Stored-geometry metadata does not explicitly assign a datum to the agency LATITUDE/LONGITUDE attribute definitions. This comparison uses the installed transformation operations; equal outputs do not prove actual accuracy or a universal datum equivalence. No coordinate or feature was changed.')


def summary(frame):
    counts=Counter(coordinate_keys(frame));n=len(frame)
    values=frame[['latitude','longitude']].to_numpy(dtype=float)
    alignment={}
    for step in GRID_STEPS:
        aligned=np.all(np.isclose(values,np.rint(values/step)*step,rtol=0,atol=GRID_ATOL_DEGREES),axis=1)
        alignment[str(step)]=dict(rows=int(aligned.sum()),fraction=float(aligned.mean()))
    repeated=sum(c for c in counts.values() if c>1)
    return dict(rows=n,unique_coordinates=len(counts),rows_on_repeated_coordinates=repeated,
        repeated_coordinate_row_fraction=repeated/n,additional_rows_beyond_unique_coordinates=n-len(counts),
        maximum_records_at_one_coordinate=max(counts.values()),both_coordinates_grid_aligned=alignment)


def audit(frame,folds,train_window=(1988,2018)):
    if frame.empty or not frame.year.between(*train_window).all() or not frame.incident_id.is_unique:
        raise ValueError('Requires unique training-period incidents')
    values=frame[['latitude','longitude']].to_numpy(dtype=float)
    if not np.isfinite(values).all() or np.any(np.abs(values)>[90,180]):
        raise ValueError('Invalid reported coordinate')
    conditions=[]
    for fold in folds:
        train,valid=split(frame,fold,train_window)
        keys=set(coordinate_keys(train));seen=np.array([key in keys for key in coordinate_keys(valid)])
        distance=cKDTree(coordinates(train)).query(coordinates(valid))[0]/1000
        conditions.append(dict(fold=fold,training_rows=len(train),validation_rows=len(valid),
            training_unique_coordinates=len(keys),validation_unique_coordinates=len(set(coordinate_keys(valid))),
            validation_rows_at_exact_training_coordinate=int(seen.sum()),exact_seen_fraction=float(seen.mean()),
            nearest_training_distance_km={str(q):float(np.quantile(distance,q)) for q in [0,.5,.9,.99,1]},
            fraction_with_training_point_within_km={str(radius):float(np.mean(distance<=radius)) for radius in [.1,1,5,10,50]}))
    return dict(summary=summary(frame),years={str(year):summary(part) for year,part in frame.groupby('year')},
        periods={f'{a}-{b}':summary(part) for a,b in [(1988,2009),(2010,2018)]
                 if not (part:=frame[frame.year.between(a,b)]).empty},
        chronological_conditions=conditions,method=dict(grid_steps_degrees=list(GRID_STEPS),
            grid_alignment_absolute_tolerance_degrees=GRID_ATOL_DEGREES,distance_crs='EPSG:3978',train_window=list(train_window),
            uses_labels=False,model_fits=0),
        limitations='Grid alignment describes numeric patterns, not positional accuracy; non-alignment does not prove fine resolution. Repeated coordinates can be distinct fires. Projected nearest distances use approximate reported points and do not establish causality, ecological independence or external-region transfer.')
