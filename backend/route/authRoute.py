from flask import Blueprint
from flask import session
from flask import jsonify
from flask import request
from services.authService import google_login, google_callback, logout
from services.authService import microsoft_login, microsoft_callback
from services.userManagementService import get_user_roles

auth_blueprint = Blueprint('auth', __name__)


@auth_blueprint.route('/login/microsoft')
def login_microsoft():
    return microsoft_login()

@auth_blueprint.route('/login/microsoft/callback')
def microsoft_authorized():
    return microsoft_callback()

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
    print("User info structure:", user_info)

    if not user_info:
        return jsonify({"logged_in": False})

    user_roles = get_user_roles(user_info['id'])
    if not user_roles:
        return jsonify({"logged_in": False})

    return jsonify({
        "logged_in": True,
        "user": user_info,
        "user_roles": user_roles.rstrip()
    })

    
@auth_blueprint.route('/logout')
def logout_route():
    return logout()