import numpy as np
import matplotlib.pyplot as plt
import heapq
from skimage import measure
from shapely.geometry import LineString, Point, Polygon
from scipy.spatial import Delaunay
from mapConverter import *

# ------------------------------------
# Step 2 : Reduce the number of nodes in the grid map
#         (using marching squares + Douglas-Peucker)
# ------------------------------------
def reduce_nodes(filled_map, tolerance):
    """
    Extract obstacle boundaries + map edges using marching squares,
    then simplify them with Douglas-Peucker.
    """
    contours = measure.find_contours(filled_map, level=0.5)

    polygons = []
    for contour in contours:
        # marching squares gives [y, x], swap to (x, y)
        coords = [(x, y) for y, x in contour]
        poly = LineString(coords).simplify(tolerance, preserve_topology=False)
        polygons.append(poly)

    return polygons


# ------------------------------------
# Step 3 : Build the triangles from the simplified polygons
# ------------------------------------
def build_triangles(filled_map, polygons):
    """
    Collect points from simplified polygons and apply Delaunay triangulation.
    """
    points = []
    for poly in polygons:
        points.extend(list(poly.coords))

    points = np.array(points)
    tri = Delaunay(points)

    return points, tri


# ---------------------------
# Utility functions
# ---------------------------
def compute_triangle_centroids(points, tri):
    """Compute centroids for all triangles once."""
    centroids = []
    for simplex in tri.simplices:
        coords = points[simplex]
        cx = coords[:,0].mean()
        cy = coords[:,1].mean()
        centroids.append((cx, cy))
    return np.array(centroids)


def is_centroid_connection_free(c1, c2, filled_map):
    """
    Check if the line between two triangle centroids is free of walls,
    using Bresenham's algorithm on grid indices.
    c1, c2: (x, y) centroids in grid coordinates
    filled_map: 2D numpy array (1 = free, 0 = wall)
    """
    x1, y1 = int(round(c1[0])), int(round(c1[1]))
    x2, y2 = int(round(c2[0])), int(round(c2[1]))

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while True:
        # Out of bounds check
        if y1 < 0 or y1 >= filled_map.shape[0] or x1 < 0 or x1 >= filled_map.shape[1]:
            return False
        # Wall check
        if filled_map[y1, x1] == 0:   # 0 = wall
            return False

        if x1 == x2 and y1 == y2:
            break

        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy

    return True

# ---------------------------
# build nav graph based on the centroids of the triangles
# ---------------------------

def build_nav_graph(points, tri, filled_map):
    """Build navigation graph with precomputed centroids."""
    graph = {i: [] for i in range(len(tri.simplices))}
    centroids = compute_triangle_centroids(points, tri)

    # Compare every pair of triangles
    for i, t1 in enumerate(tri.simplices):
        for j, t2 in enumerate(tri.simplices):
            if i < j:
                common = set(t1).intersection(set(t2))
                if len(common) == 2:  # They share an edge
                    c1, c2 = centroids[i], centroids[j]
                    if is_centroid_connection_free(c1, c2, filled_map):
                        graph[i].append(j)
                        graph[j].append(i)

    print("graph size:", len(graph))
    return graph, centroids


# ---------------------------
# Plotting functions
# ---------------------------
def plot_nav_graph(points, tri, graph, centroids, filled_map=None):
    """Plot navigation graph with precomputed centroids."""
    plt.figure(figsize=(8,8))

    # Optionally show the filled grid map (background walls)
    if filled_map is not None:
        plt.imshow(filled_map, cmap="gray_r", origin="lower")

    # Plot triangulation
    plt.triplot(points[:,0], points[:,1], tri.simplices, color="lightblue", linewidth=0.5)

    # Plot centroids
    plt.scatter(centroids[:,0], centroids[:,1], color="red", s=10, zorder=3)

    # Draw graph edges
    for i, neighbors in graph.items():
        for j in neighbors:
            if i < j:  # avoid double drawing
                x = [centroids[i][0], centroids[j][0]]
                y = [centroids[i][1], centroids[j][1]]
                plt.plot(x, y, "g-", linewidth=1)

    plt.title("Nav Graph over Triangulation")
    plt.axis("equal")
    plt.show()


