import matplotlib.pyplot as plt
import triangle.plot as trplot
import numpy as np
import heapq
from skimage import measure
from shapely.geometry import LineString, Point, Polygon
from scipy.spatial import Delaunay
from utils.mapConverter import *
import pickle
import os
from utils.nav_loader import NAV_DATA
import time
from collections import deque

def find_triangle_containing_point(point, points, tri, filled_map, centroids):
    """
    Find the nearest walkable triangle to the given point using BFS.
    If the point is directly inside a triangle and walkable, return that triangle.
    Otherwise, use BFS to find the nearest walkable triangle.
    
    Args:
        point: (x, y) coordinates
        points: triangulation vertices
        tri: Delaunay triangulation object
        filled_map: 2D array where 1=walkable, 0=wall
        centroids: precomputed triangle centroids
    """
    x, y = point
    # print(f"Searching for triangle containing point: ({x}, {y})")
    # print(f"Map shape: {filled_map.shape}")
    
    # Check if point is within map bounds
    grid_x, grid_y = int(round(x)), int(round(y))
    if not (0 <= grid_y < filled_map.shape[0] and 0 <= grid_x < filled_map.shape[1]):
        # print(f"Point ({grid_x}, {grid_y}) is outside map bounds!")
        return None
    
    # print(f"Point walkability at ({grid_x}, {grid_y}): {filled_map[grid_y, grid_x]}")
    
    # First, check if point is directly inside any triangle and walkable
    direct_triangles_found = []
    for i, simplex in enumerate(tri.simplices):
        poly = Polygon(points[simplex])
        if poly.contains(Point(point)):
            direct_triangles_found.append(i)
            # Check if the triangle centroid is in walkable area
            cx, cy = centroids[i]
            centroid_gx, centroid_gy = int(round(cx)), int(round(cy))
            if (0 <= centroid_gy < filled_map.shape[0] and 
                0 <= centroid_gx < filled_map.shape[1] and 
                filled_map[centroid_gy, centroid_gx] == 1):
                # print(f"Found direct walkable triangle: {i}")
                return i
    
    # print(f"Direct triangles found: {len(direct_triangles_found)}")
    if direct_triangles_found:
        print("But none were walkable, starting BFS...")
    else:
        print("No direct triangles found, starting BFS...")
    
    # If not found or not walkable, use BFS to find nearest walkable triangle
    # BFS setup
    queue = deque([(grid_x, grid_y, 0)])  # (x, y, distance)
    visited = set()
    visited.add((grid_x, grid_y))
    
    # Directions for 8-connected neighbors
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    max_search_radius = min(filled_map.shape) // 4  # Increased search area
    # print(f"Max search radius: {max_search_radius}")
    
    positions_checked = 0
    walkable_positions_found = 0
    
    while queue:
        curr_x, curr_y, dist = queue.popleft()
        positions_checked += 1
        
        # Stop if we've searched too far
        if dist > max_search_radius:
            continue
            
        # Check if current position is walkable
        if (0 <= curr_y < filled_map.shape[0] and 
            0 <= curr_x < filled_map.shape[1] and 
            filled_map[curr_y, curr_x] == 1):
            
            walkable_positions_found += 1
            
            # Find which triangle contains this walkable point
            search_point = (curr_x, curr_y)
            for i, simplex in enumerate(tri.simplices):
                poly = Polygon(points[simplex])
                if poly.contains(Point(search_point)):
                    # Double-check that triangle centroid is also walkable
                    cx, cy = centroids[i]
                    centroid_gx, centroid_gy = int(round(cx)), int(round(cy))
                    if (0 <= centroid_gy < filled_map.shape[0] and 
                        0 <= centroid_gx < filled_map.shape[1] and 
                        filled_map[centroid_gy, centroid_gx] == 1):
                        # print(f"BFS found walkable triangle {i} at distance {dist}")
                        # print(f"Positions checked: {positions_checked}, Walkable found: {walkable_positions_found}")
                        return i
        
        # Add neighbors to queue
        for dx, dy in directions:
            new_x, new_y = curr_x + dx, curr_y + dy
            if ((new_x, new_y) not in visited and 
                0 <= new_y < filled_map.shape[0] and 
                0 <= new_x < filled_map.shape[1]):
                visited.add((new_x, new_y))
                queue.append((new_x, new_y, dist + 1))
    
    # print(f"BFS completed. Positions checked: {positions_checked}, Walkable found: {walkable_positions_found}")
    # print("No walkable triangle found within search radius!")
    nearest_idx = min(
        range(len(centroids)),
        key=lambda i: (centroids[i][0] - x) ** 2 + (centroids[i][1] - y) ** 2
    )
    return nearest_idx


