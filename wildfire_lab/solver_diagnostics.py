"""SVM primal/dual and KKT checks on a supplied training Gram matrix."""
import numpy as np


def diagnostics(model,gram,y):
    signed=np.where(np.asarray(y)==1,1.,-1.)
    coefficient=np.zeros(len(y));coefficient[model.support_]=model.dual_coef_[0]
    alpha=np.abs(coefficient);bound=float(model.C)
    decision=gram@coefficient+model.intercept_[0];margin=signed*decision
    norm=float(coefficient@gram@coefficient)
    primal=.5*norm+bound*np.maximum(1-margin,0).sum()
    dual=alpha.sum()-.5*norm
    lower=alpha<1e-8;upper=alpha>bound-1e-8;middle=~(lower|upper)
    residual=np.zeros(len(y));residual[lower]=np.maximum(1-margin[lower],0)
    residual[upper]=np.maximum(margin[upper]-1,0);residual[middle]=np.abs(margin[middle]-1)
    return dict(primal=float(primal),dual=float(dual),duality_gap=float(primal-dual),
        kkt_max_violation=float(residual.max()),dual_equality_residual=float(abs(coefficient.sum())),
        squared_weight_norm=norm,training_decision_std=float(np.std(decision)),
        training_positive_predictions=int((decision>0).sum()),support_vectors=len(model.support_),
        solver_iterations=int(model.n_iter_.sum()),fit_status=int(model.fit_status_))
