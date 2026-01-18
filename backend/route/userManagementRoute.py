from flask import Blueprint
from flask import session
from flask import jsonify
from flask import request
from config.db import get_connection
from services.userManagementService import get_user_roles, get_user_number_of_simulation

admin_blueprint = Blueprint('admin', __name__)

@admin_blueprint.route('/get_all_users', methods = ['GET'])
def get_registered_users_route():
    # check user roles
    user_id = session.get('user_info').get('id')
    user_role = get_user_roles(user_id).rstrip()
    
    print(user_role)
    if user_role != "Admin":
        return jsonify({'success': False,'message': 'Not authorized'}), 403

    # set connection
    conn = get_connection()
    cursor = conn.cursor()

    # query to get user simulations
    query = "SELECT * FROM [User]"
    cursor.execute(query)
    rows = cursor.fetchall()

    users = []
    for row in rows:
        number_of_simulations = get_user_number_of_simulation(row[0])
        users.append({
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'role': row[3],
            'number_of_simulations': number_of_simulations,
        })
        
    return jsonify({'success': True,'users': users})

@admin_blueprint.route('/ban_user', methods = ['POST'])
def ban_user_route():
    # check user roles
    user_id = session.get('user_info').get('id')
    user_role = get_user_roles(user_id).rstrip()
    if user_role!= "Admin":
        return jsonify({'success': False,'message': 'Not authorized'}), 403
    
    # get user id from request
    banned_user_id = request.json.get('user_id')
    print(banned_user_id)
    # set connection
    conn = get_connection()
    cursor = conn.cursor()

    # query to reset user status
    query = "UPDATE [User] SET Roles = 'Banned' WHERE User_Id = ?"
    cursor.execute(query, (banned_user_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True,'message': 'User banned'}), 200

@admin_blueprint.route('/unban_user', methods = ['POST'])
def unban_user_route():
    # check user roles
    user_id = session.get('user_info').get('id')
    user_role = get_user_roles(user_id).rstrip()
    if user_role!= "Admin":
        return jsonify({'success': False,'message': 'Not authorized'}), 403
    
    # get user id from request
    unbanned_user_id = request.json.get('user_id')
    print(unbanned_user_id)
    # set connection
    conn = get_connection()
    cursor = conn.cursor()

    # query to reset user status
    query = "UPDATE [User] SET Roles = 'User' WHERE User_Id = ?"
    cursor.execute(query, (unbanned_user_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True,'message': 'User unbanned'}), 200
    

@admin_blueprint.route('/promote_user', methods = ['POST'])
def promote_user_route():
    # check user roles
    user_id = session.get('user_info').get('id')
    user_role = get_user_roles(user_id).rstrip()
    if user_role!= "Admin":
        return jsonify({'success': False,'message': 'Not authorized'}), 403
    
    # get user id from request
    promoted_user_id = request.json.get('user_id')
    print(promoted_user_id)
    # set connection
    conn = get_connection()
    cursor = conn.cursor()

    # query to reset user status
    query = "UPDATE [User] SET Roles = 'Admin' WHERE User_Id = ?"
    cursor.execute(query, (promoted_user_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True,'message': 'User promoted'}), 200

@admin_blueprint.route('/unpromote_user', methods = ['POST'])
def unpromote_user_route():
    # check user roles
    user_id = session.get('user_info').get('id')
    user_role = get_user_roles(user_id).rstrip()
    if user_role!= "Admin":
        return jsonify({'success': False,'message': 'Not authorized'}), 403
    
    # get user id from request
    unpromoted_user_id = request.json.get('user_id')
    print(unpromoted_user_id)
    # set connection
    conn = get_connection()
    cursor = conn.cursor()

    # query to reset user status
    query = "UPDATE [User] SET Roles = 'User' WHERE User_Id = ?"
    cursor.execute(query, (unpromoted_user_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True,'message': 'User unpromoted'}), 200

@admin_blueprint.route('/update_user_details', methods = ['POST'])
def update_user_details_route():
    # check current user roles
    current_user_id = session.get('user_info').get('id')
    if get_user_roles(current_user_id).rstrip()!= "Admin":
        return jsonify({'success': False,'message': 'Not authorized'}), 403
    
    if request.json.get('newUsername') == '':
        return jsonify({'success': False,'message': 'The username cannot be empty'}), 400
    
    if request.json.get('newEmail') == '':
        return jsonify({'success': False,'message': 'The email cannot be empty'}), 400
    
    # get user id from request
    data = request.json
    print("json data",data)
    updated_user_id = request.json.get('user_id')
    print("updated user id",updated_user_id)
    # set connection
    conn = get_connection()
    cursor = conn.cursor()

    # query to reset user status
    query = "UPDATE [User] SET Username = ?, Email = ? WHERE User_Id = ?"
    cursor.execute(query, (request.json.get('newUsername'), request.json.get('newEmail'), updated_user_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True,'message': 'User details updated'}), 200
    