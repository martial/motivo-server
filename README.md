# Motion Control Project

A real-time humanoid motion control interface built with Svelte, Flask, and MetaMotivo ML.

## Setup


### Server Setup

inside server terminal

**Check logs of specific container**
```bash
docker ps
docker logs -f <container_id>
```


**Check logs of all containers**
```bash
cd motivo-prod
docker compose -f prod.docker-compose.yaml logs 
```

**Restart all containers**
```bash
cd motivo-prod
./stop_sterver.sh
./start_server.sh
```




### Python Setup
Create and activate virtual environment:
```bash
uv venv
source .venv/bin/activate  # Unix/MacOS
# OR
.venv\Scripts\activate     # Windows
```

Install dependencies:
```bash
uv pip install -r requirements.txt
```

### Frontend Setup
Install Node.js dependencies:
```bash
npm install
```

## Running the Project

1. Start the Flask backend:
```bash
python webserver.py
```

2. Start the frontend development server:
```bash
npm run dev
```

3. Access the web interface at http://localhost:5173

## Project Structure

### Frontend (`/src`)
- `components/`: Svelte components
- `lib/`: Shared utilities and types
- `stores/`: Svelte stores for state management
- `styles/`: Tailwind CSS configurations
- `App.svelte`: Root component
- `main.js`: Application entry point

### Backend
- `webserver/`: Flask server implementation
  - `routes/`: API endpoints
  - `websocket/`: WebSocket handlers
- `motivo/`: ML model integration
  - `model.py`: MetaMotivo-M-1 model setup
  - `behaviors.py`: Behavior generation logic

### Vibe 



```bash
cd vibe
git clone https://github.com/mkocabas/VIBE.git
# Predict pose + shape on video
cog predict -i media="https://stableai-space.fra1.digitaloceanspaces.com/screen-club/sample_video.mp4"
# Predict pose + disable video render (faster)
cog predict -i render_video="False" -i media="https://stableai-space.fra1.digitaloceanspaces.com/screen-club/sample_video.mp4"

# Predict from youtube url
cog predict -i media="https://youtu.be/2vjPBrBU-TM?si=c4xMBCml264tyNSh"


**Api**
The API is available at `https://urlToAPI/predictions` and accepts a POST request with the following parameters:

```bash
curl -X 'POST' \
  'https://urlToAPI/predictions' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "input": {
    "media": "url-to-video.mp4",
    "render_video": true
  }
}'

It will return an output object with the rendered pose + a json file with the pose data.

```


## Key Dependencies

### Backend
- Flask (Web server & API)
- MetaMotivo-M-1 (ML model)
- WebSockets (Real-time communication)
- Anthropic Claude (Behavior processing)

### Frontend
- Svelte (UI framework)
- Vite.js (Build tool)
- Tailwind CSS v4 (Styling)
- WebSocket client

## Available Behaviors

The MetaMotivo-M-1 model supports various humanoid behaviors:

### Basic Movements
- Walking (variable speeds)
- Running
- Crouching
- Jumping

### Complex Behaviors
- Object interaction
- Environmental awareness
- Multi-step sequences
- Dynamic responses

## Development Notes

### WebSocket Communication
The system uses WebSocket connections for:
- Real-time behavior updates
- Model state synchronization
- User interaction feedback

### ML Model Performance
- Supports real-time behavior generation
- Optimized for low-latency responses
- Efficient state management

## Troubleshooting

### Headless Setup
```bash
xvfb-run python webserver/server.py
sudo apt-get install libxcb-xinerama0
export MUJOCO_GL=egl
```

Update

## License

MIT License



