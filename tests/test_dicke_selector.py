"""Check initializer amplitudes, clean counter and optimized-circuit equivalence."""
import unittest
import numpy as np
from qiskit.quantum_info import Statevector
from wildfire_lab.dicke_selector import preparation, circuit
from wildfire_lab.selector_sector import Sector


class DickeTests(unittest.TestCase):
    def test_uniform_dicke_and_zero_counter(self):
        for n,k in [(4,1),(4,2),(6,4),(10,4)]:
            state = Statevector.from_instruction(preparation(n,k)).data
            eligible = np.array([i for i in range(2**n) if i.bit_count()==k])
            np.testing.assert_allclose(state[eligible],1/np.sqrt(len(eligible)),atol=1e-10)
            self.assertAlmostEqual(float(np.sum(abs(state[eligible])**2)),1.)

    def test_sector_equivalence_with_penalty_removed(self):
        n,k,p = 6,4,2.
        rng = np.random.default_rng(71)
        obj = dict(linear=rng.normal(size=n)+p*(1-2*k),
                   pair=np.triu(rng.random((n,n))+2*p,1),constant=p*k*k,k=k,penalty=p)
        sector = Sector(obj)
        for parameters in [[.4,.2],[.4,.2,.7,-.3]]:
            full = Statevector.from_instruction(circuit(obj,parameters)).data
            small = sector.state(parameters)
            phase = np.vdot(small,full[sector.states])
            np.testing.assert_allclose(full[sector.states],phase*small,atol=1e-10)
            self.assertAlmostEqual(float(abs(phase)),1.)


if __name__=='__main__':
    unittest.main()
