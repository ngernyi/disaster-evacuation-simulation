import numpy as np
import math
import matplotlib.pyplot as plt
import pandas as pd
from mapConverter import *


# function to read the map file
# input: file_path
# output: 
# 1) map_data in array format (list of features, each feature is a list of (x, y) tuples)
# 2) minMaxXY (min x, max x, min y, max y)
def read_map_file(file_path):
    features = []
    current_feature = []

    # min and max of x and y
    # 0 -> min x
    # 1 -> max x
    # 2 -> min y
    # 3 -> max y
    minMaxXY = [float("inf"), float("-inf"), float("inf"), float("-inf")]

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("Feature"):
                if current_feature:
                    # remove duplicate last point if same as first
                    if len(current_feature) > 1 and current_feature[0] == current_feature[-1]:
                        current_feature.pop()
                    features.append(current_feature)
                    current_feature = []
            elif line and not line.startswith("Ring"):
                parts = line.split(",")
                if len(parts) >= 2:
                    try:
                        x = float(parts[0].strip())
                        y = float(parts[1].strip())
                        current_feature.append((x, y))

                        # update min and max
                        if x < minMaxXY[0]:
                            minMaxXY[0] = x
                        if x > minMaxXY[1]:
                            minMaxXY[1] = x
                        if y < minMaxXY[2]:
                            minMaxXY[2] = y
                        if y > minMaxXY[3]:
                            minMaxXY[3] = y

                    except ValueError:
                        continue

        # append the last feature if any
        if current_feature:
            if len(current_feature) > 1 and current_feature[0] == current_feature[-1]:
                current_feature.pop()
            features.append(current_feature)

    print("minMaxXY:", minMaxXY)
    return features, minMaxXY

# function to create the grid
# input: minMaxXY, cell_size, padding
# output: grid filled with 1, (min_x, max_x, min_y, max_y), (rows, cols)
def create_grid(minMaxXY, cell_size=0.05, padding=20):
    min_x, max_x, min_y, max_y = minMaxXY

    # add padding
    min_x -= padding
    max_x += padding
    min_y -= padding
    max_y += padding

    # compute cols and rows
    cols = math.ceil((max_x - min_x) / cell_size)
    rows = math.ceil((max_y - min_y) / cell_size)

    # initialize grid (1 = free, 0 = blocked)
    grid = np.ones((rows, cols), dtype=np.uint8)

    return grid, (min_x, max_x, min_y, max_y), (rows, cols)

