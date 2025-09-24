import re
import matplotlib.pyplot as plt
import triangle
import triangle.plot as trplot
from shapely.geometry import LineString
import heapq
from shapely.geometry import Point, Polygon
from shapely.geometry import Polygon
from shapely.ops import unary_union
from mapConverter import from_wgs_to_utm

# -------------------------------
# Step 1: Read input file
# -------------------------------
def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

# -------------------------------
# Step 2: Parse features
# -------------------------------
def parse_features(text):
    features = []
    current_feature = []
    for line in text.splitlines():
        line = line.strip()
        if re.match(r"Feature", line):   # new feature block
            if current_feature:
                features.append(current_feature)
                current_feature = []
        elif re.match(r"^\d", line):     # coordinate line
            parts = line.split(",")
            x = float(parts[0].strip())
            y = float(parts[1].strip())
            current_feature.append((x, y))
    if current_feature:
        if current_feature[0] == current_feature[-1]:
            current_feature.pop() 

        features.append(current_feature)
    return features

# -------------------------------
# Step 3: Merge features that are close together
# -------------------------------

def merge_close_features(features, tolerance=0.2):
    """
    Merge features that are close together by buffering and union.
    """
    polys = []
    for f in features:
        try:
            poly = Polygon(f)
            if not poly.is_valid:
                poly = poly.buffer(0)  # fix invalid polygon
            polys.append(poly.buffer(tolerance))  # expand a bit
        except Exception as e:
            continue  # skip invalid features
    
    # Merge all
    merged = unary_union(polys)

    # Shrink back
    merged = merged.buffer(-tolerance)

    # Convert back to list of features
    result = []
    if merged.geom_type == "Polygon":
        result.append(list(merged.exterior.coords))
    else:
        for geom in merged.geoms:
            result.append(list(geom.exterior.coords))
    return result


# -------------------------------
# Step 3: Add the boundaries of the map
# -------------------------------
def add_boundaries(features):
    # Find min and max x, y
    min_x = min(min(feature, key=lambda x: x[0])[0] for feature in features) -1
    max_x = max(max(feature, key=lambda x: x[0])[0] for feature in features) +1
    min_y = min(min(feature, key=lambda x: x[1])[1] for feature in features) -1
    max_y = max(max(feature, key=lambda x: x[1])[1] for feature in features) +1

    # Create boundary points
    boundary_points = [
        (min_x, min_y),
        (min_x, max_y),
        (max_x, max_y),
        (max_x, min_y),
    ]

    # Add boundary to features
    features.append(boundary_points)
    
# -------------------------------
# Step 4: Douglas-Peucker algorithm (to reduce the number of vertices)
# -------------------------------
def simplify_feature(feature, tolerance=1.0):
    """
    Simplify a feature (list of (x,y) points) using Douglas-Peucker.
    """
    line = LineString(feature)
    simplified = line.simplify(tolerance, preserve_topology=True)
    return list(simplified.coords)

# -------------------------------
# Step 5: Convert features → Triangle input dict
# -------------------------------
def build_triangle_input(features):
    points = []
    segments = []
    point_index = {}

    for feature in features:
        poly = feature 

        # add vertices to global list
        for p in poly:
            if p not in point_index:
                point_index[p] = len(points)
                points.append(p)

        # add segments for this polygon
        n = len(poly)
        for i in range(n):
            seg = (point_index[poly[i]], point_index[poly[(i+1) % n]])
            if seg not in segments and seg[::-1] not in segments:
                segments.append(seg)

    return dict(vertices=points, segments=segments)

# ------------------------------
# Step 6: Build the nav graph using the triangles
# ------------------------------
from shapely.geometry import LineString, Polygon

def extract_wall_segments(features):
    wall_segments = set()
    for feat in features:
        if hasattr(feat, "coords"):  # shapely geometry
            coords = list(feat.coords)
        else:  # plain list/tuple of points
            coords = list(feat)
        for i in range(len(coords) - 1):
            edge = tuple(sorted((tuple(coords[i]), tuple(coords[i + 1]))))
            wall_segments.add(edge)
    return wall_segments




