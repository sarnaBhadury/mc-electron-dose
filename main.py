import argparse
import sys
import os
import time
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SimulationConfig, BeamConfig, PhantomConfig, TransportConfig
from transport.simulation import MonteCarloSimulation
from visualization.plot_dose import DosePlotter

def print_banner():
    print('=' * 70)
    print('  Monte Carlo Electron Beam Dose Calculation')
    print('  Condensed History Method in Voxelized Water Phantom')
    print('  NIST ESTAR Data | Highland MCS | Full Physics')
    print('=' * 70)

def progress_callback(current, total, elapsed):
    pct = current / total * 100

    rate = current / elapsed if elapsed > 0 else 0
    eta = (total - current) / rate if rate > 0 else 0
    print(f'\r  Progress: {current}/{total} ({pct:.1f}%) | '
          f'Rate: {rate:.0f} hist/s | ETA: {eta:.0f}s', end='', flush=True)

def main():
    parser = argparse.ArgumentParser(description='MC Electron Beam Dose Calculator')
    parser.add_argument('--energy', type=float, default=12.0, help='Beam energy in MeV (default: 12)')
    parser.add_argument('--histories', type=int, default=100000, help='Number of histories (default: 100000)')
    parser.add_argument('--phantom-size', type=float, default=10.0, help='Phantom size in cm (default: 10)')
    parser.add_argument('--voxel-size', type=float, default=0.2, help='Voxel size in cm (default: 0.2)')
    parser.add_argument('--field-size', type=float, default=10.0, help='Field size in cm (default: 10)')
    parser.add_argument('--output', type=str, default='output', help='Output directory (default: output)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed (default: 42)')
    parser.add_argument('--e-cut', type=float, default=10.0, help='Electron cutoff in keV (default: 10.0)')
    args = parser.parse_args()
    
    print_banner()
    
    # Configure simulation
    beam = BeamConfig(energy=args.energy, n_histories=args.histories, field_size=args.field_size)
    phantom = PhantomConfig(size_x=args.phantom_size, size_y=args.phantom_size, size_z=args.phantom_size, voxel_size=args.voxel_size)
    transport = TransportConfig(e_cut_kinetic=args.e_cut / 1000.0)
    config = SimulationConfig(beam=beam, phantom=phantom, transport=transport, output_dir=args.output, seed=args.seed)
    
    # Print configuration
    print(f'\n  Beam Energy:     {beam.energy:.1f} MeV')
    print(f'  Histories:       {beam.n_histories:,}')
    print(f'  Phantom:         {phantom.size_x}x{phantom.size_y}x{phantom.size_z} cm³')
    print(f'  Voxel Size:      {phantom.voxel_size} cm ({phantom.voxel_size*10:.0f} mm)')
    nx = int(np.ceil(phantom.size_x / phantom.voxel_size))
    ny = int(np.ceil(phantom.size_y / phantom.voxel_size))
    nz = int(np.ceil(phantom.size_z / phantom.voxel_size))
    print(f'  Grid:            {nx}x{ny}x{nz} = {nx*ny*nz:,} voxels')
    print(f'  Field Size:      {beam.field_size}x{beam.field_size} cm²')
    print(f'  Electron Cutoff: {transport.e_cut_kinetic*1000:.0f} keV')
    print(f'  Random Seed:     {config.seed}')
    print(f'  Output Dir:      {config.output_dir}')
    print()
    
    # Run simulation
    print('  Running simulation...')
    sim = MonteCarloSimulation(config)
    elapsed = sim.run(progress_callback=progress_callback)
    print()  # newline after progress
    
    # Print results summary
    print(f'\n  Simulation completed in {elapsed:.1f} seconds')
    print(f'  Rate: {beam.n_histories/elapsed:.0f} histories/second')
    
    # Get PDD metrics
    depths, pdd, pdd_unc = sim.scorer.get_depth_dose()
    i_max = np.argmax(pdd)
    d_max = depths[i_max]
    print(f'\n  Results:')
    print(f'    d_max:        {d_max:.2f} cm')
    
    # R50 (interpolated)
    pdd_falling = pdd[i_max:]
    depths_falling = depths[i_max:]
    r50 = None
    for j in range(len(pdd_falling) - 1):
        if pdd_falling[j] >= 50.0 and pdd_falling[j+1] < 50.0:
            frac = (50.0 - pdd_falling[j]) / (pdd_falling[j+1] - pdd_falling[j])
            r50 = depths_falling[j] + frac * (depths_falling[j+1] - depths_falling[j])
            break
    if r50 is not None:
        print(f'    R_50:         {r50:.2f} cm')
        print(f'    E_0 (est):    {2.33 * r50:.1f} MeV (from R_50 × 2.33)')
    
    r80 = None
    for j in range(len(pdd_falling) - 1):
        if pdd_falling[j] >= 80.0 and pdd_falling[j+1] < 80.0:
            frac = (80.0 - pdd_falling[j]) / (pdd_falling[j+1] - pdd_falling[j])
            r80 = depths_falling[j] + frac * (depths_falling[j+1] - depths_falling[j])
            break
    if r80 is not None:
        print(f'    R_80:         {r80:.2f} cm')
    
    # Average uncertainty in high-dose region
    high_dose = pdd > 50
    if np.any(high_dose):
        avg_unc = np.mean(pdd_unc[high_dose])
        print(f'    Avg Uncertainty (>50% dose): {avg_unc:.1f}%')
    
    # Energy conservation check
    total_dep = np.sum(sim.scorer.energy_deposited)
    print(f'\n  Energy Conservation:')
    print(f'    Total Energy In:        {sim.total_energy_in:.2f} MeV')
    print(f'    Total Energy Deposited: {total_dep:.2f} MeV')
    print(f'    Fraction Deposited:     {total_dep/sim.total_energy_in*100:.1f}%')
    
    # Generate plots
    plotter = DosePlotter(sim.scorer, sim.phantom, output_dir=config.output_dir)
    plotter.plot_all(beam_energy=beam.energy)
    
    # Save raw data
    data_path = os.path.join(config.output_dir, 'dose_data.npz')
    np.savez(data_path,
             dose=sim.scorer.dose,
             uncertainty=sim.scorer.dose_uncertainty,
             energy_deposited=sim.scorer.energy_deposited,
             depths=depths, pdd=pdd, pdd_unc=pdd_unc,
             phantom_size=np.array([phantom.size_x, phantom.size_y, phantom.size_z]),
             voxel_size=phantom.voxel_size,
             beam_energy=beam.energy,
             n_histories=beam.n_histories)
    print(f'\n  Raw data saved to: {data_path}')
    
    # Save CSV summary
    csv_path = os.path.join(config.output_dir, 'dose_summary.csv')
    with open(csv_path, 'w') as f:
        f.write("Depth (cm),PDD (%),Uncertainty (%)\n")
        for d, p, u in zip(depths, pdd, pdd_unc):
            f.write(f"{d:.2f},{p:.2f},{u:.2f}\n")
    print(f'  PDD summary saved to: {csv_path}')
    
    print('\n' + '=' * 70)
    print('  Done!')
    print('=' * 70)

if __name__ == '__main__':
    main()
    

