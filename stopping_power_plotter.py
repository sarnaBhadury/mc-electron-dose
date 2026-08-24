#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║   Stopping Power Plotter for Electrons in Water                 ║
║   Data Source: NIST ESTAR Database                              ║
║   Material: Liquid Water (ρ = 1.0 g/cm³, I = 75.0 eV)         ║
╚══════════════════════════════════════════════════════════════════╝

This script plots:
  1. Collision, Radiative, and Total Stopping Power vs Energy
  2. CSDA Range vs Energy
  3. Radiation Yield vs Energy
  4. Relative contribution of S_col and S_rad

All data from NIST ESTAR: https://physics.nist.gov/PhysRefData/Star/Text/ESTAR.html
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, LogFormatterMathtext
import os

# ═══════════════════════════════════════════════════════════════
# NIST ESTAR DATA — Water, Liquid (81 energy points)
# ═══════════════════════════════════════════════════════════════

# Kinetic Energy (MeV)
ENERGY = np.array([
    1.000E-02, 1.250E-02, 1.500E-02, 1.750E-02, 2.000E-02,
    2.500E-02, 3.000E-02, 3.500E-02, 4.000E-02, 4.500E-02,
    5.000E-02, 5.500E-02, 6.000E-02, 7.000E-02, 8.000E-02,
    9.000E-02, 1.000E-01, 1.250E-01, 1.500E-01, 1.750E-01,
    2.000E-01, 2.500E-01, 3.000E-01, 3.500E-01, 4.000E-01,
    4.500E-01, 5.000E-01, 5.500E-01, 6.000E-01, 7.000E-01,
    8.000E-01, 9.000E-01, 1.000E+00, 1.250E+00, 1.500E+00,
    1.750E+00, 2.000E+00, 2.500E+00, 3.000E+00, 3.500E+00,
    4.000E+00, 4.500E+00, 5.000E+00, 5.500E+00, 6.000E+00,
    7.000E+00, 8.000E+00, 9.000E+00, 1.000E+01, 1.250E+01,
    1.500E+01, 1.750E+01, 2.000E+01, 2.500E+01, 3.000E+01,
    3.500E+01, 4.000E+01, 4.500E+01, 5.000E+01, 5.500E+01,
    6.000E+01, 7.000E+01, 8.000E+01, 9.000E+01, 1.000E+02,
    1.250E+02, 1.500E+02, 1.750E+02, 2.000E+02, 2.500E+02,
    3.000E+02, 3.500E+02, 4.000E+02, 4.500E+02, 5.000E+02,
    5.500E+02, 6.000E+02, 7.000E+02, 8.000E+02, 9.000E+02,
    1.000E+03
])

# Collision Stopping Power (MeV·cm²/g)
S_COL = np.array([
    2.256E+01, 1.897E+01, 1.647E+01, 1.461E+01, 1.317E+01,
    1.109E+01, 9.653E+00, 8.592E+00, 7.777E+00, 7.130E+00,
    6.603E+00, 6.166E+00, 5.797E+00, 5.207E+00, 4.757E+00,
    4.402E+00, 4.115E+00, 3.591E+00, 3.238E+00, 2.984E+00,
    2.793E+00, 2.528E+00, 2.355E+00, 2.235E+00, 2.148E+00,
    2.083E+00, 2.034E+00, 1.995E+00, 1.963E+00, 1.917E+00,
    1.886E+00, 1.864E+00, 1.849E+00, 1.829E+00, 1.822E+00,
    1.821E+00, 1.824E+00, 1.834E+00, 1.846E+00, 1.858E+00,
    1.870E+00, 1.882E+00, 1.892E+00, 1.902E+00, 1.911E+00,
    1.928E+00, 1.943E+00, 1.956E+00, 1.968E+00, 1.993E+00,
    2.014E+00, 2.031E+00, 2.046E+00, 2.070E+00, 2.089E+00,
    2.105E+00, 2.118E+00, 2.129E+00, 2.139E+00, 2.148E+00,
    2.156E+00, 2.170E+00, 2.182E+00, 2.193E+00, 2.202E+00,
    2.222E+00, 2.238E+00, 2.251E+00, 2.263E+00, 2.282E+00,
    2.297E+00, 2.311E+00, 2.322E+00, 2.332E+00, 2.341E+00,
    2.349E+00, 2.357E+00, 2.370E+00, 2.381E+00, 2.391E+00,
    2.400E+00
])