def plot_path(points, tri, graph, centroids, path_coords, start, goal, filled_map):
    """Plot path with precomputed centroids."""
    plt.figure(figsize=(8,8))

    # Optionally show the filled grid map (background walls)
    if filled_map is not None:
        plt.imshow(filled_map, cmap="gray_r", origin="lower")

    # Plot triangulation
    plt.triplot(points[:,0], points[:,1], tri.simplices, color="lightblue", linewidth=0.5)

    # Plot centroids
    plt.scatter(centroids[:,0], centroids[:,1], color="red", s=10, zorder=3)

    # Draw graph edges
    for i, neighbors in graph.items():
        for j in neighbors:
            if i < j:  # avoid double drawing
                x = [centroids[i][0], centroids[j][0]]
                y = [centroids[i][1], centroids[j][1]]
                plt.plot(x, y, "g-", linewidth=1)
    
    # plot start + goal
    plt.plot(start[0], start[1], "go", markersize=10, label="Start")
    plt.plot(goal[0], goal[1], "yo", markersize=10, label="Goal")

    # plot path
    if path_coords:
        xs, ys = zip(*path_coords)
        plt.plot(xs, ys, "b-", linewidth=2, label="Path")

    plt.legend()
    plt.gca().set_aspect("equal")
    plt.show()


# ----------------------------
# Pathfinding functions
# ----------------------------
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
    from collections import deque
    
    x, y = point
    print(f"Searching for triangle containing point: ({x}, {y})")
    print(f"Map shape: {filled_map.shape}")
    
    # Check if point is within map bounds
    grid_x, grid_y = int(round(x)), int(round(y))
    if not (0 <= grid_y < filled_map.shape[0] and 0 <= grid_x < filled_map.shape[1]):
        print(f"Point ({grid_x}, {grid_y}) is outside map bounds!")
        return None
    
    print(f"Point walkability at ({grid_x}, {grid_y}): {filled_map[grid_y, grid_x]}")
    
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
                print(f"Found direct walkable triangle: {i}")
                return i
    
    print(f"Direct triangles found: {len(direct_triangles_found)}")
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
    print(f"Max search radius: {max_search_radius}")
    
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
                        print(f"BFS found walkable triangle {i} at distance {dist}")
                        print(f"Positions checked: {positions_checked}, Walkable found: {walkable_positions_found}")
                        return i
        
        # Add neighbors to queue
        for dx, dy in directions:
            new_x, new_y = curr_x + dx, curr_y + dy
            if ((new_x, new_y) not in visited and 
                0 <= new_y < filled_map.shape[0] and 
                0 <= new_x < filled_map.shape[1]):
                visited.add((new_x, new_y))
                queue.append((new_x, new_y, dist + 1))
    
    print(f"BFS completed. Positions checked: {positions_checked}, Walkable found: {walkable_positions_found}")
    print("No walkable triangle found within search radius!")
    return None  # No walkable triangle found


def heuristic(a, b):
    """Euclidean distance heuristic."""
    return np.linalg.norm(np.array(a) - np.array(b))


