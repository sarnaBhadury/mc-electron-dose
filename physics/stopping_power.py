import numpy as np
from .constants import (
    ESTAR_ENERGY, ESTAR_COLLISION_SP, ESTAR_RADIATIVE_SP,
    ESTAR_TOTAL_SP, ESTAR_CSDA_RANGE,
    ELECTRON_MASS_MEV, CLASSICAL_ELECTRON_RADIUS, PI,
    AVOGADRO, WATER_Z_OVER_A
)

def _log_log_interp(x, xp, yp):
    """Perform log-log interpolation of data."""
    # Clamp x to the valid range
    x_clamped = np.clip(x, xp[0], xp[-1])
    
    # Log spaces
    log_x = np.log(x_clamped)
    log_xp = np.log(xp)
    log_yp = np.log(yp)
    
    # Interpolate
    log_y = np.interp(log_x, log_xp, log_yp)
    return np.exp(log_y)

def get_collision_stopping_power(energy_mev):
    """Get collision stopping power in MeV*cm2/g for a given energy in MeV."""
    return _log_log_interp(energy_mev, ESTAR_ENERGY, ESTAR_COLLISION_SP)

def get_radiative_stopping_power(energy_mev):
    """Get radiative stopping power in MeV*cm2/g for a given energy in MeV."""
    return _log_log_interp(energy_mev, ESTAR_ENERGY, ESTAR_RADIATIVE_SP)

def get_total_stopping_power(energy_mev):
    """Get total stopping power in MeV*cm2/g for a given energy in MeV."""
    return _log_log_interp(energy_mev, ESTAR_ENERGY, ESTAR_TOTAL_SP)

def get_csda_range(energy_mev):
    """Get CSDA range in g/cm2 for a given energy in MeV."""
    return _log_log_interp(energy_mev, ESTAR_ENERGY, ESTAR_CSDA_RANGE)

def get_restricted_collision_sp(energy_mev, ae_kinetic=0.01):
    """
    Compute restricted collision stopping power in MeV*cm2/g.
    
    Uses ESTAR S_col as the unrestricted value and subtracts the energy
    going to hard knock-on electrons (Moller events) with kinetic energy
    transfer above ae_kinetic. Based on the EGS4/EGSnrc formulation using
    restricted and unrestricted Moller correction functions F*(tau,eta)
    and F(tau).
    """
    s_col = get_collision_stopping_power(energy_mev)
    
    E_k = energy_mev
    m_e = ELECTRON_MASS_MEV
    T_max = E_k / 2.0  # max transfer for identical particles
    
    if T_max <= ae_kinetic:
        return s_col  # no hard events possible
    
    tau = E_k / m_e
    gamma = 1.0 + tau
    beta2 = 1.0 - 1.0 / (gamma * gamma)
    eta = ae_kinetic / E_k  # fractional cutoff energy
    
    # Unrestricted Moller correction F(tau)
    F_unr = (1.0 - beta2) * (1.0 + tau * tau / 8.0
                              - (2.0 * tau + 1.0) * np.log(2.0))
    
    # Restricted Moller correction F*(tau, eta)
    F_res = (-1.0 - beta2
             + np.log(4.0 * eta * (1.0 - eta))
             + 1.0 / (1.0 - eta)
             + beta2 * (tau * tau * eta * eta / 2.0
                       + (2.0 * tau + 1.0) * np.log(1.0 - eta)))
    
    # Prefactor: 2pi r_e^2 m_e N_e / beta^2
    N_e = AVOGADRO * WATER_Z_OVER_A
    prefactor = 2.0 * PI * CLASSICAL_ELECTRON_RADIUS**2 * m_e * N_e / beta2
    
    # Energy per unit path going to hard knock-ons above ae_kinetic
    delta_S = prefactor * (F_unr - F_res)
    
    L_restricted = s_col - delta_S
    
    # Safety: restricted SP should be between 50% and 100% of S_col
    return float(np.clip(L_restricted, 0.5 * s_col, s_col))
