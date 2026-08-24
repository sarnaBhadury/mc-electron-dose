import numpy as np
import time
from transport.particle import Particle, ParticleType
from transport.electron_transport import transport_electron
from transport.photon_transport import transport_photon
from geometry.voxel_phantom import VoxelPhantom
from scoring.dose_scorer import DoseScorer

class MonteCarloSimulation:
    def __init__(self, config):
        """Initialize simulation with SimulationConfig."""
        self.config = config
        self.phantom = VoxelPhantom(
            config.phantom.size_x, config.phantom.size_y, config.phantom.size_z,
            config.phantom.voxel_size, config.phantom.density
        )
        self.scorer = DoseScorer(self.phantom)
        self.rng = np.random.RandomState(config.seed)
        self.total_energy_in = 0.0
        self.total_energy_deposited = 0.0
        self.total_energy_escaped = 0.0
    
    def generate_primary_electron(self):
        """Generate a primary electron from the beam source."""
        beam = self.config.beam
        # Position: random within field size, centered on phantom
        cx = self.phantom.size_x / 2.0
        cy = self.phantom.size_y / 2.0
        half_field = beam.field_size / 2.0
        x = cx + self.rng.uniform(-half_field, half_field)
        y = cy + self.rng.uniform(-half_field, half_field)
        z = 0.0  # enter at surface
        
        # Direction: primarily along z with small angular spread
        # For divergent beam from SSD:
        theta_max = np.arctan(half_field / beam.ssd)  # small angle
        theta = self.rng.normal(0, theta_max * 0.1)  # small spread
        phi = self.rng.uniform(0, 2*np.pi)
        u = np.sin(theta) * np.cos(phi)
        v = np.sin(theta) * np.sin(phi)
        w = np.cos(theta)
        
        # Energy: Gaussian spread
        energy = self.rng.normal(beam.energy, beam.energy * beam.energy_spread)
        energy = max(energy, self.config.transport.e_cut_kinetic + 0.001)
        
        return Particle(x, y, z, u, v, w, energy, ParticleType.ELECTRON)
    
    def run(self, progress_callback=None, record_tracks=False):
        """Run the full simulation."""
        n_histories = self.config.beam.n_histories
        start_time = time.time()
        
        all_tracks = [] if record_tracks else None
        
        for i in range(n_histories):
            # Generate primary
            primary = self.generate_primary_electron()
            self.total_energy_in += primary.energy
            
            if record_tracks:
                all_tracks.append({"id": id(primary), "x": primary.x, "y": primary.y, "z": primary.z, "type": "primary", "energy": primary.energy})
            
            # Transport primary and all secondaries
            stack = [primary]
            while stack:
                particle = stack.pop()
                if particle.ptype in (ParticleType.ELECTRON, ParticleType.POSITRON):
                    transport_electron(particle, self.phantom, self.scorer, stack, self.rng, self.config.transport, all_tracks)
                elif particle.ptype == ParticleType.PHOTON:
                    transport_photon(particle, self.phantom, self.scorer, stack, self.rng, self.config.transport, all_tracks)
            
            # Commit history to scorer
            self.scorer.end_history()
            
            # Progress
            if progress_callback and (i+1) % max(1, n_histories//100) == 0:
                elapsed = time.time() - start_time
                progress_callback(i+1, n_histories, elapsed)
        
        self.scorer.finalize(n_histories)
        elapsed = time.time() - start_time
        
        if record_tracks:
            return elapsed, all_tracks
        return elapsed