def a_star_search(start_pt, goal_pt, points, tri, graph, centroids, filled_map):
    """
    Run A* on the triangle adjacency graph with precomputed centroids.
    - start_pt, goal_pt: (x, y) grid coordinates
    - points: triangulation vertices
    - tri: Delaunay triangulation object
    - graph: adjacency {tri_idx: [neighbor_tri_idx]}
    - centroids: precomputed triangle centroids
    - filled_map: 2D array for walkability checking
    """
    # Find containing triangles using BFS
    print("Start:", start_pt)
    print("Goal:", goal_pt)

    distances = np.linalg.norm(tri.points - start_pt, axis=1)
    print("Nearest vertex to start:", tri.points[np.argmin(distances)])

    start_tri = find_triangle_containing_point(start_pt, points, tri, filled_map, centroids)
    goal_tri = find_triangle_containing_point(goal_pt, points, tri, filled_map, centroids)

    print("Start triangle:", start_tri)
    print("Goal triangle:", goal_tri)
    if start_tri is None or goal_tri is None:
        raise ValueError("Start or goal point not inside any walkable triangle!")

    # Convert centroids to dictionary for easy access
    centroids_dict = {i: centroids[i] for i in range(len(centroids))}

    # A* setup
    open_set = [(0, start_tri)]
    came_from = {}
    g_score = {start_tri: 0}
    f_score = {start_tri: heuristic(centroids_dict[start_tri], centroids_dict[goal_tri])}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal_tri:
            # Reconstruct path (triangle sequence)
            tri_path = [current]
            while current in came_from:
                current = came_from[current]
                tri_path.append(current)
            tri_path.reverse()
            # Convert to coords
            path_coords = [centroids_dict[t] for t in tri_path]
            return tri_path, path_coords

        for neighbor in graph.get(current, []):
            tentative_g = g_score[current] + heuristic(
                centroids_dict[current], centroids_dict[neighbor]
            )
            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(
                    centroids_dict[neighbor], centroids_dict[goal_tri]
                )
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return None, None  # no path found

import matplotlib.pyplot as plt
import triangle.plot as trplot
import numpy as np


# def funnel_path(points, triangles, path_triangles, start, goal):
#     """
#     Improved Funnel algorithm implementation.
    
#     Args:
#         points: array of vertices from triangulation
#         triangles: triangle vertex indices (tri.simplices)
#         path_triangles: list of triangle indices from A*
#         start, goal: coordinates (x, y)
    
#     Returns:
#         path: list of points [(x0,y0), (x1,y1), ...]
#     """
#     if len(path_triangles) <= 1:
#         return [start, goal]

#     # --- Step 1: Extract and validate portals ---
#     portals = []
    
#     for i in range(len(path_triangles) - 1):
#         t1_idx, t2_idx = path_triangles[i], path_triangles[i+1]
#         verts1 = set(triangles[t1_idx])
#         verts2 = set(triangles[t2_idx])
#         shared_verts = list(verts1.intersection(verts2))
        
#         if len(shared_verts) != 2:
#             print(f"Warning: Triangles {t1_idx} and {t2_idx} don't share exactly 2 vertices")
#             continue
            
#         # Get the two points of the shared edge
#         p1, p2 = points[shared_verts[0]], points[shared_verts[1]]
        
#         # Ensure consistent ordering by comparing with triangle centers
#         t1_center = points[triangles[t1_idx]].mean(axis=0)
#         t2_center = points[triangles[t2_idx]].mean(axis=0)
        
#         # Vector from t1 to t2
#         direction = t2_center - t1_center
#         # Vector along the portal
#         portal_vec = p2 - p1
        
#         # Cross product to determine which side is "left" when moving from t1 to t2
#         cross = direction[0] * portal_vec[1] - direction[1] * portal_vec[0]
        
#         if cross > 0:
#             left, right = p1, p2
#         else:
#             left, right = p2, p1
            
#         portals.append((tuple(left), tuple(right)))
    
#     if not portals:
#         return [start, goal]
    
#     print(f"Extracted {len(portals)} portals")
    
#     # --- Step 2: Funnel Algorithm ---
#     path = [start]
    
#     # Initialize funnel
#     apex = start
#     left_point = portals[0][0]
#     right_point = portals[0][1]
#     apex_index = -1  # start point
#     left_index = 0
#     right_index = 0
    
#     def cross_2d(o, a, b):
#         """2D cross product of vectors OA and OB"""
#         return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    
#     def distance_squared(p1, p2):
#         """Squared distance between two points"""
#         return (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2
    
#     # Process each portal
#     for i in range(len(portals)):
#         left, right = portals[i]
        
