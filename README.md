# Interview Analyzer

A real-time interview question detection and answer generation tool using AI. Captures system audio, transcribes it with Whisper, detects interview questions, and generates intelligent answers using your choice of LLM providers.

## Features

- 🎙️ **Real-time Audio Capture**: System audio loopback with VAD (Voice Activity Detection)
- 🗣️ **Speech-to-Text**: Faster-Whisper with auto language detection
- 🔍 **Question Detection**: AI-powered interview question identification
- 💡 **Smart Answers**: Generate contextual answers using multiple LLM providers
- 💾 **Session History**: Store and review interview Q&A sessions
- 🖼️ **Screen Capture**: Capture screenshots during interviews
- ⚙️ **Customizable**: Multiple LLM providers, interview types, and answer modes
- 🎨 **Modern UI**: Electron + React + Tailwind CSS interface

## Supported Platforms

- ✅ **Windows 10/11** (Fully tested and supported)
- 🔄 **macOS** (In progress - community testing on separate branch)
- 🔄 **Linux** (In progress - community testing on separate branch)

## Supported LLM Providers

- OpenAI (GPT-4 Turbo)
- Anthropic (Claude 3 Opus)
- Google Gemini
- Groq (Llama 3.3)
- DeepSeek
- Ollama (Local models)

## Installation

### Prerequisites

- **Python 3.10+** 
- **Node.js 16+** (for Electron frontend)
- **npm** (comes with Node.js)

### Quick Start (OS-Automatic Setup)

```bash
# Clone the repository
git clone https://github.com/arthas009/InterviewAnalyzer.git
cd InterviewAnalyzer

# Run OS-dependent setup
python setup.py
```

The setup script will automatically:
1. Detect your operating system
2. Install platform-specific dependencies
3. Setup frontend and backend
4. Build the production app

### Manual Installation

#### Option 1: Windows

```bash
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-windows.txt

# Install frontend dependencies
cd electron
npm install
npm run build
cd ..

# Configure API keys
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys
```

#### Option 2: macOS

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-macos.txt

# Note: For audio capture on macOS, you may need:
# - BlackHole or Soundflower for system audio loopback
# - Or use microphone input mode

# Install frontend dependencies
cd electron
npm install
npm run build
cd ..

# Configure API keys
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys
```

#### Option 3: Linux

```bash
# Install system dependencies
sudo apt-get install portaudio19-dev alsa-utils pulseaudio
# or for Fedora: sudo dnf install portaudio-devel alsa-utils pulseaudio

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-linux.txt

# Install frontend dependencies
cd electron
npm install
npm run build
cd ..

# Configure API keys
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys
```

## Configuration

### API Keys Setup

Edit `backend/.env` and add your LLM provider API keys:

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
CLAUDE_API_KEY=sk-ant-...

# Google Gemini
GEMINI_API_KEY=AIza...

# Groq
GROQ_API_KEY=gsk-...

# DeepSeek
DEEPSEEK_API_KEY=sk-...

# Ollama (local, no key needed)
OLLAMA_BASE_URL=http://localhost:11434
```

### Audio Configuration

For **Windows**: WASAPI loopback is enabled by default (system audio capture)

For **macOS**:
- Install [BlackHole](https://github.com/ExistentialAudio/BlackHole) for system audio
- Or use microphone mode for local input

For **Linux**:
- Configure PulseAudio or ALSA for system audio capture
- Or use microphone mode

## Running the Application

### Development Mode

```bash
# Terminal 1: Start backend
python backend/main.py

# Terminal 2: Start frontend (from electron directory)
cd electron
npm run dev
```

On macOS you can use the included development startup script which starts the backend, Vite dev server, and Electron:

```bash
# From project root
./scripts/run-dev.sh
```

The script creates `.dev_logs/` for logs and will attempt to activate `.venv` if present.

### Production Mode

```bash
# Start the Electron app (includes backend)
cd electron
npm start
```

## Project Structure

```
Interview_analyzer/
├── backend/                 # Python FastAPI backend
│   ├── main.py             # WebSocket server & orchestration
│   ├── analyzer/           # Question detection logic
│   ├── audio/              # Audio capture & STT
│   ├── llm/                # LLM provider integrations
│   ├── stt/                # Speech-to-text engine
│   ├── config/             # Configuration management
│   └── requirements.txt     # Python dependencies
├── electron/               # Electron + React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── store/          # Zustand state management
│   │   └── types/          # TypeScript types
│   ├── main.js            # Electron main process
│   ├── preload.js         # Electron preload script
│   └── package.json       # Node dependencies
├── setup.py               # OS-dependent setup script
├── requirements.txt       # Base Python dependencies
├── requirements-windows.txt
├── requirements-macos.txt
├── requirements-linux.txt
└── .env                   # Configuration (create from .env.example)
```

## Usage

1. **Start the Application**: Run `npm start` from the electron directory
2. **Select Audio Source**: Choose between system audio or microphone
3. **Configure LLM**: Select your preferred provider and model
4. **Start Listening**: Click "Start" to begin capturing audio
5. **Real-time Transcript**: Watch transcribed text appear in real-time
6. **Automatic Detection**: Questions are detected and answers generated automatically
7. **Review Sessions**: Access previous interview sessions from history

## Troubleshooting

### No audio captured
- **Windows**: Ensure you have a loopback device (WASAPI)
- **macOS**: Install BlackHole or use microphone mode
- **Linux**: Configure PulseAudio/ALSA

### LLM provider errors
- Verify API key is correct in `.env`
- Check internet connection for cloud providers
- For Ollama, ensure it's running: `ollama serve`

### Build errors
- Rebuild frontend: `cd electron && npm run build`
- Clear cache: `rm -rf electron/dist electron/node_modules`
- Reinstall dependencies: `npm install`

## Development

### Running Backend Tests
```bash
cd backend
pytest tests/
```

### Building Frontend
```bash
cd electron
npm run build
```

### Development Tools
- **Backend**: FastAPI docs at `http://localhost:8000/docs`
- **Frontend**: React DevTools browser extension
- **Audio**: Debug VAD and transcription with backend logs

## Contributing

Contributions are welcome! To test platform-specific features:

1. **Windows**: Already fully tested
2. **macOS**: Please test on a separate branch and report issues
3. **Linux**: Please test on a separate branch and report issues

Create a new branch for each OS enhancement:
```bash
git checkout -b feature/macos-audio-support
```

## Environment-Specific Notes

### macOS Audio

For capturing system audio on macOS without background app refresh limitations:
- Install [BlackHole](https://github.com/ExistentialAudio/BlackHole)
- Or use mic mode for interviews conducted through video calls

### Linux Audio

For system audio, configure default recording device:
```bash
# List devices
pactl list short sources

# Set default if needed
pactl set-default-source <device_index>
```

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing issues and discussions
- Test on your specific OS and provide feedback

## Roadmap

- [ ] Native macOS Core Audio support
- [ ] Linux PulseAudio optimization
- [ ] Docker support for containerized deployment
- [ ] Web-based version
- [ ] Mobile apps
- [ ] Offline LLM models
- [ ] Real-time translation
- [ ] Interview analytics dashboard

---

**Status**: ✅ Production-ready for Windows | 🔄 Testing macOS/Linux support

For OS-specific testing and feedback, please create an issue with your platform details.
