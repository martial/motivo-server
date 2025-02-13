# Standard library imports
import os
import uuid
import traceback
from datetime import datetime
import subprocess
import ffmpeg

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
from sqliteHander import Content

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

# Define storage paths
STORAGE_BASE = 'storage/video'
RAW_VIDEO_FOLDER = f'{STORAGE_BASE}/raw'
TRIMMED_VIDEO_FOLDER = f'{STORAGE_BASE}/trimmed'
RENDERS_FOLDER = f'{STORAGE_BASE}/renders'

# Create necessary directories
for folder in [RAW_VIDEO_FOLDER, TRIMMED_VIDEO_FOLDER, RENDERS_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

ALLOWED_EXTENSIONS = {'mp4', 'webm', 'ogg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config['RAW_VIDEO_FOLDER'] = RAW_VIDEO_FOLDER
app.config['TRIMMED_VIDEO_FOLDER'] = TRIMMED_VIDEO_FOLDER
app.config['RENDERS_FOLDER'] = RENDERS_FOLDER

# Disable Flask's default logging
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

CORS(app, resources={
    r"/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "DELETE", "PUT"],
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
        if session_id not in chat_histories:
            chat_histories[session_id] = []
        
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
        
        print(f"Raw message response: {message}")
        print(f"Message content: {message.content}")
        
        response_content = message.content[0].text if isinstance(message.content, list) else message.content
        
        print(f"Final response content: {response_content}")
        
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
    try:
        downloads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../motivo/downloads'))
        print(f"Looking for file in: {downloads_dir}")
        os.makedirs(downloads_dir, exist_ok=True)
        return send_from_directory(downloads_dir, filename)
    except Exception as e:
        print(f"Error serving download file: {str(e)}")
        return jsonify({'error': str(e)}), 404

@app.route('/upload-video', methods=['POST'])
def upload_video():
    if 'video' not in request.files or request.files['video'].filename == '':
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
        
    filename = secure_filename(f"{str(uuid.uuid4())}_{file.filename}")
    filepath = os.path.join(RAW_VIDEO_FOLDER, filename)
    file.save(filepath)
    
    trim_sec = min(max(request.form.get('trim', type=int, default=5), 1), 15)
    start_sec = max(request.form.get('start', type=float, default=0), 0)
    
    try:
        probe = ffmpeg.probe(filepath)
        duration = float(probe['streams'][0]['duration'])
        
        if start_sec + trim_sec > duration:
            return jsonify({
                'error': 'Invalid trim parameters',
                'video_duration': duration,
                'requested_duration': start_sec + trim_sec
            }), 400
        
        trimmed_filename = f"trimmed_{filename}"
        trimmed_filepath = os.path.join(TRIMMED_VIDEO_FOLDER, trimmed_filename)
        
        ffmpeg.input(filepath).output(
            trimmed_filepath,
            r=30,
            ss=start_sec,
            t=trim_sec,
            vsync='cfr'
        ).run()
        
        video_url = f'{VITE_API_URL}/video/trimmed/{trimmed_filename}'
        
        print(f"Video URL: {video_url}")
        print(f"VITE_VIBE_URL: {VITE_VIBE_URL}")
        
        response = requests.post(
            f'{VITE_VIBE_URL}/predictions',
            headers={'accept': 'application/json', 'Content-Type': 'application/json'},
            json={
                "input": {
                    "media": video_url,
                    "render_video": True
                }
            },
            timeout=600
        )

        print(f"Response: {response}")
        response.raise_for_status()
        response_data = response.json()
        
        # Debug print to see response structure
        print("Response data:", json.dumps(response_data, indent=2))
        
        render_url = None
        if 'output' in response_data and 'video' in response_data['output']:
            import base64
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            render_filename = f"render_{timestamp}_{filename}"
            render_filepath = os.path.join(RENDERS_FOLDER, render_filename)
            
            # Get base64 data and handle padding
            b64_data = response_data['output']['video']
            # Add padding if needed
            padding = len(b64_data) % 4
            if padding:
                b64_data += '=' * (4 - padding)
                
            try:
                # Remove any potential data URL prefix
                if ',' in b64_data:
                    b64_data = b64_data.split(',')[1]
                
                # Decode and save base64 video
                video_data = base64.b64decode(b64_data)
                with open(render_filepath, 'wb') as f:
                    f.write(video_data)
                
                render_url = f'{VITE_API_URL}/video/renders/{render_filename}'
                response_data['output']['video_url'] = render_url
                print(f"Successfully saved rendered video to {render_filepath}")
                
            except Exception as e:
                print(f"Error decoding base64 data: {str(e)}")
                print(f"First 100 chars of b64 data: {b64_data[:100]}")
        else:
            print("No video data found in response")
            print("Available keys in output:", response_data.get('output', {}).keys())
        
        return json.dumps({
            'success': True,
            'video_url': video_url,
            'render_url': render_url,
            'prediction': response_data,
            'video_info': {
                'original_duration': duration,
                'trim_start': start_sec,
                'trim_duration': trim_sec
            }
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()  # Print full traceback
        return jsonify({"error": str(e)}), 500

@app.route('/video/<string:video_type>/<path:filename>')
def serve_video(video_type, filename):
    try:
        if video_type == 'raw':
            folder = RAW_VIDEO_FOLDER
        elif video_type == 'trimmed':
            folder = TRIMMED_VIDEO_FOLDER
        elif video_type == 'renders':
            folder = RENDERS_FOLDER
        else:
            return jsonify({'error': 'Invalid video type'}), 400
            
        folder_path = os.path.abspath(folder)
        filename = filename.rstrip('/')
        file_path = os.path.join(folder_path, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
            
        if not os.path.commonprefix([folder_path, os.path.abspath(file_path)]) == folder_path:
            return jsonify({'error': 'Invalid path'}), 403
            
        return send_file(file_path)
        
    except Exception as e:
        print(f"Error serving video: {str(e)}")
        return jsonify({'error': str(e)}), 500

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

@app.route('/api/version', methods=['GET'])
def get_version():
    return jsonify({'version': '1.0.0'})

#### DATABASE STUFF ####
@app.route('/api/conf', methods=['GET'])
def get_configs():
    try:
        db = Content()
        configs = db.get_all()
        return jsonify(configs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conf', methods=['POST'])
def create_config():
    try:
        data = request.json
        db = Content()
        config_id = db.add(
            title=data['title'],
            thumbnail=data['thumbnail'],
            type=data['type'],  # vibe/reward/llm
            data=data['data']   # json object
        )
        return jsonify({'id': config_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conf/<int:config_id>', methods=['PUT'])
def update_config(config_id):
    try:
        data = request.json
        db = Content()
        db.update(
            id=config_id,
            title=data.get('title'),
            thumbnail=data.get('thumbnail'),
            type=data.get('type'),
            data=data.get('data')
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conf/<int:config_id>', methods=['DELETE'])
def delete_config(config_id):
    try:
        db = Content()
        db.deleteItem(config_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)