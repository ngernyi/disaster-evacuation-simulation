from flask import Flask, jsonify
from dotenv import load_dotenv
import os
import sys
from route.authRoute import auth_blueprint
from route.simulationRoute import sim_blueprint
from route.userManagementRoute import admin_blueprint
from config.oauth import configure_google_oauth
from services.authService import set_google_tokengetter
from flask_cors import CORS
import pyodbc
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

if os.getenv("FLASK_ENV") != "development":
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config['GOOGLE_CLIENT_ID'] = os.getenv("GOOGLE_CLIENT_ID")
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv("GOOGLE_CLIENT_SECRET")
app.config['MICROSOFT_CLIENT_ID'] = os.getenv("MICROSOFT_CLIENT_ID")
app.config['MICROSOFT_CLIENT_SECRET'] = os.getenv("MICROSOFT_CLIENT_SECRET")
app.config['MICROSOFT_AUTHORITY'] = os.getenv("MICROSOFT_AUTHORITY", "https://login.microsoftonline.com/common")
app.config['MICROSOFT_REDIRECT_URI'] = os.getenv("MICROSOFT_REDIRECT_URI", "http://localhost:5000/login/microsoft/callback")
app.config['MICROSOFT_SCOPE'] = os.getenv("MICROSOFT_SCOPE", "User.Read")


CORS(app, 
     origins=["http://localhost:5501", "http://127.0.0.1:5501", "https://disaster-evacuation-simulation-web.onrender.com"], 
     supports_credentials=True)
# cors = CORS(origins=["http://localhost:5501"],supports_credentials=True, resources={r"/api/*": {"origins": "*"}})
# CORS(app)
# Configure Google OAuth
google = configure_google_oauth(app)
set_google_tokengetter(google)

# Register Blueprints
app.register_blueprint(auth_blueprint)
app.register_blueprint(sim_blueprint)
app.register_blueprint(admin_blueprint)


app.config.update(
    SESSION_COOKIE_SECURE=True,      # Required for SameSite=None
    SESSION_COOKIE_SAMESITE='Lax',   # 'Lax' is usually best for redirects
    SESSION_COOKIE_HTTPONLY=True,    # Security best practice
)

@app.route("/")
def index():
    return jsonify({"message": "Backend is running."})

# for testing db connection
@app.route('/test-db')
def test_db():
    conn_str = os.environ.get('SQL_CONNECTION_STRING')
    try:
        conn = pyodbc.connect(conn_str, timeout=5)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        return f"✅ DB connection works! Query result: {result}"
    except Exception as e:
        return f"❌ DB connection failed: {e}"

# if __name__ == "__main__":
#     app.run(debug=True)
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
