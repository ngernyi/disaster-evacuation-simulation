from flask import Blueprint
from flask import session
from flask import jsonify
from flask import request
# from services.simulationService import create_custom_sim, save_evacuees, get_simulation_metadata, get_simulation_evacuees, save_hazards, get_simulation_hazards, save_route_point, get_evacuees_route, save_route_points_bulk, get_simulation_user_id, add_config_details, get_confid_id, get_config_details
from services.simulationService import *
from services.reportService import export_pdf, export_csv
from services.userManagementService import get_user_roles, get_user_data_by_id
from utils.pathFindingAlgo import dijkstra
from utils.AStarAlgo import A_star
from utils.pathFindingWithNodes import compute_path_in_skeleton_map
from utils.GridNavMeshPathFindingFunnel import navMeshPathWithFunnel
# from utils.navMeshPolygons import rectanglePathFindings
# from utils.rvoImplement import runRVO
from utils.hazardHandler import add_hazard_to_nav_mesh
from utils.multiFloorRVO import runMultiFloorRVO
from utils.mapConverter import *
from utils.RegenerateSim import regenerate_simulation
from config.db import get_connection
from flask import send_file
import time


sim_blueprint = Blueprint('sim', __name__)

# @sim_blueprint.before_request
# def require_login():
#     if 'user_info' not in session:
#         return jsonify({'error': 'Unauthorized'}), 401

@sim_blueprint.route('/create_session_sim', methods = ['POST'])
def create_session_sim_route():
    data = request.get_json()
    
    # get the required data
    user_id = session.get('user_info').get('id')
    simulation_name = data.get('simulationName')
    days  = data.get('days')
    sessionsss = data.get('sessions')
    
    simulation_ids = []
    
    # identify the high risk simulation
    evaluation_id = create_evaluation(simulation_name)
    high_risk = None
    max_duration = 99999999
    
    # save and get the simulation id
    for day in days: # for each day
        for sessionss in sessionsss: # for each session
            status = "Created"
            simulation_result = create_custom_sim(
                user_id,
                simulation_name + " " + day + " " + sessionss,
                status,
                evaluation_id= evaluation_id
            )
            simulation_id = simulation_result.get('simulation_id')
    
            # add the evacuees based on the days and sessions
            config_id = get_confid_id(day, sessionss)
            print("config id", config_id)
            # evacuees_list = data.get('evacuees', [])  
            evacuees_list = get_config_details(config_id)
            print("evacuees",evacuees_list)
            
            evacuees_with_ids = []
            if evacuees_list:
                evacuees_with_ids = save_evacuees(simulation_id, evacuees_list)
                
            # add the hazards
            hazards_list = data.get('hazards', [])  
            print(hazards_list)
            
            if hazards_list:
                save_hazards(simulation_id, hazards_list)
                
            computational_time_start = time.time()
            #  update the nav graph based on the hazards
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
            # calculation_start = time.time()
            #  calculate the routes
            for evacuee in evacuees_with_ids:
                evacuee_id = evacuee.get('evacuee_id')
                start = evacuee.get('longitude'), evacuee.get('latitude')
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
                
                

            full_routes = runMultiFloorRVO(routes, agent_status, graphList)
            
            # save computational time
            computational_time_end = time.time()
            save_computational_time(computational_time_end - computational_time_start, simulation_id)
            
            # save duration
            cur_max_duration = max([len(route) for route in full_routes])
            save_simulation_duration(cur_max_duration, simulation_id)
            
            if cur_max_duration < max_duration:
                max_duration = cur_max_duration
                high_risk = simulation_id
            # calculation_end = time.time()
            # print("calculation time taken", calculation_end - calculation_start)

            database_start = time.time()
            for evacuee in evacuees_with_ids:
                evacuee_id = evacuee.get('evacuee_id')
                points = [
   
                    (point[0], point[1], point[2], step_idx)
                    for step_idx, point in enumerate(full_routes[evacuees_with_ids.index(evacuee)])
                ]
                save_route_points_bulk(evacuee_id, points)
                print("done saving route points")

            
            # database_end = time.time()
            # print("database time taken", database_end - database_start)
            # print("total time taken", database_end - start_time)
    
    # save high risk session
    update_high_risk_simulation_id(evaluation_id, high_risk)
    
    return jsonify({'success': True})