def fill_grid_with_map_data(grid, map_data, minMaxXY, cell_size=0.05):
    rows, cols = grid.shape  # Use grid.shape instead of len()

    def draw_line_on_grid(p1, p2):
        """Mark grid cells along line from p1 -> p2 using improved Bresenham algorithm"""
        # Convert UTM coordinates to grid coordinates
        r1, c1 = from_utm_to_grid(p1[0], p1[1], minMaxXY, cell_size)
        r2, c2 = from_utm_to_grid(p2[0], p2[1], minMaxXY, cell_size)
        
        print(f"Drawing line from UTM {p1} to {p2}")
        print(f"Grid coordinates: ({r1},{c1}) to ({r2},{c2})")
        
        # Bounds checking
        if not (0 <= r1 < rows and 0 <= c1 < cols):
            print(f"Warning: Point 1 ({r1},{c1}) is outside grid bounds")
            r1 = max(0, min(r1, rows-1))
            c1 = max(0, min(c1, cols-1))
        if not (0 <= r2 < rows and 0 <= c2 < cols):
            print(f"Warning: Point 2 ({r2},{c2}) is outside grid bounds")
            r2 = max(0, min(r2, rows-1))
            c2 = max(0, min(c2, cols-1))

        # Bresenham's line algorithm with proper bounds checking
        dr = abs(r2 - r1)
        dc = abs(c2 - c1)
        sr = 1 if r1 < r2 else -1
        sc = 1 if c1 < c2 else -1
        err = dr - dc

        current_r, current_c = r1, c1
        
        cells_marked = 0
        while True:
            # Bounds check before marking
            if 0 <= current_r < rows and 0 <= current_c < cols:
                grid[current_r][current_c] = 0  # mark wall
                cells_marked += 1
            else:
                print(f"Skipping out-of-bounds cell: ({current_r},{current_c})")
            
            if current_r == r2 and current_c == c2:
                break
                
            e2 = 2 * err
            if e2 > -dc:
                err -= dc
                current_r += sr
            if e2 < dr:
                err += dr
                current_c += sc
        
        print(f"Marked {cells_marked} cells as walls")

    def draw_thick_line(p1, p2, thickness=1):
        """Draw a line with specified thickness to ensure walls are properly marked"""
        draw_line_on_grid(p1, p2)
        
        # Add thickness by drawing parallel lines
        if thickness > 1:
            # Calculate perpendicular direction
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                # Perpendicular unit vector
                perp_x = -dy / length * cell_size * (thickness - 1) / 2
                perp_y = dx / length * cell_size * (thickness - 1) / 2
                
                # Draw parallel lines
                for i in range(1, thickness):
                    offset = i * cell_size / thickness
                    p1_offset = (p1[0] + perp_x * i, p1[1] + perp_y * i)
                    p2_offset = (p2[0] + perp_x * i, p2[1] + perp_y * i)
                    draw_line_on_grid(p1_offset, p2_offset)
                    
                    p1_offset = (p1[0] - perp_x * i, p1[1] - perp_y * i)
                    p2_offset = (p2[0] - perp_x * i, p2[1] - perp_y * i)
                    draw_line_on_grid(p1_offset, p2_offset)

    # Loop over all features
    total_features = len(map_data)
    print(f"Processing {total_features} features...")
    
    for feature_idx, feature in enumerate(map_data):
        print(f"Processing feature {feature_idx + 1}/{total_features} with {len(feature)} points")
        
        if len(feature) < 2:
            print(f"Skipping feature with insufficient points: {len(feature)}")
            continue
            
        for i in range(len(feature)):
            p1 = feature[i]
            p2 = feature[(i + 1) % len(feature)]  # close the polygon
            
            # Use thick line to ensure walls are properly marked
            draw_thick_line(p1, p2, thickness=2)

    # Count wall cells for verification
    wall_cells = np.sum(grid == 0)
    free_cells = np.sum(grid == 1)
    total_cells = rows * cols
    
    print(f"Grid processing complete:")
    print(f"Wall cells: {wall_cells}")
    print(f"Free cells: {free_cells}")
    print(f"Total cells: {total_cells}")
    print(f"Wall percentage: {wall_cells/total_cells*100:.2f}%")

    return grid

# Main execution
if __name__ == "__main__":
    print("Reading map file...")
    map_data, minMaxXY = read_map_file("/mnt/c/Users/Admin/Downloads/walls_floor1.txt")
    
    print("Creating grid...")
    grid, (min_x, max_x, min_y, max_y), (rows, cols) = create_grid(minMaxXY)
    print(f"Grid created: {rows} x {cols} = {rows*cols} total cells")
    
    print("Filling grid with map data...")
    filled_grid = fill_grid_with_map_data(grid, map_data, (min_x, max_x, min_y, max_y))

    # Save the results
    print("Saving grid data...")
    np.save("filled_grid_lv1_1.npy", filled_grid)
    minMaxXY_final = [min_x, max_x, min_y, max_y]
    np.save("minMaxXY_lv1_1.npy", minMaxXY_final)

    # Visualization with better settings
    print("Displaying grid...")
    plt.figure(figsize=(12, 8))
    plt.imshow(filled_grid, cmap='gray_r', origin='lower')  # origin='lower' for correct orientation, gray_r for better contrast
    plt.colorbar(label='0=Wall, 1=Free')
    plt.title(f'Processed Map Grid ({rows} x {cols})')
    plt.xlabel('Grid Column')
    plt.ylabel('Grid Row')
    # plt.show()
    plt.savefig("filled_grid_lv1_1.png")
    
    print("Processing complete!")