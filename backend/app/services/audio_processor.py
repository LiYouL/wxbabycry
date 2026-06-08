# backend/app/services/audio_processor.py
import librosa
import numpy as np
from pydub import AudioSegment
import io
from app.config import settings


class AudioProcessError(Exception):
    pass


def convert_to_wav(audio_bytes: bytes, original_format: str = "mp3") -> bytes:
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=original_format)
    buf = io.BytesIO()
    audio.export(buf, format="wav")
    buf.seek(0)
    return buf.read()


def validate_duration(y: np.ndarray, sr: int) -> None:
    duration = len(y) / sr
    if duration < settings.min_record_seconds:
        raise AudioProcessError(
            f"录音时长不足 {settings.min_record_seconds} 秒，请重新录制"
        )
    if duration > settings.max_record_seconds:
        y = y[: int(sr * settings.max_record_seconds)]


def has_audio(y: np.ndarray, sr: int) -> bool:
    rms = librosa.feature.rms(y=y)
    return float(np.mean(rms)) > 0.005


def extract_mfcc(y: np.ndarray, sr: int, n_mfcc: int = 40) -> np.ndarray:
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    return mfcc


def process_audio(audio_bytes: bytes, filename: str = "recording.mp3") -> np.ndarray:
    fmt = filename.rsplit(".", 1)[-1] if "." in filename else "mp3"
    wav_bytes = convert_to_wav(audio_bytes, fmt)

    y, sr = librosa.load(io.BytesIO(wav_bytes), sr=16000, mono=True)

    validate_duration(y, sr)

    if not has_audio(y, sr):
        raise AudioProcessError("未检测到有效声音，请靠近婴儿重新录音")

    y, _ = librosa.effects.trim(y, top_db=20)

    mfcc = extract_mfcc(y, sr)
    return mfcc
