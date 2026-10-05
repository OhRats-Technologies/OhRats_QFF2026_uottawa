"""Declared geographic block holdouts plus point-distance guard bands."""
import numpy as np
from rasterio.warp import transform
from scipy.spatial import cKDTree


def coordinates(frame):
    x,y=transform('EPSG:4326','EPSG:3978',frame.longitude.to_numpy(),frame.latitude.to_numpy())
    return np.column_stack((x,y))


def split(train,valid,side=0,width_m=200000,guard_m=50000):
    a,b=coordinates(train),coordinates(valid)
    ca,cb=np.floor(a/width_m).astype(int),np.floor(b/width_m).astype(int)
    train_mask=(ca.sum(axis=1)%2)==side
    valid_mask=(cb.sum(axis=1)%2)!=side
    heldout=b[valid_mask]
    if not len(heldout) or not train_mask.any():
        raise ValueError('Empty geographic holdout')
    distance,_=cKDTree(heldout).query(a)
    train_mask &= distance>=guard_m
    if not train_mask.any():
        raise ValueError('Spatial guard removes all training examples')
    selected_train,selected_valid=train.loc[train_mask].copy(),valid.loc[valid_mask].copy()
    train_cells=set(map(tuple,ca[train_mask]));valid_cells=set(map(tuple,cb[valid_mask]))
    assert not train_cells & valid_cells
    return selected_train,selected_valid,dict(crs='EPSG:3978',block_width_m=width_m,guard_m=guard_m,train_side=side,
          train_rows=len(selected_train),validation_rows=len(selected_valid),train_cells=len(train_cells),validation_cells=len(valid_cells),
          excluded_training_rows=len(train)-len(selected_train),minimum_train_validation_distance_m=float(distance[train_mask].min()),
          limitations='Checkerboard interpolation holdout, not an external province. Guard uses approximate recorded points; no ecological-region claim.')


def matched_control(base_train,valid,count,seed,metadata):
    from wildfire_lab.evaluation import sample_indices
    chosen=base_train.iloc[sample_indices(len(base_train),count,seed)].copy()
    a,b=coordinates(chosen),coordinates(valid)
    ca=set(map(tuple,np.floor(a/metadata['block_width_m']).astype(int)))
    cb=set(map(tuple,np.floor(b/metadata['block_width_m']).astype(int)))
    distance,_=cKDTree(b).query(a)
    return chosen,dict(metadata,control='random_matched_rows',guard_m=0,train_cells=len(ca),shared_cells=len(ca & cb),
            minimum_train_validation_distance_m=float(distance.min()),
            limitations='Same training count and held-out rows; training includes held-out geographic cells. Time-only size control.')
