import numpy as np

from physics.cross_sections import (photon_mean_free_path, sample_compton_scattering,
                                      photon_interaction_type)
from physics.scattering import rotate_direction
from transport.particle import Particle, ParticleType

def transport_photon(particle, phantom, dose_scorer, secondary_stack, rng, config, track_log=None):
    """
    Transport a single photon through the phantom.
    
    Algorithm:
    1. Sample distance to next interaction: s = -lambda * ln(rand)
    2. Move photon to interaction point
    3. If escaped phantom: return
    4. Determine interaction type (Compton vs photoelectric vs pair production)
    5. For Compton: sample scattered photon energy and angle (Klein-Nishina), create recoil electron
    6. For photoelectric: deposit all energy, create photoelectron
    7. For pair production: create e-/e+ pair
    8. Continue until absorbed or escaped
    
    config has attribute: p_cut (photon cutoff energy in MeV)
    """
    while particle.alive and particle.energy > config.p_cut:
        if not phantom.is_inside(particle.x, particle.y, particle.z):
            particle.alive = False
            return
            
        # 1. Sample distance to next interaction
        lambda_photon = photon_mean_free_path(particle.energy)
        if lambda_photon <= 0:
            break
        
        # -lambda * ln(rand)
        # Note: if lambda_photon is mean free path, s = -lambda_photon * ln(rand)
        s = -lambda_photon * np.log(rng.uniform())
        
        # 2. Move photon
        particle.x += s * particle.u
        particle.y += s * particle.v
        particle.z += s * particle.w
        
        if track_log is not None:
            track_log.append({"id": id(particle), "x": particle.x, "y": particle.y, "z": particle.z, "type": "photon", "energy": particle.energy})
        
        # 3. If escaped phantom: return
        if not phantom.is_inside(particle.x, particle.y, particle.z):
            particle.alive = False
            return
            
        voxel_idx = phantom.position_to_voxel(particle.x, particle.y, particle.z)
        if voxel_idx is None:
            particle.alive = False
            return
        ix, iy, iz = voxel_idx
            
        # 4. Determine interaction type
        interaction = photon_interaction_type(particle.energy, rng)
        
        if interaction == 'compton':
            # 5. For Compton: sample scattered photon energy and angle (Klein-Nishina), create recoil electron
            e_scattered, theta, phi = sample_compton_scattering(particle.energy, rng)
            e_recoil = particle.energy - e_scattered
            
            if e_recoil > 0:
                sec = Particle(particle.x, particle.y, particle.z, 
                               particle.u, particle.v, particle.w, 
                               e_recoil, ParticleType.ELECTRON, particle.weight)
                secondary_stack.append(sec)
                
            if e_scattered > config.p_cut:
                particle.energy = e_scattered
                u_new, v_new, w_new = rotate_direction(particle.u, particle.v, particle.w, theta, phi)
                particle.u, particle.v, particle.w = u_new, v_new, w_new
            else:
                dose_scorer.score(ix, iy, iz, e_scattered, particle.weight)
                particle.alive = False
                
        elif interaction == 'photoelectric':
            # 6. For photoelectric: deposit all energy, create photoelectron
            # Create a photoelectron with the full energy (ignoring binding energy for simplicity)
            sec = Particle(particle.x, particle.y, particle.z, 
                           particle.u, particle.v, particle.w, 
                           particle.energy, ParticleType.ELECTRON, particle.weight)
            secondary_stack.append(sec)
            particle.alive = False
            
        elif interaction == 'pair_production':
            # 7. For pair production: create e-/e+ pair
            e_remaining = particle.energy - 1.022
            if e_remaining > 0:
                e_elec = e_remaining / 2.0
                e_pos = e_remaining / 2.0
                
                sec_e = Particle(particle.x, particle.y, particle.z, 
                               particle.u, particle.v, particle.w, 
                               e_elec, ParticleType.ELECTRON, particle.weight)
                sec_p = Particle(particle.x, particle.y, particle.z, 
                               particle.u, particle.v, particle.w, 
                               e_pos, ParticleType.POSITRON, particle.weight)
                secondary_stack.append(sec_e)
                secondary_stack.append(sec_p)
            else:
                # If energy is exactly 1.022 or less but somehow chosen, deposit it
                dose_scorer.score(ix, iy, iz, particle.energy, particle.weight)
            particle.alive = False

    # 8. Continue until absorbed or escaped
    if particle.alive and particle.energy > 0:
        voxel_idx = phantom.position_to_voxel(particle.x, particle.y, particle.z)
        if voxel_idx is not None:
            dose_scorer.score(voxel_idx[0], voxel_idx[1], voxel_idx[2], particle.energy, particle.weight)
        if track_log is not None:
            track_log.append({"x": particle.x, "y": particle.y, "z": particle.z, "type": "photon", "energy": particle.energy})
        particle.alive = False