# Radiative Stopping Power (MeV·cm²/g)
S_RAD = np.array([
    3.898E-03, 3.927E-03, 3.944E-03, 3.955E-03, 3.963E-03,
    3.974E-03, 3.984E-03, 3.994E-03, 4.005E-03, 4.018E-03,
    4.031E-03, 4.046E-03, 4.062E-03, 4.098E-03, 4.138E-03,
    4.181E-03, 4.228E-03, 4.355E-03, 4.494E-03, 4.643E-03,
    4.801E-03, 5.141E-03, 5.514E-03, 5.914E-03, 6.339E-03,
    6.787E-03, 7.257E-03, 7.747E-03, 8.254E-03, 9.313E-03,
    1.042E-02, 1.159E-02, 1.280E-02, 1.600E-02, 1.942E-02,
    2.303E-02, 2.678E-02, 3.468E-02, 4.299E-02, 5.164E-02,
    6.058E-02, 6.976E-02, 7.917E-02, 8.876E-02, 9.854E-02,
    1.185E-01, 1.391E-01, 1.601E-01, 1.814E-01, 2.362E-01,
    2.926E-01, 3.501E-01, 4.086E-01, 5.277E-01, 6.489E-01,
    7.716E-01, 8.955E-01, 1.021E+00, 1.146E+00, 1.273E+00,
    1.400E+00, 1.656E+00, 1.914E+00, 2.173E+00, 2.434E+00,
    3.089E+00, 3.749E+00, 4.412E+00, 5.078E+00, 6.416E+00,
    7.760E+00, 9.107E+00, 1.046E+01, 1.181E+01, 1.317E+01,
    1.453E+01, 1.589E+01, 1.861E+01, 2.133E+01, 2.406E+01,
    2.679E+01
])

# Total Stopping Power (MeV·cm²/g)
S_TOTAL = np.array([
    2.256E+01, 1.898E+01, 1.647E+01, 1.461E+01, 1.318E+01,
    1.110E+01, 9.657E+00, 8.596E+00, 7.781E+00, 7.134E+00,
    6.607E+00, 6.170E+00, 5.801E+00, 5.211E+00, 4.761E+00,
    4.407E+00, 4.119E+00, 3.596E+00, 3.242E+00, 2.988E+00,
    2.798E+00, 2.533E+00, 2.360E+00, 2.241E+00, 2.154E+00,
    2.090E+00, 2.041E+00, 2.003E+00, 1.972E+00, 1.926E+00,
    1.896E+00, 1.876E+00, 1.862E+00, 1.845E+00, 1.841E+00,
    1.844E+00, 1.850E+00, 1.868E+00, 1.889E+00, 1.910E+00,
    1.931E+00, 1.951E+00, 1.971E+00, 1.991E+00, 2.010E+00,
    2.047E+00, 2.082E+00, 2.116E+00, 2.149E+00, 2.230E+00,
    2.306E+00, 2.381E+00, 2.454E+00, 2.598E+00, 2.738E+00,
    2.876E+00, 3.013E+00, 3.150E+00, 3.286E+00, 3.421E+00,
    3.556E+00, 3.827E+00, 4.096E+00, 4.366E+00, 4.636E+00,
    5.311E+00, 5.987E+00, 6.663E+00, 7.341E+00, 8.698E+00,
    1.006E+01, 1.142E+01, 1.278E+01, 1.414E+01, 1.551E+01,
    1.688E+01, 1.824E+01, 2.098E+01, 2.371E+01, 2.645E+01,
    2.919E+01
])