#         # Update right side of funnel
#         while True:
#             # If new right point is on the right side of apex->right_point line
#             if cross_2d(apex, right_point, right) <= 0:
#                 # If new right point is on the left side of apex->left_point line
#                 if cross_2d(apex, left_point, right) >= 0:
#                     # Update right side
#                     right_point = right
#                     right_index = i
#                     break
#                 else:
#                     # Right side has crossed left side, move apex
#                     if distance_squared(apex, left_point) > 1e-10:  # avoid duplicate points
#                         path.append(left_point)
#                     apex = left_point
#                     apex_index = left_index
#                     # Reset funnel
#                     right_point = right
#                     left_point = apex
#                     right_index = i
#                     left_index = apex_index
#                     break
#             else:
#                 break
        
#         # Update left side of funnel
#         while True:
#             # If new left point is on the left side of apex->left_point line
#             if cross_2d(apex, left_point, left) >= 0:
#                 # If new left point is on the right side of apex->right_point line
#                 if cross_2d(apex, right_point, left) <= 0:
#                     # Update left side
#                     left_point = left
#                     left_index = i
#                     break
#                 else:
#                     # Left side has crossed right side, move apex
#                     if distance_squared(apex, right_point) > 1e-10:  # avoid duplicate points
#                         path.append(right_point)
#                     apex = right_point
#                     apex_index = right_index
#                     # Reset funnel
#                     left_point = left
#                     right_point = apex
#                     left_index = i
#                     right_index = apex_index
#                     break
#             else:
#                 break
    
#     # # Add goal if it's not too close to the last point
#     if not path or distance_squared(path[-1], goal) > 1e-10:
#         path.append(goal)
    
#     # # Remove points that are too close together
#     # filtered_path = [path[0]]
#     # for i in range(1, len(path)):
#     #     if distance_squared(filtered_path[-1], path[i]) > 1e-3:
#     #         filtered_path.append(path[i])
    
