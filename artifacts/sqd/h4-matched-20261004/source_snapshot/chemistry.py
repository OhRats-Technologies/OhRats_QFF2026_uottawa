"""Hydrogen chains in a complete STO-3G active space; no integral downloads."""
from dataclasses import dataclass
import numpy as np
from pyscf import gto, scf, mcscf, ao2mo, fci
from qiskit_nature.second_q.hamiltonians import ElectronicEnergy
from qiskit_nature.second_q.mappers import JordanWignerMapper


@dataclass
class Molecule:
    hcore: np.ndarray
    eri: np.ndarray
    offset: float
    norb: int
    nelec: tuple[int, int]
    hamiltonian: object
    hf_energy: float
    exact_energy: float


def hydrogen_chain(atoms=2, distance=.735):
    if atoms not in (2, 4) or distance <= 0:
        raise ValueError('Use 2 or 4 hydrogen atoms and a positive distance in angstrom')
    geometry='; '.join(f'H 0 0 {i*distance}' for i in range(atoms))
    mol=gto.M(atom=geometry, basis='sto-3g', spin=0, verbose=0)
    meanfield=scf.RHF(mol).run()
    if not meanfield.converged:raise RuntimeError('Hartree-Fock did not converge')
    active=mcscf.CASCI(meanfield, atoms, atoms)
    hcore, offset=active.get_h1eff();eri=ao2mo.restore(1,active.get_h2eff(),atoms)
    nelec=tuple(active.nelecas)
    energy,_=fci.direct_spin1.kernel(hcore,eri,atoms,nelec)
    operator=ElectronicEnergy.from_raw_integrals(hcore,eri).second_q_op()
    return Molecule(hcore,eri,float(offset),atoms,nelec,JordanWignerMapper().map(operator),
                    float(meanfield.e_tot),float(energy+offset))
