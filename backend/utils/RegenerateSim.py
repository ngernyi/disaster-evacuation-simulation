from services.simulationService import *
from utils.hazardHandler import *
from utils.GridNavMeshPathFindingFunnel import *
from utils.multiFloorRVO import *

def regenerate_simulation(simulation_id, current_step, hazard_type, hazard_position):
    
    """
        Get the evacuees and hazards position at the current step
    """
    # Get the list of evacuees id of the simulation
    simulation_evacuees = get_simulation_evacuees(simulation_id)
    evacuees_id_list = []
    for evacuee in simulation_evacuees:
        evacuees_id_list.append(evacuee.get('Evacuee_Id'))
    
    # Get the list of evacuees position at the current step
    evacuees_position_list = []
    for evacuee_id in evacuees_id_list:
        current_evacuees = get_evacuees_position(evacuee_id, current_step)
        if current_evacuees is None:
            evacuees_position_list.append(None)
        else :
            evacuees_position_list.append(get_evacuees_position(evacuee_id, current_step))   
    
    # Merge the evacuees id and position
    evacuees_with_ids = []
    for i in range(len(evacuees_id_list)):
        if evacuees_position_list[i] is None:
            continue
        evacuees_with_ids.append({'evacuee_id': evacuees_id_list[i], 'longitude': evacuees_position_list[i][0], 'latitude': evacuees_position_list[i][1], 'z': evacuees_position_list[i][2]})
        
    print("evacuees with ids", evacuees_with_ids)
    # Get the list of hazards id of the simulation
    hazards_list_from_db = get_simulation_hazards(simulation_id)
    print("hazards from db", hazards_list_from_db)
    hazards_list = []
    for hazard in hazards_list_from_db:
        hazards_list.append({
            'hazard_type': hazard.get('Hazard_Type'),
            'latitude': hazard.get('Latitude'),
            'longitude': hazard.get('Longitude'),
            'z': hazard.get('Z'),
            'step_order' : hazard.get('Step_Order')
        })
    
    # Add the new hazard to the list of hazards
    hazards_list.append({
        'hazard_type': hazard_type,
        'latitude': hazard_position['latitude'],
        'longitude': hazard_position['longitude'],
        'z': hazard_position['z'],
        'step_order' : current_step
    })

    
    """
        Calculation of the new path for the evacuees
    """
    # Update the nav graph based on the hazards
    graphList = add_hazard_to_nav_mesh(hazards_list)
    
    # pre calculate the path from stair to the exit
    stair1 = -117.19603379555, 34.05624942388
    stair2 = -117.195333804329, 34.055954726546
    
    path_from_stair1_to_exit, path_1_status = navMeshPathWithFunnel(stair1, graphList, 1, 0.05, )
    path_from_stair2_to_exit, path_2_status = navMeshPathWithFunnel(stair2, graphList, 1, 0.05, )
    print("first and last step of path 1", path_from_stair1_to_exit[0], path_from_stair1_to_exit[-1])
    print("first and last step of path 2", path_from_stair2_to_exit[0], path_from_stair2_to_exit[-1])
    print("stair 1", path_from_stair1_to_exit)
    print("stair 2", path_from_stair2_to_exit)
    
     # create a list to store the routes
    routes = []
    agent_status = []
    calculation_start = time.time()
    #  calculate the routes
    for evacuee in evacuees_with_ids:
        evacuee_id = evacuee.get('evacuee_id')
        start = evacuee.get('latitude'), evacuee.get('longitude')
        print("start and id", start, evacuee_id, evacuee.get('z'))
        step = 0.05
        floor = 0
        if evacuee.get('z') < 3:
            floor = 1
        elif evacuee.get('z') <7 :
            floor = 2
        else :
            floor = 3
        
        path, status = navMeshPathWithFunnel(start, graphList, floor, path_from_stair1_to_exit,  path_from_stair2_to_exit, step,)
        agent_status.append(status)
       
        routes.append(path)
        
    # RVO
    full_routes = runMultiFloorRVO(routes, agent_status, graphList)
    calculation_end = time.time()
    print("calculation time", calculation_end - calculation_start)
    
    """
        Database update
    """
    
    # delete the steps that are not relevant any more
    for evacuee in evacuees_with_ids:
        remove_route_points(evacuee.get('evacuee_id'), current_step)
    
    # add the new steps to the database
    for evacuee in evacuees_with_ids:
        evacuee_id = evacuee.get('evacuee_id')
        points = [

            (point[0], point[1], point[2], step_idx)
            for step_idx, point in enumerate(full_routes[evacuees_with_ids.index(evacuee)], start=current_step + 1)
            # for point in full_routes[evacuees_with_ids.index(evacuee)]
        ]
        save_route_points_bulk(evacuee_id, points)
        print("done saving route points from ", current_step+1)
    
    # add the hazards
    hazard_to_add = []
    hazard_to_add.append({
        'hazard_type': hazard_type,
        'latitude': hazard_position['latitude'],
        'longitude': hazard_position['longitude'],
        'z': hazard_position['z'],
        'step_order' : current_step
    })
    save_hazards(simulation_id, hazard_to_add)
    
    # update the simulation details
    
    return True