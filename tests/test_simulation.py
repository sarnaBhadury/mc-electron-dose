import unittest
import numpy as np
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import SimulationConfig, BeamConfig, PhantomConfig, TransportConfig
from transport.simulation import MonteCarloSimulation

class TestMonteCarloSimulation(unittest.TestCase):
    def setUp(self):
        # Create a small, fast simulation configuration for testing
        self.beam = BeamConfig(energy=6.0, n_histories=100, field_size=5.0)
        self.phantom = PhantomConfig(size_x=5.0, size_y=5.0, size_z=5.0, voxel_size=0.5)
        # Higher cutoffs for speed during testing
        self.transport = TransportConfig(e_cut_kinetic=0.1, p_cut=0.01) 
        self.config = SimulationConfig(
            beam=self.beam, 
            phantom=self.phantom, 
            transport=self.transport, 
            output_dir='test_output', 
            seed=42
        )
        self.sim = MonteCarloSimulation(self.config)

    def test_initialization(self):
        """Test that the simulation initializes correctly."""
        self.assertIsNotNone(self.sim.phantom)
        self.assertIsNotNone(self.sim.scorer)
        self.assertEqual(self.sim.total_energy_in, 0.0)

    def test_run_simulation(self):
        """Test running a small simulation."""
        elapsed = self.sim.run()
        
        # Check elapsed time is recorded
        self.assertGreater(elapsed, 0)
        
        # Check energy conservation
        total_dep = np.sum(self.sim.scorer.energy_deposited)
        
        # At least some energy should be deposited
        self.assertGreater(total_dep, 0)
        
        # Some energy might escape the phantom, so deposited should be <= total_in
        # (Using a small margin of error for floating point arithmetic)
        self.assertLessEqual(total_dep, self.sim.total_energy_in + 1e-6)
        
        # Ensure that no negative doses were recorded
        self.assertTrue(np.all(self.sim.scorer.dose >= 0))
        
        # Ensure depth dose profile is generated and has correct dimensions
        depths, pdd, pdd_unc = self.sim.scorer.get_depth_dose()
        expected_len = int(np.ceil(self.phantom.size_z / self.phantom.voxel_size))
        self.assertEqual(len(depths), expected_len)
        self.assertTrue(np.any(pdd > 0))

if __name__ == '__main__':
    unittest.main()
