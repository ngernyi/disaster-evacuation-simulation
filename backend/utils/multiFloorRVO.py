import pyrvo 
from utils.mapConverter import *
from utils.nav_loader import NAV_DATA
import os
from utils.GridNavMeshPathFindingFunnel import *
import heapq

def smallAreaAStar(grid, start, goal):
    """
    A* pathfinding in a grid map.
    
    grid: 2D list/array, 0 = wall, 1 = free
    start: (row, col)
    goal: (row, col)
    return: list of ((dx, dy), steps)
            e.g. [((0,-1), 3), ((-1,0), 2)] means
            "move left 3 steps, then up 2 steps"
    """
    rows, cols = len(grid), len(grid[0])

    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def in_bounds(x, y):
        return 0 <= x < rows and 0 <= y < cols

    def neighbors(node):
        x, y = node
        for dx, dy in [(1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,1), (1,-1), (-1,-1)]:  # 8 directions
            nx, ny = x + dx, y + dy
            if in_bounds(nx, ny) and grid[int(nx)][int(ny)] == 1:
                yield (nx, ny)

    open_set = []
    heapq.heappush(open_set, (heuristic(start, goal), 0, start, None))
    came_from = {}
    g_score = {start: 0}

    while open_set:
        _, cost, current, parent = heapq.heappop(open_set)

        if current in came_from:
            continue
        came_from[current] = parent

        if current == goal:
            # reconstruct path
            path = []
            while current is not None:
                path.append(current)
                current = came_from[current]
            path = path[::-1]  # reverse

            # compress into directions
            directions = []
            if len(path) > 1:
                prev = path[0]
                dir_vec = (path[1][0] - prev[0], path[1][1] - prev[1])
                steps = 1
                for i in range(2, len(path)):
                    cur = path[i]
                    new_dir = (cur[0] - prev[0], cur[1] - prev[1])
                    if new_dir == dir_vec:
                        steps += 1
                    else:
                        directions.append((dir_vec, steps))
                        dir_vec = new_dir
                        steps = 1
                    prev = cur
                directions.append((dir_vec, steps))
            return directions

        for nxt in neighbors(current):
            new_cost = cost + 1
            if nxt not in g_score or new_cost < g_score[nxt]:
                g_score[nxt] = new_cost
                priority = new_cost + heuristic(nxt, goal)
                heapq.heappush(open_set, (priority, new_cost, nxt, current))

    return None  # no path found


    

                
# def runMultiFloorRVO(agent_paths, agent_status, graphList, time_step=0.25, neighbor_dist=30.0, max_neighbors=10,
#            time_horizon=2.0, time_horizon_obst=1.0, radius=10, max_speed=8,
#            goal_tolerance=15, target_tolerance=15):
    
def runMultiFloorRVO(agent_paths, agent_status, graphList, 
           time_step=0.25, 
           neighbor_dist=16.0,      # 5
           max_neighbors=10,        # 10
           time_horizon=2.0, 
           time_horizon_obst=1.0,  
           radius=8,              # 5
           max_speed=8,             # 8
           goal_tolerance=16.0,      # 8
           target_tolerance=16.0):   # 8

    # Create sims
    sim_floor1 = pyrvo.RVOSimulator(time_step, neighbor_dist, max_neighbors, time_horizon, time_horizon_obst, radius, max_speed)
    sim_floor2 = pyrvo.RVOSimulator(time_step, neighbor_dist, max_neighbors, time_horizon, time_horizon_obst, radius, max_speed)
    sim_floor3 = pyrvo.RVOSimulator(time_step, neighbor_dist, max_neighbors, time_horizon, time_horizon_obst, radius, max_speed)
    sims = {1: sim_floor1, 2: sim_floor2, 3: sim_floor3}
    
    # # add the walls to the simulation
    # grid = NAV_DATA["filled_map_lv3"]
    
    # rows, cols = grid.shape
    # # Convert grid to uint8 for OpenCV
    # grid_img = (1 - grid).astype(np.uint8) * 255  # now walls=255, free=0

    # kernel = np.ones((3, 3), np.uint8)  # you can try (2,2), (3,3), (5,5)
    # eroded = cv2.erode(grid_img, kernel, iterations=5)
    
    # # Find contours (boundaries of obstacles)
    # contours, _ = cv2.findContours(grid_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    # # And ensure counter-clockwise ordering for each contour    
    
    # for contour in contours:
    #     obstacle = []
    #     for point in contour:
    #         x, y = point[0]  # (col, row)
    #         # Scale if needed (depends on your map scale)
    #         obstacle.append((float(x), float(y)))
    #     # Add obstacle as a polyline
    #     sim_floor3.addObstacle(obstacle)

    # sim_floor3.processObstacles()
    
    # DEBUG PRINT
    # Check if the checkpoint is a wall
    # for i in range(len(agent_paths)):
    #     print("agent ",i)
    #     for j in range(len(agent_paths[i])):
    #         print("Checkpoint ", j, "", agent_paths[i][j], "", grid[int(agent_paths[i][j][0]), int(agent_paths[i][j][1])])


    # maps for conversions
    minMax = {
        1: NAV_DATA["minMaxXY_lv1"],
        2: NAV_DATA["minMaxXY_lv2"],
        3: NAV_DATA["minMaxXY_lv3"]
    }

    

    n_agents = len(agent_paths)
    agent_ids = [None] * n_agents
    agent_sims = [None] * n_agents
    goals = [None] * n_agents
    paths = [[] for _ in range(n_agents)]
    rvo_paths = [[] for _ in range(n_agents)]
    reached_goal = [False] * n_agents
    in_stair = [False] * n_agents
    path_progress = [0] * n_agents

    # Helper: to get the status of agent based on step
    def get_status_by_step(i, step_num):
        if i >= len(agent_status):  # check index bounds
            return False
        
        s = agent_status[i]
        for status in s:
            if status[0] == step_num:
                return status[1]
        return False
   
    def z_to_floor(z):
        if z > 7:
            return 3
        elif z > 3:
            return 2
        else:
            return 1
        
    """
        Initialisation of agents
        1) get the start floor of the agent (to know which simulation to put)
        2) get the initial position of the agent (to put as the start point)
        3) get the path/waypoints of the agent for the current floor (check with the status)
        4) get the goal of the agent for the current floor (check with the status)
    """
    for i, path in enumerate(agent_paths):
        
        # get the start floor of the agent
        floor = get_status_by_step(i, 0)
        
        # get the simulation to put the agent
        sim = sims[floor]
        
        # add the agent into the simulation by getting the initial position of the agent
        # assign the added agent to the ids
        agent_ids[i] = sim.add_agent((path[0][0], path[0][1]))
        agent_sims[i] = sim
        
        # # add the goal and waypoints
        # waypoints = []
        
        # current_index = 1
        # # if the current index is not a check point
        # while get_status_by_step(i, current_index) == False:
        #     waypoints.append((path[current_index][0], path[current_index][1]))
        #     current_index += 1
        
        # # add the goal (one step befrore the check point)
        # goals[i] = (path[current_index-1][0], path[current_index-1][1])
        
        # # add the waypoints (remove the last step)
        # paths[i] = waypoints[:-1]
        
    """
        Loops to run RVO
        1) initialise the maximum number of steps and the current step
        2) loop until all agents reach the goal or the maximum number of steps is reached
        
    """
    
    # debug print
    # for i in range(len(agent_status)):
    #     print("agent ", i , "status ", agent_status[i])
    
    # initialise the maximum number of steps and the current step
    max_steps = 2500
    step_count = 0
    while step_count < max_steps and not all(reached_goal):
        # debug print
        # if step_count % 100 == 0:
        #     print(step_count)
        #     for i in range(n_agents):
        #         if path_progress[i] >= len(agent_paths[i]) - 1:
        #             continue
        #         print("agent ", i, " path progress ", path_progress[i], " location ", agent_paths[i][path_progress[i]], " next target ", agent_paths[i][path_progress[i]+1] , )
            
        step_count += 1
        """
            Get the velocity of the agent
            1) Check if the agent has completed the path
                a) remove the agent from the simulation
                b) mark the agent as reached the goal
            2) Check if the agent is in a stair
                a) remove the agent from the simulation
                b) mark the agent as in a stair
            3) Get the position of the agent (first get the simulation, and then get the position)
            4) Get the target of the agent
                a) if the agent is more near the next target, set the target to the next target instead
                b) else set the target to the current target
            5) Set the velocity of the agent    
            
                  
        """
        
        for i in range(n_agents):
            # check if the agent has completed the path or reached goal
            if path_progress[i] >= len(agent_paths[i]) or reached_goal[i]:
                reached_goal[i] = True
                if agent_sims[i] is not None and agent_ids[i] is not None:
                    s = agent_sims[i]
                    s.set_agent_pref_velocity(agent_ids[i], (0, 0))
                    s.set_agent_radius(agent_ids[i], 0.0)
                    s.set_agent_position(agent_ids[i], (1e9, 1e9))
                    agent_sims[i] = None
                    agent_ids[i] = None
                continue
            
            # check if the agent is in a stair
            if in_stair[i]:
                # s = agent_sims[i]
                # s.set_agent_pref_velocity(agent_ids[i], (0, 0))
                # s.set_agent_radius(agent_ids[i], 0.0)
                # s.set_agent_position(agent_ids[i], (1e9, 1e9))
                # agent_sims[i] = None
                # agent_ids[i] = None
                continue
            
            simulation = agent_sims[i]
            if simulation is None or agent_ids[i] is None:
                print("Simulation is None for agent", i," in step", path_progress[i])
                continue
            
            # get the position of the agent
            pos = simulation.get_agent_position(agent_ids[i])
            
            # get the target of the agent
            target = agent_paths[i][path_progress[i]]
            
            
            
            
            
            # if step_count % 100 == 0:
                
            #     print("before change agent ", i, " location ", pos, " target ", target, " dist ", dist)

            #     if rvo_paths[i][len(rvo_paths[i])-2][:3] == rvo_paths[i][len(rvo_paths[i])-1][:3]  == rvo_paths[i][len(rvo_paths[i])-3][:3] :
                    
            #         filled_map = NAV_DATA["filled_map_lv3"]
            #         minMaxXY = NAV_DATA["minMaxXY_lv3"]
            #         centroids = NAV_DATA["centroids_lv3"]
            #         points = NAV_DATA["points_lv3"]
            #         tri = NAV_DATA["tri_lv3"]
            #         graph = graphList[2]
            #         target_list = [target[:2]]
                    
            #         path_triangles, path_coords = a_star_search(pos, target_list, points, tri, graphList[2], centroids, filled_map)
            #         if not path_triangles or not path_coords:
        
            #             path_triangles, path_coords = a_star_with_retry(
            #                 pos, target_list, points, tri, graph, centroids, filled_map
            #             )
            #         funnel_coords = funnel_path_github_adapted(points, tri.simplices, path_triangles, pos, path_coords[-1])

            #         print("A star refinement ", funnel_coords)
                    
            #         target = funnel_coords[1]
            #         print("after change agent ", i, " location ", pos, " target ", target, " dist ", dist)

                        
                            
            # set the velocity of the agent
            vx = target[0] - pos.x
            vy = target[1] - pos.y
            dist = (vx*vx + vy*vy)**0.5

            if dist > 0:
                speed = min(dist, max_speed)
                vel = (vx / dist * speed, vy / dist * speed)
            else:
                vel = (0.0, 0.0)
                
            

            simulation.set_agent_pref_velocity(agent_ids[i], vel)
            
        
        """
            Run Simulation
        """
        sim_floor1.do_step()
        sim_floor2.do_step()
        sim_floor3.do_step()
            
        """
            Record the position of the agents
            1) Check if the agent has completed the path
                a) No need to record the position
            2) Check if the agent is in a stair
                a) record the position based on the agent_path and path_progress
            3) Get the position of the agent (first get the simulation, and then get the position)
            4) Record the position of the agent
        """ 
        for i in range(n_agents):
            # check if the agent has completed the path or reached goal
            if path_progress[i] >= len(agent_paths[i]) or reached_goal[i]:
                continue
            
            # check if the agent is in a stair
            if in_stair[i]:
                # get the position of the agent in agent path
                # pos = [x,y,z]
                pos = agent_paths[i][path_progress[i]] 
                
                # get the floor of the agent
                floor_for_conv = z_to_floor(pos[2])

                # convert the position to utm and wgs
                pos_in_utm = from_grid_to_utm(pos[1], pos[0], minMax[floor_for_conv])
                pos_in_wgs = from_utm_to_wgs(pos_in_utm[0], pos_in_utm[1])
                
                # record the position of the agent in rvo path
                rvo_paths[i].append((pos_in_wgs[0], pos_in_wgs[1], pos[2], step_count))
                
            else:
                simulation = agent_sims[i]
            
                # get the position of the agent
                # pos = [x,y]
                pos = simulation.get_agent_position(agent_ids[i])
                
                # get the z coordinate of the agent
                # pos = [x,y,z]
                if simulation == sim_floor1:
                    # pos = [pos[0], pos[1], agent_paths[i][path_progress[i]][2]]
                    pos_in_utm = from_grid_to_utm(pos.y, pos.x, minMax[1])
                elif simulation == sim_floor2:
                    # pos = [pos[0], pos[1], agent_paths[i][path_progress[i]][2]]
                    pos_in_utm = from_grid_to_utm(pos.y, pos.x, minMax[2])
                elif simulation == sim_floor3:
                    # pos = [pos[0], pos[1], agent_paths[i][path_progress[i]][2]]
                    pos_in_utm = from_grid_to_utm(pos.y, pos.x, minMax[3])
            
                # record the position of the agent in rvo path
                pos_in_wgs = from_utm_to_wgs(pos_in_utm[0], pos_in_utm[1])
                z_val = agent_paths[i][path_progress[i]][2]
                rvo_paths[i].append((pos_in_wgs[0], pos_in_wgs[1], z_val, step_count))
                
        """
            Update the path progress
            1) Check if the agent has completed the path
                a) No need to update the path progress  
            2) Check if the agent is in a stair
                a) increase the path progress by 1 (no need to check whether it reach the target or not)
            3) Check if the agent is not in a stair
                a) Check if the agent has reached the target
                    i) If the agent has reached the target, increase the path progress by 1
              
            Update the simulation and stairs      
            1) Check if the agent reached the next status check point
                a) If the agent is reaching a stair
                    i) Set in stair as true
                    ii) Remove the agent from the simulation
                b) If the agent is reaching a floor
                    i) Set in stair as false
                    ii) Add the agent to the simulation
                    iii) Set new goal and path for the agent
                
        """

        for i in range(n_agents):
            # check if the agent has completed the path or reached goal
            if path_progress[i] >= len(agent_paths[i]) or reached_goal[i]:
                continue

            # check if the agent is in a stair
            if in_stair[i]:
                # increase the path progress by 1
                path_progress[i] += 1
            else:
                pos = agent_sims[i].get_agent_position(agent_ids[i])
                distance = ((pos.x - agent_paths[i][path_progress[i]][0])**2 + (pos.y - agent_paths[i][path_progress[i]][1])**2)
                
                # debug print
                # if step_count % 100 == 0:
                #     print("agent ", i, " distance ", distance)
                    
                # check if the agent has reached the target
                if distance < target_tolerance**2:
                    # increase the path progress by 1
                    path_progress[i] += 1
                    
            # update the simulation and stairs
            # check if the agent reached the next status check point
            if get_status_by_step(i, path_progress[i]) != False:
                # if the agent is reaching a stair
                if get_status_by_step(i, path_progress[i]) == 1.5 or get_status_by_step(i, path_progress[i]) == 2.5:
                    in_stair[i] = True
                    if agent_sims[i] is not None and agent_ids[i] is not None:
                        s = agent_sims[i]
                        s.set_agent_pref_velocity(agent_ids[i], (0, 0))
                        s.set_agent_radius(agent_ids[i], 0.0)
                        s.set_agent_position(agent_ids[i], (1e9, 1e9))
                        agent_sims[i] = None
                        agent_ids[i] = None

                # if the agent has completed the path
                elif get_status_by_step(i, path_progress[i]) == -1:
                    reached_goal[i] = True
                    ### FIXED BLOCK START ###
                    if agent_sims[i] is not None and agent_ids[i] is not None:
                        s = agent_sims[i]
                        s.set_agent_pref_velocity(agent_ids[i], (0, 0))
                        s.set_agent_radius(agent_ids[i], 0.0)
                        s.set_agent_position(agent_ids[i], (1e9, 1e9))
                        agent_sims[i] = None
                        agent_ids[i] = None
                    ### FIXED BLOCK END ###

                # if the agent is reaching a floor
                else:
                    in_stair[i] = False
                    floor = get_status_by_step(i, path_progress[i])
                    sim = sims[floor]
                    agent_ids[i] = sim.add_agent((agent_paths[i][path_progress[i]][0], agent_paths[i][path_progress[i]][1]))
                    agent_sims[i] = sim
                    
    print("rvo path length", len(rvo_paths))
    return rvo_paths


            
            
    
            
        
            
            
    
   