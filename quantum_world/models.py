"""Controlled noncollapsing latent basis, endpoint flows and reversible generators.

The orthogonal encoder is a learned change of coordinates, NOT learned compression
or a claim to reproduce V-JEPA. It isolates dynamics from representation collapse.
"""
from __future__ import annotations
import torch
from torch import nn
from .physics import LIE_BASIS


class OrthogonalEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.raw=nn.Parameter(torch.zeros(15,15))

    def matrix(self):
        a=(self.raw-self.raw.T)/2
        eye=torch.eye(15,device=a.device,dtype=a.dtype)
        # Cayley transform: smooth orthogonal, exactly invertible.
        return torch.linalg.solve(eye+a,eye-a)

    def forward(self,x):
        return x@self.matrix().T

    def decode(self,z):
        return z@self.matrix()


def action_features(gate,duration):
    onehot=torch.nn.functional.one_hot(gate,6).to(duration.dtype)
    return torch.cat([onehot,duration.sin()[:,None],duration.cos()[:,None]],dim=-1)


class LatentModel(nn.Module):
    def __init__(self, kind: str, width: int=96):
        super().__init__()
        if kind not in ('direct','chord','source_chord','generator','hamiltonian'):
            raise ValueError(kind)
        self.kind=kind
        self.encoder=OrthogonalEncoder()
        if kind in ('generator','hamiltonian'):
            if kind=='generator':
                self.raw=nn.Parameter(torch.zeros(6,15,15))
            else:
                self.coefficients=nn.Parameter(torch.zeros(6,15))
                self.register_buffer('lie',torch.tensor(LIE_BASIS,dtype=torch.float32))
        else:
            inp=15+8+(0 if kind=='direct' else 1)+(15 if kind=='source_chord' else 0)
            self.net=nn.Sequential(nn.Linear(inp,width),nn.SiLU(),nn.Linear(width,width),nn.SiLU(),nn.Linear(width,15))

    def matrices(self):
        if self.kind=='hamiltonian':
            physical=torch.einsum('gi,ijk->gjk',self.coefficients,self.lie)
            q=self.encoder.matrix()
            return q@physical@q.T
        return (self.raw-self.raw.transpose(-1,-2))/2

    def velocity(self,z,gate,duration,tau=None,source=None):
        if self.kind in ('generator','hamiltonian'):
            return torch.einsum('nij,nj->ni',self.matrices()[gate],z)*duration[:,None]
        features=[z,action_features(gate,duration)]
        if self.kind!='direct': features.append(tau[:,None])
        if self.kind=='source_chord': features.append(source)
        return self.net(torch.cat(features,dim=-1))

    def advance(self,z,gate,duration,steps=16):
        if self.kind=='direct':
            return self.velocity(z,gate,duration)
        if self.kind in ('generator','hamiltonian'):
            rotations=torch.matrix_exp(self.matrices()[gate]*duration[:,None,None])
            return torch.einsum('nij,nj->ni',rotations,z)
        source=z
        h=1/steps
        for i in range(steps):
            t=torch.full_like(duration,i*h)
            k1=self.velocity(z,gate,duration,t,source)
            k2=self.velocity(z+h*k1/2,gate,duration,t+h/2,source)
            k3=self.velocity(z+h*k2/2,gate,duration,t+h/2,source)
            k4=self.velocity(z+h*k3,gate,duration,t+h,source)
            z=z+h*(k1+2*k2+2*k3+k4)/6
        return z

    def predict(self,x,gate,duration,steps=16):
        return self.encoder.decode(self.advance(self.encoder(x),gate,duration,steps))


class PauliLinearBaseline:
    """Least squares with exact RZ periodic basis; a strong classical comparator.

    Discrete gates use a constant matrix; RZ uses 1, cos(theta), sin(theta).
    Neither ground-truth transition matrices nor Hamiltonians are provided.
    """
    def fit(self,data,ridge=1e-8):
        import numpy as np
        self.coefficients=[]
        for g in range(6):
            mask=data['gate']==g
            x=data['x'][mask]; y=data['y'][mask]; t=data['duration'][mask]
            features=x if g<4 else np.concatenate([x,x*np.cos(t[:,None]),x*np.sin(t[:,None])],axis=1)
            self.coefficients.append(np.linalg.solve(features.T@features+ridge*np.eye(features.shape[1]),features.T@y))
        return self

    def predict(self,x,gate,duration,steps=16):
        import numpy as np
        result=np.empty_like(x)
        for g in range(6):
            mask=gate==g
            f=x[mask] if g<4 else np.concatenate([x[mask],x[mask]*np.cos(duration[mask,None]),x[mask]*np.sin(duration[mask,None])],axis=1)
            result[mask]=f@self.coefficients[g]
        return result
