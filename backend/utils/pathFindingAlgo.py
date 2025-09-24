from pyproj import Transformer
import heapq
import math

# dijkstra's algorithm path finding
# params:
# 1) wallPoints: list of wall points (in utm)
# 2) start: start point (in wgs)
# 3) goal: goal point (in wgs)
# return:
# 1) path: path from start to goal (in wgs)
# 2) distance: distance from start to goal (in meters)

# transformers
to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32611", always_xy=True)   # lon, lat -> x,y (m)
to_wgs = Transformer.from_crs("EPSG:32611", "EPSG:4326", always_xy=True)   # x,y (m) -> lon, lat

def dijkstra(wallPoints, start, goal, step=0.5):
    # convert the start and goal to utm
    startX, startY = to_utm.transform(start[0], start[1])
    goalX, goalY = to_utm.transform(goal[0], goal[1])
    start = (round(startX, 3), round(startY, 3))
    goal = (round(goalX, 3), round(goalY, 3))
    
    # convert wall points to UTM
    wallPoints_utm = []
    for point in wallPoints:
        x, y = to_utm.transform(point[0], point[1])  # lon, lat
        wallPoints_utm.append((round(x, 3), round(y, 3)))

    print("start:", start)
    print("goal:", goal)

    # priority queue
    queue = []
    heapq.heappush(queue, (0, start))

    # distances & parents
    distance = {start: 0}
    parent = {start: None}
    final_goal = None  # will hold the reached node (due to tolerance)

    while queue:
        current_dist, current = heapq.heappop(queue)
        # print("current:", current)

        if is_goal(current, goal):
            # print("goal reached at:", current)
            final_goal = current
            break

        for neighbor in get_neighbors(current, wallPoints_utm, step):
            dx = abs(neighbor[0] - current[0])
            dy = abs(neighbor[1] - current[1])
            move_cost = math.hypot(dx, dy)

            new_dist = current_dist + move_cost
            if neighbor not in distance or new_dist < distance[neighbor]:
                distance[neighbor] = new_dist
                parent[neighbor] = current
                heapq.heappush(queue, (new_dist, neighbor))

    if not final_goal:  
        return [], float("inf")

    # reconstruct path
    path = []
    current = final_goal
    while current:
        path.append(current)
        current = parent[current]

    # reverse to get start -> goal
    path.reverse()

    # convert to WGS first
    path_wgs_only = [to_wgs.transform(p[0], p[1]) for p in path]

    # assign step order
    path_with_steps = [(coord[0], coord[1], i+1) for i, coord in enumerate(path_wgs_only)]



    return path_with_steps, distance[final_goal]

def is_goal(current, goal, tolerance=0.5):
    return abs(current[0] - goal[0]) <= tolerance and abs(current[1] - goal[1]) <= tolerance

def get_neighbors(point, wallPoints, step=0.5):
    neighbors = []
    for i in [-1, 0, 1]:
        for j in [-1, 0, 1]:
            if i == 0 and j == 0:
                continue
            neighbor = (round(point[0] + i * step, 3),
                        round(point[1] + j * step, 3))
            if neighbor not in wallPoints:
                neighbors.append(neighbor)
    return neighbors


# Example run
# wallPoints = []  # must also be in UTM if real
# start = (34.056093307118, -117.195862036856)  # (lat, lon)
# goal = (34.0560209565503, -117.19592918083)   # (lat, lon)

# result = dijkstra(wallPoints, start, goal)
# print("Path (lon,lat):", result[0])
# print("Distance (m):", result[1])

# ----------------------------------------------------------------

# function to rasterize a path
