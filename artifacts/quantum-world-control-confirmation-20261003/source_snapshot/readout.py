"""Positive physical evaluation readout, trained only on frozen representations."""
import torch
from torch import nn
from .physics import PAULIS


class PhysicalReadout(nn.Module):
    def __init__(self,latent_dim=15,width=128):
        super().__init__()
        self.net=nn.Sequential(nn.Linear(latent_dim,width),nn.SiLU(),nn.Linear(width,width),nn.SiLU(),nn.Linear(width,15))

    def density(self,z):
        logits=self.net(z)
        dtype=torch.complex128 if logits.dtype==torch.float64 else torch.complex64
        basis=torch.tensor(PAULIS,dtype=dtype,device=logits.device)
        h=torch.einsum('ni,iab->nab',logits.to(dtype),basis)
        shift=torch.linalg.eigvalsh(h).amax(dim=-1).detach()
        rho=torch.matrix_exp(h-shift[:,None,None]*torch.eye(4,device=h.device,dtype=dtype))
        return rho/rho.diagonal(dim1=-2,dim2=-1).sum(dim=-1).real[:,None,None]

    def forward(self,z):
        rho=self.density(z)
        basis=torch.tensor(PAULIS,dtype=rho.dtype,device=rho.device)
        return torch.einsum('nab,iba->ni',rho,basis).real


def fit_physical_readout(model,r,seed,steps=1800):
    """Targets are evaluation calibration data; no gradients reach the encoder."""
    torch.manual_seed(seed)
    with torch.no_grad():z=model.encoder(torch.cat([r,torch.zeros(len(r),8)],dim=-1))
    probe=PhysicalReadout(z.shape[-1])
    opt=torch.optim.Adam(probe.parameters(),lr=.003)
    rng=torch.Generator().manual_seed(seed+100000)
    for _ in range(steps):
        idx=torch.randint(len(r),(128,),generator=rng)
        loss=(probe(z[idx])-r[idx]).square().mean()
        opt.zero_grad();loss.backward();opt.step()
    return probe
