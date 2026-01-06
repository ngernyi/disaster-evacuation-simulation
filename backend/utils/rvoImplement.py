# import rvo2
# import numpy as np
# import matplotlib.pyplot as plt
# import os
# from utils.mapConverter import *
# from skimage.morphology import skeletonize
# import cv2
# from utils.nav_loader import NAV_DATA
# from skimage import measure
# from shapely.geometry import LineString

# import cv2

# def reduce_nodes_to_contours(filled_map, tolerance=1.0, inflate_radius=5):
#     """
#     Extract obstacle boundaries + map edges using marching squares,
#     then simplify them with Douglas-Peucker, returning contours.
#     Obstacles are inflated by inflate_radius pixels.
#     """
#     # Convert to binary mask
#     binary = (1 - np.array(filled_map, dtype=np.uint8)) * 255

#     if inflate_radius > 0:
#         kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2*inflate_radius+1, 2*inflate_radius+1))
#         binary = cv2.dilate(binary, kernel, iterations=1)  # thicken walls

#     contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

#     contour_polygons = []
#     for cnt in contours:
#         coords = [(int(p[0][0]), int(p[0][1])) for p in cnt]
#         poly = LineString(coords).simplify(tolerance, preserve_topology=False)
#         points = [(int(round(p[0])), int(round(p[1]))) for p in poly.coords]
#         contour_polygons.append(points)

#     return contour_polygons

# def extract_wall_contours(grid):
#     # Ensure grid is uint8 for OpenCV
#     binary = (1 - np.array(grid, dtype=np.uint8)) * 255  # wall=0 → 255 (white), free=1 → 0 (black)
#     skeleton = skeletonize(binary).astype(np.uint8) * 255
#     # Find contours
#     contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

#     # Convert contours to list of points
#     contour_polygons = []
#     for cnt in contours:
#         points = [(int(p[0][0]), int(p[0][1])) for p in cnt]
#         contour_polygons.append(points)
        
#     print("contour_polygons", len(contour_polygons))
#     # plt.figure(figsize=(8, 8))
#     # plt.imshow(binary, cmap="gray")

#     # Plot each contour
#     for cnt in contours:
#         cnt = cnt.squeeze()  # remove redundant dimensions
#         if cnt.ndim == 2:
#             plt.plot(cnt[:, 0], cnt[:, 1], linewidth=2)

#     plt.title("Extracted Wall Contours")
#     plt.gca().invert_yaxis()  # Match OpenCV coordinate system
#     # plt.show()
#     plt.savefig("wall_contours.png", dpi=300)
    
#     return contour_polygons


# def runRVO(agent_paths, floorList, time_step=0.25, neighbor_dist=30.0, max_neighbors=10,
#            time_horizon=2.0, time_horizon_obst=1.0, radius=10, max_speed=8,
#            goal_tolerance= 15, target_tolerance=15):
#     """
#     Simulate agents using RVO2.

#     Arguments:
#         agent_paths: list of lists of (x, y) tuples
#                      Each list represents the funnel path of one agent.
#                      The first point is the start, the last point is the goal.
#         time_step: simulation step size
#         neighbor_dist: max distance to other agents considered neighbors
#         max_neighbors: max number of neighbors to consider
#         time_horizon: time horizon for agent-agent avoidance
#         time_horizon_obst: time horizon for obstacle avoidance
#         radius: agent radius
#         max_speed: agent max speed
#         goal_tolerance: distance within which agent is considered at goal
#         target_tolerance: distance within which agent is considered at current funnel point

#     Returns:
#         List of RVO paths, each a list of (x, y) positions per time step
#     """
    
    
    
     

#     sim = rvo2.PyRVOSimulator(time_step, neighbor_dist, max_neighbors,
#                               time_horizon, time_horizon_obst, radius, max_speed)
    
#     filled_map_lv1 = NAV_DATA["filled_map_lv1"]
#     minMaxXY_lv1 = NAV_DATA["minMaxXY_lv1"]
#     filled_map_lv2 = NAV_DATA["filled_map_lv2"]
#     minMaxXY_lv2 = NAV_DATA["minMaxXY_lv2"]
#     filled_map_lv3 = NAV_DATA["filled_map_lv3"]
#     minMaxXY_lv3 = NAV_DATA["minMaxXY_lv3"]
#     # filled_map = NAV_DATA["filled_map"]
#     # minMaxXY = NAV_DATA["minMaxXY"]
#     # contours = reduce_nodes_to_contours(filled_map)
#     # scale = 1.0
#     # for contour in contours:
#     #     obstacle = [(x * scale, y * scale) for (x, y) in contour]
#     #     sim.addObstacle(obstacle)
#     # sim.processObstacles()
#     # print("obstacles added")
    
#     # Convert filled_map walls into obstacle segments
#     # rows, cols = filled_map.shape
#     # cell_size = 0  # or your grid resolution
#     # for r in range(rows):
#     #     for c in range(cols):
#     #         if filled_map[r, c] == 0:  # wall
#     #             sim.addObstacle([
#     #                 (c, r),
#     #                 (c+cell_size, r),
#     #                 (c+cell_size, r+cell_size),
#     #                 (c, r+cell_size)
#     #             ])
                
#     #     print("done with row", r)
#     # sim.processObstacles()
#     # print("obstacles added")


#     # Initialize agents
#     agent_ids = []
#     for path in agent_paths:
#         agent_id = sim.addAgent(path[0])  # start position
#         agent_ids.append(agent_id)

#     # Goals for each agent
#     goals = [path[-1] for path in agent_paths]

#     # Copy paths so we can pop intermediate targets
#     paths = [path[1:] for path in agent_paths]  # exclude start

