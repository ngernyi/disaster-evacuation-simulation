from flask import Blueprint
from flask import session
from flask import jsonify
from flask import request
from services.authService import google_login, google_callback, logout
from services.userManagementService import get_user_roles

auth_blueprint = Blueprint('auth', __name__)

@auth_blueprint.route('/login')
def login():
    return google_login()

@auth_blueprint.route('/login/callback')
def authorized():
    return google_callback()


# Check if user is logged in
@auth_blueprint.route('/login/status')
def login_status():
    print("Session contents:", dict(session))
    print("Session ID:", session.get('_id', 'No session ID'))
    print("Cookies received:", request.cookies)
    
    user_info = session.get('user_info')
   
    if user_info:
        user_roles = get_user_roles(user_info['id']).rstrip()
        print(user_roles)
        if user_roles is None:
            return jsonify({"logged_in": False})
            print("no login")
            
        else:
            return jsonify({"logged_in": True, "user": user_info, "user_roles": user_roles})
            print("logged")
    else:
        return jsonify({"logged_in": False})
    
@auth_blueprint.route('/logout')
def logout_route():
    return logout()