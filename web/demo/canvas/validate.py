"""Independent Qiskit/sklearn goldens for the browser teaching engine."""
import json
from pathlib import Path
import numpy as np
from qiskit.circuit.library import zz_feature_map
from qiskit.quantum_info import Statevector
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
root = Path(__file__).resolve().parent
samples = [[.03,.11,.21,.07],[-.2,.4,.5,-.01]]
states = [Statevector.from_instruction(zz_feature_map(4,reps=1,entanglement='linear').assign_parameters(x)).data for x in samples]
data = json.loads((root/'data.json').read_text())
features = [0,1,2,3]
train = [r for r in data['rows'] if r['year']<=2014]
test = [r for r in data['rows'] if 2015<=r['year']<=2018]
imputer=SimpleImputer(strategy='median')
scaler=StandardScaler()
x=scaler.fit_transform(imputer.fit_transform([[r['x'][j] for j in features] for r in train]))
cross=scaler.transform(imputer.transform([[r['x'][j] for j in features] for r in test]))
y_scaler=StandardScaler()
y=y_scaler.fit_transform(np.log1p([r['y'] for r in train]).reshape(-1,1)).ravel()
circuit=zz_feature_map(4,reps=1,entanglement='linear')
a=[Statevector.from_instruction(circuit.assign_parameters(np.pi/16*np.tanh(row/2))).data for row in x]
b=[Statevector.from_instruction(circuit.assign_parameters(np.pi/16*np.tanh(row/2))).data for row in cross]
K=np.abs(np.array(a).conj()@np.array(a).T)**2
Kt=np.abs(np.array(b).conj()@np.array(a).T)**2
model=SVR(kernel='precomputed',C=1,epsilon=.2,tol=1e-9).fit(K,y)
fixture={'samples':samples,'states':[[[v.real,v.imag] for v in state] for state in states],
 'build':{'features':features,'angle':np.pi/16,'C':1,'epsilon':.2},'gram':K.tolist(),
 'predicted':np.maximum(0,np.expm1(y_scaler.inverse_transform(model.predict(Kt).reshape(-1,1)).ravel())).tolist()}
(root/'golden.json').write_text(json.dumps(fixture,separators=(',',':'))+'\n')
print('Independent Qiskit/sklearn goldens created.')
# Independent Qiskit XY gate check on a six-state, four-bit feasible sector.
from itertools import combinations
from qiskit.circuit.library import RXXGate, RYYGate
masks = [sum(1 << j for j in combo) for combo in combinations(range(4), 2)]
objective = {m: (i - 3) / 7 for i, m in enumerate(sorted(masks))}
spread = max(objective.values()) - min(objective.values())
v = np.zeros(16, dtype=complex)
for m in masks:
    v[m] = np.exp(-2.5j * objective[m] / spread) / np.sqrt(6)
state = Statevector(v)
for bit in range(4):
    state = state.evolve(RXXGate(.35), qargs=[bit,(bit+1)%4])
    state = state.evolve(RYYGate(.35), qargs=[bit,(bit+1)%4])
fixture['sector'] = {'objective':objective,'states':{m:[state.data[m].real,state.data[m].imag] for m in masks}}
(root/'golden.json').write_text(json.dumps(fixture,separators=(',',':'))+'\n')
print('Independent Qiskit XY mixer golden created.')
# Cover very different legal widths/bandwidths; held-out development rows only.
checks=[]
for dimensions, amplitude, C, epsilon, end in [(2,np.pi/32,.3,.5,2006),(4,np.pi/2,10,.05,2014),(6,np.pi/8,3,.2,2010),(10,np.pi/32,10,.05,2014)]:
    chosen=list(range(dimensions))
    tr=[r for r in data['rows'] if r['year']<=end]
    te=[r for r in data['rows'] if end<r['year']<=end+4]
    imp=SimpleImputer(strategy='median')
    sc=StandardScaler()
    xx=sc.fit_transform(imp.fit_transform([[np.nan if r['x'][j] is None else r['x'][j] for j in chosen] for r in tr]))
    xc=sc.transform(imp.transform([[np.nan if r['x'][j] is None else r['x'][j] for j in chosen] for r in te]))
    ys=StandardScaler(); yy=ys.fit_transform(np.log1p([r['y'] for r in tr]).reshape(-1,1)).ravel()
    q=zz_feature_map(dimensions,reps=1,entanglement='linear')
    aa=np.array([Statevector.from_instruction(q.assign_parameters(amplitude*np.tanh(row/2))).data for row in xx])
    bb=np.array([Statevector.from_instruction(q.assign_parameters(amplitude*np.tanh(row/2))).data for row in xc])
    kk=np.abs(aa.conj()@aa.T)**2;kc=np.abs(bb.conj()@aa.T)**2
    m=SVR(kernel='precomputed',C=C,epsilon=epsilon,tol=1e-10).fit(kk,yy)
    checks.append({'build':{'features':chosen,'angle':amplitude,'C':C,'epsilon':epsilon},
                   'round':{2006:0,2010:1,2014:2}[end],
                   'predicted':np.maximum(0,np.expm1(ys.inverse_transform(m.predict(kc).reshape(-1,1)).ravel())).tolist()})
fixture['svr_checks']=checks
(root/'golden.json').write_text(json.dumps(fixture,separators=(',',':'))+'\n')
print('Four width/bandwidth SVR controls created.')
