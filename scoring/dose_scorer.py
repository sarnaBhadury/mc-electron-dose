import numpy as np

class DoseScorer:
    def __init__(self, phantom):
        self.phantom = phantom
        self.nx = phantom.nx
        self.ny = phantom.ny
        self.nz = phantom.nz
        # Running sums for dose calculation
        self.energy_deposited = np.zeros((self.nx, self.ny, self.nz), dtype=np.float64)
        self.energy_deposited_sq = np.zeros((self.nx, self.ny, self.nz), dtype=np.float64)
        self.history_energy = {}
        self.n_histories = 0
        self.dose = None
        self.dose_uncertainty = None
    
    def score(self, ix, iy, iz, energy_dep, weight=1.0):
        """Score energy deposition in a voxel."""
        if 0 <= ix < self.nx and 0 <= iy < self.ny and 0 <= iz < self.nz:
            idx = (ix, iy, iz)
            self.history_energy[idx] = self.history_energy.get(idx, 0.0) + energy_dep * weight
            
    def end_history(self):
        """Commit the accumulated energy for the current history to global sums."""
        for idx, dep in self.history_energy.items():
            self.energy_deposited[idx] += dep
            self.energy_deposited_sq[idx] += dep * dep
        self.history_energy.clear()
    
    def finalize(self, n_histories):
        """Compute dose and statistical uncertainty."""
        self.n_histories = n_histories
        voxel_mass = self.phantom.voxel_mass()  # grams
        
        # Dose in MeV/g per source particle
        self.dose = self.energy_deposited / (n_histories * voxel_mass)
        
        # Convert MeV/g to Gray (1 Gy = 6.2415e12 MeV/kg = 6.2415e9 MeV/g)
        # D[Gy] = D[MeV/g] / 6.2415e3 ... actually:
        # 1 Gy = 1 J/kg = 6.242e12 MeV / 1000g = 6.242e9 MeV/g
        # So D[Gy] = D[MeV/g] * 1e-3 / 1.602e-13 ... 
        # Simpler: keep dose in MeV/g and normalize to percentage
        
        # Relative statistical uncertainty
        mean = self.energy_deposited / n_histories
        mean_sq = self.energy_deposited_sq / n_histories
        variance = (mean_sq - mean**2) / max(n_histories - 1, 1)
        std = np.sqrt(np.maximum(variance, 0))
        
        self.dose_uncertainty = np.zeros_like(self.dose)
        nonzero = self.dose > 0
        self.dose_uncertainty[nonzero] = std[nonzero] / mean[nonzero]
    
    def get_depth_dose(self):
        """Get central-axis percentage depth dose."""
        if self.dose is None:
            raise RuntimeError("You must call finalize() before extracting dose profiles.")
            
        # Central voxel indices
        cx = self.nx // 2
        cy = self.ny // 2
        
        # Average over central 3x3 voxels for better statistics
        x_range = slice(max(0, cx-1), min(self.nx, cx+2))
        y_range = slice(max(0, cy-1), min(self.ny, cy+2))
        
        depth_dose = np.mean(self.dose[x_range, y_range, :], axis=(0, 1))
        depth_uncertainty = np.sqrt(np.mean(self.dose_uncertainty[x_range, y_range, :]**2, axis=(0, 1)))
        
        # Depth values (center of each voxel)
        depths = (np.arange(self.nz) + 0.5) * self.phantom.voxel_size
        
        # Normalize to percentage (100% at max)
        max_dose = np.max(depth_dose)
        if max_dose > 0:
            pdd = depth_dose / max_dose * 100.0
            pdd_unc = depth_uncertainty * 100.0  # relative uncertainty
        else:
            pdd = depth_dose
            pdd_unc = depth_uncertainty
        
        return depths, pdd, pdd_unc
    
    def get_lateral_profile(self, depth_cm, axis='x'):
        """Get lateral dose profile at given depth."""
        if self.dose is None:
            raise RuntimeError("You must call finalize() before extracting dose profiles.")
            
        iz = int(depth_cm / self.phantom.voxel_size)
        iz = min(iz, self.nz - 1)
        
        if axis == 'x':
            # Average over central 3 y-voxels
            cy = self.ny // 2
            y_range = slice(max(0, cy-1), min(self.ny, cy+2))
            profile = np.mean(self.dose[:, y_range, iz], axis=1)
            positions = (np.arange(self.nx) + 0.5) * self.phantom.voxel_size
        else:
            cx = self.nx // 2
            x_range = slice(max(0, cx-1), min(self.nx, cx+2))
            profile = np.mean(self.dose[x_range, :, iz], axis=0)
            positions = (np.arange(self.ny) + 0.5) * self.phantom.voxel_size
        
        max_val = np.max(profile)
        if max_val > 0:
            profile = profile / max_val * 100.0
        
        return positions, profile
    
    def get_2d_dose_map(self, axis='xz', index=None):
        """Get 2D dose slice.
        axis: 'xz' (sagittal at y=center), 'yz' (coronal at x=center), 'xy' (axial at given z)
        """
        if self.dose is None:
            raise RuntimeError("You must call finalize() before extracting dose profiles.")
            
        if axis == 'xz':
            idx = index if index is not None else self.ny // 2
            dose_2d = self.dose[:, idx, :]
        elif axis == 'yz':
            idx = index if index is not None else self.nx // 2
            dose_2d = self.dose[idx, :, :]
        elif axis == 'xy':
            idx = index if index is not None else self.nz // 4
            dose_2d = self.dose[:, :, idx]
        else:
            raise ValueError(f"Invalid axis '{axis}'. Choose from 'xz', 'yz', 'xy'.")
        
        return dose_2d