#     # print(f"Funnel path: {len(filtered_path)} points")
#     return path

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
    
    print(f"Extracting edges from {len(path_triangles)} triangles...")
    
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
        
        print(f"Edge {i}: ({tuple(p1)}, {tuple(p2)})")
    
    if not edge_path:
        print("No valid edges found!")
        return [start, goal]
    
    print(f"Created {len(edge_path)} edges")
    
    # Step 2: Apply the GitHub funnel algorithm
    p = tuple(start)  # Start point
    q = tuple(goal)   # Goal point
    
    tail = [p]
    left = []
    right = []
    last_edge_l = None
    last_edge_r = None
    
    print(f"\\nStarting funnel algorithm with start={p}, goal={q}")
    print(f"Processing {len(edge_path)} edges...")
    
    for i, e in enumerate(edge_path):
        print(f"\\n--- Processing edge {i}: {e} ---")
        
        p1, p2 = point_dict[e[0]], point_dict[e[1]]
        print(f"Edge points: p1={p1}, p2={p2}")
        print(f"Last edges: last_edge_l={last_edge_l}, last_edge_r={last_edge_r}")
        
        # Determine orientation: swap if needed for consistency
        original_order = (p1, p2)
        if (p2 == last_edge_l or p1 == last_edge_r or 
            (last_edge_r is None and last_edge_l is None and ccw(tail[-1], p2, p1))):
            p1, p2 = p2, p1
            print(f"Swapped edge orientation: p1={p1}, p2={p2}")
        else:
            print(f"Kept original orientation: p1={p1}, p2={p2}")
        
        print(f"Current state: tail={tail[-1]}, left={left}, right={right}")
        
        # Process left side (p1)
        if len(left) == 0 and not points_equal(p1, tail[-1]):
            left = [p1]
            print(f"Initialized left: {left}")
        elif len(left) > 0 and not points_equal(left[-1], p1):
            print(f"Testing left side: ccw({tail[-1]}, {p1}, {left[-1]}) = {ccw(tail[-1], p1, left[-1])}")
            
            if not ccw(tail[-1], p1, left[-1]):  # p1 narrows the funnel
                print("Left side narrows funnel, checking for collisions...")
                last_collision = -1
                
                for j, p in enumerate(right):
                    if ccw(tail[-1], p, p1):
                        print(f"Collision detected with right[{j}]={p}")
                        tail.append(right[j])
                        last_collision = j
                        print(f"Added to tail: {tail[-1]}")
                
                if last_collision >= 0:
                    print(f"Collision occurred, resetting funnel")
                    left = [p1]
                    right = right[last_collision + 1:]
                    print(f"New left: {left}, new right: {right}")
                else:
                    print("No collisions, narrowing left funnel")
                    left[-1] = p1
                    print(f"Updated left: {left}")
            else:
                print("Left side opens funnel, appending")
                left.append(p1)
                print(f"Left after append: {left}")
        
        # Process right side (p2)
        if len(right) == 0 and not points_equal(p2, tail[-1]):
            right = [p2]
            print(f"Initialized right: {right}")
        elif len(right) > 0 and not points_equal(right[-1], p2):
            print(f"Testing right side: ccw({tail[-1]}, {right[-1]}, {p2}) = {ccw(tail[-1], right[-1], p2)}")
            
            if not ccw(tail[-1], right[-1], p2):  # p2 narrows the funnel
                print("Right side narrows funnel, checking for collisions...")
                last_collision = -1
                
                for j, p in enumerate(left):
                    if ccw(tail[-1], p2, p):
                        print(f"Collision detected with left[{j}]={p}")
                        tail.append(left[j])
                        last_collision = j
                        print(f"Added to tail: {tail[-1]}")
                
                if last_collision >= 0:
                    print(f"Collision occurred, resetting funnel")
                    right = [p2]
                    left = left[last_collision + 1:]
                    print(f"New right: {right}, new left: {left}")
                else:
                    print("No collisions, narrowing right funnel")
                    right[-1] = p2
                    print(f"Updated right: {right}")
            else:
                print("Right side opens funnel, appending")
                right.append(p2)
                print(f"Right after append: {right}")
        
        last_edge_l = p1
        last_edge_r = p2
        
        print(f"End of edge {i}: tail={tail}, left={left}, right={right}")
    
    # Final cleanup: handle remaining collisions with goal
    apex = tail[-1]
    print(f"\\nFinal cleanup with apex={apex}, goal={q}")
    
    # Check right side collisions with goal
    for i, p in enumerate(right):
        if ccw(apex, p, q):
            print(f"Final right collision: adding right[{i}]={p}")
            tail.append(right[i])
    
    # Check left side collisions with goal  
    for i, p in enumerate(left):
        if ccw(apex, q, p):
            print(f"Final left collision: adding left[{i}]={p}")
            tail.append(left[i])
    
    # Add goal
    tail.append(q)
    
    print(f"\\nFinal path: {tail}")
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
    
    


def plot_funnel(points, tri, path, start, goal, filled_map):
    """Plot triangulation and funnel path."""
    plt.figure(figsize=(8,8))

    # Optionally show the filled grid map (background walls)
    if filled_map is not None:
        plt.imshow(filled_map, cmap="gray_r", origin="lower")

    # Plot triangulation
    plt.triplot(points[:,0], points[:,1], tri.simplices, color="lightblue", linewidth=0.5)

    # Plot centroids
    plt.scatter(centroids[:,0], centroids[:,1], color="red", s=10, zorder=3)

    # Triangulation vertices
    plt.plot(points[:,0], points[:,1], "k.", markersize=2)

    # Start + Goal
    plt.plot(start[0], start[1], "go", markersize=10, label="Start")
    plt.plot(goal[0], goal[1], "ro", markersize=10, label="Goal")

    # Path
    if path:
        xs, ys = zip(*path)
        plt.plot(xs, ys, "b-", linewidth=2, label="Funnel Path")

    plt.legend()
    plt.gca().set_aspect("equal")
    plt.show()



# ------------------------------------
# Utility function for adding border
# ------------------------------------
def add_border(grid, value=0, width=1):
    """Add border of specified value around grid."""
    h, w = grid.shape
    bordered = np.full((h + 2*width, w + 2*width), value, dtype=grid.dtype)
    bordered[width:width+h, width:width+w] = grid
    return bordered


