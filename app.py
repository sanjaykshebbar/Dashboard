from flask import Flask, render_template, send_from_directory, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO, emit
import os
import random
import hashlib

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key
socketio = SocketIO(app)

# Directory where media files are stored
MEDIA_FOLDER = 'media'

# Ensure the media folder exists
if not os.path.exists(MEDIA_FOLDER):
    os.makedirs(MEDIA_FOLDER)

# Hardcoded username and password for authentication
USERNAME = 'admin'  # Set the username here
PASSWORD = 'password'  # Set the password here (plaintext for simplicity in this example)

# Function to validate user credentials (hardcoded username and password)
def validate_user(username, password):
    # Compare the entered username and password with hardcoded values
    return username == USERNAME and password == PASSWORD

# Route to the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate credentials
        if validate_user(username, password):
            session['user'] = username  # Store user in session
            return redirect(url_for('manage'))  # Redirect to the manage page after successful login
        else:
            return render_template('login.html', error="Invalid credentials.")  # Show error if invalid credentials
    
    return render_template('login.html')  # If GET request, just render the login page

# Route to logout
@app.route('/logout')
def logout():
    session.pop('user', None)  # Clear session data on logout
    return redirect(url_for('login'))  # Redirect to login page after logout

# Function to list files in the media folder (both images and videos)
def get_media_files():
    media_files = {'images': [], 'videos': []}
    for filename in os.listdir(MEDIA_FOLDER):
        filepath = os.path.join(MEDIA_FOLDER, filename)
        if filename.endswith('.jpg') or filename.endswith('.jpeg'):
            media_files['images'].append(filename)
        elif filename.endswith('.mp4'):
            media_files['videos'].append(filename)
    return media_files

# Route to the main dashboard (index page)
@app.route('/')
def index():
    media_files = get_media_files()
    random.shuffle(media_files['images'])
    random.shuffle(media_files['videos'])
    return render_template('index.html', media_files=media_files)

# Route to the content management page (upload and manage files)
@app.route('/manage')
def manage():
    if 'user' not in session:  # Check if user is logged in
        return redirect(url_for('login'))  # Redirect to login if user is not logged in
    return render_template('manage.html')  # Render the manage page if logged in

# Route to upload a new media file (image or video)
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'user' not in session:  # Check if user is logged in
        return redirect(url_for('login'))  # Redirect to login if user is not logged in
    file = request.files.get('file')
    if file:
        file_path = os.path.join(MEDIA_FOLDER, file.filename)
        file.save(file_path)
        socketio.emit('media_uploaded', {'message': 'New media uploaded!'})
        return jsonify({'status': 'success', 'message': 'File uploaded successfully.'}), 200
    return jsonify({'status': 'error', 'message': 'No file provided.'}), 400

# Route to delete a media file
@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    if 'user' not in session:  # Check if user is logged in
        return redirect(url_for('login'))  # Redirect to login if user is not logged in
    file_path = os.path.join(MEDIA_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        socketio.emit('media_deleted', {'message': f'{filename} deleted!'})
        return jsonify({'status': 'success', 'message': f'File {filename} deleted.'}), 200
    return jsonify({'status': 'error', 'message': 'File not found.'}), 404

# Route to serve media files (images and videos)
@app.route('/media/<filename>')
def media(filename):
    return send_from_directory(MEDIA_FOLDER, filename)

# Route to get the list of media files
@app.route('/media-list', methods=['GET'])
def list_media():
    media_files = get_media_files()
    return jsonify({'media_files': media_files})

# Run the app with SocketIO
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