@sim_blueprint.route('/create_custom_sim', methods = ['POST'])
def create_custom_sim_route():
    start_time = time.time()
    if 'user_info' not in session:
        print("User not logged in")
        return jsonify({"error": "User not logged in"}), 401
    
    print("User logged in from the create custom sim", session.get('user_info'))
    data = request.get_json()
    user_id = session.get('user_info').get('id')
    simulation_name = data.get('simulationName')
    status = "Created"
    
    simulation_result = create_custom_sim(
        user_id, 
        simulation_name, 
        status, 
        )
    
    # get simulation_id
    simulation_id = simulation_result.get('simulation_id')
    print("simulation_id from the create custom sim",simulation_id)
    
    # add the evacuees
    evacuees_list = data.get('evacuees', [])  
    print(evacuees_list)
    
    evacuees_with_ids = []
    if evacuees_list:
        evacuees_with_ids = save_evacuees(simulation_id, evacuees_list)
        
    # add the hazards
    hazards_list = data.get('hazards', [])  
    print(hazards_list)
    
    if hazards_list:
        save_hazards(simulation_id, hazards_list)
        
    computational_time_start = time.time()
    #  update the nav graph based on the hazards
    graphList = add_hazard_to_nav_mesh(hazards_list)
    
    # pre calculate the path from stair to the exit
    """
        newly added
    """
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
        start = evacuee.get('longitude'), evacuee.get('latitude')
        step = 0.05
        floor = 0
        if evacuee.get('z') < 3:
            floor = 1
        elif evacuee.get('z') <7 :
            floor = 2
        else :
            floor = 3
        # for hazard in hazards_list:
        #     wallPoints.append((hazard.get('longitude'), hazard.get('latitude')))


        # path, distance = dijkstra(wallPoints, start, goal, step)
        # path = compute_path_in_skeleton_map(start, goal, step)
        path, status = navMeshPathWithFunnel(start, graphList, floor, path_from_stair1_to_exit,  path_from_stair2_to_exit, step,)
        # path = navMeshPathWithFunnel(start, graphList, floor, step,)
        agent_status.append(status)
        # for p in path:
        #     print("path", p)
        routes.append(path)
        
        # print("path", path)
        # save the route points
        # for point in path:
        #     save_route_point(evacuee_id, point[0], point[1], 0, point[2], )

    # print("routes after funnel", routes)
    #  run the rvo2
    # full_routes = runRVO(routes, floorList)
    # full_routes = routes
    full_routes = runMultiFloorRVO(routes, agent_status, graphList) 
    computational_time_end = time.time()
    total_computational_time = computational_time_end - computational_time_start
    
    # save computational time
    print("simulation id",simulation_id, total_computational_time)
    save_computational_time(total_computational_time, simulation_id)
    
    # save duration
    max_duration = max([len(route) for route in full_routes])
    save_simulation_duration(max_duration, simulation_id)
    
    print("done rvo")
    for route in full_routes:
        print("route", len(route))
        print("last step", route[-1])
        
        # print("path ", route)
        
    for idx, route in enumerate(full_routes):
        if len(route) == 0:
            print(f"⚠️ route {idx} is empty")
        else:
            print(f"route {idx} length = {len(route)}, last step = {route[-1]}, first step = {route[0]}")

    # print("full_routes", full_routes)
    
    calculation_end = time.time()
    print("calculation time taken", calculation_end - calculation_start)
    # save the computed routes
    # for evacuee in evacuees_with_ids:
    #     evacuee_id = evacuee.get('evacuee_id')
    #     for point in full_routes[evacuees_with_ids.index(evacuee)]:
    #         save_route_point(evacuee_id, point[0], point[1], 0, point[2], )
    database_start = time.time()
    for evacuee in evacuees_with_ids:
        evacuee_id = evacuee.get('evacuee_id')
        points = [
            # (point[0], point[1], evacuee.get('z'), point[2])  # (lon, lat, z, step_order)
            # (point[0], point[1], point[2], point[3])
            (point[0], point[1], point[2], step_idx)
            for step_idx, point in enumerate(full_routes[evacuees_with_ids.index(evacuee)])
            # for point in full_routes[evacuees_with_ids.index(evacuee)]
        ]
        save_route_points_bulk(evacuee_id, points)
        print("done saving route points")

       
    database_end = time.time()
    print("database time taken", database_end - database_start)
    print("total time taken", database_end - start_time)
    # return the simulation result
    
    return jsonify(simulation_result)

