import numpy as np

from physics.stopping_power import (get_total_stopping_power, get_csda_range, 
                                      get_restricted_collision_sp, get_collision_stopping_power,
                                      get_radiative_stopping_power)
from physics.cross_sections import (moller_mean_free_path, bremsstrahlung_mean_free_path,
                                      sample_moller_energy_transfer, sample_bremsstrahlung_energy)
from physics.scattering import (highland_theta_rms, sample_scattering_angles, rotate_direction)
from transport.particle import Particle, ParticleType

def transport_electron(particle, phantom, dose_scorer, secondary_stack, rng, config, track_log=None):
    """
    Transport a single electron through the phantom using Condensed History.
    
    Algorithm per step:
    1. If particle outside phantom or energy < e_cut: deposit remaining energy, return
    2. Check range rejection: if CSDA_range(E) < distance_to_boundary, deposit all energy locally
    3. Compute step size: s = min(xi * E / S_total(E), d_boundary * 0.99)
    4. Sample distance to hard Moller event: s_moller = -lambda_moller * ln(rand)
    5. Sample distance to hard Bremsstrahlung: s_brem = -lambda_brem * ln(rand)
    6. Actual step = min(s, s_moller, s_brem, d_boundary)
    7. If step hits boundary: take step to boundary, cross to next voxel
    8. Apply continuous energy loss: dE = step * L_restricted(E) * density
    9. Apply energy loss straggling: Gaussian with Bohr variance
    10. Apply Multiple Coulomb Scattering: Highland theta -> rotate direction
    11. Update position: x += step * u (using original direction before scattering for half, new direction for half)
    12. Score energy deposited in current voxel
    13. If hard Moller event occurred: create delta-ray secondary
    14. If hard Brem event occurred: create photon secondary
    15. Repeat until energy < e_cut or escaped
    
    config is a dict-like object with attributes: e_cut_kinetic, ae_kinetic, ap, step_fraction_xi
    """
    density = phantom.density
    
    # Track the number of mean free paths to the next hard events across steps
    n_mfp_moller = -np.log(rng.uniform(1e-12, 1.0))
    n_mfp_brem = -np.log(rng.uniform(1e-12, 1.0))
    
    while particle.alive and particle.energy > config.e_cut_kinetic:
        # 1. If particle outside phantom: return
        if not phantom.is_inside(particle.x, particle.y, particle.z):
            particle.alive = False
            return
            
        voxel_idx = phantom.position_to_voxel(particle.x, particle.y, particle.z)
        if voxel_idx is None:
            if track_log is not None:
                track_log.append({"id": id(particle), "x": particle.x, "y": particle.y, "z": particle.z, "type": "electron", "energy": particle.energy})
            particle.alive = False
            return
        ix, iy, iz = voxel_idx
        
        # 2. Check range rejection
        csda_range = get_csda_range(particle.energy) / density  # convert g/cm2 to cm
        d_boundary = phantom.distance_to_boundary(particle.x, particle.y, particle.z, 
                                                  particle.u, particle.v, particle.w)
        
        if csda_range < d_boundary:
            # Deposit all energy locally
            dose_scorer.score(ix, iy, iz, particle.energy, particle.weight)
            particle.energy = 0
            particle.alive = False
            return
            
        # 3. Compute step size
        s_total = get_total_stopping_power(particle.energy)
        s_max = config.step_fraction_xi * particle.energy / (s_total * density) if s_total > 0 else 1e-6
        s = min(s_max, d_boundary * 0.99)
        
        # 4. Sample distance to hard Moller event
        lambda_moller = moller_mean_free_path(particle.energy, density=density, ae_kinetic=config.ae_kinetic)
        s_moller = n_mfp_moller * lambda_moller if lambda_moller < 1e9 else 1e10
        
        # 5. Sample distance to hard Bremsstrahlung
        lambda_brem = bremsstrahlung_mean_free_path(particle.energy, density=density, ap=config.ap)
        s_brem = n_mfp_brem * lambda_brem if lambda_brem < 1e9 else 1e10
        
        # 6. Actual step
        actual_step = min(s, s_moller, s_brem, d_boundary)
        if actual_step <= 0:
            actual_step = 1e-6 # fallback
        
        # 8. Apply continuous energy loss
        # Use restricted collision SP + radiative SP for continuous energy loss.
        # This properly excludes hard collision events (which are explicitly simulated)
        # while accounting for the missing radiative loss that was causing deep penetration.
        s_col_res = get_restricted_collision_sp(particle.energy, config.ae_kinetic)
        s_rad = get_radiative_stopping_power(particle.energy)
        l_continuous = s_col_res + s_rad
        de_mean = actual_step * l_continuous * density
        
        # 9. Apply energy loss straggling
        bohr_sigma_sq = 0.0852 * config.ae_kinetic * density * actual_step
        sigma = np.sqrt(max(bohr_sigma_sq, 0.0))
        de = rng.normal(de_mean, sigma)
        de = np.clip(de, 0.0, particle.energy)
        
        # 10. Apply Multiple Coulomb Scattering
        theta_rms = highland_theta_rms(particle.energy, actual_step)
        theta, phi = sample_scattering_angles(theta_rms, rng)
        
        # 11. Update position
        u_old, v_old, w_old = particle.u, particle.v, particle.w
        
        u_new, v_new, w_new = rotate_direction(particle.u, particle.v, particle.w, theta, phi)
        particle.u, particle.v, particle.w = u_new, v_new, w_new
        
        # Half step with old direction, half with new
        dx = actual_step * 0.5 * (u_old + u_new)
        dy = actual_step * 0.5 * (v_old + v_new)
        dz = actual_step * 0.5 * (w_old + w_new)
        
        particle.x += dx
        particle.y += dy
        particle.z += dz
        
        if track_log is not None:
            track_log.append({"id": id(particle), "x": particle.x, "y": particle.y, "z": particle.z, "type": "electron", "energy": particle.energy})
        
        # 12. Score energy deposited
        dose_scorer.score(ix, iy, iz, de, particle.weight)
        particle.energy -= de
        
        if particle.energy <= config.e_cut_kinetic:
            break
            
        # Update mean free paths consumed in this step
        if lambda_moller < 1e9:
            n_mfp_moller = max(0.0, n_mfp_moller - actual_step / lambda_moller)
        if lambda_brem < 1e9:
            n_mfp_brem = max(0.0, n_mfp_brem - actual_step / lambda_brem)
            
        # 13. Hard Moller event — create delta-ray secondary
        # Hard events are explicitly simulated, so their energy is subtracted
        # from the primary electron to maintain energy conservation.
        if actual_step == s_moller:
            n_mfp_moller = -np.log(rng.uniform(1e-12, 1.0)) # reset for next event
            e_transfer = sample_moller_energy_transfer(particle.energy, config.ae_kinetic, rng)
            if 0 < e_transfer < particle.energy:
                particle.energy -= e_transfer
                sec = Particle(particle.x, particle.y, particle.z, 
                               particle.u, particle.v, particle.w, 
                               e_transfer, ParticleType.ELECTRON, particle.weight)
                secondary_stack.append(sec)
                
        # 14. Hard Brem event — create photon secondary
        elif actual_step == s_brem:
            n_mfp_brem = -np.log(rng.uniform(1e-12, 1.0)) # reset for next event
            e_gamma = sample_bremsstrahlung_energy(particle.energy, config.ap, rng)
            if 0 < e_gamma < particle.energy:
                particle.energy -= e_gamma
                sec = Particle(particle.x, particle.y, particle.z, 
                               particle.u, particle.v, particle.w, 
                               e_gamma, ParticleType.PHOTON, particle.weight)
                secondary_stack.append(sec)

    # 1. If energy < e_cut: deposit remaining energy
    if particle.alive and particle.energy > 0:
        voxel_idx = phantom.position_to_voxel(particle.x, particle.y, particle.z)
        if voxel_idx is not None:
            dose_scorer.score(voxel_idx[0], voxel_idx[1], voxel_idx[2], particle.energy, particle.weight)
        if track_log is not None:
            track_log.append({"x": particle.x, "y": particle.y, "z": particle.z, "type": "electron", "energy": particle.energy})
        particle.alive = False
