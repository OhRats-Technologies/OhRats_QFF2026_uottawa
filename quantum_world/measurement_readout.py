"""Known-channel inference under independent symmetric register readout errors."""
import numpy as np
from scipy.stats import binomtest,chisquare


def probabilities(rate,time,readout_error):
    if not 0<=readout_error<.5:raise ValueError('Readout error must be in [0,.5)')
    p=np.exp(-rate*time);e=readout_error
    return (1-p)/4+p*np.array([(1-e)**2,e*(1-e),e*(1-e),e*e])


def blind_estimate(counts,time=.8):
    n=int(sum(counts));k=int(counts[0]);q=k/n
    ci=binomtest(k,n).proportion_ci(.95,method='exact')
    transform=lambda value:float(-np.log((4*value-1)/3)/time)
    if ci.high<.25:return dict(rate=None,interval=None,model_rejected=True)
    return dict(rate=None if q<=.25 else transform(min(q,1.)),
        interval=[max(0.,transform(min(ci.high,1.))),None if ci.low<=.25 else transform(ci.low)],
        model_rejected=False,interval_method='95% exact binomial, incorrectly assumes zero readout error')


def calibrated_estimate(reference_counts,probe_counts,time=.8):
    """Bonferroni propagation of two exact binomial intervals.

    Reference is noiseless |00> before the SAME readout process; its two bit
    errors per shot are independent with a common unknown error probability.
    This guarantee relies on that readout model and the isotropic channel family.
    """
    n_ref=int(sum(reference_counts));n_probe=int(sum(probe_counts))
    flips=int(reference_counts[1]+reference_counts[2]+2*reference_counts[3])
    e=flips/(2*n_ref);q=probe_counts[0]/n_probe
    e_ci=binomtest(flips,2*n_ref).proportion_ci(.975,method='exact')
    q_ci=binomtest(int(probe_counts[0]),n_probe).proportion_ci(.975,method='exact')
    def rate(value,error):
        denominator=(1-error)**2-.25
        if denominator<=0:return None
        p=(value-.25)/denominator
        if p<=0:return None
        return max(0.,float(-np.log(min(1.,p))/time))
    point=rate(q,e);low=rate(q_ci.high,e_ci.high);high=rate(q_ci.low,e_ci.low)
    return dict(rate=point,interval=None if low is None else [low,high],readout_error=e,
        error_interval=[float(e_ci.low),float(e_ci.high)],return_probability_interval=[float(q_ci.low),float(q_ci.high)],
        interval_method='at least 95% joint coverage from Bonferroni + two exact 97.5% binomial intervals',
        scope='conditional on identical independent symmetric bit errors, ideal reference preparation, known isotropic channel')


def goodness_of_fit(counts):
    """Ideal isotropic return measurement has equal three non-return outcomes."""
    other=np.asarray(counts[1:],dtype=float)
    if other.sum()<15:return dict(p=None,reject=False,status='insufficient expected nonreturn counts')
    p=float(chisquare(other,np.full(3,other.sum()/3)).pvalue)
    return dict(p=p,reject=bool(p<.05),status='approximate Pearson check; not a channel-model certificate')
