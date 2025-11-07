from functools import wraps
from flask import request, session, jsonify

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_info' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated
