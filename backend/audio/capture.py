import asyncio
import threading
import logging
import platform
from typing import Optional, Callable

import numpy as np
from scipy.signal import resample_poly
from math import gcd

logger = logging.getLogger(__name__)

# Detect operating system
CURRENT_OS = platform.system()  # 'Windows', 'Darwin' (macOS), 'Linux'


class SystemAudioCapture:
    """
    Captures system audio with OS-specific implementation.
    - Windows: WASAPI loopback or microphone
    - macOS: Microphone or virtual audio device (BlackHole/Soundflower)
    - Linux: ALSA or PulseAudio
    """

    def __init__(self, device_index: Optional[int] = None, target_sample_rate: int = 16000, use_microphone: bool = False):
        self.device_index = device_index
        self.target_sample_rate = target_sample_rate
        self.use_microphone = use_microphone
        self._stream = None
        self._pyaudio = None
        self._capture_thread: Optional[threading.Thread] = None
        self._running = False
        self._callback: Optional[Callable[[bytes], None]] = None
        self._device_info = None
        self.os_type = CURRENT_OS

    @staticmethod
    def get_available_devices() -> list[dict]:
        """List all available audio devices for current OS."""
        if CURRENT_OS == 'Windows':
            return SystemAudioCapture._get_windows_devices()
        elif CURRENT_OS == 'Darwin':
            return SystemAudioCapture._get_macos_devices()
        else:  # Linux
            return SystemAudioCapture._get_linux_devices()

    @staticmethod
    def _get_windows_devices() -> list[dict]:
        """List WASAPI loopback and input devices (Windows)."""
        import pyaudiowpatch as pyaudio

        devices = []
        p = pyaudio.PyAudio()
        try:
            for i in range(p.get_device_count()):
                dev = p.get_device_info_by_index(i)
                # Loopback devices have maxInputChannels > 0 and are WASAPI
                if dev.get("maxInputChannels", 0) > 0:
                    devices.append({
                        "index": dev["index"],
                        "name": dev["name"],
                        "channels": dev["maxInputChannels"],
                        "sample_rate": int(dev["defaultSampleRate"]),
                        "is_loopback": "loopback" in dev.get("name", "").lower()
                            or dev.get("isLoopbackDevice", False),
                    })
        finally:
            p.terminate()
        return devices

    @staticmethod
    def _get_macos_devices() -> list[dict]:
        """List audio input devices (macOS)."""
        import pyaudio

        devices = []
        p = pyaudio.PyAudio()
        try:
            for i in range(p.get_device_count()):
                dev = p.get_device_info_by_index(i)
                # Show input devices
                if dev.get("maxInputChannels", 0) > 0:
                    devices.append({
                        "index": dev["index"],
                        "name": dev["name"],
                        "channels": dev["maxInputChannels"],
                        "sample_rate": int(dev["defaultSampleRate"]),
                        "is_loopback": "blackhole" in dev.get("name", "").lower() 
                            or "soundflower" in dev.get("name", "").lower(),
                    })
        finally:
            p.terminate()
        return devices

    @staticmethod
    def _get_linux_devices() -> list[dict]:
        """List audio input devices (Linux)."""
        import pyaudio

        devices = []
        p = pyaudio.PyAudio()
        try:
            for i in range(p.get_device_count()):
                dev = p.get_device_info_by_index(i)
                # Show input devices
                if dev.get("maxInputChannels", 0) > 0:
                    devices.append({
                        "index": dev["index"],
                        "name": dev["name"],
                        "channels": dev["maxInputChannels"],
                        "sample_rate": int(dev["defaultSampleRate"]),
                        "is_loopback": False,
                    })
        finally:
            p.terminate()
        return devices

    @staticmethod
    def get_default_loopback_device() -> Optional[dict]:
        """Get the default WASAPI loopback device."""
        import pyaudiowpatch as pyaudio

        p = pyaudio.PyAudio()
        try:
            loopback = p.get_default_wasapi_loopback()
            return {
                "index": loopback["index"],
                "name": loopback["name"],
                "channels": loopback["maxInputChannels"],
                "sample_rate": int(loopback["defaultSampleRate"]),
                "is_loopback": True,
            }
        except Exception as e:
            logger.warning(f"Could not find default WASAPI loopback: {e}")
            return None
        finally:
            p.terminate()

    def _resample_audio(self, audio_data: np.ndarray, source_rate: int) -> np.ndarray:
        """Resample audio to target sample rate."""
        if source_rate == self.target_sample_rate:
            return audio_data

        # Use rational resampling for efficiency
        divisor = gcd(source_rate, self.target_sample_rate)
        up = self.target_sample_rate // divisor
        down = source_rate // divisor

        resampled = resample_poly(audio_data, up, down)
        return resampled.astype(np.int16)

    def _convert_to_mono(self, audio_data: np.ndarray, channels: int) -> np.ndarray:
        """Convert multi-channel audio to mono."""
        if channels == 1:
            return audio_data
        # Reshape to (samples, channels) and take mean
        reshaped = audio_data.reshape(-1, channels)
        mono = reshaped.mean(axis=1)
        return mono.astype(np.int16)

    def start(self, callback: Callable[[bytes], None]) -> None:
        """Start capturing audio. Callback receives 16kHz mono int16 PCM chunks."""
        if CURRENT_OS == 'Windows':
            self._start_windows(callback)
        elif CURRENT_OS == 'Darwin':
            self._start_macos(callback)
        else:  # Linux
            self._start_linux(callback)

    def _start_windows(self, callback: Callable[[bytes], None]) -> None:
        """Start audio capture on Windows with WASAPI."""
        import pyaudiowpatch as pyaudio

        if self._running:
            logger.warning("Audio capture already running")
            return

        self._callback = callback
        self._pyaudio = pyaudio.PyAudio()

        # Resolve device
        if self.use_microphone:
            # Use default microphone input
            if self.device_index is not None:
                self._device_info = self._pyaudio.get_device_info_by_index(self.device_index)
            else:
                self._device_info = self._pyaudio.get_default_input_device_info()
            logger.info(f"Using microphone: {self._device_info['name']}")
        elif self.device_index is not None:
            self._device_info = self._pyaudio.get_device_info_by_index(self.device_index)
        else:
            try:
                self._device_info = self._pyaudio.get_default_wasapi_loopback()
            except Exception:
                # Fallback: search for any loopback device
                for i in range(self._pyaudio.get_device_count()):
                    dev = self._pyaudio.get_device_info_by_index(i)
                    if dev.get("isLoopbackDevice", False):
                        self._device_info = dev
                        break

        if self._device_info is None:
            raise RuntimeError(
                "No WASAPI loopback device found. "
                "Enable 'Stereo Mix' in Windows Sound settings or check audio drivers."
            )

        source_rate = int(self._device_info["defaultSampleRate"])
        channels = int(self._device_info["maxInputChannels"])
        frames_per_buffer = 1024

        logger.info(
            f"Starting audio capture: device='{self._device_info['name']}', "
            f"rate={source_rate}, channels={channels}"
        )

        self._stream = self._pyaudio.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=source_rate,
            input=True,
            input_device_index=int(self._device_info["index"]),
            frames_per_buffer=frames_per_buffer,
        )

        self._running = True
        self._capture_thread = threading.Thread(
            target=self._capture_loop,
            args=(source_rate, channels, frames_per_buffer),
            daemon=True,
            name="audio-capture",
        )
        self._capture_thread.start()

    def _capture_loop(self, source_rate: int, channels: int, frames_per_buffer: int) -> None:
        """Background thread that reads audio and feeds resampled mono chunks to callback."""
        try:
            while self._running and self._stream and self._stream.is_active():
                try:
                    raw_data = self._stream.read(frames_per_buffer, exception_on_overflow=False)
                except Exception as e:
                    if self._running:
                        logger.error(f"Audio read error: {e}")
                    break

                # Convert raw bytes to numpy array
                audio_array = np.frombuffer(raw_data, dtype=np.int16)

                # Convert to mono
                mono = self._convert_to_mono(audio_array, channels)

                # Resample to target rate
                resampled = self._resample_audio(mono, source_rate)

                # Send to callback as bytes
                if self._callback and len(resampled) > 0:
                    self._callback(resampled.tobytes())

        except Exception as e:
            logger.error(f"Audio capture loop error: {e}")
        finally:
            logger.info("Audio capture loop ended")

    def _start_macos(self, callback: Callable[[bytes], None]) -> None:
        """Start audio capture on macOS."""
        import pyaudio

        if self._running:
            logger.warning("Audio capture already running")
            return

        self._callback = callback
        self._pyaudio = pyaudio.PyAudio()

        # Resolve device
        if self.device_index is not None:
            self._device_info = self._pyaudio.get_device_info_by_index(self.device_index)
        else:
            self._device_info = self._pyaudio.get_default_input_device_info()

        if self._device_info is None:
            logger.warning(
                "No audio input device found. "
                "For system audio on macOS, install BlackHole or Soundflower."
            )
            raise RuntimeError("No audio input device available")

        source_rate = int(self._device_info["defaultSampleRate"])
        channels = int(self._device_info["maxInputChannels"])
        frames_per_buffer = 1024

        logger.info(
            f"Starting audio capture (macOS): device='{self._device_info['name']}', "
            f"rate={source_rate}, channels={channels}"
        )

        self._stream = self._pyaudio.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=source_rate,
            input=True,
            input_device_index=int(self._device_info["index"]),
            frames_per_buffer=frames_per_buffer,
        )

        self._running = True
        self._capture_thread = threading.Thread(
            target=self._capture_loop,
            args=(source_rate, channels, frames_per_buffer),
            daemon=True,
            name="audio-capture",
        )
        self._capture_thread.start()

    def _start_linux(self, callback: Callable[[bytes], None]) -> None:
        """Start audio capture on Linux."""
        import pyaudio

        if self._running:
            logger.warning("Audio capture already running")
            return

        self._callback = callback
        self._pyaudio = pyaudio.PyAudio()

        # Resolve device
        if self.device_index is not None:
            self._device_info = self._pyaudio.get_device_info_by_index(self.device_index)
        else:
            self._device_info = self._pyaudio.get_default_input_device_info()

        if self._device_info is None:
            logger.warning("No audio input device found. Check PulseAudio/ALSA configuration.")
            raise RuntimeError("No audio input device available")

        source_rate = int(self._device_info["defaultSampleRate"])
        channels = int(self._device_info["maxInputChannels"])
        frames_per_buffer = 1024

        logger.info(
            f"Starting audio capture (Linux): device='{self._device_info['name']}', "
            f"rate={source_rate}, channels={channels}"
        )

        self._stream = self._pyaudio.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=source_rate,
            input=True,
            input_device_index=int(self._device_info["index"]),
            frames_per_buffer=frames_per_buffer,
        )

        self._running = True
        self._capture_thread = threading.Thread(
            target=self._capture_loop,
            args=(source_rate, channels, frames_per_buffer),
            daemon=True,
            name="audio-capture",
        )
        self._capture_thread.start()

    def stop(self) -> None:
        """Stop audio capture."""
        self._running = False

        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        if self._capture_thread and self._capture_thread.is_alive():
            self._capture_thread.join(timeout=3.0)
            self._capture_thread = None

        if self._pyaudio:
            try:
                self._pyaudio.terminate()
            except Exception:
                pass
            self._pyaudio = None

        self._callback = None
        logger.info("Audio capture stopped")

    @property
    def is_running(self) -> bool:
        return self._running
