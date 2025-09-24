from flask import Blueprint
from flask import session
from flask import jsonify
from flask import request
from services.simulationService import create_custom_sim, save_evacuees, get_simulation_metadata, get_simulation_evacuees, save_hazards, get_simulation_hazards, save_route_point, get_evacuees_route, save_route_points_bulk
from services.reportService import export_pdf, export_csv
from utils.pathFindingAlgo import dijkstra
from utils.AStarAlgo import A_star
from utils.pathFindingWithNodes import compute_path_in_skeleton_map
from utils.GridNavMeshPathFindingFunnel import navMeshPathWithFunnel
# from utils.navMeshPolygons import rectanglePathFindings
from utils.rvoImplement import runRVO
from utils.hazardHandler import add_hazard_to_nav_mesh
from config.db import get_connection
from flask import send_file
import time


sim_blueprint = Blueprint('sim', __name__)

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
        
    #  update the nav graph based on the hazards
    graphList = add_hazard_to_nav_mesh(hazards_list)
    
    # pre calculate the goal points from higher levels to lower levels
        
    # create a list to store the routes
    routes = []
    floorList = []
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
        wallPoints = []
        # for hazard in hazards_list:
        #     wallPoints.append((hazard.get('longitude'), hazard.get('latitude')))


        # path, distance = dijkstra(wallPoints, start, goal, step)
        # path = compute_path_in_skeleton_map(start, goal, step)
        path = navMeshPathWithFunnel(start, graphList, floor, step, )
        floorList.append(floor)
        routes.append(path)
        
        # print("path", path)
        # save the route points
        # for point in path:
        #     save_route_point(evacuee_id, point[0], point[1], 0, point[2], )

    # print("routes after funnel", routes)
    #  run the rvo2
    full_routes = runRVO(routes, floorList)
    print("done rvo")
    for route in full_routes:
        print("route", len(route))
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
            (point[0], point[1], evacuee.get('z'), point[2])  # (lon, lat, z, step_order)
            for point in full_routes[evacuees_with_ids.index(evacuee)]
        ]
        save_route_points_bulk(evacuee_id, points)
        print("done saving route points")

       
    database_end = time.time()
    print("database time taken", database_end - database_start)
    print("total time taken", database_end - start_time)
    # return the simulation result
    
    return jsonify(simulation_result)

@sim_blueprint.route('/get_user_simulations', methods = ['GET'])
def get_user_simulations_route():
    # get user id
    user_id = session.get('user_info').get('id')
    
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
        })

    return jsonify({'simulations': simulations})
   
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
    
@sim_blueprint.route('/export_pdf', methods=['GET','POST'])
def export_pdf_route():
    pdf_buffer = export_pdf()
    
    # send_file properly handles in-memory file responses
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='simulation_report.pdf'  # For Flask 2.x
    )
    
@sim_blueprint.route('/export_csv', methods=['GET','POST'])
def export_csv_route():
    csv_buffer = export_csv()
    
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
    simulation_metadata = get_simulation_metadata(simulation_id)
    evacuees = get_simulation_evacuees(simulation_id)
    hazards = get_simulation_hazards(simulation_id)

    # print("evacuees", evacuees)
    evacuees_routes = []
    for evacuee in evacuees:
        evacuee_id = evacuee.get('Evacuee_Id')
        evacuee_route = get_evacuees_route(evacuee_id)
        if evacuee_route:
            evacuees_routes.append(evacuee_route)

    
    return jsonify({
        'success': True,
        'simulation_metadata': simulation_metadata,
        'evacuees': evacuees,
        'hazards': hazards,
        'evacuees_routes': evacuees_routes
    })


    