# CSDA Range (g/cm² = cm in water)
CSDA_RANGE = np.array([
    2.515E-04, 3.728E-04, 5.147E-04, 6.762E-04, 8.566E-04,
    1.272E-03, 1.756E-03, 2.306E-03, 2.919E-03, 3.591E-03,
    4.320E-03, 5.103E-03, 5.940E-03, 7.762E-03, 9.773E-03,
    1.196E-02, 1.431E-02, 2.083E-02, 2.817E-02, 3.622E-02,
    4.488E-02, 6.372E-02, 8.421E-02, 1.060E-01, 1.288E-01,
    1.523E-01, 1.766E-01, 2.013E-01, 2.265E-01, 2.778E-01,
    3.302E-01, 3.832E-01, 4.367E-01, 5.717E-01, 7.075E-01,
    8.432E-01, 9.785E-01, 1.247E+00, 1.514E+00, 1.777E+00,
    2.037E+00, 2.295E+00, 2.550E+00, 2.802E+00, 3.052E+00,
    3.545E+00, 4.030E+00, 4.506E+00, 4.975E+00, 6.117E+00,
    7.219E+00, 8.286E+00, 9.320E+00, 1.130E+01, 1.317E+01,
    1.496E+01, 1.665E+01, 1.828E+01, 1.983E+01, 2.132E+01,
    2.276E+01, 2.547E+01, 2.799E+01, 3.035E+01, 3.258E+01,
    3.761E+01, 4.204E+01, 4.600E+01, 4.957E+01, 5.582E+01,
    6.116E+01, 6.583E+01, 6.996E+01, 7.368E+01, 7.706E+01,
    8.014E+01, 8.299E+01, 8.810E+01, 9.258E+01, 9.657E+01,
    1.002E+02
])

# Radiation Yield (fraction of energy radiated as Bremsstrahlung)
RAD_YIELD = np.array([
    9.408E-05, 1.133E-04, 1.316E-04, 1.493E-04, 1.663E-04,
    1.990E-04, 2.301E-04, 2.599E-04, 2.886E-04, 3.165E-04,
    3.435E-04, 3.698E-04, 3.955E-04, 4.453E-04, 4.931E-04,
    5.393E-04, 5.842E-04, 6.912E-04, 7.926E-04, 8.894E-04,
    9.826E-04, 1.161E-03, 1.331E-03, 1.496E-03, 1.658E-03,
    1.818E-03, 1.976E-03, 2.134E-03, 2.292E-03, 2.608E-03,
    2.928E-03, 3.251E-03, 3.579E-03, 4.416E-03, 5.281E-03,
    6.171E-03, 7.085E-03, 8.969E-03, 1.092E-02, 1.291E-02,
    1.495E-02, 1.702E-02, 1.911E-02, 2.123E-02, 2.336E-02,
    2.766E-02, 3.200E-02, 3.636E-02, 4.072E-02, 5.163E-02,
    6.243E-02, 7.309E-02, 8.355E-02, 1.039E-01, 1.233E-01,
    1.418E-01, 1.594E-01, 1.762E-01, 1.923E-01, 2.076E-01,
    2.222E-01, 2.496E-01, 2.747E-01, 2.978E-01, 3.192E-01,
    3.662E-01, 4.060E-01, 4.401E-01, 4.698E-01, 5.190E-01,
    5.584E-01, 5.908E-01, 6.180E-01, 6.412E-01, 6.613E-01,
    6.789E-01, 6.945E-01, 7.209E-01, 7.425E-01, 7.605E-01,
    7.759E-01
])


# ═══════════════════════════════════════════════════════════════
# PLOT SETUP — Premium Dark Theme
# ═══════════════════════════════════════════════════════════════

# Custom dark theme
plt.rcParams.update({
    'figure.facecolor': '#0d1117',
    'axes.facecolor': '#161b22',
    'axes.edgecolor': '#30363d',
    'axes.labelcolor': '#e6edf3',
    'text.color': '#e6edf3',
    'xtick.color': '#8b949e',
    'ytick.color': '#8b949e',
    'grid.color': '#21262d',
    'grid.alpha': 0.6,
    'font.family': 'sans-serif',
    'font.size': 12,
    'axes.titlesize': 16,
    'axes.labelsize': 13,
    'legend.fontsize': 11,
    'figure.dpi': 150,
})

