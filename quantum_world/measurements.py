"""Equal-shot estimation of a known isotropic channel; no hardware submission."""
import numpy as np
from scipy.optimize import minimize_scalar,brentq
from scipy.stats import binomtest,chi2
from .physics import haar_states,state_to_pauli,LABELS


def tomography_design(budget,seed,n_states=64):
    if budget<n_states*15:raise ValueError('At least one shot per observable required')
    x=state_to_pauli(haar_states(n_states,seed))
    times=np.random.default_rng(seed+1).uniform(.05,.8,n_states)
    shots=np.full(x.shape,budget//x.size,dtype=int)
    shots.flat[:budget%x.size]+=1
    assert shots.sum()==budget
    return dict(x=x,times=times,shots=shots)


def tomography_estimate(design,rate,measurement_seed):
    x,times,shots=(design[k] for k in ('x','times','shots'))
    probs=(1+x*np.exp(-rate*times[:,None]))/2
    counts=np.random.default_rng(measurement_seed).binomial(shots,probs)
    def objective(gamma):
        q=np.clip((1+x*np.exp(-gamma*times[:,None]))/2,1e-12,1-1e-12)
        return float(-np.sum(counts*np.log(q)+(shots-counts)*np.log1p(-q)))
    optimum=minimize_scalar(objective,bounds=(0.,8.),method='bounded',options={'xatol':1e-8})
    if not optimum.success:raise RuntimeError('Tomography likelihood fit failed')
    point=float(optimum.x);cut=objective(point)+chi2.ppf(.95,1)/2
    low=0. if objective(0.)<=cut else float(brentq(lambda g:objective(g)-cut,0.,point))
    high_search=max(8.,point*2)
    while high_search<128 and objective(high_search)<=cut:high_search*=2
    high=None if objective(high_search)<=cut else float(brentq(lambda g:objective(g)-cut,point,high_search))
    p=np.exp(-rate*times[:,None]);information=float(np.sum(shots*times[:,None]**2*p*p*x*x/(1-p*p*x*x)))
    return dict(rate=point,interval=[low,high],counts=counts.tolist(),shots=int(shots.sum()),
        fisher_information=information,interval_method='approximate 95% profile-likelihood interval')


def focused_estimate(budget,rate,measurement_seed,time=.8):
    """Complete basis measurement; return event is sufficient under isotropic noise.

    A |00> probe in the Z basis and Bell probe followed by inverse preparation
    have identical probabilities. One shared simulated count draw represents
    that equivalence control, not two independent observations.
    """
    if budget<=0 or time<=0 or rate<=0:raise ValueError('Positive budget, rate and time required')
    p=np.exp(-rate*time)
    probs=np.array([(1+3*p)/4,*([(1-p)/4]*3)])
    counts=np.random.default_rng(measurement_seed).multinomial(budget,probs)
    k=int(counts[0]);q=k/budget
    interval=binomtest(k,budget).proportion_ci(.95,method='exact')
    if interval.high<.25:
        return dict(rate=None,interval=None,counts=counts.tolist(),shots=budget,model_rejected=True)
    transform=lambda value:float(-np.log((4*value-1)/3)/time)
    point=None if q<=.25 else transform(min(q,1.))
    low=transform(min(interval.high,1.))
    high=None if interval.low<=.25 else transform(interval.low)
    information=float(budget*3*time*time*p*p/((1+3*p)*(1-p)))
    return dict(rate=point,interval=[max(0.,low),high],counts=counts.tolist(),shots=budget,
        fisher_information=information,model_rejected=False,
        interval_method='exact 95% binomial interval mapped through known isotropic family')


def grouped_design(budget,seed,n_states=64):
    if budget<n_states*9:raise ValueError('At least one shot per basis required')
    x=state_to_pauli(haar_states(n_states,seed));times=np.random.default_rng(seed+1).uniform(.05,.8,n_states)
    signs=np.array([[1,1],[1,-1],[-1,1],[-1,-1]])
    contrast=[]
    for left in 'XYZ':
        for right in 'XYZ':
            a=x[:,LABELS.index(left+'I')];b=x[:,LABELS.index('I'+right)];c=x[:,LABELS.index(left+right)]
            contrast.append(a[:,None]*signs[:,0]+b[:,None]*signs[:,1]+c[:,None]*np.prod(signs,axis=1))
    contrast=np.stack(contrast,axis=1)
    shots=np.full((n_states,9),budget//(n_states*9),dtype=int);shots.flat[:budget%(n_states*9)]+=1
    return dict(contrast=contrast,times=times,shots=shots)


def grouped_estimate(design,rate,measurement_seed):
    contrast,times,shots=(design[k] for k in ('contrast','times','shots'))
    probability=(1+contrast*np.exp(-rate*times[:,None,None]))/4
    rng=np.random.default_rng(measurement_seed)
    counts=np.array([[rng.multinomial(int(n),p) for n,p in zip(ns,ps)] for ns,ps in zip(shots,probability)])
    def objective(gamma):
        q=np.clip((1+contrast*np.exp(-gamma*times[:,None,None]))/4,1e-12,1.)
        return float(-np.sum(counts*np.log(q)))
    optimum=minimize_scalar(objective,bounds=(0.,8.),method='bounded',options={'xatol':1e-8})
    if not optimum.success:raise RuntimeError('Grouped likelihood fit failed')
    point=float(optimum.x);cut=objective(point)+chi2.ppf(.95,1)/2
    low=0. if objective(0.)<=cut else float(brentq(lambda g:objective(g)-cut,0.,point))
    high_search=8.
    while high_search<128 and objective(high_search)<=cut:high_search*=2
    high=None if objective(high_search)<=cut else float(brentq(lambda g:objective(g)-cut,point,high_search))
    p=np.exp(-rate*times[:,None,None])
    information=float(np.sum(shots[:,:,None]*times[:,None,None]**2*p*p*contrast*contrast/(4*(1+p*contrast))))
    return dict(rate=point,interval=[low,high],counts=counts.tolist(),shots=int(shots.sum()),
        fisher_information=information,interval_method='approximate 95% grouped-multinomial profile-likelihood interval')


def single_pauli_estimate(basis_estimate,time=.8):
    """Targeted Z0 marginal of the same computational-basis shots."""
    counts=basis_estimate['counts'];budget=basis_estimate['shots'];k=int(counts[0]+counts[1]);q=k/budget
    ci=binomtest(k,budget).proportion_ci(.95,method='exact')
    if ci.high<.5:return dict(rate=None,interval=None,counts=[k,budget-k],shots=budget,model_rejected=True)
    transform=lambda value:float(-np.log(2*value-1)/time)
    point=None if q<=.5 else transform(min(q,1.))
    low=transform(min(ci.high,1.));high=None if ci.low<=.5 else transform(ci.low)
    return dict(rate=point,interval=[max(0.,low),high],counts=[k,budget-k],shots=budget,
        interval_method='exact 95% targeted-Pauli binomial interval; shared basis shots')


def index_interval(interval,step=.5):
    if interval is None:return None
    low,high=interval
    earliest=1 if high is None else max(1,int(np.ceil(np.log(5)/(high*step))))
    latest=None if low<=0 else max(1,int(np.ceil(np.log(5)/(low*step))))
    return [earliest,latest]


def assessment(estimate,true_rate,step=.5):
    interval=estimate['interval'];indices=index_interval(interval,step)
    true_index=int(np.ceil(np.log(5)/(true_rate*step)))
    coverage=False if interval is None else interval[0]<=true_rate and (interval[1] is None or true_rate<=interval[1])
    resolved=indices is not None and indices[0]==indices[1]
    return dict(coverage=bool(coverage),index_interval=indices,true_index=true_index,
        resolved_correct=bool(resolved and indices[0]==true_index),resolved_wrong=bool(resolved and indices[0]!=true_index),
        squared_rate_error=None if estimate['rate'] is None else float((estimate['rate']-true_rate)**2))
