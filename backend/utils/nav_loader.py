import os
from utils.mapConverter import *
import pickle

def load_nav_data_pickle(filename):
    """
    Load nav mesh data (graph, centroids, points, triangles) using pickle.
    """
    with open(filename, "rb") as f:
        data = pickle.load(f)
    print(f"Navigation data loaded (pickle) from {filename}")
    return data["graph"], data["centroids"], data["points"], data["triangles"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
filled_map_path_lv1 = os.path.join(BASE_DIR, "filled_grid.npy")
minMaxXY_path_lv1= os.path.join(BASE_DIR, "minMaxXY.npy")
nav_data_path_lv1 = os.path.join(BASE_DIR, "nav_data2.pkl")

filled_map_path_lv2 = os.path.join(BASE_DIR, "filled_grid_lv2.npy")
minMaxXY_path_lv2= os.path.join(BASE_DIR, "minMaxXY_lv2.npy")
nav_data_path_lv2 = os.path.join(BASE_DIR, "nav_data2_lv2.pkl")

filled_map_path_lv3 = os.path.join(BASE_DIR, "filled_grid_lv3.npy")
minMaxXY_path_lv3 = os.path.join(BASE_DIR, "minMaxXY_lv3.npy")
nav_data_path_lv3 = os.path.join(BASE_DIR, "nav_data2_lv3.pkl")

filled_map_lv1, minMaxXY_lv1 = read_filled_grid_and_minMaxXY(
    filled_map_path_lv1, 
    minMaxXY_path_lv1
)
graph_lv1, centroids_lv1, points_lv1, tri_lv1 = load_nav_data_pickle(nav_data_path_lv1)

filled_map_lv2, minMaxXY_lv2 = read_filled_grid_and_minMaxXY(
    filled_map_path_lv2, 
    minMaxXY_path_lv2
)
graph_lv2, centroids_lv2, points_lv2, tri_lv2 = load_nav_data_pickle(nav_data_path_lv2)

filled_map_lv3, minMaxXY_lv3 = read_filled_grid_and_minMaxXY(
    filled_map_path_lv3, 
    minMaxXY_path_lv3
)
graph_lv3, centroids_lv3, points_lv3, tri_lv3 = load_nav_data_pickle(nav_data_path_lv3)

NAV_DATA = {
    "filled_map_lv1": filled_map_lv1,
    "minMaxXY_lv1": minMaxXY_lv1,
    "graph_lv1": graph_lv1,
    "centroids_lv1": centroids_lv1,
    "points_lv1": points_lv1,
    "tri_lv1": tri_lv1,
    
    "filled_map_lv2": filled_map_lv2,
    "minMaxXY_lv2": minMaxXY_lv2,
    "graph_lv2": graph_lv2,
    "centroids_lv2": centroids_lv2,
    "points_lv2": points_lv2,
    "tri_lv2": tri_lv2,
    
    "filled_map_lv3": filled_map_lv3,
    "minMaxXY_lv3": minMaxXY_lv3,
    "graph_lv3": graph_lv3,
    "centroids_lv3": centroids_lv3,
    "points_lv3": points_lv3,
    "tri_lv3": tri_lv3,
}