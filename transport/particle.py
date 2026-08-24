import numpy as np
from enum import IntEnum

class ParticleType(IntEnum):
    ELECTRON = 0
    PHOTON = 1
    POSITRON = 2

class Particle:
    __slots__ = ['x', 'y', 'z', 'u', 'v', 'w', 'energy', 'ptype', 'weight', 'alive']
    
    def __init__(self, x=0.0, y=0.0, z=0.0, u=0.0, v=0.0, w=1.0, 
                 energy=0.0, ptype=ParticleType.ELECTRON, weight=1.0):
        self.x = x
        self.y = y
        self.z = z
        self.u = u  # direction cosine x
        self.v = v  # direction cosine y
        self.w = w  # direction cosine z (beam direction)
        self.energy = energy  # kinetic energy in MeV
        self.ptype = ptype
        self.weight = weight
        self.alive = True
    
    def copy(self):
        p = Particle(self.x, self.y, self.z, self.u, self.v, self.w,
                     self.energy, self.ptype, self.weight)
        p.alive = self.alive
        return p
