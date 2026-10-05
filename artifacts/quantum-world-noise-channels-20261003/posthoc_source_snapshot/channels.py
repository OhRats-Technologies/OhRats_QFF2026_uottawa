"""Nonunitary physical-coordinate calibration; not nonlinear JEPA training."""
import numpy as np
import torch
from torch import nn
from .physics import PAULIS,haar_states,pauli_to_density,project_density

RATES=np.array([1.10,.65]) # held by the data generator, never passed to fitting
BASIS=np.concatenate([np.eye(4,dtype=complex)[None],PAULIS])


def density_to_pauli(rho):return np.einsum('...ab,iba->...i',rho,PAULIS).real


def states(n,seed):
    rng=np.random.default_rng(seed);a=rng.normal(size=(n,4,4))+1j*rng.normal(size=(n,4,4))
    rho=a@a.conj().transpose(0,2,1);rho/=np.trace(rho,axis1=-2,axis2=-1).real[:,None,None]
    pure=haar_states(n//2,seed+1)
    rho[:len(pure)]=np.einsum('na,nb->nab',pure,pure.conj())
    return rho


def channel(rho,gate,duration,rate):
    if duration<0:raise ValueError('Noise evolution requires nonnegative time')
    p=np.exp(-rate*duration)
    if gate==0:return p*rho+(1-p)*np.eye(4)/4
    if gate!=1:raise ValueError(gate)
    k0=np.kron(np.diag([1,np.sqrt(p)]),np.eye(2))
    k1=np.kron(np.array([[0,np.sqrt(1-p)],[0,0]]),np.eye(2))
    return k0@rho@k0.conj().T+k1@rho@k1.conj().T


def lindblad_bases():
    dep=np.diag([0.,*([-1.]*15)])
    jump=np.kron(np.array([[0,1],[0,0]]),np.eye(2));gram=jump.conj().T@jump
    dissipator=np.array([jump@p@jump.conj().T-(gram@p+p@gram)/2 for p in BASIS])
    damping=np.einsum('iab,jba->ij',BASIS,dissipator).real/4
    return np.stack([dep,damping])


class ChannelWorld(nn.Module):
    def __init__(self,kind):
        super().__init__();self.kind=kind
        if kind=='physical':
            self.raw_rate=nn.Parameter(torch.zeros(2));self.register_buffer('basis',torch.tensor(lindblad_bases(),dtype=torch.float32))
        elif kind in ('skew','affine'):self.raw=nn.Parameter(torch.zeros(2,15,15 if kind=='skew' else 16))
        else:raise ValueError(kind)

    def matrices(self):
        if self.kind=='physical':return torch.nn.functional.softplus(self.raw_rate)[:,None,None]*self.basis
        zeros=torch.zeros((2,1,16),dtype=self.raw.dtype)
        if self.kind=='affine':return torch.cat([zeros,self.raw],dim=1)
        a=(self.raw-self.raw.transpose(-1,-2))/2
        return torch.cat([zeros,torch.cat([torch.zeros(2,15,1,dtype=a.dtype),a],dim=-1)],dim=1)

    def forward(self,x,gate,duration):
        if torch.any(duration<0):raise ValueError('Noise evolution requires nonnegative time')
        aug=torch.cat([torch.ones(len(x),1,dtype=x.dtype),x],dim=-1)
        evolution=torch.matrix_exp(self.matrices()[gate]*duration[:,None,None])
        return torch.einsum('nij,nj->ni',evolution,aug)[:,1:]


def transitions(n,seed,shots=0):
    rho=states(n,seed);rng=np.random.default_rng(seed+100000)
    gate=rng.integers(0,2,n);duration=rng.uniform(.05,.8,n)
    future=np.array([channel(r,int(g),float(t),RATES[g]) for r,g,t in zip(rho,gate,duration)])
    y=density_to_pauli(future)
    if shots:y=2*rng.binomial(shots,np.clip((y+1)/2,0,1))/shots-1
    return dict(x=density_to_pauli(rho),y=y,rho=rho,future=future,gate=gate,duration=duration)


def mixed_metrics(predicted,truth):
    if not np.isfinite(predicted).all():raise FloatingPointError('Nonfinite mixed-state prediction')
    raw=pauli_to_density(predicted);eig=np.linalg.eigvalsh(raw);repaired=project_density(raw)
    values,vectors=np.linalg.eigh(truth)
    root=(vectors*np.sqrt(np.maximum(values,0))[:,None,:])@vectors.conj().transpose(0,2,1)
    middle=root@repaired@root
    fidelity=np.square(np.sqrt(np.maximum(np.linalg.eigvalsh(middle),0)).sum(axis=-1))
    if np.any(fidelity>1+1e-6):raise FloatingPointError('Mixed-state fidelity exceeded numerical tolerance')
    fidelity=np.clip(fidelity,0,1)
    return dict(mean_fidelity=float(fidelity.mean()),pauli_mse=float(np.mean((predicted-density_to_pauli(truth))**2)),
        raw_valid_fraction=float((eig[:,0]>=-1e-6).mean()),min_eigenvalue=float(eig[:,0].min()),
        projection_frobenius_mean=float(np.linalg.norm(raw-repaired,axis=(-2,-1)).mean()))


def anchor_conflict(contraction):
    """Scalar isotropic covariance optimum for current/future whitening together."""
    if not 0<contraction<=1:raise ValueError(contraction)
    s=(1+contraction**2)/(1+contraction**4)
    return dict(contraction=contraction,optimal_current_covariance=s,
        optimal_future_covariance=contraction**2*s,
        minimum_paired_anchor=((s-1)**2+(contraction**2*s-1)**2)/2)


def depolarizing_certificate(rate,step=.5):
    """Known isotropic-channel threshold, conditional on the fitted model family.

    This is not a confidence certificate for a noisy rate estimate or evidence
    about an arbitrary hardware channel. For d=4 the isotropic Choi state is
    separable exactly when p <= 1/5; generic 4x4 PPT states need not be separable.
    """
    if rate<=0 or step<=0:raise ValueError('Positive rate and step required')
    time=float(np.log(5)/rate);index=int(np.ceil(time/step))
    def record(t):
        p=np.exp(-rate*t);omega=np.eye(4).reshape(-1)/2
        choi=p*np.outer(omega,omega)+(1-p)*np.eye(16)/16
        pt=choi.reshape(4,4,4,4).transpose(0,3,2,1).reshape(16,16)
        return dict(time=float(t),contraction=float(p),choi_pt_min_eigenvalue=float(np.linalg.eigvalsh(pt).min()),
            worst_case_trace_distance_to_stationary=float(.75*p))
    return dict(rate=float(rate),step=float(step),entanglement_breaking_time=time,
        entanglement_breaking_index=index,before=record((index-1)*step),after=record(index*step),
        at_threshold=record(time),model_conditional=True,rate_uncertainty_certified=False)


def choi_from_transfer(transfer):
    """Normalized Choi state, reference tensor factor first, for Pauli transfer."""
    result=np.zeros((16,16),dtype=complex)
    for i in range(16):
        for j in range(16):result+=transfer[i,j]*np.kron(BASIS[j].T,BASIS[i])/16
    return (result+result.conj().T)/2