def build_nav_graph(triangles, features):
    wall_segments = extract_wall_segments(features)
    graph = {i: [] for i in range(len(triangles))}

    # Edge -> list of triangle indices that share it
    edge_map = {}

    for i, tri in enumerate(triangles):
        coords = list(tri.exterior.coords)[:-1]  # skip duplicate last point
        edges = [(coords[j], coords[(j + 1) % 3]) for j in range(3)]
        for e in edges:
            edge = tuple(sorted(e))  # normalize direction
            if edge not in edge_map:
                edge_map[edge] = []
            edge_map[edge].append(i)

    # Now connect triangles that share edges
    for edge, tris in edge_map.items():
        if len(tris) == 2:  # edge shared by 2 triangles
            if edge not in wall_segments:
                t1, t2 = tris
                graph[t1].append(t2)
                graph[t2].append(t1)

    return graph


# ------------------------------
# Step 7: Find the triangle that contains the point
# ------------------------------
def find_triangle(point, triangles):
    for i, tri in enumerate(triangles):
        if tri.contains(point):
            return i
    return None

# ------------------------------
# Step 8: Find the shortest path between two triangles
# ------------------------------
def astar(start_idx, goal_idx, graph, centroids):
    frontier = [(0, start_idx)]
    came_from = {start_idx: None}
    cost_so_far = {start_idx: 0}

    while frontier:
        _, current = heapq.heappop(frontier)
        if current == goal_idx:
            break
        for nxt in graph[current]:
            new_cost = cost_so_far[current] + centroids[current].distance(centroids[nxt])
            if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                cost_so_far[nxt] = new_cost
                priority = new_cost + centroids[nxt].distance(centroids[goal_idx])
                heapq.heappush(frontier, (priority, nxt))
                came_from[nxt] = current

    # Reconstruct path
    path = []
    cur = goal_idx
    while cur is not None:
        path.append(cur)
        cur = came_from.get(cur)
    return list(reversed(path))



if __name__ == "__main__":
    # Example input file
    data = read_file("C:\\Users\\Admin\\Downloads\\walls_floor1.txt")
    features = parse_features(data)
    # features = merge_close_features(features, tolerance=0.1)  # <--- merge nearby features
    add_boundaries(features)
    print("done cleaning")
    simplified_features = [simplify_feature(f) for f in features]
    A = build_triangle_input(simplified_features)

    # Run Constrained Delaunay Triangulation
    B = triangle.triangulate(A, 'p')
    print("done triangulating")
    # -------------------------
    # Build triangles as shapely Polygons
    # -------------------------
    vertices = B["vertices"]
    triangles = []
    for tri in B["triangles"]:
        coords = [tuple(vertices[i]) for i in tri]
        triangles.append(Polygon(coords))
    centroids = [t.centroid for t in triangles]
    print("done building triangles")
    # -------------------------
    # Build navgraph
    # -------------------------
    graph = build_nav_graph(triangles, features)
    print("done building graph")

    # -------------------------
    # Define start & goal points
    # -------------------------
    start_lon = -117.19576862944419
    start_lat = 34.05611636531915
    goal_lon = -117.19588947833753
    goal_lat = 34.05612622715027

    # convert to UTM
    start_x, start_y = from_wgs_to_utm(start_lon, start_lat)
    goal_x, goal_y = from_wgs_to_utm(goal_lon, goal_lat)

    print("Start (UTM):", start_x, start_y)
    print("Goal (UTM):", goal_x, goal_y)

    start = Point(start_x, start_y)
    goal = Point(goal_x, goal_y)

    start_idx = find_triangle(start, triangles)
    goal_idx = find_triangle(goal, triangles)

    if start_idx is None or goal_idx is None:
        print("Start or goal not inside the navmesh!")
    else:
        # -------------------------
        # Run A* search
        # -------------------------
        triangle_path = astar(start_idx, goal_idx, graph, centroids)
        print("Triangle sequence:", triangle_path)

        # Build raw path (through centroids of triangles)
        path_coords = [centroids[i].coords[0] for i in triangle_path]

        # -------------------------
        # Plot navmesh + path
        # -------------------------
        fig, ax = plt.subplots(figsize=(8, 8))
        triangle.plot(ax, **B)
        ax.set_aspect('equal')

        # Plot start/goal
        ax.plot(start.x, start.y, "go", markersize=10, label="Start")
        ax.plot(goal.x, goal.y, "ro", markersize=10, label="Goal")

        # Plot path
        xs, ys = zip(*path_coords)
        ax.plot(xs, ys, "b-", linewidth=2, label="Path")

        ax.legend()
        plt.show()
