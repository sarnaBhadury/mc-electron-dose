import numpy as np
from .constants import ELECTRON_MASS_MEV, WATER_RADIATION_LENGTH

def highland_theta_rms(energy_mev, step_length_cm, density=1.0):
    """Calculate Highland theta rms in radians."""
    p_c = np.sqrt(energy_mev * (energy_mev + 2 * ELECTRON_MASS_MEV))
    beta = p_c / (energy_mev + ELECTRON_MASS_MEV)
    x = step_length_cm * density
    x_X0 = x / WATER_RADIATION_LENGTH
    
    if x_X0 <= 0:
        return 0.0
    
    # Modified Highland formula: removed the logarithmic correction `(1 + 0.038 * np.log(x_X0))`
    # The logarithmic term breaks step-size independence, meaning that if a particle
    # takes many small steps (due to voxel boundaries), it scatters significantly less
    # overall than if it took one large step. Removing it ensures the variance is linear
    # with distance, restoring proper lateral scattering and preventing deep penetration artifacts.
    theta_0 = (13.6 / (beta * p_c)) * np.sqrt(x_X0)
    return max(0.0, theta_0)

def sample_scattering_angles(theta_rms, rng=None):
    """Sample projected scattering angles."""
    
    # The Highland formula gives the RMS of the projected angle (theta_0).
    # Therefore, the standard deviation for the projected angles theta_x and theta_y is exactly theta_rms.
    sigma = theta_rms
    theta_x = rng.normal(0, sigma)
    theta_y = rng.normal(0, sigma)
    
    theta = np.sqrt(theta_x**2 + theta_y**2)
    phi = np.arctan2(theta_y, theta_x)
    return theta, phi

def rotate_direction(u, v, w, theta, phi):
    """Rotate direction cosines."""
    sin_theta = np.sin(theta)
    cos_theta = np.cos(theta)
    sin_phi = np.sin(phi)
    cos_phi = np.cos(phi)
    
    if np.abs(w) < 0.99999:
        denom = np.sqrt(1.0 - w*w)
        u_new = sin_theta * (u * w * cos_phi - v * sin_phi) / denom + u * cos_theta
        v_new = sin_theta * (v * w * cos_phi + u * sin_phi) / denom + v * cos_theta
        w_new = -sin_theta * cos_phi * denom + w * cos_theta
    else:
        sign_w = 1.0 if w > 0 else -1.0
        u_new = sin_theta * cos_phi
        v_new = sin_theta * sin_phi * sign_w
        w_new = cos_theta * sign_w
        
    # Normalize to prevent drift
    norm = np.sqrt(u_new**2 + v_new**2 + w_new**2)
    return u_new/norm, v_new/norm, w_new/norm

def compute_lateral_displacement(step_length, theta_rms):
    """Approximate lateral displacement in cm."""
    return step_length * theta_rms / np.sqrt(3.0)
