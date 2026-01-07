from config.db import get_connection
from datetime import datetime

def get_export_stats_batch(simulation_ids):
    if not simulation_ids:
        return {}
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Use tuple for the IN clause
    placeholders = ','.join(['?'] * len(simulation_ids))
    query = f"""
        SELECT 
            s.Simulation_Id,
            (SELECT COUNT(*) FROM Evacuees WHERE Simulation_Id = s.Simulation_Id) as EvacCount,
            (SELECT COUNT(*) FROM Hazards WHERE Simulation_Id = s.Simulation_Id) as HazCount,
            (SELECT MAX(Step_Order) FROM ROUTE_POINT rp 
             JOIN Evacuees e ON rp.Evacuee_Id = e.evacuee_id 
             WHERE e.simulation_id = s.Simulation_Id) as MaxSteps
        FROM Simulation s
        WHERE s.Simulation_Id IN ({placeholders})
    """
    
    try:
        cursor.execute(query, tuple(simulation_ids))
        rows = cursor.fetchall()
        
        stats_map = {}
        for r in rows:
            # Using index [0], [1] is safer across different ODBC drivers
            sim_id = r[0]
            stats_map[sim_id] = {
                'evacuees': r[1] if r[1] else 0,
                'hazards': r[2] if r[2] else 0,
                'duration': (r[3] if r[3] else 0) / 50
            }
        return stats_map
    except Exception as e:
        print(f"DATABASE ERROR IN BATCH STATS: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()
        
def get_batch_simulation_stats(evaluation_id):
    conn = get_connection()
    cursor = conn.cursor()
    # This query calculates the Max steps (duration) for every simulation in the batch
    # It also counts evacuees and hazards in one go
    query = """
        SELECT 
            s.Simulation_Id,
            (SELECT COUNT(*) FROM Evacuees WHERE Simulation_Id = s.Simulation_Id) as EvacueeCount,
            (SELECT COUNT(*) FROM Hazards WHERE Simulation_Id = s.Simulation_Id) as HazardCount,
            (SELECT MAX(Step_Order) FROM ROUTE_POINT rp 
             JOIN Evacuees e ON rp.Evacuee_Id = e.evacuee_id 
             WHERE e.simulation_id = s.Simulation_Id) as MaxSteps
        FROM Simulation s
        WHERE s.Evaluation_Id = ?
    """
    cursor.execute(query, (evaluation_id,))
    rows = cursor.fetchall()
    
    stats_map = {}
    for r in rows:
        stats_map[r.Simulation_Id] = {
            'evacuees': r.EvacueeCount,
            'hazards': r.HazardCount,
            'duration': (r.MaxSteps or 0) / 50
        }
    conn.close()
    return stats_map
    
def get_all_evacuee_routes_batch(simulation_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    # We JOIN Route_Point with Evacuees to get all points for this Simulation_Id at once
    query = """
        SELECT RP.Route_Point_Id, RP.Evacuee_Id, RP.Latitude, RP.Longitude, RP.Z, RP.Step_Order
        FROM ROUTE_POINT RP
        JOIN Evacuees E ON RP.Evacuee_Id = E.evacuee_id
        WHERE E.simulation_id = ?
        ORDER BY RP.Evacuee_Id, RP.Step_Order
    """
    
    cursor.execute(query, (simulation_id,))
    rows = cursor.fetchall()
    
    # We organize the flat rows into the nested dictionary format your frontend expects
    # Format: { evac_id: { 'route': [...] } }
    routes_map = {}
    for row in rows:
        e_id = row.Evacuee_Id
        if e_id not in routes_map:
            routes_map[e_id] = {'route': []}
            
        routes_map[e_id]['route'].append({
            'Route_Point_Id': row.Route_Point_Id,
            'Evacuee_Id': row.Evacuee_Id,
            'Latitude': row.Latitude,
            'Longitude': row.Longitude,
            'Z': row.Z,
            'Step_Order': row.Step_Order,
        })
    
    cursor.close()
    conn.close()
    return routes_map

def get_simulation_metadata(simulation_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT * FROM Simulation WHERE Simulation_Id = ?
    """
    
    cursor.execute(query, (simulation_id,))
    row = cursor.fetchone()

    if row:
        return {
            'Simulation_Id': row.Simulation_Id,
            'Simulation_Name': row.Simulation_Name,
            'Created_At': str(row.Created_At),
            'Status': row.Status,
            'Computational_Time': row.Computational_Time,
            'Evaluation_Id': row.Evaluation_Id,
        }
    else:
        return None
    
def get_simulation_evacuees(simulation_id):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT * FROM Evacuees WHERE Simulation_Id =?
    """

    cursor.execute(query, (simulation_id,))
    rows = cursor.fetchall()

    evacuees = []
    for row in rows:
        evacuees.append({
            'Evacuee_Id': row.evacuee_id,
            'Simulation_Id': row.simulation_id,
            'Latitude': row.latitude,
            'Longitude': row.longitude,
            'Z': row.z,
        })

    return evacuees

def get_simulation_hazards(simulation_id):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT * FROM Hazards WHERE Simulation_Id =?
    """

    cursor.execute(query, (simulation_id,))
    rows = cursor.fetchall()

    hazards = []
    for row in rows:
        hazards.append({
            'Hazard_Id': row.Hazard_Id,
            'Simulation_Id': row.Simulation_Id,
            'Hazard_Type': row.Hazard_Type,
            'Latitude': row.Latitude,
            'Longitude': row.Longitude,
            'Z': row.Z,
            'Step_Order': getattr(row, 'Step_Order', 0) or 0
        })
        print("hazard", hazards)

    return hazards

def get_evacuees_route(evacuees_id):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT * FROM ROUTE_POINT WHERE Evacuee_Id =?
    """

    cursor.execute(query, (evacuees_id,))
    rows = cursor.fetchall()
    # print("rows", rows)
    route = []
    for row in rows:
        route.append({
            'Route_Point_Id': row.Route_Point_Id,
            'Evacuee_Id': row.Evacuee_Id,
            'Latitude': row.Latitude,
            'Longitude': row.Longitude,
            'Z': row.Z,
            'Step_Order': row.Step_Order,
        })
    
    
    return {'route': route}


def create_custom_sim(user_id, simulation_name, status, computational_time=1000, evaluation_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO Simulation (User_Id, Simulation_Name, Created_At, Status, Computational_Time, Evaluation_Id)
        OUTPUT INSERTED.Simulation_Id
        VALUES (?, ?, ?, ?, ?, ?)
    """

    timestamp = datetime.now()  # current time

    cursor.execute(query, (user_id, simulation_name, timestamp, status, computational_time, evaluation_id))
    
    # fetch the autogenerated simulation_id
    simulation_id = cursor.fetchone()[0]
    print("simulation id from database:", simulation_id)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return {
        "message": "Simulation created successfully",
        "simulation_id": simulation_id
    }


def save_evacuees(simulation_id, evacuees_data):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
    INSERT INTO evacuees (simulation_id, latitude, longitude, z)
    OUTPUT INSERTED.evacuee_id
    VALUES (?, ?, ?, ?)
    """

    evacuee_ids = []

    for data in evacuees_data:
        cursor.execute(query, (simulation_id, data['latitude'], data['longitude'], data['z']))
        evacuee_id = cursor.fetchone()[0]  # this now works, since OUTPUT returns a row
        evacuee_ids.append({
            "evacuee_id": evacuee_id,
            "latitude": data['latitude'],
            "longitude": data['longitude'],
            "z": data['z']
        })

    conn.commit()
    cursor.close()
    conn.close()

    return evacuee_ids


def save_hazards(simulation_id, hazards_data):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        INSERT INTO Hazards (Simulation_Id,Hazard_Type, Latitude, Longitude, Z, Step_Order)
        VALUES (?,?,?,?,?,?)
    """
    
    for data in hazards_data:
        step_order = data.get('step_order') or 0
        print("step order", step_order)
        cursor.execute(query, (simulation_id, data['hazard_type'], data['latitude'], data['longitude'], data['z'], step_order))
        
    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "Hazards saved successfully"}
    
def save_route_points_bulk(evacuee_id, points):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.fast_executemany = True
    query = """
        INSERT INTO ROUTE_POINT (Evacuee_Id, Latitude, Longitude, Z, Step_Order)
        VALUES (?,?,?,?,?)
    """

    # Build list of tuples for executemany
    data = [(evacuee_id, lat, lon, z, step_order) for (lon, lat, z, step_order) in points]

    cursor.executemany(query, data)

    conn.commit()
    cursor.close()
    conn.close()

    return {"message": f"{len(points)} route points saved successfully"}

def save_route_point(evacuees_id, longitude, latitude, z, step_order):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        INSERT INTO ROUTE_POINT (Evacuee_Id, Latitude, Longitude, Z, Step_Order)
        VALUES (?,?,?,?,?)
    """
    
    cursor.execute(query, (evacuees_id, latitude, longitude, z, step_order))

    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "Route point saved successfully"}

def get_evacuees_position(evacuee_id, current_step):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT Latitude, Longitude, Z FROM ROUTE_POINT WHERE Evacuee_Id = ? AND Step_Order = ?
    """

    cursor.execute(query, (evacuee_id, current_step))
    rows = cursor.fetchone()

    evacuees_position = rows or None
    print("evacuees position current step", evacuees_position, current_step, evacuee_id)

    cursor.close()
    conn.close()

    return evacuees_position

def remove_route_points(evacuee_id, step_order):
    conn = get_connection()
    cursor = conn.cursor()  
    
    query = """
        DELETE FROM ROUTE_POINT WHERE Evacuee_Id = ? AND Step_Order > ?
    """
    
    cursor.execute(query, (evacuee_id, step_order))

    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "Route point deleted successfully"}

def get_simulation_user_id(simulation_id):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT User_Id FROM Simulation WHERE Simulation_Id = ?"
    cursor.execute(query, (simulation_id,))
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        return None
    
def add_config_details(config_id, longitude, latitude, z):
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO EvacueeConfigDetail (Config_Id, longitude, latitude ,z)
        VALUES (?,?,?,?)
    """
    cursor.execute(query, (config_id, longitude, latitude, z))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Config details added successfully"}	

def get_confid_id(day, session):    
    SESSION_MAP = {
        "8:00 AM": "8am",
        "9:00 AM": "9am",
        "10:00 AM": "10am",
        "11:00 AM": "11am",
        "12:00 PM": "12pm",
        "1:00 PM": "1pm",
        "2:00 PM": "2pm",
        "3:00 PM": "3pm",
        "4:00 PM": "4pm",
        "5:00 PM": "5pm"
    }
    day_str = day[0]
    session_str = session[0]
    db_session = SESSION_MAP.get(session)
    print("db session", db_session) 
    print("day", day, "session", session_str)
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT config_id FROM EvacueeConfig WHERE day = ? AND session =?"
    cursor.execute(query, (day, db_session))
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        return None

def get_config_details(config_id):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT longitude, latitude, z FROM EvacueeConfigDetail WHERE config_id = ?"
    cursor.execute(query, (config_id,))
    
    rows = cursor.fetchall()  # fetch all rows
    cursor.close()
    conn.close()

    if not rows:
        return []

    # Convert each row to a dict matching frontend
    evacuees_list = []
    for row in rows:
        evacuees_list.append({
            "longitude": row[0],
            "latitude": row[1],
            "z": row[2]
        })

    return evacuees_list

def create_evaluation(batch_sim_name):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO evaluation (batch_name, high_risk_simulation_id)
        OUTPUT INSERTED.evaluation_id
        VALUES (?, NULL)
    """, (batch_sim_name,))

    evaluation_id = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    print("evaluation id", evaluation_id)
    return evaluation_id




def update_high_risk_simulation_id(evaluation_id, simulation_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE evaluation
        SET high_risk_simulation_id = ?
        WHERE evaluation_id = ?
    """, (simulation_id, evaluation_id))

    conn.commit()
    cursor.close()
    conn.close()

def get_simulations_by_evaluation(evaluation_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM Simulation
        WHERE Evaluation_Id =?
    """, (evaluation_id,))

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

    cursor.close()
    return simulations

def save_computational_time(time, simulation_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Simulation
            SET Computational_Time = ?
            WHERE Simulation_Id = ?
        """, (time, simulation_id))

        conn.commit()
        print(f"Computational time saved for Simulation_Id {simulation_id}")
    except Exception as e:
        print("Error saving computational time:", e)
    finally:
        cursor.close()
        conn.close()

def save_simulation_duration(duration, simulation_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Simulation
            SET Duration =?
            WHERE Simulation_Id =?
        """, (duration, simulation_id))

        conn.commit()
        print(f"Simulation duration saved for Simulation_Id {simulation_id}")
    except Exception as e:
        print("Error saving simulation duration:", e)
    finally:
        cursor.close()
        conn.close()
