from config.db import get_connection

def get_user_roles(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT Roles FROM [User] WHERE User_Id = ?"
    cursor.execute(query, (user_id,))
    row = cursor.fetchone()

    if row:
        return row[0]
    else:
        return None
    
def get_user_number_of_simulation(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM Simulation WHERE User_Id =?"
    cursor.execute(query, (user_id,))
    rows = cursor.fetchall()

    return len(rows)

def get_user_data_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM [User] WHERE User_Id = ?"
    cursor.execute(query, (user_id,))
    row = cursor.fetchone()
    user_data = {
        'id': row[0].strip(),
        'name': row[1],
        'email': row[2],
        'roles': row[3],
    }
    
    return user_data