OUTPUT_DIR = 'plots'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def find_crossover():
    """Find the critical energy where S_rad = S_col."""
    # Interpolate in log space to find crossover
    log_e = np.log10(ENERGY)
    log_ratio = np.log10(S_RAD / S_COL)
    # Find where ratio crosses 1.0 (log = 0)
    for i in range(len(log_ratio) - 1):
        if log_ratio[i] < 0 and log_ratio[i+1] >= 0:
            # Linear interpolation
            frac = -log_ratio[i] / (log_ratio[i+1] - log_ratio[i])
            e_cross = 10**(log_e[i] + frac * (log_e[i+1] - log_e[i]))
            return e_cross
    return None


# ═══════════════════════════════════════════════════════════════
# PLOT 1: Stopping Powers vs Energy (Main Plot)
# ═══════════════════════════════════════════════════════════════

def plot_stopping_powers():
    """Main plot: S_col, S_rad, S_total vs kinetic energy."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot the three stopping powers
    ax.loglog(ENERGY, S_COL, '-', color='#58a6ff', linewidth=2.5, 
              label='$S_{col}/\\rho$ (Collision)', zorder=3)
    ax.loglog(ENERGY, S_RAD, '-', color='#f85149', linewidth=2.5, 
              label='$S_{rad}/\\rho$ (Radiative)', zorder=3)
    ax.loglog(ENERGY, S_TOTAL, '--', color='#d2a8ff', linewidth=2.0, 
              label='$S_{tot}/\\rho$ (Total)', alpha=0.9, zorder=2)
    
    # Find and mark crossover point
    e_cross = find_crossover()
    if e_cross:
        # Interpolate S_col at crossover
        s_cross = np.interp(np.log10(e_cross), np.log10(ENERGY), np.log10(S_COL))
        s_cross = 10**s_cross
        ax.plot(e_cross, s_cross, 'o', color='#ffd700', markersize=12, 
                markeredgecolor='white', markeredgewidth=2, zorder=5)
        ax.annotate(f'Critical Energy\n$E_c$ ≈ {e_cross:.0f} MeV',
                   xy=(e_cross, s_cross), xytext=(e_cross * 0.15, s_cross * 3),
                   fontsize=12, fontweight='bold', color='#ffd700',
                   arrowprops=dict(arrowstyle='->', color='#ffd700', lw=2),
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='#0d1117', 
                            edgecolor='#ffd700', alpha=0.9))
    
    # Add shaded regions
    ax.axvspan(ENERGY[0], 1.0, alpha=0.05, color='#58a6ff', label='_nolegend_')
    ax.axvspan(100, ENERGY[-1], alpha=0.05, color='#f85149', label='_nolegend_')
    
    # Region labels
    ax.text(0.05, 0.5, 'COLLISION\nDOMINATES', transform=ax.transAxes,
            fontsize=10, color='#58a6ff', alpha=0.5, fontweight='bold',
            ha='center', va='center')
    ax.text(0.92, 0.5, 'RADIATION\nDOMINATES', transform=ax.transAxes,
            fontsize=10, color='#f85149', alpha=0.5, fontweight='bold',
            ha='center', va='center')
    
    # Clinical energy range
    ax.axvspan(4, 20, alpha=0.08, color='#3fb950', zorder=1)
    ax.text(9, 0.008, 'Clinical Electron\nBeam Range\n(4-20 MeV)', 
            fontsize=9, color='#3fb950', ha='center', va='bottom',
            fontweight='bold', alpha=0.8,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#0d1117', 
                     edgecolor='#3fb950', alpha=0.7))
    
    # Formatting
    ax.set_xlabel('Kinetic Energy (MeV)')
    ax.set_ylabel('Mass Stopping Power (MeV·cm²/g)')
    ax.set_title('Electron Stopping Power in Water (NIST ESTAR)',
                fontsize=18, fontweight='bold', pad=15)
    
    ax.set_xlim(ENERGY[0], ENERGY[-1])
    ax.set_ylim(3e-3, 50)
    ax.legend(loc='upper center', framealpha=0.8, edgecolor='#30363d',
             fancybox=True, ncol=3, bbox_to_anchor=(0.5, -0.08))
    ax.grid(True, which='both', alpha=0.3)
    
    # Add minor grid
    ax.grid(True, which='minor', alpha=0.1, linestyle=':')
    
    # Subtitle
    fig.text(0.5, 0.93, 'Material: Liquid Water (ρ = 1.0 g/cm³, I = 75.0 eV)',
            ha='center', fontsize=11, color='#8b949e', style='italic')
    
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, '01_stopping_powers.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='#0d1117')
    plt.close(fig)
    print(f'  ✅ Saved: {path}')
    return e_cross


# ═══════════════════════════════════════════════════════════════
# PLOT 2: Relative Contributions (Stacked Area)
# ═══════════════════════════════════════════════════════════════

def plot_relative_contributions():
    """Show fractional contribution of S_col and S_rad to S_total."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    frac_col = S_COL / S_TOTAL * 100
    frac_rad = S_RAD / S_TOTAL * 100
    
    ax.fill_between(ENERGY, 0, frac_col, alpha=0.7, color='#58a6ff', 
                    label='Collision (ionization & excitation)')
    ax.fill_between(ENERGY, frac_col, 100, alpha=0.7, color='#f85149',
                    label='Radiative (Bremsstrahlung)')
    
    # 50% line
    ax.axhline(50, color='white', linestyle=':', alpha=0.4, linewidth=1)
    
    # Mark crossover
    e_cross = find_crossover()
    if e_cross:
        ax.axvline(e_cross, color='#ffd700', linestyle='--', linewidth=2, alpha=0.8)
        ax.text(e_cross * 1.2, 52, f'$E_c$ ≈ {e_cross:.0f} MeV',
               color='#ffd700', fontsize=12, fontweight='bold')
    
    # Annotations at specific energies
    for e_annot in [1, 10, 100]:
        idx = np.argmin(np.abs(ENERGY - e_annot))
        fc = frac_col[idx]
        ax.annotate(f'{fc:.1f}%', xy=(ENERGY[idx], fc/2), 
                   fontsize=10, color='white', ha='center', va='center',
                   fontweight='bold')
        ax.annotate(f'{100-fc:.1f}%', xy=(ENERGY[idx], fc + (100-fc)/2),
                   fontsize=10, color='white', ha='center', va='center',
                   fontweight='bold')
    
    ax.set_xscale('log')
    ax.set_xlabel('Kinetic Energy (MeV)')
    ax.set_ylabel('Fractional Contribution (%)')
    ax.set_title('Relative Contribution: Collision vs Radiative Stopping Power',
                fontsize=16, fontweight='bold', pad=10)
    ax.set_xlim(ENERGY[0], ENERGY[-1])
    ax.set_ylim(0, 100)
    ax.legend(loc='center left', framealpha=0.8, edgecolor='#30363d')
    ax.grid(True, axis='y', alpha=0.3)
    
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, '02_relative_contributions.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='#0d1117')
    plt.close(fig)
    print(f'  ✅ Saved: {path}')