def heuristic(a, b):
    """Euclidean distance heuristic."""
    return np.linalg.norm(np.array(a) - np.array(b))

def a_star_with_retry(start_pt, goal_pts, points, tri, graph, centroids, filled_map, max_retries=200):
    """
    Try A* repeatedly by nudging the start point to neighboring centroids
    if no path is found.
    """
    tried = set()
    attempt = 0
    current_start = start_pt

    while attempt < max_retries:
        attempt += 1
        tri_path, path_coords = a_star_search(current_start, goal_pts, points, tri, graph, centroids, filled_map)
        if tri_path:  # ✅ Success
            return tri_path, path_coords

        # Mark current start as tried
        tried.add(tuple(current_start))

        # Find a nearby centroid to try next
        start_tri = int(tri.find_simplex(current_start))
        if start_tri < 0 or start_tri not in graph:
            # print(f"[Attempt {attempt}] Invalid start. Expanding search radius...")
            current_start = find_nearest_walkable(current_start, points, tri, tried)
            continue

        # Choose a neighbor triangle centroid as a new start
        neighbors = graph.get(start_tri, [])
        if not neighbors:
            # print(f"[Attempt {attempt}] No neighbors for {start_tri}. Expanding search radius...")
            current_start = find_nearest_walkable(current_start, points, tri, tried)
            continue

        # Pick the closest neighbor centroid not tried yet
        neighbor_pts = [
            centroids[n] for n in neighbors 
            if tuple(centroids[n]) not in tried
        ]

        if not neighbor_pts:
            # print(f"[Attempt {attempt}] All neighbors tried. Expanding search radius...")
            current_start = find_nearest_walkable(current_start, points, tri, tried)
            continue

        # Pick the closest neighbor to the goal
        goal_avg = tuple(sum(x)/len(x) for x in zip(*goal_pts))
        current_start = min(neighbor_pts, key=lambda p: heuristic(p, goal_avg))
        # print(f"[Attempt {attempt}] Retrying from {current_start}")

    raise RuntimeError("Failed to find a path after retries.")


def find_nearest_walkable(start_pt, points, tri, tried, radius_step=0.5, max_radius=5.0):
    """
    Fallback search for a valid walkable point around the start point.
    """
    r = radius_step
    while r <= max_radius:
        for dx in (-r, 0, r):
            for dy in (-r, 0, r):
                candidate = (start_pt[0] + dx, start_pt[1] + dy)
                if candidate not in tried and tri.find_simplex(candidate) >= 0:
                    return candidate
        r += radius_step
    raise RuntimeError("Could not find a valid nearby start point.")


def a_star_search(start_pt, goal_pts, points, tri, graph, centroids, filled_map):
    # Convert goals to triangles
    goal_tris = [int(tri.find_simplex(g)) for g in goal_pts if tri.find_simplex(g) >= 0]
    if not goal_tris:
        raise ValueError("No valid goal inside triangulation")

    start_tri = int(tri.find_simplex(start_pt))
    if start_tri < 0:
        raise ValueError("Start not inside triangulation")

    centroids_dict = {i: centroids[i] for i in range(len(centroids))}
    open_set = [(0, start_tri)]
    came_from = {}
    g_score = {start_tri: 0}
    f_score = {start_tri: min(heuristic(centroids_dict[start_tri], centroids_dict[g]) for g in goal_tris)}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current in goal_tris:  # ✅ Stop if reached any goal
            tri_path = [current]
            while current in came_from:
                current = came_from[current]
                tri_path.append(current)
            tri_path.reverse()
            path_coords = [centroids_dict[t] for t in tri_path]
            return tri_path, path_coords

        for neighbor in graph.get(current, []):
            tentative_g = g_score[current] + heuristic(
                centroids_dict[current], centroids_dict[neighbor]
            )
            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + min(
                    heuristic(centroids_dict[neighbor], centroids_dict[g]) for g in goal_tris
                )
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    print("No path found")
    return None, None


