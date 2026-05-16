"""Interview Analyzer Backend - FastAPI application with WebSocket for real-time communication."""

import argparse
import asyncio
import json
import logging
import signal
import sys
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

# Fix console encoding for non-ASCII characters (e.g. Turkish) - MUST be before logging setup
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config.settings import AppSettings, get_data_dir
from audio.capture import SystemAudioCapture
from stt.engine import TranscriptionEngine
from llm.factory import create_provider
from llm.base import BaseLLMProvider
from analyzer.question_detector import QuestionDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# Global state
class AppState:
    settings: Optional[AppSettings] = None
    data_dir: Optional[Path] = None
    audio_capture: Optional[SystemAudioCapture] = None
    stt_engine: Optional[TranscriptionEngine] = None
    llm_provider: Optional[BaseLLMProvider] = None
    question_detector: Optional[QuestionDetector] = None
    active_websocket: Optional[WebSocket] = None
    is_listening: bool = False
    analysis_task: Optional[asyncio.Task] = None


state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    state.data_dir = get_data_dir()
    state.data_dir.mkdir(parents=True, exist_ok=True)
    (state.data_dir / "models").mkdir(exist_ok=True)
    (state.data_dir / "logs").mkdir(exist_ok=True)

    state.settings = AppSettings.load(state.data_dir)
    logger.info(f"Data directory: {state.data_dir}")
    logger.info(f"Settings loaded. LLM provider: {state.settings.llm.provider}")

    # Setup file logging
    file_handler = logging.FileHandler(state.data_dir / "logs" / "backend.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logging.getLogger().addHandler(file_handler)

    yield

    # Shutdown
    await stop_pipeline()
    logger.info("Backend shutdown complete")


app = FastAPI(title="Interview Analyzer Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- HTTP Endpoints ---

@app.get("/health")
async def health():
    """Health check endpoint for Electron to poll."""
    return {"status": "ok", "listening": state.is_listening}


@app.post("/shutdown")
async def shutdown():
    """Graceful shutdown endpoint."""
    logger.info("Shutdown requested")
    await stop_pipeline()
    # Schedule the actual shutdown
    asyncio.get_event_loop().call_later(0.5, lambda: sys.exit(0))
    return {"status": "shutting_down"}


# --- WebSocket Handler ---

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """Main WebSocket endpoint for real-time communication with Electron frontend."""
    await ws.accept()
    state.active_websocket = ws
    logger.info("WebSocket client connected")

    try:
        # Send initial state
        await send_ws_message(ws, "status", {"state": "idle"})
        await send_ws_message(ws, "system_info", get_system_info())

        # Message loop
        while True:
            raw = await ws.receive_text()
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await send_ws_message(ws, "error", {"message": "Invalid JSON"})
                continue

            msg_type = message.get("type")
            logger.debug(f"Received WS message: {msg_type}")

            if msg_type == "start":
                await handle_start(ws, message.get("settings"))
            elif msg_type == "stop":
                await handle_stop(ws)
            elif msg_type == "update_settings":
                await handle_update_settings(ws, message.get("settings", {}))
            elif msg_type == "get_devices":
                await handle_get_devices(ws)
            elif msg_type == "get_system_info":
                await send_ws_message(ws, "system_info", get_system_info())
            elif msg_type == "get_models":
                await send_ws_message(ws, "models", {
                    "whisper": TranscriptionEngine.get_available_models()
                })
            else:
                await send_ws_message(ws, "error", {"message": f"Unknown message type: {msg_type}"})

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        state.active_websocket = None
        await stop_pipeline()


# --- Message Handlers ---

async def handle_start(ws: WebSocket, settings: Optional[dict]) -> None:
    """Start the listening/analysis pipeline."""
    if state.is_listening:
        await send_ws_message(ws, "error", {"message": "Already listening"})
        return

    # Apply settings if provided
    if settings:
        await handle_update_settings(ws, settings, save=False)

    try:
        # Initialize LLM provider
        llm_settings = state.settings.llm
        state.llm_provider = create_provider(
            provider=llm_settings.provider,
            openai_api_key=llm_settings.openai_api_key,
            openai_model=llm_settings.openai_model,
            claude_api_key=llm_settings.claude_api_key,
            claude_model=llm_settings.claude_model,
            ollama_base_url=llm_settings.ollama_base_url,
            ollama_model=llm_settings.ollama_model,
        )

        # Initialize question detector
        state.question_detector = QuestionDetector(
            llm_provider=state.llm_provider,
            temperature=llm_settings.temperature,
            max_tokens=llm_settings.max_tokens,
        )

        # Initialize STT engine
        stt_settings = state.settings.stt
        state.stt_engine = TranscriptionEngine(
            model_size=stt_settings.model_size,
            language=stt_settings.language,
            device=stt_settings.device,
            compute_type=stt_settings.compute_type,
            cpu_threads=stt_settings.cpu_threads,
            vad_sensitivity=stt_settings.vad_sensitivity,
            models_dir=state.data_dir / "models",
        )

        # Start STT engine with transcript callback
        loop = asyncio.get_running_loop()

        def on_transcript(text: str, is_partial: bool):
            asyncio.run_coroutine_threadsafe(
                _handle_transcript(text, is_partial),
                loop,
            )

        state.stt_engine.start(on_transcript)

        # Initialize audio capture
        audio_settings = state.settings.audio
        state.audio_capture = SystemAudioCapture(
            device_index=audio_settings.device_index,
            target_sample_rate=audio_settings.sample_rate,
            use_microphone=audio_settings.use_microphone,
        )

        # Start audio capture feeding into STT
        def on_audio_chunk(chunk: bytes):
            if state.stt_engine and state.stt_engine.is_running:
                state.stt_engine.feed_audio(chunk)

        state.audio_capture.start(on_audio_chunk)
        state.is_listening = True

        await send_ws_message(ws, "status", {"state": "listening"})
        logger.info("Pipeline started successfully")

    except Exception as e:
        logger.error(f"Failed to start pipeline: {e}")
        await stop_pipeline()
        await send_ws_message(ws, "error", {"message": f"Failed to start: {str(e)}"})
        await send_ws_message(ws, "status", {"state": "idle"})


async def _handle_transcript(text: str, is_partial: bool) -> None:
    """Handle transcribed text from STT engine."""
    ws = state.active_websocket
    if not ws:
        return

    # Send transcript to frontend
    await send_ws_message(ws, "transcript", {"text": text, "is_partial": is_partial})

    # Feed to question detector
    if state.question_detector and not is_partial:
        state.question_detector.add_transcript(text)

        # Analyze if not already analyzing
        if not state.question_detector.is_analyzing:
            # Run analysis in background
            if state.analysis_task is None or state.analysis_task.done():
                state.analysis_task = asyncio.create_task(_run_analysis())


async def _run_analysis() -> None:
    """Run question detection analysis."""
    ws = state.active_websocket
    if not ws or not state.question_detector:
        return

    async def on_question(qid: str, question: str):
        await send_ws_message(ws, "question_detected", {"question_id": qid, "question": question})

    async def on_answer_chunk(qid: str, chunk: str):
        await send_ws_message(ws, "answer_chunk", {"question_id": qid, "chunk": chunk})

    async def on_answer_complete(qid: str, full_answer: str):
        await send_ws_message(ws, "answer_complete", {"question_id": qid, "full_answer": full_answer})

    try:
        result = await state.question_detector.analyze(
            on_question=lambda qid, q: asyncio.ensure_future(on_question(qid, q)),
            on_answer_chunk=lambda qid, c: asyncio.ensure_future(on_answer_chunk(qid, c)),
            on_answer_complete=lambda qid, a: asyncio.ensure_future(on_answer_complete(qid, a)),
        )
        if result:
            logger.info(f"Analysis found question: {result.question[:80]}")
        else:
            logger.debug("Analysis: no question found")
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)


async def handle_stop(ws: WebSocket) -> None:
    """Stop the listening/analysis pipeline."""
    await stop_pipeline()
    await send_ws_message(ws, "status", {"state": "idle"})


async def handle_update_settings(ws: WebSocket, settings: dict, save: bool = True) -> None:
    """Update application settings."""
    try:
        # Merge with current settings
        current = state.settings.model_dump()

        # Deep merge
        for key, value in settings.items():
            if key in current and isinstance(current[key], dict) and isinstance(value, dict):
                current[key].update(value)
            else:
                current[key] = value

        state.settings = AppSettings.model_validate(current)

        if save:
            state.settings.save(state.data_dir)

        await send_ws_message(ws, "settings_updated", {"success": True})
        logger.info("Settings updated")
    except Exception as e:
        await send_ws_message(ws, "error", {"message": f"Failed to update settings: {str(e)}"})


async def handle_get_devices(ws: WebSocket) -> None:
    """Get available audio devices."""
    try:
        devices = SystemAudioCapture.get_available_devices()
        default_device = SystemAudioCapture.get_default_loopback_device()
        await send_ws_message(ws, "devices", {
            "devices": devices,
            "default": default_device,
        })
    except Exception as e:
        await send_ws_message(ws, "error", {"message": f"Failed to get devices: {str(e)}"})


# --- Utilities ---

def stop_pipeline_sync() -> None:
    """Stop all pipeline components (synchronous)."""
    state.is_listening = False

    if state.analysis_task and not state.analysis_task.done():
        state.analysis_task.cancel()
        state.analysis_task = None

    if state.audio_capture:
        state.audio_capture.stop()
        state.audio_capture = None

    if state.stt_engine:
        state.stt_engine.stop()
        state.stt_engine = None

    state.question_detector = None
    state.llm_provider = None
    logger.info("Pipeline stopped")


async def stop_pipeline() -> None:
    """Stop all pipeline components (async wrapper)."""
    await asyncio.to_thread(stop_pipeline_sync)


async def send_ws_message(ws: WebSocket, msg_type: str, data: dict) -> None:
    """Send a JSON message over WebSocket."""
    try:
        await ws.send_json({"type": msg_type, **data})
    except Exception as e:
        logger.debug(f"Failed to send WS message: {e}")


def get_system_info() -> dict:
    """Get system information (GPU, CPU, etc.)."""
    info = {"gpu": False, "gpu_name": None, "cpu_threads": 0}

    try:
        import torch
        info["gpu"] = torch.cuda.is_available()
        if info["gpu"]:
            info["gpu_name"] = torch.cuda.get_device_name(0)
    except ImportError:
        pass

    import os
    info["cpu_threads"] = os.cpu_count() or 4

    return info


# --- Entry Point ---

def main():
    parser = argparse.ArgumentParser(description="Interview Analyzer Backend")
    parser.add_argument("--port", type=int, default=19400, help="Port to run on")
    parser.add_argument("--data-dir", type=str, default=None, help="Data directory path")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    args = parser.parse_args()

    # Print port for Electron to read
    print(f"BACKEND_PORT={args.port}", flush=True)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
        access_log=False,
    )


if __name__ == "__main__":
    main()
