"""Fixed ridge/RBF/Qiskit-QSVR fits with reconstructible coefficients and kernels."""
import time
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.svm import SVR
from qiskit_machine_learning.algorithms import QSVR
from wildfire_lab.annual_classical import errors,inverse,gamma
from wildfire_lab.library_kernel import matrices


def prepare(x,cross,targets):
    imputer=SimpleImputer(strategy='median',keep_empty_features=True)
    scaler=StandardScaler()
    x=scaler.fit_transform(imputer.fit_transform(x))
    cross=scaler.transform(imputer.transform(cross))
    target=StandardScaler()
    y=target.fit_transform(np.log1p(targets).reshape(-1,1)).ravel()
    preprocessing=dict(median=imputer.statistics_.tolist(),mean=scaler.mean_.tolist(),
        scale=scaler.scale_.tolist(),y_mean=float(target.mean_[0]),y_scale=float(target.scale_[0]))
    return x,cross,y,target,preprocessing


def rbf(x,cross,bandwidth):
    return np.exp(-bandwidth*np.sum((cross[:,None,:]-x[None,:,:])**2,axis=-1))


def fit(x_raw,cross_raw,targets,actual,columns,plan):
    start=time.perf_counter()
    x,cross,y,scaler,preprocessing=prepare(x_raw,cross_raw,targets)
    amplitude=plan['quantum']['angle_amplitude']
    angles=amplitude*np.tanh(x/2)
    cross_angles=amplitude*np.tanh(cross/2)
    gram,test,resource=matrices(angles,cross_angles,reps=plan['quantum']['reps'])
    eigenvalues=np.linalg.eigvalsh(gram)
    if eigenvalues.min()<-1e-7:
        raise ValueError('Analytic fidelity Gram matrix is not PSD')
    positive=np.maximum(eigenvalues,0)
    p=positive/positive.sum()
    resource.update(qubits=len(columns),minimum_eigenvalue=float(eigenvalues.min()),
        off_diagonal_mean=float(gram[~np.eye(len(x),dtype=bool)].mean()),
        effective_rank=float(np.exp(-np.sum(p[p>0]*np.log(p[p>0])))))
    bandwidth=gamma(x)
    classical,classic_test=rbf(x,x,bandwidth),rbf(x,cross,bandwidth)
    model_params=plan['models']
    models={'ridge':Ridge(**model_params['ridge']),
            'rbf':SVR(kernel='precomputed',**model_params['svr']),
            'qsvr':QSVR(quantum_kernel='precomputed',**model_params['svr'])}
    inputs={'ridge':(x,cross),'rbf':(classical,classic_test),'qsvr':(gram,test)}
    rows=[]
    for label,model in models.items():
        train_input,test_input=inputs[label]
        model.fit(train_input,y)
        scaled_prediction=model.predict(test_input)
        prediction=inverse(scaled_prediction,scaler)
        parameters=dict(intercept=float(np.asarray(model.intercept_).ravel()[0]))
        if label=='ridge':
            parameters['coef']=model.coef_.tolist()
        else:
            parameters.update(support=model.support_.tolist(),dual_coef=model.dual_coef_.ravel().tolist())
        rows.append(dict(model=label,features=columns,parameters=parameters,
            predicted_scaled=scaled_prediction.tolist(),predicted_ha=prediction.tolist(),
            actual_ha=np.asarray(actual).tolist(),**errors(actual,prediction)))
    return dict(rows=rows,preprocessing=preprocessing,scaled_train=x.tolist(),
        scaled_cross=cross.tolist(),scaled_targets=y.tolist(),rbf_gamma=bandwidth,
        quantum_gram=gram.tolist(),quantum_cross=test.tolist(),resource=resource,
        seconds=time.perf_counter()-start)
