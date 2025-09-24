import numpy as np
import matplotlib.pyplot as plt
import heapq
from skimage import measure
from shapely.geometry import LineString, Point, Polygon
from scipy.spatial import Delaunay
from mapConverter import *
import pickle
from mapConverter import read_filled_grid_and_minMaxXY
import os


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
# def build_triangles(filled_map, polygons):
#     """
#     Collect points from simplified polygons and apply Delaunay triangulation.
#     """
#     points = []
#     for poly in polygons:
#         points.extend(list(poly.coords))

#     points = np.array(points)
#     tri = Delaunay(points)

#     return points, tri

def build_triangles(filled_map, polygons, spacing=50):
    """
    Collect points from simplified polygons + interior samples,
    then apply Delaunay triangulation.
    """
    points = []

    # Add polygon boundary points
    for poly in polygons:
        points.extend(list(poly.coords))

    # Add interior grid points to prevent huge triangles
    rows, cols = filled_map.shape
    for y in range(0, rows, spacing):
        for x in range(0, cols, spacing):
            if filled_map[y, x] == 1:  # free space only
                points.append((x, y))

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

# ------------------------------------
# Utility function for adding border
# ------------------------------------
def add_border(grid, value=0, width=1):
    """Add border of specified value around grid."""
    h, w = grid.shape
    bordered = np.full((h + 2*width, w + 2*width), value, dtype=grid.dtype)
    bordered[width:width+h, width:width+w] = grid
    return bordered

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
    # plt.show()
    plt.savefig("smaller_nav_graph_lv3.png")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
filled_map_path = os.path.join(BASE_DIR, "filled_grid_lv3.npy")
minMaxXY_path = os.path.join(BASE_DIR, "minMaxXY_lv3.npy")

filled_map, minMaxXY = read_filled_grid_and_minMaxXY(
    filled_map_path, 
    minMaxXY_path
)

# Add border of 0 (walls) around map
filled_map = add_border(filled_map, value=0, width=1)

# Step 2: simplify polygons
polygons = reduce_nodes(filled_map, tolerance=1)

# Step 3: build triangulation
points, tri = build_triangles(filled_map, polygons)
print("triangulation size:", len(tri.simplices))

 # Build graph and compute centroids once
graph, centroids = build_nav_graph(points, tri, filled_map)

plot_nav_graph(points, tri, graph, centroids, filled_map)




def save_nav_data_pickle(filename, graph, centroids, points, triangles):
    """
    Save nav mesh data (graph, centroids, points, triangles) using pickle.
    """
    data = {
        "graph": graph,
        "centroids": centroids,
        "points": points,
        "triangles": triangles
    }
    with open(filename, "wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"Navigation data saved (pickle) to {filename}")





save_nav_data_pickle("nav_data2_lv3.pkl", graph, centroids, points, tri)