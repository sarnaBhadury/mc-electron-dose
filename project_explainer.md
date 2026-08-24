# 🔬 mc-electron-dose — Complete Beginner's Guide

> Think of this project as a **virtual physics laboratory**. Instead of using a real hospital radiation machine, this program simulates in a computer what happens when a beam of electrons is fired into a block of water. The goal is to figure out **how much radiation energy gets deposited at different depths** — something doctors need to know when planning cancer treatment.

---

## 🌍 The Big Picture — What Does This Project Do?

In **radiation therapy (cancer treatment)**, doctors use electron beams to destroy tumors. Before treating a real patient, they need to know:
- How deep does the beam penetrate?
- Where does most of the energy land?
- How does the dose "spread out" sideways?

Measuring this in real life every time is expensive. So we do it in a **computer simulation** instead.

This project uses a technique called **Monte Carlo simulation** — which basically means: *"use random numbers to simulate what many many particles do, and average the results."*

It's like: if you want to know the average height of people in a city, you don't measure everyone — you randomly pick 50,000 people and measure them.

---

## 🗂️ Project Folder Map

```
mc-electron-dose/
│
├── main.py                  ← THE ENTRY POINT. Run this to start everything.
├── config.py                ← Settings/options (like energy, phantom size)
│
├── geometry/
│   └── voxel_phantom.py     ← The "box of water" the beam goes through
│
├── physics/
│   ├── constants.py         ← Real physics numbers (mass of electron, etc.)
│   ├── stopping_power.py    ← How fast electrons lose energy in water
│   ├── cross_sections.py    ← How likely each physics event is
│   └── scattering.py        ← How electrons get deflected/scattered
│
├── transport/
│   ├── particle.py          ← What a particle (electron/photon) looks like
│   ├── simulation.py        ← The main loop that runs all histories
│   ├── electron_transport.py← How ONE electron travels step by step
│   └── photon_transport.py  ← How ONE photon travels step by step
│
├── scoring/
│   └── dose_scorer.py       ← Tallies how much energy lands in each voxel
│
└── visualization/
    └── plot_dose.py         ← Makes the graphs/plots at the end
```

---

## 🔑 Key Concepts (Before We Start)

### What is a Voxel?
A **voxel** is a tiny 3D cube — like a pixel, but in 3D. The water phantom is divided into thousands of tiny cubes. Each cube records how much energy was deposited in it.

> 🧊 Imagine a big ice cube tray — each little cell is a voxel.

### What is a History?
One **history** = one electron particle being fired, and following it (and all the secondary particles it creates) until everything stops. We run 50,000 histories and average them.

### What are Direction Cosines?
Instead of saying "the electron is going 45 degrees", we use three numbers `(u, v, w)` that describe the direction in 3D space. `u` = how much it moves in X, `v` = in Y, `w` = in Z. They always satisfy `u² + v² + w² = 1`.

---

## 📂 File-by-File Explanation

---