@sim_blueprint.route('/add_dynamic_hazards', methods = ['POST'])
def add_dynamic_hazards_route():
    data = request.get_json()
    simulation_id = data.get('simulationId')
    current_step = data.get('currentStep')
    hazard_type = data.get('hazardType')
    hazard_position = data.get('hazardPosition')
    
    print("add_dynamic_hazards", simulation_id, current_step, hazard_type, hazard_position)

    if simulation_id is None or current_step is None or hazard_type is None or hazard_position is None:
        return jsonify({'success': False, 'message': 'Missing simulation ID, current step, hazard type or hazard position'}), 400

    regenerate_simulation(simulation_id, current_step, hazard_type, hazard_position)
    return jsonify({'success': True})
    # try:
    #     regenerate_simulation(simulation_id, current_step, hazard_type, hazard_position)
    #     print("done regenerating simulation")
    #     return jsonify({'success': True})
    # except Exception as e:
    #     print(e)
    #     traceback.print_exc()
    #     return jsonify({'success': False,'message': 'Database error'}), 500

@sim_blueprint.route('/get_user_simulations', methods = ['GET'])
def get_user_simulations_route():
    
    # if session == None:
    #     return jsonify({'error': 'Please log in to view simulations'}), 401
    
    user_info = session.get('user_info')
    # if not user_info:
    #     # User is not logged in
    #     return jsonify({'error': 'Please log in to view simulations'}), 401
    
    # get user id
    current_user_id = session.get('user_info').get('id')
    user_id = request.args.get('user_id')
    
    if get_user_roles(current_user_id).rstrip()!= "Admin" and user_id != current_user_id:
        return jsonify({'success': False,'message': 'Not authorized'}), 403
    
    if user_id is None:
        user_id = current_user_id
        
    # Get user data
    user_data = get_user_data_by_id(user_id)
    print("user data", user_data)
        
    # set connection
    conn = get_connection()
    cursor = conn.cursor()
    
    # query to get user simulations
    query = "SELECT * FROM Simulation WHERE User_Id = ?"
    cursor.execute(query, (user_id,))
    rows = cursor.fetchall()
    
    simulations = []
    for row in rows:
        simulations.append({
            'Simulation_Id': row.Simulation_Id,
            'Simulation_Name': row.Simulation_Name,
            'Created_At': str(row.Created_At),
            'Status': row.Status,
            'Computational_Time': row.Computational_Time,
            'Evaluation_Id': row.Evaluation_Id,
            'Duration':row.Duration,
        })

    return jsonify({'simulations': simulations, 'user_data': user_data})
   
@sim_blueprint.route('/delete_simulation', methods=['POST'])
def delete_simulation_route():
    data = request.get_json()
    simulation_id = data.get('simulation_id')

    if not simulation_id:
        return jsonify({'success': False, 'message': 'Missing simulation ID'}), 400

    try:
        conn = get_connection() 
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Simulation WHERE Simulation_Id = ?', (simulation_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': 'Database error'}), 500

