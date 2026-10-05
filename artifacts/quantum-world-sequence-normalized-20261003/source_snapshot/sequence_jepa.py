"""Matched observed triplets: teacher forcing versus short free-running consistency."""
import time
import numpy as np
import torch
from .physics import haar_states,state_to_pauli,unitary
from .jepa import JEPAWorld,observations,covariance_anchor


def triplets(n,seed):
    psi=haar_states(n,seed);rng=np.random.default_rng(seed+100000)
    states=[psi];gates=[];durations=[]
    for _ in range(2):
        g=rng.integers(0,6,n);t=np.where(g>=4,rng.uniform(-1.2,1.2,n),1.)
        psi=np.array([unitary(int(k),float(d))@s for k,d,s in zip(g,t,psi)])
        states.append(psi);gates.append(g);durations.append(t)
    return dict(observed=state_to_pauli(np.array(states)),psi=np.array(states),gate=np.array(gates),duration=np.array(durations))


def prediction_objective(teacher,rollout,consistency,normalize=False):
    """Keep prediction weight fixed when testing a different supervision mixture."""
    if consistency < 0:raise ValueError('Consistency weight must be nonnegative')
    return (teacher+consistency*rollout)/(1+consistency if normalize else 1)


def train_sequence(kind,seed,data,steps=4000,consistency=1.,batch=64,lr=.003,normalize_prediction=False):
    if kind not in ('direct','latent_generator'):raise ValueError(kind)
    torch.manual_seed(seed);model=JEPAWorld(kind);optimizer=torch.optim.Adam(model.parameters(),lr=lr)
    x=torch.tensor(data['observed'],dtype=torch.float32);g=torch.tensor(data['gate']);t=torch.tensor(data['duration'],dtype=torch.float32)
    indices=torch.Generator().manual_seed(seed+100000);views=torch.Generator().manual_seed(seed+200000)
    augment=torch.Generator().manual_seed(seed+400000);history=[];started=time.perf_counter()
    for step in range(steps):
        idx=torch.randint(x.shape[1],(batch,),generator=indices)
        z=[model.encoder(observations(x[k,idx],views)) for k in range(3)]
        first=model.advance(z[0],g[0,idx],t[0,idx]);second=model.advance(z[1],g[1,idx],t[1,idx])
        teacher=((first-z[1].detach()).square().mean()+(second-z[2].detach()).square().mean())/2
        rollout=torch.zeros((),dtype=first.dtype)
        if consistency:
            free=model.advance(first,g[1,idx],t[1,idx])
            rollout=(free-z[2].detach()).square().mean()
        anchor=sum(covariance_anchor(v) for v in z)/3
        agreement=(z[0]-model.encoder(observations(x[0,idx],augment))).square().mean()
        loss=prediction_objective(teacher,rollout,consistency,normalize_prediction)+20*anchor+agreement
        optimizer.zero_grad();loss.backward();gradient=torch.nn.utils.clip_grad_norm_(model.parameters(),10.)
        if not torch.isfinite(loss) or not torch.isfinite(gradient):raise FloatingPointError('Nonfinite sequence training')
        optimizer.step()
        if step%200==0 or step==steps-1:history.append(dict(step=step,loss=float(loss.detach()),teacher=float(teacher.detach()),
            rollout=float(rollout.detach()),anchor=float(anchor.detach()),agreement=float(agreement.detach())))
    return model,dict(seconds=time.perf_counter()-started,steps=steps,batch=batch,lr=lr,consistency=consistency,
        reconstruction_loss=False,normalize_prediction=normalize_prediction,
        targets='stop-gradient intermediate/final encoder, same observed triplets',
        extra_compute='one additional free-running transition when consistency is enabled',history=history)
