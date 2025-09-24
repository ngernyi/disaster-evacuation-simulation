# Fixed A* Algorithm
import numpy as np
import matplotlib.pyplot as plt
from utils.mapConverter import *
import heapq
import math

def heuristic(a, b):
    # Chebyshev distance
    distance = max(abs(a[0] - b[0]), abs(a[1] - b[1]))
    
    # euclidean distance
    # distance = ((a[0] - b[0])**2 + (a[1] - b[1])**2)
    return distance

# def wall_penalty(node, filled_map):
#     """Penalize nodes that are in walls"""
#     # get the number of free neighbours
#     neighbours = get_neighbors(node, filled_map)
    
#     # substract the number of free neighbours
#     wall_penalty = 8 - len(neighbours)
    
#     return wall_penalty

def wall_penalty(node, filled_map):
    """
    Penalize nodes closer to walls. 
    Lower distance to wall => higher penalty.
    """
    x, y = node
    max_check = 5  # how far to look for walls (tune this)
    min_dist = float('inf')

    for dx in range(-max_check, max_check + 1):
        for dy in range(-max_check, max_check + 1):
            nx, ny = x + dx, y + dy
            if (0 <= nx < len(filled_map)) and (0 <= ny < len(filled_map[0])):
                if filled_map[nx][ny] == 1:  # wall cell
                    dist = max(abs(dx), abs(dy))  # Chebyshev distance
                    min_dist = min(min_dist, dist)

    # If very close to a wall, apply higher penalty
    if min_dist == float('inf'):
        return 0  # no walls found nearby
    return 1.0 / (min_dist + 1)  # closer walls = higher penalty


def get_neighbors(node, filled_map, step=1):
    """Get valid neighboring cells"""
    directions = [(1,0), (-1,0), (0,1), (0,-1) , (1,1) , (-1,1) , (1,-1) , (-1,-1)]  # 8-directional
    neighbors = []
    rows, cols = filled_map.shape  # Get actual grid dimensions
    
    for dx, dy in directions:
        new_row, new_col = node[0] + dx, node[1] + dy
        
        # Check bounds correctly
        if 0 <= new_row < rows and 0 <= new_col < cols:
            if filled_map[new_row, new_col] == 1:  # free space
                neighbors.append((new_row, new_col))
    return neighbors

def reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    # print("path in grid:", path)
    return path

def A_star(start, goal, step=0.05):
    filled_map, minMaxXY = read_filled_grid_and_minMaxXY(
        "C:\\Users\\Admin\\Documents\\University of Malaya\\Y3S2\\FYP\\Code\\backend\\utils\\filled_grid.npy", 
        "C:\\Users\\Admin\\Documents\\University of Malaya\\Y3S2\\FYP\\Code\\backend\\utils\\minMaxXY.npy"
    )
    
    # Convert start and goal from WGS to UTM
    start_utm = from_wgs_to_utm(start[0], start[1])
    goal_utm = from_wgs_to_utm(goal[0], goal[1])
    
    print("start UTM:", start_utm)
    print("goal UTM:", goal_utm)
    print("minMaxXY:", minMaxXY)
    print("Grid shape:", filled_map.shape)

    # Convert UTM to grid coordinates
    start_grid = from_utm_to_grid(start_utm[0], start_utm[1], minMaxXY, cell_size=step)
    goal_grid = from_utm_to_grid(goal_utm[0], goal_utm[1], minMaxXY, cell_size=step)

    print("converted start (grid):", start_grid)
    print("converted goal (grid):", goal_grid)
    
    # Verify that start and goal are within bounds and in free space
    rows, cols = filled_map.shape
    if not (0 <= start_grid[0] < rows and 0 <= start_grid[1] < cols):
        print(f"ERROR: Start position {start_grid} is outside grid bounds {filled_map.shape}")
        return None
    if not (0 <= goal_grid[0] < rows and 0 <= goal_grid[1] < cols):
        print(f"ERROR: Goal position {goal_grid} is outside grid bounds {filled_map.shape}")
        return None
        
    if filled_map[start_grid[0], start_grid[1]] == 0:
        print(f"ERROR: Start position {start_grid} is in a wall!")
        return None
    if filled_map[goal_grid[0], goal_grid[1]] == 0:
        print(f"ERROR: Goal position {goal_grid} is in a wall!")
        return None

    # Priority queue: (f_score, g_score, node)
    open_set = []
    heapq.heappush(open_set, (0 + heuristic(start_grid, goal_grid), 0, start_grid))
    
    came_from = {}
    g_score = {start_grid: 0}
    closed_set = set()
    
    while open_set:
        # get the node with lowest cost
        _, current_g, current = heapq.heappop(open_set)
        
        # if the 
        if current in closed_set:
            continue
            
        closed_set.add(current)
        
        if current == goal_grid:
            # Reconstruct path in grid coords
            path = reconstruct_path(came_from, current)

            # Convert back to UTM coords
            path_utm = [from_grid_to_utm(p[0], p[1], minMaxXY, step) for p in path]

            # Convert to WGS84
            path_wgs_only = [from_utm_to_wgs(p[0], p[1]) for p in path_utm]

            # Assign step order
            path_with_steps = [(coord[0], coord[1], i+1) for i, coord in enumerate(path_wgs_only)]

            return path_with_steps
        
        for neighbor in get_neighbors(current, filled_map):
            if neighbor in closed_set:
                continue
                
            tentative_g = current_g + 1  # each step = cost 1
            
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g 
                # f_score = tentative_g + heuristic(neighbor, goal_grid)+ (wall_penalty(neighbor, filled_map) * 0.5)
                f_score = tentative_g + heuristic(neighbor, goal_grid)
                heapq.heappush(open_set, (f_score, tentative_g, neighbor))
    
    print("No path found!")
    return None  # no path found