### 1. `config.py` — The Settings File
[config.py](file:///Users/arpanbhowmik/Desktop/mc-electron-dose/config.py)

This file defines **4 settings groups** using Python `dataclass` (a dataclass is like a simple box for holding related data).

```python
@dataclass
class BeamConfig:
    energy: float = 12.0       # Beam energy in MeV (like the power of the beam)
    energy_spread: float = 0.03 # ±3% variation in energy (beams aren't perfect)
    ssd: float = 100.0          # Source-to-surface distance in cm
    field_size: float = 10.0   # 10cm x 10cm area the beam covers
    n_histories: int = 100000  # How many electrons to simulate
```

```python
@dataclass
class PhantomConfig:
    size_x: float = 10.0    # 10cm wide
    size_y: float = 10.0    # 10cm deep (left-right)
    size_z: float = 10.0    # 10cm tall (how far the beam goes)
    voxel_size: float = 0.2 # Each little cube is 0.2cm = 2mm
    material: str = 'water'
    density: float = 1.0    # Water density = 1 g/cm³
```

```python
@dataclass
class TransportConfig:
    e_cut_kinetic: float = 0.01  # Stop tracking electron when energy < 10 keV
    p_cut: float = 0.001          # Stop tracking photon when energy < 1 keV
    ae_kinetic: float = 0.01     # Minimum energy for Möller events
    ap: float = 0.01              # Minimum energy for Bremsstrahlung photons
    step_fraction_xi: float = 0.03 # Each step = max 3% of current energy
```

```python
@dataclass
class SimulationConfig:
    beam: BeamConfig
    phantom: PhantomConfig
    transport: TransportConfig
    output_dir: str = 'output'
    seed: int = 42  # Random seed (same seed = same result every time)
    
    def __post_init__(self):
        # Automatically create the 'output' folder if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
```

---

### 2. `main.py` — The Entry Point
[main.py](file:///Users/arpanbhowmik/Desktop/mc-electron-dose/main.py)

This is the **first file that runs** when you type `python main.py`. It's like the director of a movie.

#### `print_banner()` — Lines 14–19
```python
def print_banner():
    print('=' * 70)
    print('  Monte Carlo Electron Beam Dose Calculation')
    ...
```
Just prints a nice header in the terminal. Nothing complex.

---

#### `progress_callback(current, total, elapsed)` — Lines 21–27
```python
def progress_callback(current, total, elapsed):
    pct = current / total * 100          # e.g. 30000/50000 = 60%
    rate = current / elapsed             # e.g. 2000 particles/second
    eta = (total - current) / rate       # estimated time remaining
    print(f'\r  Progress: {current}/{total} ({pct:.1f}%) ...')
```
This prints a **live progress bar** in the terminal while the simulation runs. The `\r` at the start makes it overwrite the same line instead of printing a new line each time.

---

#### `main()` — Lines 29–128 — THE BRAIN

**Step 1: Parse command-line arguments**
```python
parser = argparse.ArgumentParser(...)
parser.add_argument('--energy', type=float, default=12.0, ...)
args = parser.parse_args()
```
This lets you run `python main.py --energy 6 --histories 10000` to change settings without editing the code.

**Step 2: Build configuration objects**
```python
beam = BeamConfig(energy=args.energy, ...)
phantom = PhantomConfig(...)
transport = TransportConfig()
config = SimulationConfig(beam=beam, ...)
```

**Step 3: Run the simulation**
```python
sim = MonteCarloSimulation(config)
elapsed = sim.run(progress_callback=progress_callback)
```

**Step 4: Extract and print results**
```python
depths, pdd, pdd_unc = sim.scorer.get_depth_dose()
i_max = np.argmax(pdd)   # index of maximum dose
d_max = depths[i_max]    # depth where dose is highest (e.g. 2.5 cm)
```

It also calculates:
- **R50** = depth where dose falls to 50% of maximum (important clinical metric)
- **R80** = depth where dose falls to 80%
- **E₀ estimate** = beam energy estimate from R50 × 2.33

**Step 5: Check energy conservation**
```python
total_dep = np.sum(sim.scorer.energy_deposited)
print(f'Fraction Deposited: {total_dep/sim.total_energy_in*100:.1f}%')
```
Some energy escapes the phantom (exits the sides or bottom), so we check what fraction we actually captured.

**Step 6: Make plots and save data**
```python
plotter = DosePlotter(sim.scorer, sim.phantom, output_dir=config.output_dir)
plotter.plot_all(beam_energy=beam.energy)
np.savez(data_path, dose=..., depths=..., ...)  # Save raw numbers
```

---

### 3. `geometry/voxel_phantom.py` — The Water Block
[voxel_phantom.py](file:///Users/arpanbhowmik/Desktop/mc-electron-dose/geometry/voxel_phantom.py)

Represents the **10cm × 10cm × 10cm box of water** that electrons travel through.

#### `__init__(...)` — Sets up the box
```python
self.nx = int(np.ceil(size_x / voxel_size))  # = ceil(10/0.2) = 50 voxels in X
self.ny = 50  # same in Y
self.nz = 50  # same in Z
```
So the phantom is a 50 × 50 × 50 = 125,000 tiny cubes.

#### `position_to_voxel(x, y, z)` — Which cube am I in?
```python
ix = int(x / self.voxel_size)  # e.g. x=3.7cm / 0.2cm = voxel 18
iy = int(y / self.voxel_size)
iz = int(z / self.voxel_size)
```
> 🧩 Think of it like asking: "which grid square on a map is this GPS coordinate in?"

Returns `(ix, iy, iz)` tuple, or `None` if outside the phantom.

#### `is_inside(x, y, z)` — Am I still inside the box?
```python
return (0 <= x < self.size_x and 0 <= y < self.size_y and 0 <= z < self.size_z)
```
Simple boundary check. Returns `True` or `False`.

#### `distance_to_boundary(x, y, z, u, v, w)` — How far until I hit a voxel wall?
This is the most mathematically interesting function here. It uses **ray-plane intersection**.

Imagine the electron is at position `(x,y,z)` moving in direction `(u,v,w)`. It will hit the wall of its current voxel at some distance. This function calculates that distance in all three directions and returns the **smallest** one (the first wall it hits).

```python
# In X direction: if moving right (u>0), next wall is at (ix+1)*voxel_size
if u > 0:
    x_boundary = (ix + 1) * self.voxel_size
    d = (x_boundary - x) / u   # distance = gap / speed_in_x
    d_min = min(d_min, d)
```

#### `voxel_mass()` — Mass of one tiny cube
```python
return self.density * self.voxel_size**3  # = 1.0 g/cm³ * (0.2cm)³ = 0.008 g
```
Needed later to convert energy (MeV) to dose (MeV/g).

---

### 4. `transport/particle.py` — What a Particle Is
[particle.py](file:///Users/arpanbhowmik/Desktop/mc-electron-dose/transport/particle.py)

#### `ParticleType` — Labels for particle types
```python
class ParticleType(IntEnum):
    ELECTRON = 0
    PHOTON = 1
    POSITRON = 2
```
Just integer labels (0, 1, 2) so we can tell particles apart.

#### `Particle` — The particle itself
```python
class Particle:
    __slots__ = ['x', 'y', 'z', 'u', 'v', 'w', 'energy', 'ptype', 'weight', 'alive']
```
> `__slots__` is a memory-saving trick — it tells Python exactly what attributes this object will have so Python doesn't waste memory on a dictionary.

Each particle has:
- **Position**: `x`, `y`, `z` — where it is right now (in cm)
- **Direction**: `u`, `v`, `w` — which way it's going (direction cosines)
- **Energy**: `energy` — how much kinetic energy it has (in MeV)
- **Type**: `ptype` — electron, photon, or positron
- **Weight**: `weight` — statistical weight (always 1.0 here, but kept for generality)
- **Alive**: `alive` — `True` until it stops or leaves the phantom

#### `copy()` — Make a copy of a particle
Used when creating secondary particles (delta-rays, photons) that share the same position/direction as the parent.

---

### 5. `transport/simulation.py` — The Main Loop
[simulation.py](file:///Users/arpanbhowmik/Desktop/mc-electron-dose/transport/simulation.py)

This is the **conductor** of the whole simulation.

#### `__init__(config)` — Set up the simulation
```python
self.phantom = VoxelPhantom(...)   # Create the water box
self.scorer = DoseScorer(phantom)  # Create the tally system
self.rng = np.random.RandomState(config.seed)  # Controlled randomness
self.total_energy_in = 0.0
```

The `rng` (random number generator) is seeded with a fixed number (42 by default). This means every run gives exactly the same result — important for reproducibility.

#### `generate_primary_electron()` — Fire one electron
```python
# Pick a random position inside the field
x = cx + self.rng.uniform(-half_field, half_field)
y = cy + self.rng.uniform(-half_field, half_field)
z = 0.0  # Always starts at the surface of the phantom

# Give it a tiny random angle (real beams aren't perfectly parallel)
theta = self.rng.normal(0, theta_max * 0.1)
phi = self.rng.uniform(0, 2*np.pi)
u = np.sin(theta) * np.cos(phi)
v = np.sin(theta) * np.sin(phi)
w = np.cos(theta)  # mostly going in Z direction

# Energy with a small Gaussian spread (±3%)
energy = self.rng.normal(beam.energy, beam.energy * beam.energy_spread)
```

Returns a `Particle` object at the surface, ready to enter the phantom.

#### `run(progress_callback)` — THE MAIN LOOP

```python
for i in range(n_histories):          # For each of 50,000 electrons:
    primary = self.generate_primary_electron()
    self.total_energy_in += primary.energy
    
    stack = [primary]                  # Start with just one electron
    while stack:
        particle = stack.pop()         # Grab one particle from the stack
        if particle is electron:
            transport_electron(particle, phantom, scorer, stack, rng, config)
        elif particle is photon:
            transport_photon(particle, phantom, scorer, stack, rng, config)
    
    # Report progress every 1%
    if progress_callback and (i+1) % (n_histories//100) == 0:
        progress_callback(i+1, n_histories, elapsed)

self.scorer.finalize(n_histories)   # Compute final doses
```

The **stack** is like a to-do list of particles. The primary electron goes in. As it travels, it may create secondary electrons (delta-rays) and photons (bremsstrahlung). Those go into the stack too. We keep processing until the stack is empty (all particles stopped or escaped).

> 🃏 Think of the stack like a deck of cards. You deal cards (particles) off the top, and sometimes playing a card generates new cards. You keep playing until the deck is empty.

---

### 6. `transport/electron_transport.py` — How One Electron Moves
[electron_transport.py](file:///Users/arpanbhowmik/Desktop/mc-electron-dose/transport/electron_transport.py)

This is the **most complex and important** file. The function `transport_electron()` uses the **Condensed History method**.

> **Condensed History** means: instead of simulating every tiny collision (there are millions per cm), we group them into steps, and apply average effects for each step. This makes simulation millions of times faster.

The function is a `while` loop that keeps running until the electron either runs out of energy or escapes.

#### Step-by-step breakdown of each loop iteration:

**Step 1 — Check if outside phantom**
```python
if not phantom.is_inside(particle.x, particle.y, particle.z):
    particle.alive = False
    return  # ← just stop. Particle escaped.
```

**Step 2 — Range Rejection (Big Optimization!)**
```python
csda_range = get_csda_range(particle.energy)  # How far could this electron go?
d_boundary = phantom.distance_to_boundary(...)  # How far to nearest wall?

if csda_range < d_boundary:
    # The electron will stop before hitting any boundary
    # → just dump ALL its remaining energy here, don't simulate step-by-step
    dose_scorer.score(ix, iy, iz, particle.energy, particle.weight)
    particle.alive = False
    return
```
This is a huge speed-up: if the electron definitely won't reach the voxel boundary, we skip all the remaining steps.

**Step 3 — Calculate step size**
```python
s_total = get_total_stopping_power(particle.energy)  # energy loss rate
s_max = 0.03 * particle.energy / s_total  # step = at most 3% energy loss
s = min(s_max, d_boundary * 0.99)         # don't step past the boundary
```
We limit step size so we don't lose too much energy at once, and don't overshoot voxel boundaries.

**Steps 4 & 5 — Sample distances to rare events**
```python
lambda_moller = moller_mean_free_path(particle.energy, ...)
s_moller = -lambda_moller * np.log(rng.uniform())  # exponential distribution

lambda_brem = bremsstrahlung_mean_free_path(particle.energy, ...)
s_brem = -lambda_brem * np.log(rng.uniform())
```
In physics, the distance to the next rare collision follows an **exponential distribution**. The formula `-λ * ln(random)` samples from that distribution.

> 🎲 It's like asking: "based on probability, how far until this electron has a rare hard collision?"

**Step 6 — Pick the smallest distance (wins!)**
```python
actual_step = min(s, s_moller, s_brem, d_boundary)
```
The electron takes the **shortest** of all four distances. It stops at whichever event happens first.

**Step 8 — Continuous energy loss**
```python
l_restricted = get_restricted_collision_sp(particle.energy, ...)
de_mean = actual_step * l_restricted * density  # ΔE = step × stopping power × density
```
Stopping power is like "how many MeV does the electron lose per cm of water". Multiply by the step length to get the energy lost.

**Step 9 — Energy straggling (randomness)**
```python
sigma = 0.05 * np.sqrt(actual_step)
de = rng.normal(de_mean, sigma)  # add random fluctuation
de = np.clip(de, 0.0, particle.energy)  # can't lose more than you have
```
Real electrons don't all lose exactly the same energy — there's random variation. This adds that realistic scatter.

**Step 10 — Multiple Coulomb Scattering (direction change)**
```python
theta_rms = highland_theta_rms(particle.energy, actual_step)  # how much it bends
theta, phi = sample_scattering_angles(theta_rms, rng)
u_new, v_new, w_new = rotate_direction(u, v, w, theta, phi)
```
Electrons constantly get slightly deflected by atoms. After each step, the direction changes by a small random angle (bigger steps = bigger deflection).

**Step 11 — Move the particle**
```python
dx = actual_step * 0.5 * (u_old + u_new)  # average of before & after direction
dy = actual_step * 0.5 * (v_old + v_new)
dz = actual_step * 0.5 * (w_old + w_new)
particle.x += dx
particle.y += dy
particle.z += dz
```
Uses the **midpoint method**: half the step in old direction, half in new — more accurate than just using old or new alone.

**Step 12 — Score energy**
```python
dose_scorer.score(ix, iy, iz, de, particle.weight)
particle.energy -= de
```
Tell the scorer "voxel (ix,iy,iz) got `de` MeV of energy". Then subtract from electron's energy.

**Steps 13 & 14 — Create secondary particles if hard event occurred**
```python
if actual_step == s_moller:  # A Möller event happened (electron-electron collision)
    e_transfer = sample_moller_energy_transfer(particle.energy, ...)
    particle.energy -= e_transfer
    # Create a new delta-ray electron with that energy
    sec = Particle(..., e_transfer, ParticleType.ELECTRON, ...)
    secondary_stack.append(sec)  # ← will be transported later

elif actual_step == s_brem:  # A Bremsstrahlung event happened
    e_gamma = sample_bremsstrahlung_energy(particle.energy, ...)
    particle.energy -= e_gamma
    # Create a new photon
    sec = Particle(..., e_gamma, ParticleType.PHOTON, ...)
    secondary_stack.append(sec)
```

---

### 7. `transport/photon_transport.py` — How One Photon Moves
[photon_transport.py](file:///Users/arpanbhowmik/Desktop/mc-electron-dose/transport/photon_transport.py)

Photons (X-rays/gamma rays) travel very differently from electrons. They **don't slow down gradually** — they travel freely and then suddenly interact in one of three ways:

#### Step 1 — Sample distance to next interaction
```python
lambda_photon = photon_mean_free_path(particle.energy)  # mean free path in cm
s = -lambda_photon * np.log(rng.uniform())  # same exponential sampling trick
```

#### Step 2 — Jump to interaction point
```python
particle.x += s * particle.u
particle.y += s * particle.v
particle.z += s * particle.w
```
Photons fly straight there, no gradual slowdown.

#### Step 4 — Decide type of interaction
```python
interaction = photon_interaction_type(particle.energy, rng)
# Returns 'compton', 'photoelectric', or 'pair_production'
```
The probability of each depends on the photon's energy.

#### Compton Scattering
```python
e_scattered, theta, phi = sample_compton_scattering(particle.energy, rng)
e_recoil = particle.energy - e_scattered  # energy given to recoil electron
# Create a recoil electron secondary
sec = Particle(..., e_recoil, ParticleType.ELECTRON, ...)
secondary_stack.append(sec)
# The photon continues with reduced energy in a new direction
particle.energy = e_scattered
```
The photon bounces off an electron, giving it some energy. The photon continues, the electron gets added to the stack.

#### Photoelectric Effect
```python
sec = Particle(..., particle.energy, ParticleType.ELECTRON, ...)
secondary_stack.append(sec)
particle.alive = False  # photon is absorbed completely
```
The photon is completely absorbed and kicks out an electron with all its energy.

#### Pair Production (only above 1.022 MeV)
```python
e_remaining = particle.energy - 1.022  # 1.022 MeV is needed to create 2 electrons
e_elec = e_remaining / 2.0
e_pos  = e_remaining / 2.0
# Create one electron + one positron
```
The photon disappears and creates an electron-positron pair. Positrons eventually annihilate to create more photons, but this code simplifies that.

---

### 8. `physics/constants.py` — The Physics Dictionary
[constants.py](file:///Users/arpanbhowmik/Desktop/mc-electron-dose/physics/constants.py)

Just a collection of real-world physical constants and **NIST ESTAR data** — a table of measured values for electrons in water at 81 different energy levels.

```python
ELECTRON_MASS_MEV = 0.510999    # MeV (E=mc²)
CLASSICAL_ELECTRON_RADIUS = 2.81794e-13  # cm
AVOGADRO = 6.02214e23           # atoms per mole
WATER_RADIATION_LENGTH = 36.08  # g/cm² (key for scattering calc)
```

The big `_estar_data` array is like a lookup table. Each row is one energy level, and the columns are:
- [0] Energy (MeV)
- [1] Collision stopping power (MeV·cm²/g)
- [2] Radiative stopping power (MeV·cm²/g)
- [3] Total stopping power (MeV·cm²/g)
- [4] CSDA range (g/cm²)
- [5] Radiation yield
- [6] Density effect

---

### 9. `physics/stopping_power.py` — How Fast Electrons Lose Energy
[stopping_power.py](file:///Users/arpanbhowmik/Desktop/mc-electron-dose/physics/stopping_power.py)

#### `_log_log_interp(x, xp, yp)` — Log-log interpolation
```python
log_x = np.log(x_clamped)     # Take log of energy
log_xp = np.log(xp)           # Take log of known energies
log_yp = np.log(yp)           # Take log of known stopping powers
log_y = np.interp(log_x, log_xp, log_yp)   # Interpolate in log space
return np.exp(log_y)           # Convert back
```
Physics data often curves nicely on a log-log scale. We interpolate in that space for better accuracy.

> 📈 If you have a table of [energy → stopping power] for 81 specific energies, and you want the stopping power at 7.3 MeV (not in the table), you interpolate between the two nearest values.

#### `get_total_stopping_power(energy_mev)` 
Returns how many MeV the electron loses per (g/cm²) of material traversed.

#### `get_csda_range(energy_mev)`
CSDA = **Continuous Slowing Down Approximation**. Returns the total path length (in g/cm²) the electron would travel if it lost energy continuously. Used in range rejection.

#### `get_restricted_collision_sp(energy_mev, ae_kinetic)`
Like total stopping power but only counts small energy losses (below a threshold). Large energy transfers are handled separately as Möller events. Here simplified as 90% of collision SP.

---

### 10. `physics/cross_sections.py` — How Likely Each Event Is
[cross_sections.py](file:///Users/arpanbhowmik/Desktop/mc-electron-dose/physics/cross_sections.py)

**Cross section** = a measure of how likely a specific physics interaction is. Bigger cross section = more likely to happen.

#### `moller_mean_free_path(energy_mev, ...)` 
```python
sigma = (2*pi*r_e² * N_A * Z/A) / energy
return 1.0 / (density * sigma)  # mean free path = 1 / (density × cross_section)
```
Möller scattering = electron knocking another electron out of an atom (creates a delta-ray).

#### `bremsstrahlung_mean_free_path(energy_mev, ...)`
Bremsstrahlung = "braking radiation". When an electron slows down near an atom's nucleus, it emits a photon (X-ray). This gives the mean free path for that.

#### `sample_moller_energy_transfer(energy_mev, ae_kinetic, rng)`
```python
u = rng.uniform(0, 1)
return ae_kinetic / (1.0 - u * (1.0 - ae_kinetic/max_transfer))
```
Samples a random amount of energy transferred to the new delta-ray electron.

#### `sample_bremsstrahlung_energy(energy_mev, ap, rng)`
```python
u = rng.uniform(0, 1)
return ap * np.exp(u * np.log(energy_mev / ap))
```
Samples the photon energy from a "Kramers" distribution (roughly 1/energy shaped — more low-energy photons than high-energy ones).

#### `photon_mean_free_path(energy_mev, density)`
```python
mu_c = ... (Compton attenuation)
mu_p = ... (Photoelectric attenuation)
mu_pair = ... (Pair production attenuation)
return 1.0 / (density * (mu_c + mu_p + mu_pair))
```
Total mean free path = how far a photon goes on average before interacting.

#### `photon_interaction_type(energy_mev, rng)`
```python
u = rng.uniform(0, total)  # pick a random number between 0 and total
if u < mu_c: return 'compton'
elif u < mu_c + mu_p: return 'photoelectric'
else: return 'pair'
```
Uses the relative size of each cross section to randomly pick which interaction happens. Higher probability = wider "slice".

> 🎡 Think of a pie chart: Compton is 60%, photoelectric is 35%, pair is 5%. A random spin of the wheel lands in one slice.

---

### 11. `physics/scattering.py` — Direction Changes
[scattering.py](file:///Users/arpanbhowmik/Desktop/mc-electron-dose/physics/scattering.py)

#### `highland_theta_rms(energy_mev, step_length_cm)` — How much the electron bends
The **Highland formula** is a standard physics formula that gives the root-mean-square (typical) scattering angle after traveling a step:

```python
p_c = sqrt(E * (E + 2*m_e))   # momentum × speed_of_light
beta = p_c / (E + m_e)         # relativistic beta (fraction of speed of light)
x_X0 = step * density / radiation_length  # step in units of radiation lengths

theta_0 = (13.6 / (beta * p_c)) * sqrt(x_X0) * (1 + 0.038*ln(x_X0))
```
Higher energy → less bending. Longer step → more bending.

#### `sample_scattering_angles(theta_rms, rng)` — Random angle in 2D
```python
sigma = theta_rms / sqrt(2)        # split into two perpendicular components
theta_x = rng.normal(0, sigma)     # random angle in X plane
theta_y = rng.normal(0, sigma)     # random angle in Y plane
theta = sqrt(theta_x² + theta_y²) # total angle
phi = arctan2(theta_y, theta_x)   # azimuthal direction of scatter
```

#### `rotate_direction(u, v, w, theta, phi)` — Apply the deflection
This is pure 3D geometry — rotating a direction vector by angle `theta` around the azimuthal angle `phi`. The math uses standard Euler rotation formulas. After rotation, the result is normalized (made into a unit vector again).

---

### 12. `scoring/dose_scorer.py` — The Tally
[dose_scorer.py](file:///Users/arpanbhowmik/Desktop/mc-electron-dose/scoring/dose_scorer.py)

#### `__init__(phantom)` — Set up counters
```python
self.energy_deposited = np.zeros((nx, ny, nz))     # 3D grid of zeros
self.energy_deposited_sq = np.zeros((nx, ny, nz))  # for uncertainty calculation
```
Creates two 3D arrays — one for total energy, one for sum of squares (needed for statistics).

#### `score(ix, iy, iz, energy_dep, weight)` — Add energy to a voxel
```python
dep = energy_dep * weight
self.energy_deposited[ix, iy, iz] += dep
self.energy_deposited_sq[ix, iy, iz] += dep * dep
```
Every time a particle deposits energy in a voxel, we add it to the running total. We also store the squared value so we can later compute statistical uncertainty.

#### `finalize(n_histories)` — Compute final doses
```python
voxel_mass = self.phantom.voxel_mass()  # 0.008 g
self.dose = self.energy_deposited / (n_histories * voxel_mass)
# dose in MeV/g per source particle
```

Then for uncertainty (using standard statistical formula):
```python
mean = energy_deposited / n_histories
mean_sq = energy_deposited_sq / n_histories
variance = (mean_sq - mean²) / (n_histories - 1)
std = sqrt(variance)
dose_uncertainty = std / (mean * sqrt(n_histories))
```

#### `get_depth_dose()` — Central axis PDD
```python
# Take the central 3×3 voxels (for better statistics than just 1 column)
cx, cy = nx//2, ny//2
depth_dose = np.mean(dose[cx-1:cx+2, cy-1:cy+2, :], axis=(0,1))
# Average over x and y, leave z axis → gives dose vs depth
```
Returns `(depths, pdd, pdd_unc)` where pdd is normalized to 100% at maximum.

#### `get_lateral_profile(depth_cm, axis)` — Side profile at a depth
Returns the dose across the phantom at a specific depth — shows the beam's "width".

#### `get_2d_dose_map(axis)` — 2D slice of the 3D dose
Returns a 2D cross-section (like a CT scan slice) through the 3D dose distribution.

---

### 13. `visualization/plot_dose.py` — The Graphs
[plot_dose.py](file:///Users/arpanbhowmik/Desktop/mc-electron-dose/visualization/plot_dose.py)

#### `plot_depth_dose()` — The main clinical graph
Plots the **Percentage Depth Dose (PDD)** curve — dose vs depth from the surface. Marks d_max, R50, R80 with vertical dashed lines.

#### `plot_2d_dose_map()` — Color map of the dose
Shows a bird's-eye-view heatmap of the dose distribution through the center of the phantom. Adds isodose contour lines (like contour lines on a map, but for dose).

#### `plot_lateral_profiles()` — How wide is the beam?
Shows horizontal slices at different depths — shows where the beam spreads out laterally.

#### `plot_uncertainty_map()` — How reliable are our numbers?
Shows where statistical uncertainty is high (usually at the edges where few particles reach).

#### `plot_all()` — Generate all four plots
```python
def plot_all(self, beam_energy=None):
    self.plot_depth_dose(beam_energy)
    self.plot_2d_dose_map(beam_energy)
    self.plot_lateral_profiles(beam_energy)
    self.plot_uncertainty_map()
```

---

## 🔄 Complete Flow Diagram

```
python main.py
│
├── 1. Parse arguments (--energy, --histories, etc.)
├── 2. Create BeamConfig, PhantomConfig, TransportConfig, SimulationConfig
│
├── 3. Create MonteCarloSimulation(config)
│   ├── Creates VoxelPhantom (the water box)
│   ├── Creates DoseScorer (the tally system)
│   └── Creates random number generator
│
├── 4. sim.run() ← THE BIG LOOP (50,000 times)
│   │
│   └── For each history:
│       ├── generate_primary_electron() → Particle at surface
│       ├── Push to stack
│       └── While stack not empty:
│           ├── Pop a particle
│           │
│           ├── If ELECTRON → transport_electron()
│           │   └── While alive and energy > cutoff:
│           │       ├── Check if outside → stop
│           │       ├── Range rejection → dump energy and stop
│           │       ├── Calculate step size
│           │       ├── Sample Möller distance
│           │       ├── Sample Bremsstrahlung distance
│           │       ├── Take min step
│           │       ├── Lose energy continuously
│           │       ├── Scatter in new direction
│           │       ├── Move to new position
│           │       ├── Score energy in voxel
│           │       ├── If Möller event → create delta-ray → push to stack
│           │       └── If Brem event → create photon → push to stack
│           │
│           └── If PHOTON → transport_photon()
│               └── While alive and energy > cutoff:
│                   ├── Sample free path distance
│                   ├── Jump to interaction point
│                   ├── If outside → stop
│                   ├── Compton → reduce energy, create recoil e⁻ → push
│                   ├── Photoelectric → create photoelectron → push
│                   └── Pair production → create e⁻ + e⁺ → push both
│
├── 5. scorer.finalize() → Compute doses and uncertainties
│
├── 6. Print results (d_max, R50, R80, energy conservation)
│
├── 7. DosePlotter.plot_all() → Save 4 PNG graphs
│
└── 8. np.savez() → Save raw data to .npz file
```

---

## 🧮 Key Physics Concepts Summarized

| Concept | What It Means in Plain English |
|--------|-------------------------------|
| **Stopping Power** | How quickly electrons lose energy in water (MeV/cm) |
| **CSDA Range** | Maximum distance an electron can travel before stopping |
| **Möller Scattering** | Electron hits another electron, creates a "delta-ray" secondary |
| **Bremsstrahlung** | Electron is slowed near an atom's nucleus → emits an X-ray photon |
| **MCS (Multiple Coulomb Scattering)** | Thousands of tiny deflections from atomic nuclei, modeled statistically |
| **Compton Scattering** | Photon bounces off an electron, loses some energy |
| **Photoelectric Effect** | Photon is completely absorbed, kicks out an electron |
| **Pair Production** | High-energy photon (>1.022 MeV) converts into electron + positron |
| **Mean Free Path** | Average distance before next interaction (bigger = rarer) |
| **PDD Curve** | Graph of dose vs. depth — the main clinical output |
| **d_max** | Depth where dose is at its maximum |
| **R50** | Depth where dose falls to 50% — used to estimate beam energy |
| **Monte Carlo** | Simulate thousands of random particle histories, average the results |

---

## 🚀 How to Run the Project

```bash
# Basic run with defaults (12 MeV, 50,000 histories)
python main.py

# Custom run: 6 MeV beam, 100,000 histories
python main.py --energy 6 --histories 100000

# Smaller, faster test run
python main.py --energy 12 --histories 5000 --voxel-size 0.5
```

Output files will appear in the `output/` folder:
- `depth_dose.png` — The PDD curve
- `dose_2d_map.png` — 2D color map of dose
- `lateral_profiles.png` — Beam width at different depths
- `uncertainty_map.png` — Statistical noise map
- `dose_data.npz` — Raw numbers for further analysis
