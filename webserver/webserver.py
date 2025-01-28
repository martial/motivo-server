from flask import Flask, send_from_directory, request, jsonify, send_file
from flask_cors import CORS
import os
from anthropic import Anthropic
import json
from datetime import datetime
from dotenv import load_dotenv


# Add these imports at the top
import uuid
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

# use os to get VITE_BACKEND_DOMAIN
BACKEND_DOMAIN = os.getenv('VITE_BACKEND_DOMAIN')
VITE_API_PORT = os.getenv('VITE_API_PORT')


# Add these configurations after app initialization
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'webm', 'ogg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app, resources={
    r"/*": {
        "origins": ["*"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})
anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Load prompt template at startup
try:
    with open('prompt_template.txt', 'r', encoding='utf-8') as f:
        PROMPT_TEMPLATE = f.read()
    print("Successfully loaded prompt template")
    print("First few characters:", PROMPT_TEMPLATE[:50])
except Exception as e:
    print(f"Error loading prompt template: {str(e)}")
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
    
    # Get session ID from request, or create new one
    session_id = request.json.get('sessionId', str(datetime.now().timestamp()))
    prompt = request.json.get('prompt')
    
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    try:
        # Initialize chat history for new sessions
        if session_id not in chat_histories:
            chat_histories[session_id] = []
            # Only format with template for the first message in a new session
            formatted_prompt = PROMPT_TEMPLATE.replace("{prompt}", prompt)
        else:
            # Use raw prompt for subsequent messages
            formatted_prompt = prompt
        
        # Create messages array with chat history
        messages = [
            *chat_histories[session_id],  # Include previous messages
            {
                "role": "user",
                "content": formatted_prompt
            }
        ]
        
        # Call Claude API with chat history
        message = anthropic.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            messages=messages
        )
        
        # Extract response and update chat history
        response_content = message.content[0].text if isinstance(message.content, list) else message.content
        
        # Add the exchange to chat history
        chat_histories[session_id].extend([
            {"role": "user", "content": formatted_prompt},
            {"role": "assistant", "content": response_content}
        ])
        
        return jsonify({
            'reward_config': response_content,
            'sessionId': session_id
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
        
        # Return the video URL
        video_url = f'http://{BACKEND_DOMAIN}:{VITE_API_PORT}/uploads/{filename}'
        return jsonify({
            'success': True,
            'video_url': video_url
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/uploads/<filename>')
def serve_video(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
