"""Verify and reconstruct the original labels-free matrix inputs."""
import hashlib
import json
import numpy as np
import pandas as pd
from wildfire_lab.evaluation import split,sample_indices
from wildfire_lab.encoding_screen import preprocess


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def load(root,plan):
    cache=root/plan['parent_cache']
    assert sha(cache/'outcome.json')==plan['parent_outcome_sha256'] and sha(cache/'intent.json')==plan['parent_intent_sha256']
    record=json.loads((cache/'outcome.json').read_text());intent=json.loads((cache/'intent.json').read_text())
    assert record['status']=='complete' and record['intent']==intent
    for name,expected in intent['recipe_sha256'].items():
        if name.startswith('wildfire_lab/'):
            assert sha(root/name)==expected,name
    parent=intent['parent_plan'];source=root/parent['dataset']/'features.csv'
    assert sha(source)==parent['dataset_sha256']
    frame=pd.read_csv(source,usecols=['incident_id','year',*parent['features']])
    assert frame.year.between(1988,2018).all() and frame.incident_id.is_unique
    train,valid=split(frame,parent['fold'],train_window=(1988,2018));inputs={}
    for seed in intent['plan']['seeds']:
        ti=sample_indices(len(train),parent['train_cap'],seed);vi=sample_indices(len(valid),parent['validation_cap'],seed)
        _,_,x,v=preprocess(train.iloc[ti],valid.iloc[vi],parent['features'],parent['preprocessing'])
        inputs[seed]=(x,v,hashlib.sha256(ti.tobytes()).hexdigest(),hashlib.sha256(vi.tobytes()).hexdigest())
    seen=set();conditions=[]
    for row in record['conditions']:
        key=(row['seed'],row['angle_scale']);assert key not in seen;seen.add(key)
        x,v,ti,vi=inputs[row['seed']]
        assert (row['train_indices_sha256'],row['validation_indices_sha256'])==(ti,vi)
        path=cache/row['matrix_file'];assert path.parent==cache and sha(path)==row['matrix_sha256']
        with np.load(path,allow_pickle=False) as arrays:gram,cross=arrays['gram'].copy(),arrays['cross'].copy()
        assert gram.shape==(len(x),len(x)) and cross.shape==(len(v),len(x))
        conditions.append((row,x,v,gram,cross))
    assert seen=={(s,a) for s in intent['plan']['seeds'] for a in intent['plan']['angle_scales']}
    return intent,conditions
