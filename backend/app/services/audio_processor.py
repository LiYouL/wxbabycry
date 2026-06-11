# backend/app/services/audio_processor.py
import librosa
import numpy as np
import soundfile as sf
import io
from app.config import settings


class AudioProcessError(Exception):
    pass


def load_audio_signal(audio_bytes: bytes, original_format: str = "mp3") -> tuple:
    """Load uploaded audio as mono float32 at 16 kHz without extra re-encoding."""
    fmt = original_format.lower()
    if fmt in ("wav", "wave", "flac", "ogg"):
        y, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32", always_2d=False)
        if y.ndim > 1:
            y = np.mean(y, axis=1)
        if sr != 16000:
            y = librosa.resample(y, orig_sr=sr, target_sr=16000)
            sr = 16000
        return y.astype(np.float32), sr

    from pydub import AudioSegment

    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=fmt)
    audio = audio.set_channels(1).set_frame_rate(16000)
    samples = np.array(audio.get_array_of_samples()).astype(np.float32)
    scale = float(1 << (8 * audio.sample_width - 1))
    y = samples / max(scale, 1.0)
    return y.astype(np.float32), 16000


def validate_duration(y: np.ndarray, sr: int) -> np.ndarray:
    duration = len(y) / sr
    if duration < settings.min_record_seconds:
        raise AudioProcessError(
            f"录音时长不足 {settings.min_record_seconds} 秒，请重新录制"
        )
    if duration > settings.max_record_seconds:
        return y[: int(sr * settings.max_record_seconds)]
    return y


def has_audio(y: np.ndarray, sr: int) -> bool:
    return float(np.sqrt(np.mean(np.square(y)))) > 0.005


def extract_mfcc(y: np.ndarray, sr: int, n_mfcc: int = 40) -> np.ndarray:
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    return mfcc


def process_audio(audio_bytes: bytes, filename: str = "recording.mp3") -> np.ndarray:
    fmt = filename.rsplit(".", 1)[-1] if "." in filename else "mp3"
    y, sr = load_audio_signal(audio_bytes, fmt)

    y = validate_duration(y, sr)
    if not has_audio(y, sr):
        raise AudioProcessError("未检测到有效声音，请靠近婴儿重新录音")

    y, _ = librosa.effects.trim(y, top_db=20)

    mfcc = extract_mfcc(y, sr)
    return mfcc
