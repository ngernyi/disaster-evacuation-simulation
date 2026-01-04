import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import networkx as nx
from largestinteriorrectangle import lir

# ----------------------------
# Step 1: Load the grid
# ----------------------------
current_dir = os.path.dirname(__file__)
grid_path = os.path.join(current_dir, "..", "filled_grid.npy")
grid = np.load(grid_path)
print("[INFO] Grid shape:", grid.shape)

# ----------------------------
# Step 2: Extract rectangles
# ----------------------------
def extract_rectangles(grid, min_area=1000):
    """
    Repeatedly extract largest interior rectangles from a free-space grid.
    grid: 2D numpy array (1 = free, 0 = wall)
    min_area: minimum rectangle area to keep
    """
    grid = grid.copy().astype(bool)
    rectangles = []

    while True:
        result = lir(grid)  # largest interior rectangle
        if result is None:
            break

        x, y, w, h = result
        area = w * h
        print(area)

        if area == 0:
            break

        rectangles.append((y, x, y + h - 1, x + w - 1))  # (top, left, bottom, right)
        grid[y:y+h, x:x+w] = 0  # mark as used

    return rectangles, grid

rectangles, leftover_grid = extract_rectangles(grid, min_area=2000)
print(f"[INFO] Extracted {len(rectangles)} rectangles")

# ----------------------------
# Step 3: Build rectangle graph
# ----------------------------
def rectangles_touch(rect1, rect2):
    t1, l1, b1, r1 = rect1
    t2, l2, b2, r2 = rect2
    horiz_overlap = not (r1 < l2 or r2 < l1)
    vert_overlap  = not (b1 < t2 or b2 < t1)
    return horiz_overlap and vert_overlap

def build_rectangle_graph(rectangles):
    G = nx.Graph()
    for i, rect in enumerate(rectangles):
        G.add_node(i, rect=rect)
    for i in range(len(rectangles)):
        for j in range(i+1, len(rectangles)):
            if rectangles_touch(rectangles[i], rectangles[j]):
                G.add_edge(i, j)
    return G

G = build_rectangle_graph(rectangles)
print(f"[INFO] Graph nodes: {len(G.nodes)}, edges: {len(G.edges)}")

# ----------------------------
# Step 4: Find critical areas
# ----------------------------
critical_nodes = list(nx.articulation_points(G))
print("[RESULT] Critical rectangles indices:", critical_nodes)

# ----------------------------
# Step 5: Visualization
# ----------------------------
def visualize_rectangles(grid, rectangles, critical_nodes=None):
    plt.figure(figsize=(10, 10))
    plt.imshow(grid, cmap='gray_r')
    ax = plt.gca()

    for idx, (y1, x1, y2, x2) in enumerate(rectangles):
        w = x2 - x1 + 1
        h = y2 - y1 + 1

        color = 'red' if critical_nodes and idx in critical_nodes else 'blue'
        rect = patches.Rectangle((x1, y1), w, h, linewidth=2, edgecolor=color, facecolor='none')
        ax.add_patch(rect)

    plt.title("Blue: all rectangles | Red: critical rectangles")
    plt.savefig("rectangles.png")

visualize_rectangles(grid, rectangles, critical_nodes)