@sim_blueprint.route('/rename_simulation', methods=['POST'])
def rename_simulation_route():
    data = request.get_json()
    simulation_id = data.get('simulation_id')
    new_name = data.get('new_name')

    if not simulation_id or not new_name:
        return jsonify({'success': False,'message': 'Missing simulation ID or new name'}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE Simulation SET Simulation_Name =? WHERE Simulation_Id =?', (new_name, simulation_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        print(e)
        return jsonify({'success': False,'message': 'Database error'}), 500
    
import traceback

@sim_blueprint.route('/export_pdf')
def export_pdf_route():
    try:
        simulation_id = request.args.get('simulation_id', type=int)
        
        # Call the function
        pdf_buffer = export_pdf(simulation_id)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'Report_{simulation_id}.pdf'
        )
    except Exception as e:
        # This will catch the EXACT error and print it to your screen
        error_info = traceback.format_exc()
        return f"<h1>Debug Error Info:</h1><pre>{error_info}</pre>", 500
    
@sim_blueprint.route('/export_csv', methods=['GET'])
def export_csv_route():
    simulation_id = request.args.get('simulation_id') 
    csv_buffer = export_csv(simulation_id)
    
    
    # send_file properly handles in-memory file responses
    return send_file(
        csv_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='simulation_report.pdf'  # For Flask 2.x
    )

@sim_blueprint.route('/get_simulation_data', methods=['GET'])
def get_simulation_data_route():
    simulation_id = request.args.get('simulation_id', type=int)
    print("sim id from get simulation", simulation_id)
    
    # 1. Get standard metadata
    simulation_metadata = get_simulation_metadata(simulation_id)
    evacuees = get_simulation_evacuees(simulation_id)
    hazards = get_simulation_hazards(simulation_id)

    # 2. Get ALL routes in ONE trip to the database
    all_routes_data = get_all_evacuee_routes_batch(simulation_id)

    # 3. Match the routes to the evacuees list to maintain your exact return format
    evacuees_routes = []
    for evacuee in evacuees:
        evac_id = evacuee.get('Evacuee_Id')
        # Get the route from our pre-fetched dictionary (Lightning fast RAM access)
        route_data = all_routes_data.get(evac_id)
        if route_data:
            evacuees_routes.append(route_data)
        else:
            # Maintain consistency even if an evacuee has no route
            evacuees_routes.append({'route': []})

    return jsonify({
        'success': True,
        'simulation_metadata': simulation_metadata,
        'evacuees': evacuees,
        'hazards': hazards,
        'evacuees_routes': evacuees_routes
    })
    
# @sim_blueprint.route('/get_simulation_data', methods=['GET'])
# def get_simulation_data_route():
#     simulation_id = request.args.get('simulation_id', type=int)
#     print("sim id from get simulation", simulation_id)
#     simulation_metadata = get_simulation_metadata(simulation_id)
#     evacuees = get_simulation_evacuees(simulation_id)
#     hazards = get_simulation_hazards(simulation_id)

#     # print("evacuees", evacuees)
#     evacuees_routes = []
#     for evacuee in evacuees:
#         evacuee_id = evacuee.get('Evacuee_Id')
#         evacuee_route = get_evacuees_route(evacuee_id)
#         if evacuee_route:
#             evacuees_routes.append(evacuee_route)

    
#     return jsonify({
#         'success': True,
#         'simulation_metadata': simulation_metadata,
#         'evacuees': evacuees,
#         'hazards': hazards,
#         'evacuees_routes': evacuees_routes
#     })
    

@sim_blueprint.route('/get_simulation_user_id', methods=['GET'])
def get_simulation_user_id_route():
    simulation_id = request.args.get('simulation_id', type=int)
    
    user_id = get_simulation_user_id(simulation_id)
    return jsonify({'user_id': user_id})
    
    
@sim_blueprint.route('/create_config', methods=['POST'])
def create_config_route():
    data = request.get_json()
    evacuees = data.get('evacuees')
    days = data.get('days')
    sessions = data.get('sessions')
    print("days", days)
    print("sessions", sessions)
    
    for day in days:
        for session in sessions:
                
            config_id = get_confid_id(day, session)
            print("config id", config_id)
            print("evacuees", evacuees)
            
            for evacuee in evacuees:
                add_config_details(config_id, evacuee['longitude'], evacuee['latitude'], evacuee['z'])
    
    return jsonify({'success': True})
