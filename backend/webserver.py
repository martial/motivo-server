from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
import os
from anthropic import Anthropic
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173"],
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
