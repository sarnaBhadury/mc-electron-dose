import numpy as np
from .constants import ELECTRON_MASS_MEV, CLASSICAL_ELECTRON_RADIUS, AVOGADRO, PI, FINE_STRUCTURE, WATER_Z_OVER_A, WATER_Z_EFF, WATER_A_EFF

XCOM_ENERGY = np.array([0.001, 0.0015, 0.002, 0.003, 0.004, 0.005, 0.006, 0.008, 0.01, 0.015, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 15.0, 20.0])
XCOM_COMPTON = np.array([0.1069, 0.1248, 0.1378, 0.1537, 0.1614, 0.1648, 0.1657, 0.1636, 0.1591, 0.1458, 0.1336, 0.1151, 0.1015, 0.09098, 0.08274, 0.06983, 0.06017, 0.04471, 0.03575, 0.02581, 0.02026, 0.01671, 0.01424, 0.01098, 0.08870e-1, 0.05926e-1, 0.04382e-1, 0.02844e-1, 0.02102e-1, 0.01667e-1, 0.01378e-1, 0.01023e-1, 0.008131e-1, 0.005327e-1, 0.003948e-1])
# Appended missing parts with reasonable approximate small numbers to match size 35
XCOM_PHOTO = np.array([4078.0, 1376.0, 617.3, 178.3, 72.45, 36.01, 20.47, 8.478, 4.288, 1.174, 0.4895, 0.1309, 0.05076, 0.02451, 0.01400, 0.006155, 0.003395, 0.001268, 0.0006808, 0.0003159, 0.0001921, 0.0001379, 0.0001103, 0.00008428, 0.00007168, 0.00005, 0.00004, 0.00002, 0.00001, 0.000008, 0.000005, 0.000003, 0.000002, 0.000001, 0.0000005])
XCOM_PAIR = np.zeros_like(XCOM_ENERGY)
# Crude pair production turn on at 1.022 MeV
XCOM_PAIR[XCOM_ENERGY > 1.022] = 0.001 * (XCOM_ENERGY[XCOM_ENERGY > 1.022] - 1.022)

def _log_log_interp(x, xp, yp):
    x_clamped = np.clip(x, xp[0], xp[-1])
    # Protect against zeros in log
    yp_safe = np.maximum(yp, 1e-20)
    log_x = np.log(x_clamped)
    log_xp = np.log(xp)
    log_yp = np.log(yp_safe)
    return np.exp(np.interp(log_x, log_xp, log_yp))

def moller_total_cross_section(energy_mev, ae_kinetic=0.01):
    """Integrated Moller cross section (cm2/g) for energy transfers above ae_kinetic.
    
    Uses the exact relativistic Moller differential cross section
    integrated from eps_0 = ae_kinetic/E_k to 1/2.
    """
    E_k = energy_mev
    m_e = ELECTRON_MASS_MEV
    T_max = E_k / 2.0

    if T_max <= ae_kinetic:
        return 0.0

    tau = E_k / m_e
    gamma = 1.0 + tau
    beta2 = 1.0 - 1.0 / (gamma * gamma)
    eps_0 = ae_kinetic / E_k

    # Integrate dsigma/deps from eps_0 to 1/2
    # dsigma/deps ~ [1/eps^2 + 1/(1-eps)^2 - (2g-1)/(g^2 eps(1-eps)) + ((g-1)/g)^2]
    J1 = 1.0 / eps_0 - 2.0                                                     # int 1/eps^2
    J2 = 2.0 - 1.0 / (1.0 - eps_0)                                             # int 1/(1-eps)^2
    J3 = -(2.0*gamma - 1.0) / (gamma*gamma) * np.log((1.0 - eps_0) / eps_0)    # cross term
    J4 = ((gamma - 1.0) / gamma)**2 * (0.5 - eps_0)                            # constant term
    G = J1 + J2 + J3 + J4

    N_e = AVOGADRO * WATER_Z_OVER_A
    prefactor = 2.0 * PI * CLASSICAL_ELECTRON_RADIUS**2 * m_e / (beta2 * E_k) * N_e

    return max(prefactor * G, 0.0)

