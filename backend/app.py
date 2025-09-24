from flask import Flask, jsonify
from dotenv import load_dotenv
import os
from route.authRoute import auth_blueprint
from route.simulationRoute import sim_blueprint
from route.userManagementRoute import admin_blueprint
from config.oauth import configure_google_oauth
from services.authService import set_google_tokengetter
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config['GOOGLE_CLIENT_ID'] = os.getenv("GOOGLE_CLIENT_ID")
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv("GOOGLE_CLIENT_SECRET")

CORS(app, 
     origins=["http://localhost:5501", "http://127.0.0.1:5501"], 
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

@app.route("/")
def index():
    return jsonify({"message": "Backend is running."})

if __name__ == "__main__":
    app.run(debug=True)