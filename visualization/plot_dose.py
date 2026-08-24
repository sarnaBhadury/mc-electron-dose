import numpy as np
import matplotlib
matplotlib.use('Agg')  # non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib import cm
import os

class DosePlotter:
    def __init__(self, scorer, phantom, output_dir='output'):
        self.scorer = scorer
        self.phantom = phantom
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        plt.style.use('dark_background')
    
    def plot_depth_dose(self, beam_energy=None, save=True):
        """Plot percentage depth dose curve with clinical markers."""
        fig, ax = plt.subplots(figsize=(10, 7))
        
        depths, pdd, pdd_unc = self.scorer.get_depth_dose()
        
        # Prepend x=0 for plotting to make the line start exactly on the Y-axis
        plot_depths = np.insert(depths, 0, 0.0)
        plot_pdd = np.insert(pdd, 0, pdd[0])
        plot_pdd_unc = np.insert(pdd_unc, 0, pdd_unc[0])
        
        # Apply a mild Gaussian filter to smooth the PDD curve (reduces jagged noise)
        from scipy.ndimage import gaussian_filter1d
        plot_pdd_smoothed = gaussian_filter1d(plot_pdd, sigma=1.0)
        
        # Plot smoothed PDD (no shaded uncertainty region to keep it clean)
        ax.plot(plot_depths, plot_pdd_smoothed, 'c-', linewidth=2, label='Monte Carlo PDD')
        
        # Find clinical parameters
        if np.max(pdd) > 0:
            # d_max
            i_max = np.argmax(pdd)
            d_max = depths[i_max]
            ax.axvline(d_max, color='gold', linestyle='--', alpha=0.7, label=f'$d_{{max}}$ = {d_max:.2f} cm')
            
            # R50 (depth at 50% of max) - use linear interpolation
            pdd_falling = pdd[i_max:]
            depths_falling = depths[i_max:]
            if len(pdd_falling) > 1:
                # Interpolate to find R50
                for j in range(len(pdd_falling) - 1):
                    if pdd_falling[j] >= 50.0 and pdd_falling[j+1] < 50.0:
                        frac = (50.0 - pdd_falling[j]) / (pdd_falling[j+1] - pdd_falling[j])
                        r50 = depths_falling[j] + frac * (depths_falling[j+1] - depths_falling[j])
                        ax.axvline(r50, color='lime', linestyle='--', alpha=0.7, label=f'$R_{{50}}$ = {r50:.2f} cm')
                        break
            
            # R80 - use linear interpolation
            if len(pdd_falling) > 1:
                for j in range(len(pdd_falling) - 1):
                    if pdd_falling[j] >= 80.0 and pdd_falling[j+1] < 80.0:
                        frac = (80.0 - pdd_falling[j]) / (pdd_falling[j+1] - pdd_falling[j])
                        r80 = depths_falling[j] + frac * (depths_falling[j+1] - depths_falling[j])
                        ax.axvline(r80, color='orange', linestyle=':', alpha=0.7, label=f'$R_{{80}}$ = {r80:.2f} cm')
                        break
        
        # Formatting
        title = 'Percentage Depth Dose - Electron Beam'
        if beam_energy:
            title += f' ({beam_energy} MeV)'
        ax.set_title(title, fontsize=16, fontweight='bold', color='white')
        ax.set_xlabel('Depth in Water (cm)', fontsize=13)
        ax.set_ylabel('Relative Dose (%)', fontsize=13)
        ax.set_ylim(-5, 115)
        ax.set_xlim(0, depths[-1])
        ax.legend(fontsize=11, loc='upper right')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        if save:
            path = os.path.join(self.output_dir, 'depth_dose.png')
            fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='black')
            print(f'Saved: {path}')
        plt.close(fig)
        return fig
    
    def plot_2d_dose_map(self, beam_energy=None, save=True):
        """Plot 2D dose distribution (XZ sagittal plane through beam center)."""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        dose_2d = self.scorer.get_2d_dose_map(axis='xz')
        
        # Normalize to percentage
        max_dose = np.max(dose_2d)
        if max_dose > 0:
            dose_pct = dose_2d / max_dose * 100.0
        else:
            dose_pct = dose_2d
        
        # Create extent [z_min, z_max, x_min, x_max]
        extent = [0, self.phantom.size_z, 0, self.phantom.size_x]
        
        # Plot dose colormap
        im = ax.imshow(dose_pct, extent=extent, origin='lower', aspect='auto',
                       cmap='hot', vmin=0, vmax=100, interpolation='bilinear')
        
        # Add isodose contour lines
        x_centers = (np.arange(dose_pct.shape[0]) + 0.5) * self.phantom.voxel_size
        z_centers = (np.arange(dose_pct.shape[1]) + 0.5) * self.phantom.voxel_size
        Z_grid, X_grid = np.meshgrid(z_centers, x_centers)
        
        contour_levels = [10, 20, 30, 50, 70, 80, 90, 95]
        cs = ax.contour(Z_grid, X_grid, dose_pct, levels=contour_levels,
                       colors='cyan', linewidths=0.8, alpha=0.6)
        ax.clabel(cs, inline=True, fontsize=8, fmt='%d%%')
        
        # Colorbar
        cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
        cbar.set_label('Relative Dose (%)', fontsize=12)
        
        title = '2D Dose Distribution (Sagittal Plane)'
        if beam_energy:
            title += f' - {beam_energy} MeV Electron Beam'
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Depth in Water (cm)', fontsize=12)
        ax.set_ylabel('Lateral Position (cm)', fontsize=12)
        
        plt.tight_layout()
        if save:
            path = os.path.join(self.output_dir, 'dose_2d_map.png')
            fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='black')
            print(f'Saved: {path}')
        plt.close(fig)
        return fig
    
    def plot_lateral_profiles(self, beam_energy=None, save=True):
        """Plot lateral dose profiles at multiple depths."""
        fig, ax = plt.subplots(figsize=(10, 7))
        
        # Get d_max from PDD
        depths_pdd, pdd, _ = self.scorer.get_depth_dose()
        i_max = np.argmax(pdd)
        d_max = depths_pdd[i_max]
        
        # Plot profiles at d_max, R50 approximate, and deeper
        profile_depths = [d_max, d_max * 1.5, d_max * 2.5]
        colors = ['cyan', 'lime', 'orange']
        
        for depth, color in zip(profile_depths, colors):
            if depth < self.phantom.size_z:
                positions, profile = self.scorer.get_lateral_profile(depth, axis='x')
                ax.plot(positions - self.phantom.size_x/2, profile, '-', 
                       color=color, linewidth=2, label=f'Depth = {depth:.1f} cm')
        
        title = 'Lateral Dose Profiles'
        if beam_energy:
            title += f' - {beam_energy} MeV'
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Off-axis Distance (cm)', fontsize=12)
        ax.set_ylabel('Relative Dose (%)', fontsize=12)
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(-5, 115)
        
        plt.tight_layout()
        if save:
            path = os.path.join(self.output_dir, 'lateral_profiles.png')
            fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='black')
            print(f'Saved: {path}')
        plt.close(fig)
        return fig
    
    def plot_uncertainty_map(self, save=True):
        """Plot 2D map of statistical uncertainty."""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Get uncertainty at central plane
        iy = self.phantom.ny // 2
        unc_2d = self.scorer.dose_uncertainty[:, iy, :] * 100  # percentage
        
        extent = [0, self.phantom.size_z, 0, self.phantom.size_x]
        im = ax.imshow(unc_2d, extent=extent, origin='lower', aspect='auto',
                       cmap='viridis', vmin=0, interpolation='bilinear')
        
        cbar = fig.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('Relative Uncertainty (%)', fontsize=12)
        
        ax.set_title('Statistical Uncertainty Map', fontsize=14, fontweight='bold')
        ax.set_xlabel('Depth (cm)', fontsize=12)
        ax.set_ylabel('Lateral Position (cm)', fontsize=12)
        
        plt.tight_layout()
        if save:
            path = os.path.join(self.output_dir, 'uncertainty_map.png')
            fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='black')
            print(f'Saved: {path}')
        plt.close(fig)
        return fig
    
    def plot_all(self, beam_energy=None):
        """Generate all plots."""
        print('\nGenerating plots...')
        self.plot_depth_dose(beam_energy)
        self.plot_2d_dose_map(beam_energy)
        self.plot_lateral_profiles(beam_energy)
        self.plot_uncertainty_map()
        print(f'All plots saved to: {self.output_dir}/')
