document.addEventListener('DOMContentLoaded', () => {
    // Grid calculator
    const phantomSizeInput = document.getElementById('phantom_size');
    const voxelSizeInput = document.getElementById('voxel_size');
    const gridCalc = document.getElementById('grid-calc');

    function updateGrid() {
        const pSize = parseFloat(phantomSizeInput.value) || 10;
        const vSize = parseFloat(voxelSizeInput.value) || 0.2;
        const n = Math.ceil(pSize / vSize);
        const total = n * n * n;
        gridCalc.textContent = total.toLocaleString();
    }

    phantomSizeInput.addEventListener('input', updateGrid);
    voxelSizeInput.addEventListener('input', updateGrid);

    // Form inputs
    function getInputs() {
        return {
            energy: parseFloat(document.getElementById('energy').value),
            histories: parseInt(document.getElementById('histories').value),
            phantom_size: parseFloat(document.getElementById('phantom_size').value),
            voxel_size: parseFloat(document.getElementById('voxel_size').value),
            field_size: parseFloat(document.getElementById('field_size').value),
            e_cut: parseFloat(document.getElementById('e_cut').value),
            seed: parseInt(document.getElementById('seed').value)
        };
    }

    // UI state
    const btnFull = document.getElementById('btn-run-full');
    const btnAnim = document.getElementById('btn-run-anim');
    const loading = document.getElementById('loading');
    const loadingText = document.getElementById('loading-text');
    const resultsContent = document.getElementById('results-content');

    function setLoading(isLoading, text) {
        btnFull.disabled = isLoading;
        btnAnim.disabled = isLoading;
        if (isLoading) {
            loading.classList.remove('hidden');
            loadingText.textContent = text;
            resultsContent.innerHTML = '<div class="placeholder"><p>Working...</p></div>';
        } else {
            loading.classList.add('hidden');
        }
    }

    // Run Full
    btnFull.addEventListener('click', async () => {
        setLoading(true, "Running Full Simulation (this may take a few minutes)...");
        try {
            const res = await fetch('/run_full', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(getInputs())
            });
            const data = await res.json();
            
            if (data.status === 'success') {
                // Add timestamp to prevent caching
                const t = new Date().getTime();
                resultsContent.innerHTML = `
                    <div class="results-grid">
                        <img src="/output/dose_2d_map.png?t=${t}" alt="2D Dose Map">
                        <img src="/output/depth_dose.png?t=${t}" alt="Depth Dose">
                        <img src="/output/lateral_profiles.png?t=${t}" alt="Lateral Profiles">
                        <img src="/output/uncertainty_map.png?t=${t}" alt="Uncertainty Map">
                    </div>
                    <pre style="margin-top: 1rem; max-height: 200px; overflow-y: auto; font-size: 0.8rem; color: #94a3b8; background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 8px;">${data.logs}</pre>
                `;
            } else {
                resultsContent.innerHTML = `<p style="color: #ef4444;">Error: ${data.message}</p>`;
            }
        } catch (e) {
            resultsContent.innerHTML = `<p style="color: #ef4444;">Connection Error: ${e.message}</p>`;
        } finally {
            setLoading(false);
        }
    });

    // Run Animation
    btnAnim.addEventListener('click', async () => {
        setLoading(true, "Simulating 10 electron histories for 3D animation...");
        try {
            const inputs = getInputs();
            inputs.histories = 10; // Force 10 histories
            
            const res = await fetch('/run_animation', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(inputs)
            });
            const data = await res.json();
            
            if (data.status === 'success') {
                resultsContent.innerHTML = '<div id="plotly-canvas"></div>';
                
                // Prepare Plotly Traces
                const traces = [];
                const colorMap = {
                    'primary': '#3b82f6', // blue
                    'electron': '#10b981', // green (delta rays)
                    'photon': '#f59e0b' // yellow (bremsstrahlung)
                };

                const phantomSize = inputs.phantom_size;
                const halfP = phantomSize / 2;

                // Add Phantom bounding box
                traces.push({
                    type: 'mesh3d',
                    x: [-halfP, -halfP, halfP, halfP, -halfP, -halfP, halfP, halfP],
                    y: [-halfP, halfP, halfP, -halfP, -halfP, halfP, halfP, -halfP],
                    z: [0, 0, 0, 0, phantomSize, phantomSize, phantomSize, phantomSize],
                    i: [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
                    j: [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
                    k: [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
                    opacity: 0.1,
                    color: '#94a3b8',
                    name: 'Water Phantom',
                    hoverinfo: 'skip'
                });

                // Prepare initial empty traces for particles
                const initialTraces = [...traces];
                const trackDataList = data.tracks;
                const updateIndices = [];
                
                trackDataList.forEach((track, i) => {
                    let name = 'Delta Ray';
                    if (track.type === 'primary') name = 'Primary e-';
                    else if (track.type === 'photon') name = 'Photon';
                    
                    const traceIdx = initialTraces.length;
                    updateIndices.push(traceIdx);
                    
                    initialTraces.push({
                        type: 'scatter3d',
                        mode: 'lines',
                        x: track.points.length > 0 ? [track.points[0][0]] : [],
                        y: track.points.length > 0 ? [track.points[0][1]] : [],
                        z: track.points.length > 0 ? [track.points[0][2]] : [],
                        line: {
                            color: colorMap[track.type] || '#ffffff',
                            width: track.type === 'primary' ? 4 : 2
                        },
                        name: name,
                        showlegend: i < 50
                    });
                });

                const layout = {
                    title: '3D Monte Carlo Electron Tracks',
                    paper_bgcolor: 'transparent',
                    plot_bgcolor: 'transparent',
                    font: { color: '#f8fafc' },
                    scene: {
                        xaxis: { title: 'X (cm)', range: [-halfP, halfP] },
                        yaxis: { title: 'Y (cm)', range: [-halfP, halfP] },
                        zaxis: { title: 'Depth (cm)', range: [0, phantomSize], autorange: 'reversed' },
                        camera: {
                            eye: { x: 1.5, y: 1.5, z: -1.5 }
                        }
                    },
                    margin: { l: 0, r: 0, b: 0, t: 40 }
                };

                Plotly.newPlot('plotly-canvas', initialTraces, layout);
                
                // Animation loop
                let maxPoints = 0;
                trackDataList.forEach(t => { if(t.points.length > maxPoints) maxPoints = t.points.length; });
                
                let currentPoint = 1;
                function animateTracks() {
                    if (currentPoint >= maxPoints) return;
                    
                    const updateX = [];
                    const updateY = [];
                    const updateZ = [];
                    const indices = [];
                    
                    trackDataList.forEach((track, i) => {
                        if (currentPoint < track.points.length) {
                            updateX.push([track.points[currentPoint][0]]);
                            updateY.push([track.points[currentPoint][1]]);
                            updateZ.push([track.points[currentPoint][2]]);
                            indices.push(updateIndices[i]);
                        }
                    });
                    
                    if (indices.length > 0) {
                        Plotly.extendTraces('plotly-canvas', {
                            x: updateX,
                            y: updateY,
                            z: updateZ
                        }, indices);
                    }
                    
                    currentPoint++;
                    // Add a tiny delay between frames to see the electron moving more clearly
                    setTimeout(() => requestAnimationFrame(animateTracks), 15);
                }
                
                // Start animation shortly after initial render
                setTimeout(animateTracks, 500);
            } else {
                resultsContent.innerHTML = `<p style="color: #ef4444;">Error: ${data.message}</p>`;
            }
        } catch (e) {
            resultsContent.innerHTML = `<p style="color: #ef4444;">Connection Error: ${e.message}</p>`;
        } finally {
            setLoading(false);
        }
    });
});