def funnel_path_github_adapted(points, triangles, path_triangles, start, goal):
    """
    Adapted version of the GitHub funnel algorithm implementation.
    
    Args:
        points: array of vertices from triangulation
        triangles: triangle vertex indices (tri.simplices)  
        path_triangles: list of triangle indices from A*
        start, goal: coordinates (x, y)
    
    Returns:
        path: list of points [(x0,y0), (x1,y1), ...]
    """
    
    if len(path_triangles) <= 1:
        return [start, goal]
    
    def ccw(A, B, C):
        """
        Counter-clockwise test. Returns True if points A, B, C are in counter-clockwise order.
        This is equivalent to testing if C is to the left of line AB.
        """
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
    
    def points_equal(p1, p2, tolerance=1e-9):
        """Check if two points are approximately equal"""
        return abs(p1[0] - p2[0]) < tolerance and abs(p1[1] - p2[1]) < tolerance
    
    # Step 1: Extract edge_path (portals) from triangles
    edge_path = []
    point_dict = {}  # Will map edge indices to actual coordinates
    edge_counter = 0
    
    # print(f"Extracting edges from {len(path_triangles)} triangles...")
    
    for i in range(len(path_triangles) - 1):
        t1_idx, t2_idx = path_triangles[i], path_triangles[i+1]
        verts1 = set(triangles[t1_idx])
        verts2 = set(triangles[t2_idx])
        shared_verts = list(verts1.intersection(verts2))
        
        if len(shared_verts) != 2:
            print(f"Warning: Triangles {t1_idx} and {t2_idx} don't share exactly 2 vertices")
            continue
            
        # Get the shared edge points
        p1, p2 = points[shared_verts[0]], points[shared_verts[1]]
        
        # Add to point dictionary
        edge_idx1 = edge_counter
        edge_idx2 = edge_counter + 1
        point_dict[edge_idx1] = tuple(p1)
        point_dict[edge_idx2] = tuple(p2)
        
        # Add edge to path
        edge_path.append((edge_idx1, edge_idx2))
        edge_counter += 2
        
        # print(f"Edge {i}: ({tuple(p1)}, {tuple(p2)})")
    
    if not edge_path:
        print("No valid edges found!")
        return [start, goal]
    
    # print(f"Created {len(edge_path)} edges")
    
    # Step 2: Apply the GitHub funnel algorithm
    p = tuple(start)  # Start point
    q = tuple(goal)   # Goal point
    
    tail = [p]
    left = []
    right = []
    last_edge_l = None
    last_edge_r = None
    
    # print(f"\\nStarting funnel algorithm with start={p}, goal={q}")
    # print(f"Processing {len(edge_path)} edges...")
    
    for i, e in enumerate(edge_path):
        # print(f"\\n--- Processing edge {i}: {e} ---")
        
        p1, p2 = point_dict[e[0]], point_dict[e[1]]
        # print(f"Edge points: p1={p1}, p2={p2}")
        # print(f"Last edges: last_edge_l={last_edge_l}, last_edge_r={last_edge_r}")
        
        # Determine orientation: swap if needed for consistency
        original_order = (p1, p2)
        if (p2 == last_edge_l or p1 == last_edge_r or 
            (last_edge_r is None and last_edge_l is None and ccw(tail[-1], p2, p1))):
            p1, p2 = p2, p1
            # print(f"Swapped edge orientation: p1={p1}, p2={p2}")
        # else:
            # print(f"Kept original orientation: p1={p1}, p2={p2}")
        
        # print(f"Current state: tail={tail[-1]}, left={left}, right={right}")
        
        # Process left side (p1)
        if len(left) == 0 and not points_equal(p1, tail[-1]):
            left = [p1]
            # print(f"Initialized left: {left}")
        elif len(left) > 0 and not points_equal(left[-1], p1):
            # print(f"Testing left side: ccw({tail[-1]}, {p1}, {left[-1]}) = {ccw(tail[-1], p1, left[-1])}")
            
            if not ccw(tail[-1], p1, left[-1]):  # p1 narrows the funnel
                # print("Left side narrows funnel, checking for collisions...")
                last_collision = -1
                
                for j, p in enumerate(right):
                    if ccw(tail[-1], p, p1):
                        # print(f"Collision detected with right[{j}]={p}")
                        tail.append(right[j])
                        last_collision = j
                        # print(f"Added to tail: {tail[-1]}")
                
                if last_collision >= 0:
                    # print(f"Collision occurred, resetting funnel")
                    left = [p1]
                    right = right[last_collision + 1:]
                    # print(f"New left: {left}, new right: {right}")
                else:
                    # print("No collisions, narrowing left funnel")
                    left[-1] = p1
                    # print(f"Updated left: {left}")
            else:
                # print("Left side opens funnel, appending")
                left.append(p1)
                # print(f"Left after append: {left}")
        
        # Process right side (p2)
        if len(right) == 0 and not points_equal(p2, tail[-1]):
            right = [p2]
            # print(f"Initialized right: {right}")
        elif len(right) > 0 and not points_equal(right[-1], p2):
            # print(f"Testing right side: ccw({tail[-1]}, {right[-1]}, {p2}) = {ccw(tail[-1], right[-1], p2)}")
            
            if not ccw(tail[-1], right[-1], p2):  # p2 narrows the funnel
                # print("Right side narrows funnel, checking for collisions...")
                last_collision = -1
                
                for j, p in enumerate(left):
                    if ccw(tail[-1], p2, p):
                        # print(f"Collision detected with left[{j}]={p}")
                        tail.append(left[j])
                        last_collision = j
                        # print(f"Added to tail: {tail[-1]}")
                
                if last_collision >= 0:
                    # print(f"Collision occurred, resetting funnel")
                    right = [p2]
                    left = left[last_collision + 1:]
                    # print(f"New right: {right}, new left: {left}")
                else:
                    # print("No collisions, narrowing right funnel")
                    right[-1] = p2
                    # print(f"Updated right: {right}")
            else:
                # print("Right side opens funnel, appending")
                right.append(p2)
                # print(f"Right after append: {right}")
        
        last_edge_l = p1
        last_edge_r = p2
        
        # print(f"End of edge {i}: tail={tail}, left={left}, right={right}")
    
    # Final cleanup: handle remaining collisions with goal
    apex = tail[-1]
    # print(f"\\nFinal cleanup with apex={apex}, goal={q}")
    
    # Check right side collisions with goal
    for i, p in enumerate(right):
        if ccw(apex, p, q):
            # print(f"Final right collision: adding right[{i}]={p}")
            tail.append(right[i])
    
    # Check left side collisions with goal  
    for i, p in enumerate(left):
        if ccw(apex, q, p):
            # print(f"Final left collision: adding left[{i}]={p}")
            tail.append(left[i])
    
    # Add goal
    tail.append(q)
    
    # print(f"\\nFinal path: {tail}")
    return tail


