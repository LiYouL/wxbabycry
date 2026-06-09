# backend/scripts/augment.py
"""Audio augmentation for baby cry training data."""
import numpy as np
import librosa
import soundfile as sf

SR = 16000


def add_white_noise(y, noise_level=0.01):
    """Add white Gaussian noise simulating recording static."""
    noise = np.random.randn(len(y)) * noise_level * np.max(np.abs(y))
    return y + noise


def add_babble_noise(y, sr=SR):
    """Add low-frequency rumble simulating household noise."""
    t = np.arange(len(y)) / sr
    rumble = 0.01 * np.sin(2 * np.pi * 60 * t) + 0.005 * np.sin(2 * np.pi * 120 * t)
    return y + rumble


def add_pink_noise(y):
    """Add pink noise (1/f) simulating ambient room noise."""
    n = len(y)
    freqs = np.fft.rfftfreq(n)
    pink = np.random.randn(n)
    pink_fft = np.fft.rfft(pink)
    mask = np.ones(len(freqs))
    mask[1:] = 1.0 / np.sqrt(freqs[1:])
    pink_fft = pink_fft * mask
    pink = np.fft.irfft(pink_fft)
    pink = pink * 0.01 * np.max(np.abs(y)) / np.max(np.abs(pink))
    return y + pink[:len(y)]


def random_gain(y, min_db=-10, max_db=10):
    """Apply random volume change simulating phone distance variation."""
    db_change = np.random.uniform(min_db, max_db)
    factor = 10 ** (db_change / 20)
    return y * factor


def time_stretch(y, min_rate=0.9, max_rate=1.1):
    """Stretch time axis simulating different cry speeds."""
    rate = np.random.uniform(min_rate, max_rate)
    return librosa.effects.time_stretch(y, rate=rate)


def pitch_shift(y, sr=SR, min_semitones=-2, max_semitones=2):
    """Shift pitch simulating different babies' voices."""
    steps = np.random.uniform(min_semitones, max_semitones)
    return librosa.effects.pitch_shift(y, sr=sr, n_steps=steps)


def frequency_mask(y, sr=SR, max_mask_pct=0.3):
    """Apply frequency masking simulating muffled recording."""
    n = len(y)
    mask_len = int(n * np.random.uniform(0.05, max_mask_pct))
    mask_start = np.random.randint(0, n - mask_len)
    result = y.copy()
    result[mask_start:mask_start + mask_len] *= np.random.uniform(0.1, 0.5)
    return result


def augment_sample(y, sr=SR, n_variants=3):
    """Generate n_variants augmented versions from one audio sample.

    Each variant applies a random subset of augmentations.
    """
    augmentations = [
        lambda x: add_white_noise(x),
        lambda x: add_babble_noise(x, sr),
        lambda x: add_pink_noise(x),
        lambda x: random_gain(x),
        lambda x: time_stretch(x),
        lambda x: pitch_shift(x, sr),
        lambda x: frequency_mask(x, sr),
    ]

    variants = []
    for _ in range(n_variants):
        v = y.copy()
        n_augs = np.random.randint(1, 4)
        augs = np.random.choice(augmentations, size=n_augs, replace=False)
        for aug in augs:
            v = aug(v)
        variants.append(v)
    return variants