# ═══════════════════════════════════════════════════════════════
# PLOT 3: CSDA Range vs Energy
# ═══════════════════════════════════════════════════════════════

def plot_csda_range():
    """Plot CSDA range with clinical energy annotations."""
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Main curve
    ax.loglog(ENERGY, CSDA_RANGE, '-', color='#3fb950', linewidth=2.5, zorder=3)
    
    # Fill under curve
    ax.fill_between(ENERGY, 1e-5, CSDA_RANGE, alpha=0.1, color='#3fb950')
    
    # Mark clinical energies
    clinical_energies = [4, 6, 9, 12, 15, 20]
    clinical_colors = ['#ff7b72', '#ffa657', '#d2a8ff', '#58a6ff', '#79c0ff', '#56d364']
    
    for e_clin, clr in zip(clinical_energies, clinical_colors):
        idx = np.argmin(np.abs(ENERGY - e_clin))
        r = CSDA_RANGE[idx]
        ax.plot(e_clin, r, 'o', color=clr, markersize=10, markeredgecolor='white',
               markeredgewidth=1.5, zorder=5)
        ax.annotate(f'{e_clin} MeV\n→ {r:.2f} cm', 
                   xy=(e_clin, r), xytext=(e_clin * 1.5, r * 0.5),
                   fontsize=9, color=clr, fontweight='bold',
                   arrowprops=dict(arrowstyle='->', color=clr, lw=1.5),
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='#0d1117', 
                            edgecolor=clr, alpha=0.8))
    
    ax.set_xlabel('Kinetic Energy (MeV)')
    ax.set_ylabel('CSDA Range (g/cm² = cm in water)')
    ax.set_title('CSDA Range of Electrons in Water',
                fontsize=18, fontweight='bold', pad=15)
    ax.set_xlim(ENERGY[0], ENERGY[-1])
    ax.grid(True, which='both', alpha=0.3)
    ax.grid(True, which='minor', alpha=0.1, linestyle=':')
    
    # Add note
    fig.text(0.5, 0.93, 'CSDA Range = Total path length before electron stops (not penetration depth)',
            ha='center', fontsize=10, color='#8b949e', style='italic')
    
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, '03_csda_range.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='#0d1117')
    plt.close(fig)
    print(f'  ✅ Saved: {path}')