def plot_funnel_debug(points, tri, path_triangles, funnel_path_coords, start, goal, filled_map):
    """Plot triangulation, triangle path, and funnel path with triangle labels."""
    plt.figure(figsize=(12, 8))

    # Background map
    if filled_map is not None:
        plt.imshow(filled_map, cmap="gray_r", origin="lower", alpha=0.7)

    # Plot all triangulation
    plt.triplot(points[:,0], points[:,1], tri.simplices, color="lightblue", linewidth=0.3, alpha=0.5)

    # Highlight path triangles and add labels
    if path_triangles:
        for tri_idx in path_triangles:
            tri_points = points[tri.simplices[tri_idx]]
            # Highlight the triangle
            triangle = plt.Polygon(tri_points, alpha=0.3, facecolor='yellow', edgecolor='orange', linewidth=2)
            plt.gca().add_patch(triangle)
            
            # *** NEW: Add triangle index label ***
            # Calculate the center of the triangle to place the text
            center = tri_points.mean(axis=0)
            plt.text(center[0], center[1], str(tri_idx), 
                     color='black', ha='center', va='center', fontsize=9, fontweight='bold')

    # Plot portals (no changes here)
    if len(path_triangles) > 1:
        for i in range(len(path_triangles) - 1):
            t1_idx, t2_idx = path_triangles[i], path_triangles[i+1]
            verts1 = set(tri.simplices[t1_idx])
            verts2 = set(tri.simplices[t2_idx])
            shared = list(verts1.intersection(verts2))
            if len(shared) == 2:
                p1, p2 = points[shared[0]], points[shared[1]]
                plt.plot([p1[0], p2[0]], [p1[1], p2[1]], 'r-', linewidth=3, alpha=0.8, label='Portals' if i == 0 else "")

    # Plot Start, Goal, and Funnel Path (no changes here)
    plt.plot(start[0], start[1], "go", markersize=12, label="Start", zorder=5)
    plt.plot(goal[0], goal[1], "ro", markersize=12, label="Goal", zorder=5)
    if funnel_path_coords and len(funnel_path_coords) > 1:
        xs, ys = zip(*funnel_path_coords)
        plt.plot(xs, ys, "b-", linewidth=3, label="Funnel Path", zorder=4)
        plt.scatter(xs, ys, color="blue", s=30, zorder=5)

    plt.legend()
    plt.title("Funnel Algorithm Debug View")
    plt.gca().set_aspect("equal")
    plt.show()
    