#     # Record RVO paths
#     rvo_paths = [[] for _ in agent_paths]

#     # Track which agents reached their goal
#     reached = [False] * len(agent_paths)
#     max_steps = 10000  # safety cap, adjust as needed
#     step_count = 0

#     while not all(reached) and step_count < max_steps:
#         step_count += 1
#         for i, agent_id in enumerate(agent_ids):
#             if reached[i]:
#                 sim.setAgentPrefVelocity(agent_id, (0, 0))
#                 sim.setAgentRadius(agent_id, 0.000)
#                 sim.setAgentPosition(agent_id, (1e9, 1e9))
#                 continue

#             pos = sim.getAgentPosition(agent_id)

#             # Determine next target
#             if paths[i]:
#                 target = paths[i][0]
#                 # Pop target if close enough
#                 if (pos[0]-target[0])**2 + (pos[1]-target[1])**2 < target_tolerance**2:
#                     paths[i].pop(0)
#                     target = paths[i][0] if paths[i] else goals[i]
#                  # --- NEW: skip forward if closer to next waypoint ---
#                 elif len(paths[i]) > 1:
#                     next_target = paths[i][1]
#                     dist_curr = (pos[0]-target[0])**2 + (pos[1]-target[1])**2
#                     dist_next = (pos[0]-next_target[0])**2 + (pos[1]-next_target[1])**2
#                     if dist_next < dist_curr:
#                         # Skip the current waypoint
#                         paths[i].pop(0)
#                         target = paths[i][0] if paths[i] else goals[i]
#             else:
#                 target = goals[i]

#             # Compute preferred velocity toward target
#             vel = (target[0]-pos[0], target[1]-pos[1])
#             dist = (vel[0]**2 + vel[1]**2)**0.5
#             if dist > 0:
#                 speed = min(dist, max_speed)  # don’t overshoot target
#                 vel = (vel[0]/dist*speed, vel[1]/dist*speed)
#             else:
#                 vel = (0, 0)
#             sim.setAgentPrefVelocity(agent_id, vel)


#         # Step simulation
#         sim.doStep()

#         # Record positions and check goal reached
#                 # Record positions and check goal reached
#         for i, agent_id in enumerate(agent_ids):
#             pos = sim.getAgentPosition(agent_id)

#             if not reached[i]:   # ✅ only record if not already at goal
#                 rvo_paths[i].append(pos)

#                 if ((pos[0]-goals[i][0])**2 + (pos[1]-goals[i][1])**2) < goal_tolerance**2:
#                     reached[i] = True
#                     sim.setAgentPrefVelocity(agent_id, (0, 0))
#                     sim.setAgentRadius(agent_id, 0.000)
#                     sim.setAgentPosition(agent_id, (1e9, 1e9))

#                     # ✅ make sure we store the goal once
#                     rvo_paths[i].append(pos)

                

#     if not all(reached):
#         print("Warning: Some agents did not reach their goals.")
        
#     # switch x and y of rvo paths
#     for i, path in enumerate(rvo_paths):
#         for j, pos in enumerate(path):
#             rvo_paths[i][j] = (pos[1], pos[0])
            
#     # turn rvo paths to utm
#     for i, path in enumerate(rvo_paths):
#         if floorList[i] == 2:
#             for j, pos in enumerate(path):
#                 rvo_paths[i][j] = from_grid_to_utm(pos[0], pos[1], minMaxXY_lv2)
#         elif floorList[i] == 3:
#             for j, pos in enumerate(path):
#                 rvo_paths[i][j] = from_grid_to_utm(pos[0], pos[1], minMaxXY_lv3)
#         else:
#             for j, pos in enumerate(path):
#                 rvo_paths[i][j] = from_grid_to_utm(pos[0], pos[1], minMaxXY_lv1)
#         # for j, pos in enumerate(path):
#         #     rvo_paths[i][j] = from_grid_to_utm(pos[0], pos[1], minMaxXY_lv1)
            
#     # turn rvo paths to wgs
#     for i, path in enumerate(rvo_paths):
#         for j, pos in enumerate(path):
#             rvo_paths[i][j] = from_utm_to_wgs(pos[0], pos[1])

#     # # add the z and the steps to all agents
#     # for i, path in enumerate(rvo_paths):
#     #     for j, pos in enumerate(path):
#     #         rvo_paths[i][j] = (pos[0], pos[1], agent_paths[i][j][2], j)
            
#     # add step to rvo paths
#     for i, path in enumerate(rvo_paths):
#         for j, pos in enumerate(path):
#             rvo_paths[i][j] = (pos[0], pos[1], j)
            
#     return rvo_paths


# # # Example usage
# # agent1 = [(821, 582), (772, 256)]
# # agent3 = [(772, 256), (821,582)]
# # agent2 = [(703, 593), (np.float64(756.5), np.float64(346.0)), (np.float64(756.0), np.float64(334.5)), (772, 256)]

# # agents = [agent1,agent2,agent3]

# # paths = runRVO(agents)
# # print(paths)


# # load map
# # filled_map = np.load("filled_grid.npy")  # 0 = obstacle, 1 = free space

# # plt.figure(figsize=(8, 8))

# # show filled map first
# # cmap 'gray_r': obstacle (0) = black, free (1) = white
# # plt.imshow(filled_map, cmap='gray_r', origin='lower')

# # overlay agent paths
# # for path in paths:
# #     path = np.array(path)
# #     plt.plot(path[:, 0], path[:, 1], marker='o', linewidth=2, markersize=4)

# # plt.title("Agent Paths on Filled Map")
# # plt.savefig("paths_on_map.png", dpi=300)
