"""Transferred-encoder periodic regression: isolates dynamics from representation."""
import numpy as np
import torch
from torch import nn


class LatentLinear(nn.Module):
    kind='periodic_linear'
    def __init__(self,encoder):
        super().__init__();self.encoder=encoder

    def fit(self,data,ridge=1e-6):
        with torch.no_grad():
            def encode(r):
                r=torch.tensor(r,dtype=torch.float64)
                return self.encoder(torch.cat([r,torch.zeros(len(r),8,dtype=r.dtype)],dim=-1)).numpy()
            x=encode(data['x']);y=encode(data['y'])
        self.coefficients=[]
        for g in range(6):
            mask=data['gate']==g
            z=np.column_stack([x[mask],np.ones(mask.sum())]);t=data['duration'][mask]
            f=z if g<4 else np.concatenate([z,z*np.cos(t[:,None]),z*np.sin(t[:,None])],axis=1)
            self.coefficients.append(torch.tensor(np.linalg.solve(f.T@f+ridge*np.eye(f.shape[1]),f.T@y[mask]),dtype=torch.float64))
        return self

    def advance(self,z,gate,duration,noise=None):
        # Differentiable in state and duration, with fitted coefficients frozen.
        result=torch.zeros_like(z)
        for g in range(6):
            mask=gate==g
            x=torch.cat([z[mask],torch.ones(int(mask.sum()),1,dtype=z.dtype)],dim=-1)
            t=duration[mask,None]
            f=x if g<4 else torch.cat([x,x*t.cos(),x*t.sin()],dim=-1)
            result[mask]=f@self.coefficients[g]
        return result
