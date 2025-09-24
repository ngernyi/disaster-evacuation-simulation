from flask import url_for, redirect, session
from flask import redirect
from config.oauth import oauth
from flask import jsonify
from config.db import get_connection
from services.userManagementService import get_user_roles
import requests


def google_login():
    google = oauth.remote_apps.get('google')
    return google.authorize(callback=url_for('auth.authorized', _external=True))


def google_callback():
    google = oauth.remote_apps.get('google')
    resp = google.authorized_response()
    if resp is None or resp.get('access_token') is None:
        return 'Access denied: reason={} error={}'.format(
            request.args['error_reason'],
            request.args['error_description']
        )
    session['google_token'] = (resp['access_token'], '')
    user_info = google.get('userinfo')
    session['user_info'] = user_info.data
    print("logged in")
    print(session['user_info'])
    if not check_user_existence_in_db(session['user_info']):
        save_user_in_db(session['user_info'])
    else:
        print("saved"+session['user_info']['id'])
        print("uoihkjgfhffhkj"+get_user_roles(session['user_info']['id']))
        if get_user_roles(session['user_info']['id']).rstrip() == 'Banned':
            token = session.get('google_token', [None])[0]  # ✅ Correct here
            if token:
                revoke = requests.get('https://accounts.google.com/o/oauth2/revoke',
                                    params={'token': token},
                                    headers={'content-type': 'application/x-www-form-urlencoded'})
                if revoke.status_code == 200:
                    print('Token successfully revoked')
                else:
                    print(f'Failed to revoke token: {revoke.status_code}')

            session.clear()  # Clear all session data
            print("Logged outttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttt")
            return redirect('http://localhost:5501/Code/frontend/auth/banned.html')
        
        
    print("Not banned")
    return redirect('http://localhost:5501/Code/frontend/html/landingPage.html')


def check_user_existence_in_db(user_info):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM [User] WHERE User_Id = ?"
    cursor.execute(query, (user_info['id']))
    row = cursor.fetchone()

    if row:
        return True
    else:
        return False

def save_user_in_db(user_info):
    conn = get_connection()
    cursor = conn.cursor()

    query = "INSERT INTO [User] (User_Id, Username, Email, Roles) VALUES (?, ?, ?, ?)"
    cursor.execute(query, (user_info['id'], user_info['name'], user_info['email'], 'Admin'))
    conn.commit()
    conn.close()

def logout():
    token = session.get('google_token', [None])[0]  # ✅ Correct here
    if token:
        revoke = requests.get('https://accounts.google.com/o/oauth2/revoke',
                              params={'token': token},
                              headers={'content-type': 'application/x-www-form-urlencoded'})
        if revoke.status_code == 200:
            print('Token successfully revoked')
        else:
            print(f'Failed to revoke token: {revoke.status_code}')

    session.clear()  # Clear all session data
    return redirect('http://localhost:5501/Code/frontend/map/landingPage.html')


def set_google_tokengetter(google):
    @google.tokengetter
    def get_google_oauth_token():
        return session.get('google_token')