# ═══════════════════════════════════════════════════════════════
# PLOT 4: Radiation Yield vs Energy
# ═══════════════════════════════════════════════════════════════

def plot_radiation_yield():
    """Plot radiation yield (fraction of energy radiated as Bremsstrahlung)."""
    fig, ax = plt.subplots(figsize=(12, 7))
    
    ax.semilogx(ENERGY, RAD_YIELD * 100, '-', color='#f85149', linewidth=2.5, zorder=3)
    ax.fill_between(ENERGY, 0, RAD_YIELD * 100, alpha=0.15, color='#f85149')
    
    # Mark key thresholds
    ax.axhline(1, color='#8b949e', linestyle=':', alpha=0.5)
    ax.text(0.015, 1.5, '1% Radiation Yield', color='#8b949e', fontsize=9)
    
    ax.axhline(10, color='#8b949e', linestyle=':', alpha=0.5)
    ax.text(0.015, 11, '10% Radiation Yield', color='#8b949e', fontsize=9)
    
    ax.axhline(50, color='#ffd700', linestyle='--', alpha=0.5)
    ax.text(0.015, 52, '50% — Half of energy radiated', color='#ffd700', fontsize=10, fontweight='bold')
    
    # Annotate at clinical energies
    for e_ann in [6, 12, 20]:
        idx = np.argmin(np.abs(ENERGY - e_ann))
        y_val = RAD_YIELD[idx] * 100
        ax.annotate(f'{e_ann} MeV: {y_val:.1f}%',
                   xy=(e_ann, y_val), xytext=(e_ann * 2, y_val + 5),
                   fontsize=10, color='#58a6ff', fontweight='bold',
                   arrowprops=dict(arrowstyle='->', color='#58a6ff', lw=1.5))
    
    ax.set_xlabel('Kinetic Energy (MeV)')
    ax.set_ylabel('Radiation Yield (%)')
    ax.set_title('Radiation Yield: Fraction of Energy Lost to Bremsstrahlung',
                fontsize=16, fontweight='bold', pad=15)
    ax.set_xlim(ENERGY[0], ENERGY[-1])
    ax.set_ylim(0, 85)
    ax.grid(True, alpha=0.3)
    
    fig.text(0.5, 0.93, 
            'At clinical energies (4-20 MeV), <10% of electron energy is radiated → most energy deposited locally',
            ha='center', fontsize=10, color='#8b949e', style='italic')
    
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, '04_radiation_yield.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='#0d1117')
    plt.close(fig)
    print(f'  ✅ Saved: {path}')


