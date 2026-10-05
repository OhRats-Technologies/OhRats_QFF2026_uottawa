"""Goal-conditioned control with frozen world models; no outcome feedback."""
from __future__ import annotations
import time
import numpy as np
import torch
from .physics import GENERATORS, unitary


def control_template():
    """Four local Euler layers separated by three alternating CNOT gates."""
    result=[];parameter=0
    for layer in range(4):
        for rz,h in ((4,0),(5,1)):
            for gate in (rz,h,rz,h,rz):
                if gate>=4:
                    result.append((gate,parameter));parameter+=1
                else:result.append((gate,None))
        if layer<3:result.append((2+layer%2,None))
    return result


class CachedRotation:
    """Frozen skew generators with differentiable duration, avoiding repeated expm."""
    def __init__(self,generators):
        a=torch.as_tensor(generators,dtype=torch.float64).detach()
        if not torch.allclose(a,-a.transpose(-1,-2),atol=1e-10):
            raise ValueError('Expected real skew generators')
        self.values,self.vectors=torch.linalg.eigh(1j*a.to(torch.complex128))
        self.discrete=torch.matrix_exp(a)

    def advance(self,z,gate,duration):
        if gate<4:return z@self.discrete[gate].T
        v=self.vectors[gate]
        coordinates=z.to(v.dtype)@v.conj()
        phase=torch.exp(-1j*duration[:,None]*self.values[gate])
        return ((coordinates*phase)@v.T).real


class FrozenModel:
    def __init__(self,model):
        self.model=model.eval().double()
        for parameter in self.model.parameters():parameter.requires_grad_(False)
        self.rotation=None
        if model.kind=='latent_generator':
            raw=model.raw_generator.detach()
            self.rotation=CachedRotation((raw-raw.transpose(-1,-2))/2)

    def encode(self,r):
        r=torch.as_tensor(r,dtype=torch.float64)
        with torch.no_grad():return self.model.encoder(torch.cat([r,torch.zeros(len(r),8,dtype=r.dtype)],dim=-1))

    def advance(self,z,gate,duration):
        if self.rotation is not None:return self.rotation.advance(z,gate,duration)
        g=torch.full((len(z),),gate,dtype=torch.long)
        return self.model.advance(z,g,duration)


class ExactPauliModel:
    def __init__(self):self.rotation=CachedRotation(GENERATORS)
    def encode(self,r):return torch.as_tensor(r,dtype=torch.float64)
    def advance(self,z,gate,duration):return self.rotation.advance(z,gate,duration)


def rollout(model,z,angles):
    for gate,index in control_template():
        duration=torch.ones(len(z),dtype=z.dtype) if index is None else angles[:,index]
        z=model.advance(z,gate,duration)
    return z


def plan(model,initial,goal,seed,steps=250,restarts=4,lr=.05):
    """Optimize and select using latent goal distance exclusively.

    Physical states/outcomes are deliberately absent from this function.
    Every episode gets the same restart budget, including unsuccessful ones.
    """
    source=model.encode(initial);target=model.encode(goal)
    n=len(source)
    rng=torch.Generator().manual_seed(seed)
    raw=torch.randn((n,restarts,24),dtype=torch.float64,generator=rng)*.7
    initial_angles=(np.pi*torch.tanh(raw[:,0])).numpy().copy()
    raw.requires_grad_(True)
    optimizer=torch.optim.Adam([raw],lr=lr)
    source=source.repeat_interleave(restarts,dim=0)
    target=target.repeat_interleave(restarts,dim=0)
    start=time.perf_counter()
    for _ in range(steps):
        angles=np.pi*torch.tanh(raw.reshape(-1,24))
        error=(rollout(model,source,angles)-target).square().mean(dim=-1)
        loss=error.sum() # independent episode/restart gradients
        if not torch.isfinite(loss):raise FloatingPointError('Nonfinite planner loss')
        optimizer.zero_grad();loss.backward();optimizer.step()
    with torch.no_grad():
        angles=np.pi*torch.tanh(raw.reshape(-1,24))
        errors=(rollout(model,source,angles)-target).square().mean(dim=-1).reshape(n,restarts)
        selected=errors.argmin(dim=-1)
        controls=angles.reshape(n,restarts,24)[torch.arange(n),selected].numpy()
    return dict(angles=controls,latent_cost=errors[torch.arange(n),selected].numpy(),
                selected_restart=selected.numpy(),random_angles=initial_angles,
                seconds=time.perf_counter()-start,steps=steps,restarts=restarts)


def exact_states(initial,angles):
    """Post-selection evaluator; never called by the planner."""
    states=np.array(initial,dtype=complex,copy=True)
    for gate,index in control_template():
        times=np.ones(len(states)) if index is None else angles[:,index]
        states=np.array([unitary(gate,float(t))@psi for psi,t in zip(states,times)])
    return states
