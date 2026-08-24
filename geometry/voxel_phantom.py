import numpy as np

class VoxelPhantom:
    def __init__(self, size_x=10.0, size_y=10.0, size_z=10.0, voxel_size=0.2, density=1.0):
        """Create a 3D water phantom.
        
        Origin is at (0,0,0) = corner. Beam enters at z=0 surface, centered at (size_x/2, size_y/2, 0).
        
        Args:
            size_x, size_y, size_z: phantom dimensions in cm
            voxel_size: uniform voxel size in cm
            density: material density in g/cm3
        """
        self.size_x = size_x
        self.size_y = size_y  
        self.size_z = size_z
        self.voxel_size = voxel_size
        self.density = density
        self.nx = int(np.ceil(size_x / voxel_size))
        self.ny = int(np.ceil(size_y / voxel_size))
        self.nz = int(np.ceil(size_z / voxel_size))
    
    def position_to_voxel(self, x, y, z):
        """Convert position to voxel indices. Returns (ix, iy, iz) or None if outside."""
        ix = int(x / self.voxel_size)
        iy = int(y / self.voxel_size)
        iz = int(z / self.voxel_size)
        if 0 <= ix < self.nx and 0 <= iy < self.ny and 0 <= iz < self.nz:
            return (ix, iy, iz)
        return None
    
    def is_inside(self, x, y, z):
        """Check if position is inside phantom."""
        return (0 <= x < self.size_x and 0 <= y < self.size_y and 0 <= z < self.size_z)
    
    def distance_to_boundary(self, x, y, z, u, v, w):
        """Compute distance to nearest voxel boundary along direction (u,v,w).
        Returns distance in cm. Uses parametric ray-plane intersection."""
        # Current voxel boundaries
        ix = int(x / self.voxel_size)
        iy = int(y / self.voxel_size)
        iz = int(z / self.voxel_size)
        
        d_min = 1e10  # large number
        
        # X boundaries
        if u > 0:
            x_boundary = (ix + 1) * self.voxel_size
            d = (x_boundary - x) / u
            d_min = min(d_min, d)
        elif u < 0:
            x_boundary = ix * self.voxel_size
            d = (x_boundary - x) / u
            d_min = min(d_min, d)
        
        # Y boundaries  
        if v > 0:
            y_boundary = (iy + 1) * self.voxel_size
            d = (y_boundary - y) / v
            d_min = min(d_min, d)
        elif v < 0:
            y_boundary = iy * self.voxel_size
            d = (y_boundary - y) / v
            d_min = min(d_min, d)
        
        # Z boundaries
        if w > 0:
            z_boundary = (iz + 1) * self.voxel_size
            d = (z_boundary - z) / w
            d_min = min(d_min, d)
        elif w < 0:
            z_boundary = iz * self.voxel_size
            d = (z_boundary - z) / w
            d_min = min(d_min, d)
        
        return max(d_min, 1e-8)  # avoid zero
    
    def voxel_mass(self):
        """Mass of a single voxel in grams."""
        return self.density * self.voxel_size**3