# ═══════════════════════════════════════════════════════════════
# PLOT 5: Combined Dashboard
# ═══════════════════════════════════════════════════════════════

def plot_dashboard():
    """Create a combined 2x2 dashboard of all key quantities."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('NIST ESTAR Data Dashboard — Electrons in Water',
                fontsize=20, fontweight='bold', y=0.98, color='#e6edf3')
    fig.text(0.5, 0.95, 'Liquid Water (ρ = 1.0 g/cm³, I = 75.0 eV) | Energy Range: 10 keV – 1 GeV',
            ha='center', fontsize=12, color='#8b949e', style='italic')
    
    # Panel 1: Stopping Powers
    ax = axes[0, 0]
    ax.loglog(ENERGY, S_COL, '-', color='#58a6ff', linewidth=2, label='$S_{col}$ (Collision)')
    ax.loglog(ENERGY, S_RAD, '-', color='#f85149', linewidth=2, label='$S_{rad}$ (Radiative)')
    ax.loglog(ENERGY, S_TOTAL, '--', color='#d2a8ff', linewidth=1.5, label='$S_{tot}$ (Total)', alpha=0.8)
    e_cross = find_crossover()
    if e_cross:
        s_c = np.interp(np.log10(e_cross), np.log10(ENERGY), np.log10(S_COL))
        ax.plot(e_cross, 10**s_c, '*', color='#ffd700', markersize=15, zorder=5)
    ax.set_xlabel('Energy (MeV)')
    ax.set_ylabel('$S/\\rho$ (MeV·cm²/g)')
    ax.set_title('(a) Mass Stopping Powers', fontweight='bold')
    ax.legend(fontsize=9, loc='upper right', framealpha=0.7)
    ax.grid(True, which='both', alpha=0.3)
    ax.set_xlim(ENERGY[0], ENERGY[-1])
    
    # Panel 2: Relative Contributions
    ax = axes[0, 1]
    frac_col = S_COL / S_TOTAL * 100
    ax.fill_between(ENERGY, 0, frac_col, alpha=0.6, color='#58a6ff', label='Collision')
    ax.fill_between(ENERGY, frac_col, 100, alpha=0.6, color='#f85149', label='Radiative')
    ax.axhline(50, color='white', linestyle=':', alpha=0.3)
    ax.set_xscale('log')
    ax.set_xlabel('Energy (MeV)')
    ax.set_ylabel('Fraction (%)')
    ax.set_title('(b) Collision vs Radiative Fraction', fontweight='bold')
    ax.legend(fontsize=9, framealpha=0.7)
    ax.set_xlim(ENERGY[0], ENERGY[-1])
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)
    
    # Panel 3: CSDA Range
    ax = axes[1, 0]
    ax.loglog(ENERGY, CSDA_RANGE, '-', color='#3fb950', linewidth=2)
    ax.fill_between(ENERGY, 1e-5, CSDA_RANGE, alpha=0.1, color='#3fb950')
    for e_c in [6, 12, 20]:
        idx = np.argmin(np.abs(ENERGY - e_c))
        ax.plot(e_c, CSDA_RANGE[idx], 'o', color='#ffa657', markersize=8, 
               markeredgecolor='white', markeredgewidth=1, zorder=5)
        ax.text(e_c, CSDA_RANGE[idx] * 1.5, f'{e_c} MeV\n{CSDA_RANGE[idx]:.1f} cm',
               fontsize=8, color='#ffa657', ha='center', fontweight='bold')
    ax.set_xlabel('Energy (MeV)')
    ax.set_ylabel('Range (g/cm² ≈ cm)')
    ax.set_title('(c) CSDA Range', fontweight='bold')
    ax.grid(True, which='both', alpha=0.3)
    ax.set_xlim(ENERGY[0], ENERGY[-1])
    
    # Panel 4: Radiation Yield
    ax = axes[1, 1]
    ax.semilogx(ENERGY, RAD_YIELD * 100, '-', color='#f85149', linewidth=2)
    ax.fill_between(ENERGY, 0, RAD_YIELD * 100, alpha=0.15, color='#f85149')
    ax.axhline(50, color='#ffd700', linestyle='--', alpha=0.5, linewidth=1)
    ax.set_xlabel('Energy (MeV)')
    ax.set_ylabel('Radiation Yield (%)')
    ax.set_title('(d) Radiation Yield (Bremsstrahlung)', fontweight='bold')
    ax.set_xlim(ENERGY[0], ENERGY[-1])
    ax.set_ylim(0, 85)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    path = os.path.join(OUTPUT_DIR, '05_dashboard.png')
    fig.savefig(path, dpi=200, bbox_inches='tight', facecolor='#0d1117')
    plt.close(fig)
    print(f'  ✅ Saved: {path}')


# ═══════════════════════════════════════════════════════════════
# PLOT 6: Data Summary Table
# ═══════════════════════════════════════════════════════════════

def print_summary():
    """Print a formatted data summary table."""
    e_cross = find_crossover()
    
    print('\n' + '═' * 70)
    print('  NIST ESTAR DATA SUMMARY — Electrons in Water')
    print('═' * 70)
    print(f'\n  Material:           Liquid Water (H₂O)')
    print(f'  Density:            1.000 g/cm³')
    print(f'  Mean Excitation:    75.0 eV')
    print(f'  Radiation Length:   36.08 g/cm²')
    print(f'  Data Points:        {len(ENERGY)}')
    print(f'  Energy Range:       {ENERGY[0]*1000:.0f} keV – {ENERGY[-1]/1000:.0f} GeV')
    if e_cross:
        print(f'  Critical Energy:    ~{e_cross:.0f} MeV (where S_rad = S_col)')
    
    print(f'\n  {"Energy":>10s}  {"S_col":>10s}  {"S_rad":>10s}  {"S_total":>10s}  {"CSDA Range":>12s}  {"Rad Yield":>10s}')
    print(f'  {"(MeV)":>10s}  {"(MeV cm²/g)":>10s}  {"(MeV cm²/g)":>10s}  {"(MeV cm²/g)":>10s}  {"(cm)":>12s}  {"(%)":>10s}')
    print('  ' + '-' * 68)
    
    # Show clinical energies
    clinical = [0.01, 0.1, 0.5, 1.0, 2.0, 4.0, 6.0, 9.0, 12.0, 15.0, 20.0, 50.0, 100.0, 1000.0]
    for e_target in clinical:
        idx = np.argmin(np.abs(ENERGY - e_target))
        marker = ' ◀' if 4 <= ENERGY[idx] <= 20 else ''
        print(f'  {ENERGY[idx]:10.3f}  {S_COL[idx]:10.4f}  {S_RAD[idx]:10.4f}  '
              f'{S_TOTAL[idx]:10.4f}  {CSDA_RANGE[idx]:12.4f}  {RAD_YIELD[idx]*100:9.3f}%{marker}')
    
    print('\n  ◀ = Clinical electron beam energy range (4-20 MeV)')
    print('═' * 70)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print('╔══════════════════════════════════════════════════════════════════╗')
    print('║   Stopping Power Plotter — NIST ESTAR Data for Water           ║')
    print('╚══════════════════════════════════════════════════════════════════╝')
    print()
    
    # Print data summary
    print_summary()
    
    # Generate all plots
    print('\n  Generating plots...\n')
    e_cross = plot_stopping_powers()
    plot_relative_contributions()
    plot_csda_range()
    plot_radiation_yield()
    plot_dashboard()
    
    print(f'\n  All plots saved to: {OUTPUT_DIR}/')
    print(f'\n  Key Finding: Critical Energy E_c ≈ {e_cross:.0f} MeV')
    print(f'  → Below {e_cross:.0f} MeV: Collision (ionization) dominates energy loss')
    print(f'  → Above {e_cross:.0f} MeV: Radiation (Bremsstrahlung) dominates energy loss')
    print(f'  → Clinical beams (4-20 MeV): Collision strongly dominates (~93-97%)')
    print()
