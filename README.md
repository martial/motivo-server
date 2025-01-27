# Motion Control Project

A real-time humanoid motion control interface built with Svelte, Flask, and MetaMotivo ML.

## Setup

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

WIP not working yet but can be prebuilt and run with the following commands:

```bash
cd vibe
git clone https://github.com/mkocabas/VIBE.git
cog predict -i image="https://stableai-space.fra1.digitaloceanspaces.com/screen-club/sample_video.mp4"


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

## License

MIT License



