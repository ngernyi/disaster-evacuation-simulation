# mapConverter.py - Fixed version
from pyproj import Transformer
import numpy as np

to_wgs = Transformer.from_crs("EPSG:32611", "EPSG:4326", always_xy=True)
to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32611", always_xy=True)

def from_utm_to_wgs(x, y):
    return to_wgs.transform(x, y)

def from_wgs_to_utm(x, y):
    return to_utm.transform(x, y)

def from_utm_to_grid(x, y, minMaxXY, cell_size=0.05):
    """Convert UTM coordinates to grid indices"""
    min_x, max_x, min_y, max_y = minMaxXY
    
    # Calculate column (X direction)
    col = int((x - min_x) / cell_size)
    
    row = int((y - min_y) / cell_size)
    
    # Clamp to grid bounds
    max_rows = int((max_y - min_y) / cell_size)
    max_cols = int((max_x - min_x) / cell_size)
    
    row = max(0, min(row, max_rows - 1))
    col = max(0, min(col, max_cols - 1))
    
    return row, col

def from_grid_to_utm(row, col, minMaxXY, cell_size=0.05):
    """Convert grid indices to UTM coordinates"""
    min_x, max_x, min_y, max_y = minMaxXY
    
    # Convert back to UTM
    x = min_x + col * cell_size + cell_size/2  # Add cell_size/2 to get center of cell
    y = min_y + row * cell_size + cell_size/2  # Add cell_size/2 to get center of cell
    
    return x, y

def read_filled_grid_and_minMaxXY(filled_grid_path, minMaxXY_path):
    """
    Read the filled grid and minMaxXY from files and return them.
    """
    filled_map = np.load(filled_grid_path)
    minMaxXY = np.load(minMaxXY_path)
    return filled_map, minMaxXY