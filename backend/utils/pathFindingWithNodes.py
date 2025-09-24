from collections import deque
import numpy as np
from utils.mapConverter import *
import heapq
import math
import matplotlib.pyplot as plt

#  function to read the skeletoned data
def read_skeletoned_data():
    skeleton = np.load("C:\\Users\\Admin\\Documents\\University of Malaya\\Y3S2\\FYP\\Code\\backend\\utils\\skeleton.npy") # the map
    junctions = np.load("C:\\Users\\Admin\\Documents\\University of Malaya\\Y3S2\\FYP\\Code\\backend\\utils\\junctions.npy")
    dead_ends = np.load("C:\\Users\\Admin\\Documents\\University of Malaya\\Y3S2\\FYP\\Code\\backend\\utils\\dead_ends.npy")
    neighbor_count = np.load("C:\\Users\\Admin\\Documents\\University of Malaya\\Y3S2\\FYP\\Code\\backend\\utils\\neighbor_count.npy")

    return skeleton, junctions, dead_ends, neighbor_count

# function to find the nearest skeleton point using bfs
# params: skeleton, start_grid (in grid point)
# return: path to the nearest skeleton point (in grid point), nearest skeleton point (in grid point)
def find_nearest_skeleton_point_bfs(skeleton, start_grid):
    rows, cols = skeleton.shape
    visited = np.zeros((rows, cols), dtype=bool)
    parent = {}  # to reconstruct path
    
    queue = deque([start_grid])
    visited[start_grid] = True
    
    while queue:
        current_point = queue.popleft()
        
        # If current point is part of skeleton
        if skeleton[current_point]:
            # Reconstruct path
            path = []
            while current_point != start_grid:
                path.append(current_point)
                current_point = parent[current_point]
            path.append(start_grid)
            path.reverse()
            return path, path[-1]  # (full path, nearest skeleton point)
        
        # Check neighbors
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
            nr, nc = current_point[0] + dr, current_point[1] + dc
            if 0 <= nr < rows and 0 <= nc < cols and not visited[nr, nc]:
                visited[nr, nc] = True
                parent[(nr, nc)] = current_point
                queue.append((nr, nc))
    
    return None, None

# function to find path between two skeleton points (using dijkstra)
# params: skeleton, start_grid (in grid point), goal_grid (in grid point)
# return: path from start to goal (in grid point)
def find_path_between_skeleton_points(skeleton, start_grid, goal_grid):
    rows, cols = skeleton.shape
    visited = np.zeros((rows, cols), dtype=bool)
    dist = {start_grid: 0}
    parent = {}
    pq = [(0, start_grid)]  # (distance, node)

    while pq:
        current_dist, current = heapq.heappop(pq)
        if visited[current]:
            continue
        visited[current] = True
        
        if current == goal_grid:
            # reconstruct path
            path = []
            while current in parent:
                path.append(current)
                current = parent[current]
            path.append(start_grid)
            return path[::-1]
        
        r, c = current
        for dr, dc in [(1,0), (-1,0), (0,1), (0,-1), 
                       (1,1), (-1,-1), (1,-1), (-1,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and skeleton[nr, nc] == 1:
                cost = math.sqrt(dr**2 + dc**2)
                new_dist = current_dist + cost
                if (nr, nc) not in dist or new_dist < dist[(nr, nc)]:
                    dist[(nr, nc)] = new_dist
                    parent[(nr, nc)] = current
                    heapq.heappush(pq, (new_dist, (nr, nc)))
    
    return None

# function to compute the path in skeleton map
def compute_path_in_skeleton_map(start, goal, step=0.05):
    filled_map, minMaxXY = read_filled_grid_and_minMaxXY(
        "C:\\Users\\Admin\\Documents\\University of Malaya\\Y3S2\\FYP\\Code\\backend\\utils\\filled_grid.npy", 
        "C:\\Users\\Admin\\Documents\\University of Malaya\\Y3S2\\FYP\\Code\\backend\\utils\\minMaxXY.npy"
    )
    skeleton, junctions, dead_ends, neighbor_count = read_skeletoned_data()

    # plot the skeleton
    # plt.imshow(skeleton, cmap='gray')
    # plt.show()
    # Convert to UTM
    start_utm = from_wgs_to_utm(start[0], start[1])
    goal_utm = from_wgs_to_utm(goal[0], goal[1])

    # Convert UTM to grid
    start_grid = from_utm_to_grid(start_utm[0], start_utm[1], minMaxXY, cell_size=step)
    goal_grid = from_utm_to_grid(goal_utm[0], goal_utm[1], minMaxXY, cell_size=step)
    print("start grid:", start_grid)
    print("goal grid:", goal_grid)

    # BFS to skeleton
    initial_path, initial_nearest_skeleton_point = find_nearest_skeleton_point_bfs(skeleton, start_grid)
    goal_path, goal_nearest_skeleton_point = find_nearest_skeleton_point_bfs(skeleton, goal_grid)

    if initial_path is None or goal_path is None:
        print("No path found from start or goal to skeleton")
        return None

    # Dijkstra on skeleton
    skeleton_path = find_path_between_skeleton_points(skeleton, initial_nearest_skeleton_point, goal_nearest_skeleton_point)
    if skeleton_path is None:
        print("No path found within skeleton")
        return None

    # Merge paths without duplicates
    path = initial_path[:-1] + skeleton_path[:-1] + goal_path

    # Convert back to WGS
    path_utm = [from_grid_to_utm(p[0], p[1], minMaxXY, step) for p in path]
    path_wgs_only = [from_utm_to_wgs(p[0], p[1]) for p in path_utm]
    path_with_steps = [(coord[0], coord[1], i+1) for i, coord in enumerate(path_wgs_only)]
    return path_with_steps

# start_in_wgs = [-117.196062324132, 34.0559540688677]
# goal_in_wgs = [-117.195679043251, 34.05594565305]
# result = compute_path_in_skeleton_map(start_in_wgs, goal_in_wgs)
# print(result)


