import os
import subprocess
from flask import Flask, render_template, request, jsonify, send_from_directory

from config import SimulationConfig, BeamConfig, PhantomConfig, TransportConfig
from transport.simulation import MonteCarloSimulation

app = Flask(__name__)

# Ensure output directory exists for plots
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/output/<path:filename>')
def serve_output(filename):
    return send_from_directory(OUTPUT_DIR, filename)

@app.route('/run_full', methods=['POST'])
def run_full():
    data = request.json
    try:
        # Build command based on inputs
        cmd = [
            "python3", "main.py",
            "--energy", str(data.get('energy', 12.0)),
            "--histories", str(data.get('histories', 100000)),
            "--phantom-size", str(data.get('phantom_size', 10.0)),
            "--voxel-size", str(data.get('voxel_size', 0.2)),
            "--field-size", str(data.get('field_size', 10.0)),
            "--e-cut", str(data.get('e_cut', 10.0)),
            "--seed", str(data.get('seed', 42)),
            "--output", "output"
        ]
        
        # Run subprocess and block until complete
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        return jsonify({"status": "success", "message": "Simulation completed successfully.", "logs": result.stdout})
        
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": str(e), "logs": e.stdout + "\n" + e.stderr}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/run_animation', methods=['POST'])
def run_animation():
    data = request.json
    try:
        # Animation requires a very small number of histories
        histories = min(int(data.get('histories', 10)), 1000) # Cap at 1000 for browser safety
        
        beam = BeamConfig(
            energy=float(data.get('energy', 12.0)), 
            n_histories=histories, 
            field_size=float(data.get('field_size', 10.0))
        )
        phantom = PhantomConfig(
            size_x=float(data.get('phantom_size', 10.0)), 
            size_y=float(data.get('phantom_size', 10.0)), 
            size_z=float(data.get('phantom_size', 10.0)), 
            voxel_size=float(data.get('voxel_size', 0.2))
        )
        transport = TransportConfig(e_cut_kinetic=float(data.get('e_cut', 10.0)) / 1000.0)
        
        config = SimulationConfig(beam=beam, phantom=phantom, transport=transport, seed=int(data.get('seed', 42)))
        
        sim = MonteCarloSimulation(config)
        elapsed, tracks = sim.run(record_tracks=True)
        
        # Group tracks by particle ID to make drawing lines easier in JS
        grouped_tracks = {}
        for point in tracks:
            pid = point['id']
            if pid not in grouped_tracks:
                grouped_tracks[pid] = {"type": point["type"], "points": []}
            grouped_tracks[pid]["points"].append([point["x"], point["y"], point["z"]])
            
        return jsonify({"status": "success", "tracks": list(grouped_tracks.values())})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
