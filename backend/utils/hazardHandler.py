from utils.nav_loader import NAV_DATA
from utils.mapConverter import *

# function to add the hazard to the nav mesh
from shapely.geometry import Point, Polygon

def add_hazard_to_nav_mesh(hazard_coords, impact_radius=30):
    
    # categories the hazards based on the floor level
    hazards_by_floor = {0: [], 1: [], 2: []}
    for hazard in hazard_coords:
        floor = hazard.get('z')
        if floor < 3:
            floor = 0
        elif floor < 7:
            floor = 1
        else:
            floor = 2
            
        hazards_by_floor[floor].append(hazard)
        
    # graphList
    graphList = []
    # for each floor, add the hazards to the nav mesh
    for floor in hazards_by_floor:
        if floor == 0:
            filled_map = NAV_DATA["filled_map_lv1"]
            minMaxXY = NAV_DATA["minMaxXY_lv1"]
            centroids = NAV_DATA["centroids_lv1"]
            points = NAV_DATA["points_lv1"]
            tri = NAV_DATA["tri_lv1"]
            graph = NAV_DATA["graph_lv1"]
        elif floor == 1:
            filled_map = NAV_DATA["filled_map_lv2"]
            minMaxXY = NAV_DATA["minMaxXY_lv2"]
            centroids = NAV_DATA["centroids_lv2"]
            points = NAV_DATA["points_lv2"]
            tri = NAV_DATA["tri_lv2"]
            graph = NAV_DATA["graph_lv2"]
        else:
            filled_map = NAV_DATA["filled_map_lv3"]
            minMaxXY = NAV_DATA["minMaxXY_lv3"]
            centroids = NAV_DATA["centroids_lv3"]
            points = NAV_DATA["points_lv3"]
            tri = NAV_DATA["tri_lv3"]
            graph = NAV_DATA["graph_lv3"]

        blocked_nodes = set()
        graph = {k: set(v) for k, v in graph.items()}  # shallow copy


        for hazard_coord in hazards_by_floor[floor]:
            lon = hazard_coord["longitude"]
            lat = hazard_coord["latitude"]
            # convert wgs to utm
            x, y = from_wgs_to_utm(lon, lat)

            # convert utm to grid
            x, y = from_utm_to_grid(x, y, minMaxXY)

            # reverse
            hazard_point = Point(y, x)

            # hazard area = circle around the hazard point
            hazard_poly = hazard_point.buffer(impact_radius)

            # check affected triangles
            for i, simplex in enumerate(tri.simplices):
                tri_poly = Polygon([points[idx] for idx in simplex])
                if tri_poly.intersects(hazard_poly):
                    # block the centroid node (or triangle index)
                    blocked_nodes.add(i)

        print("blocked nodes:", len(blocked_nodes))
        # remove blocked nodes from graph
        for node in blocked_nodes:
            if node in graph:
                for neighbor in list(graph[node]):
                    graph[neighbor].discard(node)  # remove from neighbors
                graph.pop(node, None)  # remove node itself

        # update the graphList
        graphList.append(graph)
        
    print("graphList", len(graphList))
    return graphList

        
        
        