def bresenham_line(x0, y0, x1, y1):
    """Return list of grid cells from (x0,y0) to (x1,y1) using Bresenham."""
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        points.append((x, y))
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy

    return points

    
def expand_funnel_path(funnel_points):
    """Expand funnel waypoints into full grid path using Bresenham."""
    full_path = []
    for i in range(len(funnel_points) - 1):
        (x0, y0) = funnel_points[i]
        (x1, y1) = funnel_points[i+1]
        line = bresenham_line(int(round(x0)), int(round(y0)),
                              int(round(x1)), int(round(y1)))
        # avoid duplicate when joining
        if full_path:
            full_path.extend(line[1:])
        else:
            full_path.extend(line)
    return full_path

    


"""
    START NEW CODE - add 2 stairs (CHANGE ARGUMENTS)
"""
def navMeshPathWithFunnel(start, graphList, floor, path_from_stair1_to_exit=None,  path_from_stair2_to_exit=None, path_from_stair3_to_exit=None, path_from_stair4_to_exit=None,step=0.05,):
    """
        END NEW CODE - add 2 stairs, add 2 more assembly points
    """
    start_time = time.time()
    # goal_main = -117.195679043251, 34.05594565305
    goal1 = -117.19623505024354, 34.05621487659595
    goal2 = -117.1956520625412, 34.05639161712975
    goal3 = -117.19512781129663, 34.056053736202315
    stair1 = -117.19603379555, 34.05624942388
    stair2 = -117.195333804329, 34.055954726546
    """
        START NEW CODE - add 2 stairs (ADD 2 STAIRS and modified goal)
    """
    stair3 = -117.19557424707945, 34.056118766847334
    stair4 = -117.19578962444298, 34.0560899781941
    
    goal_lv1 = [goal1, goal2, goal3]
    goal_lv2 = [stair1, stair2, stair3, stair4]
    goal_lv3 = [stair1, stair2, stair3, stair4]
    
    
    if path_from_stair1_to_exit == None:
        goal_lv2.remove(stair1)
        goal_lv3.remove(stair1)
        
    if path_from_stair2_to_exit == None:
        goal_lv2.remove(stair2)
        goal_lv3.remove(stair2)
        
    if path_from_stair3_to_exit == None:
        goal_lv2.remove(stair3)
        goal_lv3.remove(stair3)
        
    if path_from_stair4_to_exit == None:
        goal_lv2.remove(stair4)
        goal_lv3.remove(stair4)
    """
        END NEW CODE - add 2 stairs
    """
    floor_data = [0,5.66999911144376, 10.2499997382984]
    if floor == 1:
        filled_map = NAV_DATA["filled_map_lv1"]
        minMaxXY= NAV_DATA["minMaxXY_lv1"]
        centroids = NAV_DATA["centroids_lv1"]
        points = NAV_DATA["points_lv1"]
        tri = NAV_DATA["tri_lv1"]
        goal = goal_lv1
        graph = graphList[0]
    
    elif floor == 2:
        filled_map = NAV_DATA["filled_map_lv2"]
        minMaxXY = NAV_DATA["minMaxXY_lv2"]
        centroids = NAV_DATA["centroids_lv2"]
        points = NAV_DATA["points_lv2"]
        tri = NAV_DATA["tri_lv2"]
        goal = goal_lv2
        graph = graphList[1]
        
    else: 
        filled_map = NAV_DATA["filled_map_lv3"]
        minMaxXY = NAV_DATA["minMaxXY_lv3"]
        centroids = NAV_DATA["centroids_lv3"]
        points = NAV_DATA["points_lv3"]
        tri = NAV_DATA["tri_lv3"]
        goal = goal_lv3
        graph = graphList[2]
    
    
    start_x, start_y = from_wgs_to_utm(start[0], start[1])
    # goal_x, goal_y = from_wgs_to_utm(goal[0], goal[1])
    start_grid_x, start_grid_y = from_utm_to_grid(start_x, start_y, minMaxXY)
    # goal_grid_x, goal_grid_y = from_utm_to_grid(goal_x, goal_y, minMaxXY)
    goalList = []
    for g in goal:
        gx, gy = from_wgs_to_utm(g[0], g[1])
        ggrid_x, ggrid_y = from_utm_to_grid(gx, gy, minMaxXY)
        goalList.append((ggrid_y, ggrid_x))
        
    start = (start_grid_y, start_grid_x)
    # goal = (goal_grid_y, goal_grid_x)
    print("start:", start)
    print("goal:", goal)
    
    
    # Find path using precomputed centroids and BFS triangle finding
    path_triangles, path_coords = a_star_search(start, goalList, points, tri, graph, centroids, filled_map)
    # print("Path triangles:", path_triangles)
    # print("Path coords:", path_coords)
    if not path_triangles or not path_coords:
        
        path_triangles, path_coords = a_star_with_retry(
            start, goalList, points, tri, graph, centroids, filled_map
        )

    funnel_coords = funnel_path_github_adapted(points, tri.simplices, path_triangles, start, path_coords[-1])
    # print("Funnel smoothed path:", funnel_coords)
    # full_path = expand_funnel_path(funnel_coords)
    full_path = funnel_coords + [funnel_coords[-1]]
    # full_path = full_path.append(funnel_coords[-1])
    # choose 2,4,6,8, ... of the full path only
    # full_path = full_path[::15]
    # add the z to the full path
    full_path = [(coord[0], coord[1], floor_data[floor-1]) for coord in full_path]
    # print("full path bfr adding lower floors", full_path )
    print("full path length bfr adding lower floors", len(full_path))
    # path_utm = [(from_grid_to_utm(p[1], p[0], minMaxXY, step), p[2]) for p in full_path]
    # path_wgs_only = [(from_utm_to_wgs(p[0][0], p[0][1]), p[1]) for p in path_utm]
    # full_path = [(coord[0][0], coord[0][1], coord[1], i+1) for i, coord in enumerate(path_wgs_only)]
    
    """
        newly added
         
        => add the path in the stair
        => add the path from stairs to the main goal
        => add the agent status 
       
    """
    
    # add the list of floor to the path
    # full_path = [(coord[0], coord[1], coord[2]) for coord in full_path]
    
    # add the agent status (step_num, status)
    agent_status = []
    # add starting point
    agent_status.append((0, floor))
    
    # add the path in the stairs
    # if the agent is not at the floor 1
    # --- START OF FIXED STAIRCASE LOGIC ---
    
    # if the agent is not at the floor 1 (needs to go down)
    if floor != 1:
        
        # 1. Get the starting position (Top of stair)
        start_node = full_path[-1] 
        # Convert start node to UTM using the CURRENT floor's minMax
        current_utm_x, current_utm_y = from_grid_to_utm(start_node[1], start_node[0], NAV_DATA[f"minMaxXY_lv{floor}"], step)
        
        # 2. Pre-calculate Grid Coordinates (Same as your code)
        stair_coords_map = {}
        
        # Floor 1
        f1_row, f1_col = from_utm_to_grid(current_utm_x, current_utm_y, NAV_DATA["minMaxXY_lv1"], step)
        stair_coords_map[1] = (f1_col, f1_row)
        
        # Floor 2
        if "minMaxXY_lv2" in NAV_DATA:
            f2_row, f2_col = from_utm_to_grid(current_utm_x, current_utm_y, NAV_DATA["minMaxXY_lv2"], step)
            stair_coords_map[2] = (f2_col, f2_row)
            
        # Floor 3
        if "minMaxXY_lv3" in NAV_DATA:
            f3_row, f3_col = from_utm_to_grid(current_utm_x, current_utm_y, NAV_DATA["minMaxXY_lv3"], step)
            stair_coords_map[3] = (f3_col, f3_row)

        # 3. Begin Descent Loop
        down_path = start_node
        
        while down_path[2] > 0:
            current_z = down_path[2]
            
            # Update Agent Status (Visuals) - Keep your existing logic
            if current_z > 5:
                if agent_status[-1][1] != 2.5:
                    agent_status.append((len(full_path), 2.5))
            else:
                if agent_status[-1][1] != 1.5:
                    agent_status.append((len(full_path), 1.5))

            # --- CALCULATE NEW Z FIRST ---
            new_z = current_z - 0.10

            # Handle ground floor snap
            if new_z <= 0:
                new_z = 0
                active_floor_id = 1 # Ground is Floor 1
            else:
                # --- FIX 1: DETERMINE FLOOR BASED ON THE FUTURE Z (new_z) ---
                # This ensures the (x,y) matches the map that will be used for this Z
                if new_z > 7:
                    active_floor_id = 3
                elif new_z > 3:
                    active_floor_id = 2
                else:
                    active_floor_id = 1
            
            # Safety clamp
            if active_floor_id > floor: active_floor_id = floor

            # Retrieve coordinates for the CORRECT floor
            target_x, target_y = stair_coords_map.get(active_floor_id, (down_path[0], down_path[1]))
            
            # Create point
            down_path = (target_x, target_y, new_z)
            full_path.append(down_path)

            # Break if we hit ground
            if new_z <= 0:
                # Add status for reaching floor 1
                agent_status.append((len(full_path), 1)) 
                break
            
        print("full path length after adding stairs", len(full_path))
        
        
        """
            STAIR CONNECTION LOGIC (Refined for Problem 2)
        """
        
        # 1. Get the last point (This is now definitely on Floor 1 Grid)
        last_point_grid = full_path[-1] 
        
        # 2. Convert Agent Grid -> UTM
        # --- FIX 2: FORCE USE OF FLOOR 1 MINMAX ---
        # Do NOT use 'minMaxXY' (which might be Floor 3). Use NAV_DATA["minMaxXY_lv1"]
        agent_utm_x, agent_utm_y = from_grid_to_utm(last_point_grid[1], last_point_grid[0], NAV_DATA["minMaxXY_lv1"], step)
        
        # 3. Define Stairs
        stair_options = [
            {'name': 'stair1', 'wgs': stair1, 'path': path_from_stair1_to_exit},
            {'name': 'stair2', 'wgs': stair2, 'path': path_from_stair2_to_exit},
            {'name': 'stair3', 'wgs': stair3, 'path': path_from_stair3_to_exit},
            {'name': 'stair4', 'wgs': stair4, 'path': path_from_stair4_to_exit}
        ]

        best_path = None
        min_dist = float('inf') 
        chosen_stair_name = ""

        print(f"Checking distance to stairs (Agent UTM: {agent_utm_x:.2f}, {agent_utm_y:.2f})")

        for option in stair_options:
            if option['path'] is None: continue 

            # Convert Fixed Stair WGS -> UTM
            s_wgs = option['wgs']
            s_utm_x, s_utm_y = from_wgs_to_utm(s_wgs[0], s_wgs[1])
            
            # Calculate Distance in METERS
            dist_meters = ((s_utm_x - agent_utm_x) ** 2 + (s_utm_y - agent_utm_y) ** 2) ** 0.5
            
            if dist_meters < min_dist:
                min_dist = dist_meters
                best_path = option['path']
                chosen_stair_name = option['name']

        # 4. Attach path
        # Using 5.0 meters tolerance
        if best_path and min_dist < 5.0: 
            full_path.extend(best_path)
            print(f"✅ Snapped to {chosen_stair_name} (Distance: {min_dist:.2f}m)")
        else:
            if best_path:
                full_path.extend(best_path)
                print(f"⚠️ WARNING: Agent was far ({min_dist:.2f}m) but forced to {chosen_stair_name}")
            else:
                print("❌ CRITICAL: No stair path available to attach.")
        # Get the current end point
        # current_end_x = full_path[-1][0]
        # current_end_y = full_path[-1][1]
        
        # # Check Stair 1
        # if path_from_stair1_to_exit and abs(path_from_stair1_to_exit[0][0] - current_end_x) <100 and abs(path_from_stair1_to_exit[0][1] - current_end_y) < 100:
        #     full_path.extend(path_from_stair1_to_exit)
        #     print("stair 1 is used")
        # # Check Stair 2
        # elif path_from_stair2_to_exit and abs(path_from_stair2_to_exit[0][0] - current_end_x) < 100 and abs(path_from_stair2_to_exit[0][1] - current_end_y) < 100:
        #     full_path.extend(path_from_stair2_to_exit)
        #     print("stair 2 is used")
        # # Check Stair 3
        # elif path_from_stair3_to_exit and abs(path_from_stair3_to_exit[0][0] - current_end_x) < 100 and abs(path_from_stair3_to_exit[0][1] - current_end_y) < 100:
        #     full_path.extend(path_from_stair3_to_exit)
        #     print("stair 3 is used")
        # # Check Stair 4
        # elif path_from_stair4_to_exit and abs(path_from_stair4_to_exit[0][0] - current_end_x) < 100 and abs(path_from_stair4_to_exit[0][1] - current_end_y) < 100:
        #     full_path.extend(path_from_stair4_to_exit)
        #     print("stair 4 is used")
        # else:
        #     print("⚠️ No matching stair path found close to the agent")
            
        # print("full path length after adding floor 1 path to main goal", len(full_path))
        ### END MODIFICATION
        """
            END NEW CODE - add 2 stairs
        """
        # if abs(path_from_stair1_to_exit[0][0] - full_path[-1][0]) < 50 and abs(path_from_stair1_to_exit[0][1] - full_path[-1][1]) < 50:
        # # if abs(grid_of_stair1[0] - full_path[-1][0]) < 10 and abs(grid_of_stair1[1] - full_path[-1][1]) < 10:
        #     # add the path
        #     full_path.extend(path_from_stair1_to_exit)
        #     print("stair 1 is used")
        # else:
        #     full_path.extend(path_from_stair2_to_exit)
        #     print("stair 2 is used")
            
        # print("full path length after adding floor 1 path to main goal", len(full_path))
        
        
        
    
    # add the agent status for the last step (-1 means reach the goal)
    agent_status.append((len(full_path) - 1, -1))
    
    
    
    
    print("Full path:", (full_path))
    print("status", agent_status)
    print("Full path length ", len(full_path))
    end_time = time.time()
    print("Time taken: ", end_time - start_time)
    
    # plot_funnel_debug(points, tri, path_triangles, full_path, start, goal, filled_map)
    
    
    

    #  show the lentgh and last path
    # print("path_with_steps", len(full_path))
    # print("path_with_steps", path_with_steps[-1])

    return full_path, agent_status
    # return path_with_steps
    