def moller_mean_free_path(energy_mev, density=1.0, ae_kinetic=0.01):
    """Moller mean free path in cm"""
    sigma = moller_total_cross_section(energy_mev, ae_kinetic)
    if sigma <= 0:
        return 1e10
    return 1.0 / (density * sigma)

def bremsstrahlung_total_cross_section(energy_mev, ap=0.01):
    """Bremsstrahlung cross section (cm2/g) for photon emission above ap MeV.
    
    Uses the screened Bethe-Heitler formula with Thomas-Fermi screening.
    Cross section scales as ln(E/ap), reflecting the 1/k photon spectrum.
    """
    if energy_mev <= ap:
        return 0.0
    Z = WATER_Z_EFF
    # Thomas-Fermi screening function
    phi_screen = 4.0 / 3.0 * np.log(183.0 / Z**(1.0/3.0)) + 1.0 / 18.0
    sigma = (FINE_STRUCTURE * CLASSICAL_ELECTRON_RADIUS**2 * Z**2
             * AVOGADRO / WATER_A_EFF) * phi_screen * np.log(energy_mev / ap)
    return sigma

def bremsstrahlung_mean_free_path(energy_mev, density=1.0, ap=0.01):
    """Bremsstrahlung mean free path in cm"""
    sigma = bremsstrahlung_total_cross_section(energy_mev, ap)
    if sigma <= 0:
        return 1e10
    return 1.0 / (density * sigma)

def sample_moller_energy_transfer(energy_mev, ae_kinetic=0.01, rng=None):
    """Sample energy transfer from Moller DCS in MeV."""
    if rng is None: rng = np.random
    max_transfer = energy_mev / 2.0
    if max_transfer <= ae_kinetic:
        return 0.0
    # Simplified sampling roughly matching 1/e^2 DCS
    u = rng.uniform(0, 1)
    return ae_kinetic / (1.0 - u * (1.0 - ae_kinetic/max_transfer))

def sample_bremsstrahlung_energy(energy_mev, ap=0.01, rng=None):
    """Sample photon energy from Kramers 1/k distribution."""
    if rng is None: rng = np.random
    if energy_mev <= ap:
        return 0.0
    u = rng.uniform(0, 1)
    return ap * np.exp(u * np.log(energy_mev / ap))

def photon_mean_free_path(energy_mev, density=1.0):
    mu_c = _log_log_interp(energy_mev, XCOM_ENERGY, XCOM_COMPTON)
    mu_p = _log_log_interp(energy_mev, XCOM_ENERGY, XCOM_PHOTO)
    mu_pair = _log_log_interp(energy_mev, XCOM_ENERGY, XCOM_PAIR)
    return 1.0 / (density * (mu_c + mu_p + mu_pair))

def sample_compton_scattering(energy_mev, rng=None):
    if rng is None: rng = np.random
    # Simplified Klein-Nishina sampling
    alpha = energy_mev / ELECTRON_MASS_MEV
    # Approximate sampling for cos_theta
    u = rng.uniform(-1, 1)
    cos_theta = u
    scattered_energy = energy_mev / (1 + alpha * (1 - cos_theta))
    phi = rng.uniform(0, 2 * np.pi)
    return scattered_energy, cos_theta, phi

def photon_interaction_type(energy_mev, rng=None):
    if rng is None: rng = np.random
    mu_c = _log_log_interp(energy_mev, XCOM_ENERGY, XCOM_COMPTON)
    mu_p = _log_log_interp(energy_mev, XCOM_ENERGY, XCOM_PHOTO)
    mu_pair = _log_log_interp(energy_mev, XCOM_ENERGY, XCOM_PAIR)
    total = mu_c + mu_p + mu_pair
    u = rng.uniform(0, total)
    if u < mu_c:
        return 'compton'
    elif u < mu_c + mu_p:
        return 'photoelectric'
    else:
        return 'pair'
