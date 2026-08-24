import numpy as np
import os
import sys

from geometry.voxel_phantom import VoxelPhantom
from scoring.dose_scorer import DoseScorer
from visualization.plot_dose import DosePlotter

def main():
    data_path = 'output/dose_data.npz'
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Please run the simulation first.")
        sys.exit(1)

    print("Loading saved simulation data...")
    data = np.load(data_path)

    # Reconstruct Phantom
    p_size = data['phantom_size']
    voxel_size = float(data['voxel_size'])
    phantom = VoxelPhantom(size_x=p_size[0], size_y=p_size[1], size_z=p_size[2], voxel_size=voxel_size)

    # Reconstruct Scorer
    scorer = DoseScorer(phantom)
    scorer.dose = data['dose']
    scorer.dose_uncertainty = data['uncertainty']
    scorer.energy_deposited = data['energy_deposited']

    # Regenerate all plots
    print("Regenerating plots with updated plotting code...")
    plotter = DosePlotter(scorer, phantom, output_dir='output')
    plotter.plot_all(beam_energy=float(data['beam_energy']))
    print("Done! Plots successfully regenerated in the output/ directory.")

if __name__ == '__main__':
    main()
