from pyproj import Transformer
import heapq
import math

# transformers
to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32611", always_xy=True)   # lon, lat -> x,y (m)
to_wgs = Transformer.from_crs("EPSG:32611", "EPSG:4326", always_xy=True)   # x,y (m) -> lon, lat

def dijkstra(wallPoints, start, goal, step=0.5):
    # start and goal given as (lat, lon) -> swap for transformer
    startX, startY = to_utm.transform(start[1], start[0])
    goalX, goalY = to_utm.transform(goal[1], goal[0])
    start = (round(startX, 3), round(startY, 3))
    goal = (round(goalX, 3), round(goalY, 3))

    print("start:", start)
    print("goal:", goal)
    print("Projected start:", startX, startY)
    print("Projected goal:", goalX, goalY)

    # priority queue
    queue = []
    heapq.heappush(queue, (0, start))

    # distances & parents
    distance = {start: 0}
    parent = {start: None}
    final_goal = None  # will hold the reached node

    while queue:
        current_dist, current = heapq.heappop(queue)
        print("current:", current)

        if is_goal(current, goal):
            print("goal reached at:", current)
            final_goal = current
            break

        for neighbor in get_neighbors(current, wallPoints, step):
            dx = abs(neighbor[0] - current[0])
            dy = abs(neighbor[1] - current[1])
            move_cost = math.hypot(dx, dy)

            new_dist = current_dist + move_cost
            if neighbor not in distance or new_dist < distance[neighbor]:
                distance[neighbor] = new_dist
                parent[neighbor] = current
                heapq.heappush(queue, (new_dist, neighbor))

    if not final_goal:  # never reached
        return [], float("inf")

    # reconstruct path
    path = []
    current = final_goal
    while current:
        path.append(current)
        current = parent[current]

    path.reverse()

    # convert path back to WGS (lon, lat)
    path_wgs = [to_wgs.transform(p[0], p[1]) for p in path]

    return path_wgs, distance[final_goal]

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
wallPoints = []  # must also be in UTM if real
start = (34.056093307118, -117.195862036856)  # (lat, lon)
goal = (34.0560209565503, -117.19592918083)   # (lat, lon)

result = dijkstra(wallPoints, start, goal)
print("Path (lon,lat):", result[0])
print("Distance (m):", result[1])
