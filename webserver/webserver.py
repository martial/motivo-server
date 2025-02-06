# Standard library imports
import os
import uuid
import traceback
from datetime import datetime
import subprocess

# Third-party imports
from flask import Flask, send_from_directory, request, jsonify, send_file
from flask_cors import CORS
from anthropic import Anthropic
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import requests

# Add these imports at the top
from flask import Flask, send_from_directory, request, jsonify, send_file
from flask_cors import CORS
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# use os to get environment variables
VITE_API_URL = os.getenv('VITE_API_URL') or 'localhost'
VITE_API_PORT = os.getenv('VITE_API_PORT') or 5002
VITE_VIBE_URL = os.getenv('VITE_VIBE_URL') or 5000
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY' or "")

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

# Initialize Anthropic client with API key
try:
    anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
    print("Successfully initialized Anthropic client")
except Exception as e:
    print(f"Error initializing Anthropic client: {str(e)}")
    

# Add these configurations after app initialization
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'webm', 'ogg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Disable Flask's default logging
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

CORS(app, resources={
    r"/*": {
        "origins": ["*"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Load system instructions at startup
try:
    with open('system_instructions.txt', 'r', encoding='utf-8') as f:
        SYSTEM_INSTRUCTIONS = f.read()
    print("Successfully loaded system instructions")
except Exception as e:
    print(f"Error loading system instructions: {str(e)}")
    raise



# Add chat history storage
chat_histories = {}

@app.route('/')
def serve_index():
    return send_from_directory('dist', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('dist', path)

@app.route('/amjpeg', methods=['GET'])
def serve_image():
    try:
        # Serve the output.png file
        file_path = os.path.join(os.getcwd(), '../output.jpg')
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='image/jpg')
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        print(f"Error serving image: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/generate-reward', methods=['POST'])
def generate_reward():
    print("\n=== New Request ===")
    
    session_id = request.json.get('sessionId', str(datetime.now().timestamp()))
    prompt = request.json.get('prompt')
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    try:
        # Initialize chat history for new sessions
        if session_id not in chat_histories:
            chat_histories[session_id] = []
        
        # Debug print
        print(f"Sending prompt: {prompt}")
        print(f"System instructions length: {len(SYSTEM_INSTRUCTIONS)}")
        
        message = anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            system=SYSTEM_INSTRUCTIONS,
            messages=[
                *chat_histories[session_id],
                {
                    "role": "user",
                    "content": f"Generate a reward configuration that achieves this behavior: {prompt}"
                }
            ]
        )
        
        # Debug print
        print(f"Raw message response: {message}")
        print(f"Message content: {message.content}")
        
        response_content = message.content[0].text if isinstance(message.content, list) else message.content
        
        # Debug print
        print(f"Final response content: {response_content}")
        
        # Add the exchange to chat history
        chat_histories[session_id].extend([
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": response_content}
        ])
        
        return jsonify({
            'reward_config': response_content,
            'sessionId': session_id,
            'conversation': chat_histories[session_id]
        })
        
    except Exception as e:
        print(f"Error in generate_reward: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/downloads/<path:filename>')
def download_file(filename):
    """Serve files from the downloads directory"""
    try:
        # Look in motivo/downloads directory
        downloads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../motivo/downloads'))
        print(f"Looking for file in: {downloads_dir}")  # Debug print
        os.makedirs(downloads_dir, exist_ok=True)
        return send_from_directory(downloads_dir, filename)
    except Exception as e:
        print(f"Error serving download file: {str(e)}")
        return jsonify({'error': str(e)}), 404

@app.route('/upload-video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(f"{str(uuid.uuid4())}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Generate the video URL
        video_url = f'{VITE_API_URL}/uploads/{filename}'
        
        # Make prediction request
        try:
            prediction_response = requests.post(
                f'{VITE_VIBE_URL}/predictions',
                headers={
                    'accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                json={
                    "input": {
                        "media": video_url,
                        "render_video": True
                    }
                }
            )
            print(f'{VITE_VIBE_URL}/predictions',)
            print(prediction_response.text)
            prediction_data = prediction_response.json()
            
            # Return both the video URL and prediction results
            return jsonify({
                'success': True,
                'video_url': video_url,
                'prediction': prediction_data
            })
            
        except requests.exceptions.RequestException as e:
            print(f"Prediction error: {str(e)}")
            return jsonify({
                'success': True,
                'video_url': video_url,
                'prediction_error': 'Failed to get prediction'
            })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/uploads/<path:filename>')
def serve_video(filename):
    try:
        # Get absolute path of the uploads folder
        uploads_path = os.path.abspath(app.config['UPLOAD_FOLDER'])
        print(f"Absolute uploads path: {uploads_path}")
        
        # Clean the filename to prevent directory traversal
        filename = filename.rstrip('/')
        
        # Create absolute path to the file
        file_path = os.path.join(uploads_path, filename)
        print(f"Absolute file path: {file_path}")
        
        # Verify file exists and is within uploads directory
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
            
        if not os.path.commonprefix([uploads_path, os.path.abspath(file_path)]) == uploads_path:
            return jsonify({'error': 'Invalid path'}), 403
            
        # Try serving the file directly using send_file instead
        return send_file(file_path)
        
    except Exception as e:
        print(f"Error serving video: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_git_info():
    try:
        commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
        # Get the last commit date on main branch - fixed command
        last_commit_date = subprocess.check_output(
            ['git', 'log', '-1', '--format=%cd', '--date=iso'],
            stderr=subprocess.DEVNULL
        ).decode('ascii').strip()
        
        try:
            version = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0']).decode('ascii').strip()
        except subprocess.CalledProcessError:
            version = 'v0.0.0'
            
        return {
            'version': version,
            'commitHash': commit_hash,
            'lastCommitDate': last_commit_date,
            'environment': 'production' if not app.debug else 'development'
        }
    except Exception as e:
        print(f"Error getting git info: {e}")
        return {
            'version': 'local',
            'commitHash': 'development',
            'lastCommitDate': datetime.utcnow().isoformat(),
            'environment': 'development' if app.debug else 'production'
        }

@app.route('/api/version')
def get_version():
    return jsonify(get_git_info())

@app.route('/clear-chat', methods=['POST'])
def clear_chat():
    try:
        session_id = request.json.get('sessionId')
        if session_id and session_id in chat_histories:
            chat_histories[session_id] = []
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error clearing chat: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
