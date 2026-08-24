from dataclasses import dataclass, field
import os

@dataclass
class BeamConfig:
    energy: float = 12.0
    energy_spread: float = 0.03
    ssd: float = 100.0
    field_size: float = 10.0
    n_histories: int = 100000

@dataclass
class PhantomConfig:
    size_x: float = 10.0
    size_y: float = 10.0
    size_z: float = 10.0
    voxel_size: float = 0.2
    material: str = 'water'
    density: float = 1.0

@dataclass
class TransportConfig:
    e_cut_kinetic: float = 0.01
    p_cut: float = 0.001
    ae_kinetic: float = 0.01
    ap: float = 0.01
    step_fraction_xi: float = 0.03

@dataclass
class SimulationConfig:
    beam: BeamConfig = field(default_factory=BeamConfig)
    phantom: PhantomConfig = field(default_factory=PhantomConfig)
    transport: TransportConfig = field(default_factory=TransportConfig)
    output_dir: str = 'output'
    seed: int = 42

    def __post_init__(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
