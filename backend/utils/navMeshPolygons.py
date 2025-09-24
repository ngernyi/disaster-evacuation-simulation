import numpy as np
import matplotlib.pyplot as plt
import random
import networkx as nx
from shapely.geometry import Polygon, Point, LineString
from utils.mapConverter import *
from utils.pathFindingAlgo import *
# from mapConverter import *
# from pathFindingAlgo import *

def decompose_into_rectangles(grid):
    visited = np.zeros_like(grid, dtype=bool)
    rectangles = []
    rows, cols = grid.shape
    
    for i in range(rows):
        for j in range(cols):
            if grid[i, j] == 1 and not visited[i, j]:
                # Expand to the right
                max_col = j
                while max_col + 1 < cols and np.all(grid[i, j:max_col+2] == 1) and not np.any(visited[i, j:max_col+2]):
                    max_col += 1

                # Expand downward
                max_row = i
                valid = True
                while valid and max_row + 1 < rows:
                    if np.all(grid[max_row+1, j:max_col+1] == 1) and not np.any(visited[max_row+1, j:max_col+1]):
                        max_row += 1
                    else:
                        valid = False

                # Convert to Shapely Polygon (note col=x, row=y)
                poly = Polygon([(j, i), (max_col+1, i), (max_col+1, max_row+1), (j, max_row+1)])
                rectangles.append(poly)

                visited[i:max_row+1, j:max_col+1] = True
    return rectangles


def plot_rectangles(grid, rectangles):
    plt.imshow(grid, cmap="gray_r")
    ax = plt.gca()
    for rect in rectangles:
        x,y = rect.exterior.xy
        color = [random.random() for _ in range(3)]
        ax.plot(x, y, color=color, linewidth=2)
    plt.show()


def build_rectangle_graph(rectangles):
    G = nx.Graph()
    for i, rect1 in enumerate(rectangles):
        G.add_node(i, polygon=rect1)
        for j, rect2 in enumerate(rectangles[:i]):
            if rect1.touches(rect2) or rect1.intersects(rect2):
                G.add_edge(i, j)
    return G


def find_rectangle(point, rectangles):
    p = Point(point)
    for i, rect in enumerate(rectangles):
        if rect.contains(p):
            return i
    return None


def shortest_rectangle_path(rectangles, start, goal):
    G = build_rectangle_graph(rectangles)

    start_rect = find_rectangle(start, rectangles)
    goal_rect = find_rectangle(goal, rectangles)

    if start_rect is None or goal_rect is None:
        print("Start or goal is outside walkable area!")
        return None

    try:
        rect_path = nx.shortest_path(G, source=start_rect, target=goal_rect)
    except nx.NetworkXNoPath:
        print("No path found between start and goal")
        return None

    return rect_path


# ----------------------------
# Funnel (string pulling)
# ----------------------------
def funnel_path(rectangles, rect_path, start, goal):
    # Corridor is union of rects along path
    corridor = [rectangles[i] for i in rect_path]

    # Build portals = shared edges between consecutive rects
    portals = []
    for i in range(len(corridor)-1):
        inter = corridor[i].intersection(corridor[i+1])
        if inter.is_empty:
            continue
        if isinstance(inter, LineString):
            coords = list(inter.coords)
            portals.append(coords)
        else:
            # Fallback: centroid if no clean edge
            portals.append([corridor[i].centroid.coords[0], corridor[i+1].centroid.coords[0]])

    # Funnel algorithm
    path = [start]
    apex = start
    left = right = None
    idx_left = idx_right = 0

    for i, portal in enumerate(portals + [[goal, goal]]):
        left_pt, right_pt = portal[0], portal[-1]

        if left is None: left, right = left_pt, right_pt

        # Update funnel
        if _area2(apex, right, right_pt) <= 0:  # tighten right
            if apex == right or _area2(apex, left, right_pt) > 0:
                right = right_pt
                idx_right = i
            else:  # left funnel collapses
                path.append(left)
                apex = left
                i = idx_left
                left, right = apex, apex
                continue

        if _area2(apex, left, left_pt) >= 0:  # tighten left
            if apex == left or _area2(apex, right, left_pt) < 0:
                left = left_pt
                idx_left = i
            else:  # right funnel collapses
                path.append(right)
                apex = right
                i = idx_right
                left, right = apex, apex
                continue

    path.append(goal)
    return path


def _area2(a, b, c):
    """Twice signed area of triangle abc. Positive if c is left of ab"""
    return (b[0]-a[0])*(c[1]-a[1]) - (c[0]-a[0])*(b[1]-a[1])


# === Example usage ===
grid = np.load("filled_grid.npy")
rectangles = decompose_into_rectangles(grid)

# Debug
print("Number of rectangles:", len(rectangles))

plot_rectangles(grid, rectangles)

# Choose start/goal
start = (771, 1437) # x=col, y=row
goal = (256, 772)

# start = start[::-1]
# goal = goal[::-1]

# start = (grid.shape[1] - start[0], grid.shape[0] - start[0])
# goal = (grid.shape[1] - goal[0], grid.shape[0] - goal[0])

start = (start[1], start[0])
goal = (goal[1], goal[0])
print("start:", start)
print("goal:", goal)
rect_path = shortest_rectangle_path(rectangles, start, goal)

if rect_path:
    path_coords = funnel_path(rectangles, rect_path, start, goal)



    # Visualize path
    plt.imshow(grid, cmap="gray_r")
    for rect in rectangles:
        x,y = rect.exterior.xy
        plt.plot(x,y,alpha=0.3)
    xs, ys = zip(*path_coords)
    plt.plot(xs, ys, 'r-o', linewidth=2)
    plt.scatter([start[0]], [start[1]], c='g', s=80, label="Start")
    plt.scatter([goal[0]], [goal[1]], c='b', s=80, label="Goal")
    plt.legend()
    plt.show()


def rectanglePathFindings(start, goal, step=0.05):
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
    start_grid = (start_grid[1], start_grid[0])
    goal_grid = (goal_grid[1], goal_grid[0])

    # start_grid = (minMaxXY[3] - start_grid[1], start_grid[0])
    print("converted start (grid):", start_grid)
    print("converted goal (grid):", goal_grid)
    
    rectangles = decompose_into_rectangles(filled_map)
    rect_path = shortest_rectangle_path(rectangles, start_grid, goal_grid)
    if rect_path is None:
        print("No path found")
        return None
    path_coords = funnel_path(rectangles, rect_path, start_grid, goal_grid)
    
     # Convert back to UTM coords
    path_utm = [from_grid_to_utm(p[0], p[1], minMaxXY, step) for p in path_coords]

    # Convert to WGS84
    path_wgs_only = [from_utm_to_wgs(p[0], p[1]) for p in path_utm]

    # Assign step order
    path_with_steps = [(coord[0], coord[1], i+1) for i, coord in enumerate(path_wgs_only)]

    return path_with_steps

# rectanglePathFindings((600, 1000), (1000, 1000))