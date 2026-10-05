"""Reconstruction-free nonlinear encoder pilot with independent physical readout.

State features plus nuisance channels are observations. No decoder or physical
state reconstruction loss participates in encoder/dynamics training. A separate
readout is trained AFTER freezing the world model, for physical evaluation only.
"""
from __future__ import annotations
import torch
from torch import nn
from .models import action_features


class JEPAWorld(nn.Module):
    def __init__(self,kind='direct',latent_dim=15,width=128):
        super().__init__()
        if kind not in ('direct','source_chord','gaussian','latent_generator'):raise ValueError(kind)
        self.kind=kind
        self.encoder=nn.Sequential(nn.Linear(23,width),nn.SiLU(),nn.Linear(width,width),nn.SiLU(),nn.Linear(width,latent_dim))
        if kind=='latent_generator':
            self.raw_generator=nn.Parameter(torch.zeros(6,latent_dim,latent_dim))
        else:
            inp=latent_dim+8 if kind=='direct' else 2*latent_dim+9
            self.predictor=nn.Sequential(nn.Linear(inp,width),nn.SiLU(),nn.Linear(width,width),nn.SiLU(),nn.Linear(width,latent_dim))

    def field(self,z,tau,source,gate,duration):
        features=[z,action_features(gate,duration)]
        if self.kind!='direct':features += [tau[:,None],source]
        return self.predictor(torch.cat(features,dim=-1))

    def advance(self,source,gate,duration,steps=16,noise=None):
        if self.kind=='latent_generator':
            a=(self.raw_generator-self.raw_generator.transpose(-1,-2))/2
            return torch.einsum('nij,nj->ni',torch.matrix_exp(a[gate]*duration[:,None,None]),source)
        if self.kind=='direct':return self.field(source,None,None,gate,duration)
        z=source if self.kind=='source_chord' else (torch.zeros_like(source) if noise is None else noise)
        h=1/steps
        for i in range(steps):
            t=torch.full_like(duration,i*h)
            k1=self.field(z,t,source,gate,duration)
            k2=self.field(z+h*k1/2,t+h/2,source,gate,duration)
            k3=self.field(z+h*k2/2,t+h/2,source,gate,duration)
            k4=self.field(z+h*k3,t+h,source,gate,duration)
            z=z+h*(k1+2*k2+2*k3+k4)/6
        return z


def covariance_anchor(z):
    """Anti-collapse moment objective; does not claim Gaussianity."""
    centered=z-z.mean(dim=0)
    covariance=centered.T@centered/(len(z)-1)
    eye=torch.eye(z.shape[-1],dtype=z.dtype,device=z.device)
    return z.mean(dim=0).square().mean()+(covariance-eye).square().mean()


def observations(r,generator,scale=1.):
    nuisance=scale*torch.randn((len(r),8),dtype=r.dtype,device=r.device,generator=generator)
    return torch.cat([r,nuisance],dim=-1)


def train_world(kind,seed,data,steps=2000,lr=.003,anchor_weight=1.,batch=128,target_grad='stop',invariance_weight=0.,algebra_weight=0.):
    import time
    torch.manual_seed(seed)
    model=JEPAWorld(kind)
    opt=torch.optim.Adam(model.parameters(),lr=lr)
    x=torch.tensor(data['x'],dtype=torch.float32);y=torch.tensor(data['y'],dtype=torch.float32)
    g=torch.tensor(data['gate'],dtype=torch.long);duration=torch.tensor(data['duration'],dtype=torch.float32)
    # Independent RNGs guarantee identical example IDs and nuisance observations
    # across models, regardless of how many flow-time/noise draws each consumes.
    index_rng=torch.Generator().manual_seed(seed+100000)
    view_rng=torch.Generator().manual_seed(seed+200000)
    flow_rng=torch.Generator().manual_seed(seed+300000)
    invariance_rng=torch.Generator().manual_seed(seed+400000)
    if target_grad not in ('stop','joint','stop_velocity'):raise ValueError(target_grad)
    if algebra_weight and kind!='latent_generator':raise ValueError('Algebra prior requires generator')
    history=[];start=time.perf_counter()
    for step in range(steps):
        idx=torch.randint(len(x),(batch,),generator=index_rng)
        current=model.encoder(observations(x[idx],view_rng))
        future=model.encoder(observations(y[idx],view_rng))
        target=future if target_grad=='joint' else future.detach()
        if kind in ('direct','latent_generator'):
            pred=model.advance(current,g[idx],duration[idx])
            prediction=(pred-target).square().mean()
        else:
            base=current if kind=='source_chord' else torch.randn(current.shape,generator=flow_rng)
            tau=torch.rand(batch,generator=flow_rng)
            state=(1-tau[:,None])*base+tau[:,None]*target
            velocity=target-base
            if target_grad=='stop_velocity':velocity=velocity.detach()
            prediction=(model.field(state,tau,current,g[idx],duration[idx])-velocity).square().mean()
        anchor=(covariance_anchor(current)+covariance_anchor(future))/2
        invariance=torch.zeros((),dtype=current.dtype)
        if invariance_weight:
            augmented=model.encoder(observations(x[idx],invariance_rng))
            invariance=(current-augmented).square().mean()
        algebra=torch.zeros((),dtype=current.dtype)
        if algebra_weight:
            from .algebra import gate_algebra_penalty
            algebra=gate_algebra_penalty(model.raw_generator)
        loss=prediction+anchor_weight*anchor+invariance_weight*invariance+algebra_weight*algebra
        opt.zero_grad();loss.backward();grad=torch.nn.utils.clip_grad_norm_(model.parameters(),10);opt.step()
        if not torch.isfinite(loss) or not torch.isfinite(grad):raise FloatingPointError('Nonfinite JEPA training')
        if step%200==0 or step==steps-1:history.append(dict(step=step,loss=float(loss.detach()),prediction=float(prediction.detach()),anchor=float(anchor.detach()),invariance=float(invariance.detach()),algebra=float(algebra.detach())))
    return model,dict(seconds=time.perf_counter()-start,history=history,steps=steps,
        reconstruction_loss=False,target=target_grad,invariance_weight=invariance_weight,algebra_weight=algebra_weight,
        parameters=sum(p.numel() for p in model.parameters()))


def fit_readout(model,r,seed,steps=1200):
    """Freeze encoder, then fit a physical evaluation probe on independent states."""
    torch.manual_seed(seed)
    model.eval()
    with torch.no_grad():z=model.encoder(torch.cat([r,torch.zeros(len(r),8)],dim=-1))
    readout=nn.Sequential(nn.Linear(15,128),nn.SiLU(),nn.Linear(128,128),nn.SiLU(),nn.Linear(128,15))
    opt=torch.optim.Adam(readout.parameters(),lr=.003)
    generator=torch.Generator().manual_seed(seed+100000)
    for step in range(steps):
        idx=torch.randint(len(z),(128,),generator=generator)
        loss=(readout(z[idx])-r[idx]).square().mean()
        opt.zero_grad();loss.backward();opt.step()
    return readout