# ---------------- Example Usage ----------------
if __name__ == "__main__":
    from mapConverter import read_filled_grid_and_minMaxXY

    filled_map, minMaxXY = read_filled_grid_and_minMaxXY(
        "C:\\Users\\Admin\\Documents\\University of Malaya\\Y3S2\\FYP\\Code\\backend\\utils\\filled_grid.npy", 
        "C:\\Users\\Admin\\Documents\\University of Malaya\\Y3S2\\FYP\\Code\\backend\\utils\\minMaxXY.npy"
    )

    # Add border of 0 (walls) around map
    filled_map = add_border(filled_map, value=0, width=1)

    # Step 2: simplify polygons
    polygons = reduce_nodes(filled_map, tolerance=10.0)

    # Step 3: build triangulation
    points, tri = build_triangles(filled_map, polygons)

    # Plot initial triangulation
    plt.figure(figsize=(8, 8))
    plt.imshow(filled_map, cmap='gray', origin='lower')

    # Draw simplified outlines
    for poly in polygons:
        x, y = poly.xy
        plt.plot(x, y, color="purple", linewidth=2)

    # Draw triangulation
    plt.triplot(points[:, 0], points[:, 1], tri.simplices, color="cyan", linewidth=0.5)
    plt.scatter(points[:, 0], points[:, 1], s=5, color="red")
    plt.title("Marching Squares → Simplification → Delaunay Triangulation")
    plt.show()

    # Build graph and compute centroids once
    graph, centroids = build_nav_graph(points, tri, filled_map)
    plot_nav_graph(points, tri, graph, centroids, filled_map)

    # Define start and goal coordinates
    # start_lon = -117.19605818250982
    # start_lat = 34.05592363955583
    start_lon = -117.19579771003762
    start_lat = 34.05611964177133
    # goal_lon = -117.19535536619419
    # goal_lat = 34.05591153718531
    goal_lon = -117.19588947833753
    goal_lat = 34.05612622715027

   
    # Convert to UTM
    start_x, start_y = from_wgs_to_utm(start_lon, start_lat)
    goal_x, goal_y = from_wgs_to_utm(goal_lon, goal_lat)
    print("Start (UTM):", start_x, start_y)
    print("Goal (UTM):", goal_x, goal_y)

    # Convert to grid 
    start_grid_x, start_grid_y = from_utm_to_grid(start_x, start_y, minMaxXY)
    goal_grid_x, goal_grid_y = from_utm_to_grid(goal_x, goal_y, minMaxXY)
    print("Start (grid):", start_grid_x, start_grid_y)
    print("Goal (grid):", goal_grid_x, goal_grid_y)
    print("Map shape:", filled_map.shape)
    print("Map bounds: x=[0,{}], y=[0,{}]".format(filled_map.shape[1]-1, filled_map.shape[0]-1))
    start = (start_grid_y, start_grid_x)
    goal = (goal_grid_y, goal_grid_x)
    plot_path(points, tri, graph, centroids, [], start, goal, filled_map)
   
    
    # # Convert to tuples for pathfinding
    # start = (start_grid_x, start_grid_y)
    # goal = (goal_grid_x, goal_grid_y)

    # Find path using precomputed centroids and BFS triangle finding
    path_triangles, path_coords = a_star_search(start, goal, points, tri, graph, centroids, filled_map)
    print("Path coordinates:", path_coords)
    # plot_path(points, tri, graph, centroids, path_coords, start, goal, filled_map)
    
    
    # # Compute funnel-smoothed path
    # funnel_coords = funnel_path(points, tri.simplices, path_triangles, start, goal)
    # print("Funnel smoothed path:", funnel_coords)

    # # funnel_constrained_in_area = funnel_path_constrained(points, tri.simplices, path_triangles, start, goal)
    # plot_funnel_debug(points, tri, path_triangles ,funnel_coords, start, goal, filled_map)




    funnel_coords = funnel_path_github_adapted(points, tri.simplices, path_triangles, start, goal)
    print("Funnel smoothed path:", funnel_coords)

    # funnel_constrained_in_area = funnel_path_constrained(points, tri.simplices, path_triangles, start, goal)
    plot_funnel_debug(points, tri, path_triangles ,funnel_coords, start, goal, filled_map)
