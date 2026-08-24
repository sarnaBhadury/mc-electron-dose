import numpy as np
from scoring.dose_scorer import DoseScorer

class DummyPhantom:
    def __init__(self):
        self.nx = 10
        self.ny = 10
        self.nz = 10
        self.voxel_size = 0.5
    
    def voxel_mass(self):
        return 1.0

phantom = DummyPhantom()
scorer = DoseScorer(phantom)
scorer.score(5, 5, 5, 10.0)
scorer.end_history()
scorer.finalize(1)
try:
    scorer.get_depth_dose()
except Exception as e:
    import traceback
    traceback.print_exc()

try:
    scorer.get_lateral_profile(2.5, 'x')
except Exception as e:
    import traceback
    traceback.print_exc()

