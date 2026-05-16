import logging
import threading
import queue
import time
from pathlib import Path
from typing import Optional, Callable

import numpy as np

logger = logging.getLogger(__name__)


class TranscriptionEngine:
    """Real-time speech-to-text using faster-whisper with silero-vad."""

    def __init__(
        self,
        model_size: str = "base",
        language: str = "en",
        device: str = "auto",
        compute_type: str = "auto",
        cpu_threads: int = 4,
        vad_sensitivity: float = 0.4,
        models_dir: Optional[Path] = None,
    ):
        self.model_size = model_size
        self.language = language if language != "auto" else None
        self.device = self._resolve_device(device)
        self.compute_type = self._resolve_compute_type(compute_type, self.device)
        self.cpu_threads = cpu_threads
        self.vad_sensitivity = vad_sensitivity
        self.models_dir = models_dir

        self._model = None
        self._vad_model = None
        self._audio_buffer = bytearray()
        self._running = False
        self._process_thread: Optional[threading.Thread] = None
        self._audio_queue: queue.Queue = queue.Queue()
        self._on_transcript: Optional[Callable[[str, bool], None]] = None

        # VAD state
        self._speech_active = False
        self._silence_frames = 0
        self._speech_buffer = bytearray()
        self._min_speech_duration_ms = 300
        self._min_silence_duration_ms = 400
        self._sample_rate = 16000
        self._frame_size_ms = 32  # VAD frame size in ms (512 samples at 16kHz for Silero)
        self._frame_size_samples = 512  # Silero VAD requires exactly 512 samples at 16kHz

    @staticmethod
    def _resolve_device(device: str) -> str:
        if device != "auto":
            return device
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    @staticmethod
    def _resolve_compute_type(compute_type: str, device: str) -> str:
        if compute_type != "auto":
            return compute_type
        return "float16" if device == "cuda" else "int8"

    def _load_model(self) -> None:
        """Load the whisper model."""
        from faster_whisper import WhisperModel

        logger.info(
            f"Loading whisper model: size={self.model_size}, "
            f"device={self.device}, compute_type={self.compute_type}"
        )

        kwargs = {
            "model_size_or_path": self.model_size,
            "device": self.device,
            "compute_type": self.compute_type,
        }

        if self.device == "cpu":
            kwargs["cpu_threads"] = self.cpu_threads

        if self.models_dir:
            kwargs["download_root"] = str(self.models_dir)

        self._model = WhisperModel(**kwargs)
        logger.info("Whisper model loaded successfully")

    def _load_vad(self) -> None:
        """Load the Silero VAD model."""
        import torch

        logger.info("Loading Silero VAD model")
        model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            onnx=True,
            trust_repo=True,
        )
        self._vad_model = model
        logger.info("Silero VAD model loaded")

    def _is_speech(self, audio_chunk: np.ndarray) -> bool:
        """Check if audio chunk contains speech using energy-based detection."""
        rms = np.sqrt(np.mean(audio_chunk.astype(np.float32) ** 2))
        return rms > 300

    def start(self, on_transcript: Callable[[str, bool], None]) -> None:
        """Start the transcription engine.

        Args:
            on_transcript: Callback(text, is_partial). Called with transcribed text.
                          is_partial=True for intermediate results, False for final.
        """
        if self._running:
            logger.warning("Transcription engine already running")
            return

        self._on_transcript = on_transcript
        self._running = True

        # Load models in background
        self._process_thread = threading.Thread(
            target=self._process_loop,
            daemon=True,
            name="stt-engine",
        )
        self._process_thread.start()

    def _process_loop(self) -> None:
        """Main processing loop: loads models then processes audio."""
        try:
            self._load_model()
            self._load_vad()
        except Exception as e:
            logger.error(f"Failed to load STT models: {e}")
            return

        logger.info("STT engine ready, processing audio...")

        audio_chunks_received = 0
        speech_frames_detected = 0

        while self._running:
            try:
                # Get audio chunk from queue (with timeout to check _running)
                try:
                    audio_bytes = self._audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                audio_chunks_received += 1
                if audio_chunks_received % 100 == 1:
                    # Log audio level to verify we're getting real audio
                    audio_arr = np.frombuffer(audio_bytes, dtype=np.int16)
                    rms = np.sqrt(np.mean(audio_arr.astype(np.float32) ** 2))
                    logger.info(f"Audio chunks: {audio_chunks_received}, speech frames: {speech_frames_detected}, RMS: {rms:.1f}")

                self._process_audio_chunk(audio_bytes)

            except Exception as e:
                logger.error(f"STT processing error: {e}")

    def _process_audio_chunk(self, audio_bytes: bytes) -> None:
        """Process an audio chunk through VAD and accumulate speech segments."""
        # Accumulate incoming audio into internal buffer
        self._audio_buffer.extend(audio_bytes)

        # Process in VAD frame-sized chunks from the accumulated buffer
        frame_bytes = self._frame_size_samples * 2  # 2 bytes per int16 sample
        while len(self._audio_buffer) >= frame_bytes:
            frame_data = bytes(self._audio_buffer[:frame_bytes])
            del self._audio_buffer[:frame_bytes]

            frame = np.frombuffer(frame_data, dtype=np.int16)
            is_speech = self._is_speech(frame)

            if is_speech:
                self._silence_frames = 0
                if not self._speech_active:
                    self._speech_active = True
                    logger.info("Speech started")
                self._speech_buffer.extend(frame.tobytes())
            else:
                if self._speech_active:
                    self._silence_frames += 1
                    silence_duration_ms = self._silence_frames * self._frame_size_ms

                    # Still add to buffer during short silences (within words)
                    self._speech_buffer.extend(frame.tobytes())

                    if silence_duration_ms >= self._min_silence_duration_ms:
                        # Speech segment ended - transcribe it
                        self._transcribe_buffer()
                        self._speech_active = False
                        self._silence_frames = 0

    def _transcribe_buffer(self) -> None:
        """Transcribe accumulated speech buffer."""
        if len(self._speech_buffer) == 0:
            return

        # Check minimum duration
        duration_ms = len(self._speech_buffer) / (2 * self._sample_rate) * 1000  # 2 bytes per int16 sample
        if duration_ms < self._min_speech_duration_ms:
            self._speech_buffer.clear()
            return

        # Convert buffer to numpy array
        audio = np.frombuffer(bytes(self._speech_buffer), dtype=np.int16)
        self._speech_buffer.clear()

        # Normalize to float32 [-1, 1] for faster-whisper
        audio_float = audio.astype(np.float32) / 32768.0

        try:
            segments, info = self._model.transcribe(
                audio_float,
                beam_size=5,
                language=self.language,
                vad_filter=False,  # We already did VAD
                condition_on_previous_text=False,
            )

            # Lock detected language for the session (avoid per-segment flip-flopping)
            if self.language is None and info.language_probability > 0.7:
                self.language = info.language
                logger.info(f"Auto-detected language: {info.language} (prob: {info.language_probability:.2f}), locking for session")

            full_text = ""
            for segment in segments:
                full_text += segment.text

            text = full_text.strip()
            if text and self._on_transcript:
                logger.info(f"[TRANSCRIPT] {text}")
                self._on_transcript(text, False)

        except Exception as e:
            logger.error(f"Transcription error: {e}")

    def feed_audio(self, audio_bytes: bytes) -> None:
        """Feed audio data (16kHz, mono, int16 PCM) into the engine."""
        if self._running:
            self._audio_queue.put(audio_bytes)

    def stop(self) -> None:
        """Stop the transcription engine."""
        self._running = False

        # Transcribe any remaining buffer
        if self._speech_buffer:
            self._transcribe_buffer()

        if self._process_thread and self._process_thread.is_alive():
            self._process_thread.join(timeout=10.0)
            self._process_thread = None

        self._model = None
        self._vad_model = None
        self._audio_queue = queue.Queue()
        self._speech_buffer.clear()
        logger.info("STT engine stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    @staticmethod
    def get_available_models() -> list[dict]:
        """Return list of available whisper model sizes with metadata."""
        return [
            {"id": "tiny", "name": "Tiny", "size_mb": 75, "speed": "fastest", "accuracy": "low"},
            {"id": "base", "name": "Base", "size_mb": 145, "speed": "fast", "accuracy": "moderate"},
            {"id": "small", "name": "Small", "size_mb": 488, "speed": "moderate", "accuracy": "good"},
            {"id": "medium", "name": "Medium", "size_mb": 1460, "speed": "slow", "accuracy": "high"},
            {"id": "large-v3", "name": "Large V3", "size_mb": 3090, "speed": "slowest", "accuracy": "best"},
        ]
