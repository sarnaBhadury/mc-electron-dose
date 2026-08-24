import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
import mpl_toolkits.mplot3d.axes3d as p3
from itertools import combinations, product

# Add project root to path if needed
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import SimulationConfig, BeamConfig, PhantomConfig, TransportConfig
from transport.simulation import MonteCarloSimulation

def generate_video():
    print("Setting up simulation...")
    # Config for 10 histories
    beam = BeamConfig(energy=12.0, n_histories=10, field_size=5.0)
    phantom = PhantomConfig(size_x=10.0, size_y=10.0, size_z=10.0, voxel_size=0.5)
    transport = TransportConfig(e_cut_kinetic=0.01)
    config = SimulationConfig(beam=beam, phantom=phantom, transport=transport, seed=42)
    
    sim = MonteCarloSimulation(config)
    
    print("Running simulation and capturing tracks...")
    elapsed, tracks = sim.run(record_tracks=True)
    print(f"Captured {len(tracks)} coordinate points across all histories.")
    
    # Group tracks by particle ID
    grouped_tracks = {}
    for point in tracks:
        pid = point['id']
        if pid not in grouped_tracks:
            grouped_tracks[pid] = {"type": point["type"], "x": [], "y": [], "z": []}
        grouped_tracks[pid]["x"].append(point["x"])
        grouped_tracks[pid]["y"].append(point["y"])
        grouped_tracks[pid]["z"].append(point["z"])
        
    print(f"Grouped into {len(grouped_tracks)} distinct particle paths.")

    # Setup figure
    fig = plt.figure(figsize=(12, 10), facecolor='black')
    ax = fig.add_subplot(111, projection='3d')
    ax.set_facecolor('black')
    
    # Remove grid and axes for cinematic look
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.xaxis.set_pane_color((0.0, 0.0, 0.0, 0.0))
    ax.yaxis.set_pane_color((0.0, 0.0, 0.0, 0.0))
    ax.zaxis.set_pane_color((0.0, 0.0, 0.0, 0.0))
    ax.xaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
    ax.yaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
    ax.zaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
    
    halfP = phantom.size_x / 2.0
    ax.set_xlim([-halfP, halfP])
    ax.set_ylim([-halfP, halfP])
    ax.set_zlim([phantom.size_z, 0]) # Invert depth so z=0 is top
    
    # Draw faint wireframe box for phantom
    r = [-halfP, halfP]
    for s, e in combinations(np.array(list(product(r, r, [0, phantom.size_z]))), 2):
        if np.sum(np.abs(s-e)) == r[1]-r[0] or np.sum(np.abs(s-e)) == phantom.size_z:
            ax.plot3D(*zip(s, e), color="white", alpha=0.15)

    # Prepare lines
    lines = []
    track_list = list(grouped_tracks.values())
    
    color_map = {
        'primary': '#3b82f6', # Blue
        'electron': '#10b981', # Green (delta)
        'photon': '#f59e0b' # Yellow
    }
    
    for t in track_list:
        lw = 2.5 if t['type'] == 'primary' else 1.0
        alpha = 0.8 if t['type'] == 'primary' else 0.5
        line, = ax.plot([], [], [], color=color_map.get(t['type'], 'white'), lw=lw, alpha=alpha)
        lines.append(line)
        
    # Find max points to determine frames
    max_frames = max([len(t['x']) for t in track_list])
    
    print(f"Generating animation with {max_frames} frames...")
    
    def update(num):
        # Rotate camera slowly (1 full rotation over the entire animation)
        ax.view_init(elev=15, azim=num * (360 / max_frames))
        
        # Update lines
        for i, t in enumerate(track_list):
            limit = min(num, len(t['x']))
            if limit > 0:
                lines[i].set_data(t['x'][:limit], t['y'][:limit])
                lines[i].set_3d_properties(t['z'][:limit])
        return lines

    anim = FuncAnimation(fig, update, frames=max_frames, interval=30, blit=False)
    
    output_path = os.path.join(config.output_dir, 'electron_animation.mp4')
    writer = FFMpegWriter(fps=30, metadata=dict(artist='Monte Carlo Simulator'), bitrate=2000)
    
    print(f"Saving video to {output_path} (This may take a minute)...")
    anim.save(output_path, writer=writer)
    print("Done!")

if __name__ == '__main__':
    generate_video()
