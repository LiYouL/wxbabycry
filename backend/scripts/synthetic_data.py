# backend/scripts/synthetic_data.py
"""Generate synthetic baby cry MFCC data with strong class-specific acoustic fingerprints.

Strategy: each cry type has a unique spectral template + temporal envelope pattern.
The MFCC coefficients encode frequency bands where different cry types have different energy.
With enough SNR, a CNN can learn to distinguish these patterns reliably.
"""
import numpy as np

N_MFCC = 40
TIME_FRAMES = 128
OUR_CLASSES = ["饥饿", "尿布不适", "疲倦", "疼痛", "需要安抚", "其他"]


def _class_template(class_id, n_samples, seed):
    """Create MFCC templates with class-specific spectral and temporal fingerprints.

    Each class gets:
    1. A spectral fingerprint (which MFCC bands have high energy)
    2. A temporal envelope (rhythmic pattern)
    3. Controlled random variation (noise) added on top
    """
    rng = np.random.RandomState(seed)
    X = np.zeros((n_samples, N_MFCC, TIME_FRAMES), dtype=np.float32)

    # Define class-specific spectral fingerprints (key MFCC bands with boosted energy)
    profiles = {
        0: [0, 1, 2, 3, 4],           # 饥饿: strongest low-MFCC energy
        1: [8, 9, 10, 11, 12],        # 尿布不适: mid-high MFCC emphasis (nasal)
        2: [2, 3, 4, 5],              # 疲倦: low-mid only, weak
        3: [0, 1, 6, 7, 8, 9],        # 疼痛: broad spectrum, strong high
        4: [1, 2, 3, 10, 11],         # 需要安抚: mixed low+mid
        5: [0, 3, 7, 12, 15],         # 其他: scattered across spectrum
    }

    # Class-specific temporal rhythms
    rhythms = {
        0: [(8, 14, 0.6)],              # 饥饿: regular fast rhythm
        1: [(20, 35, 0.3)],             # 尿布不适: slow irregular
        2: [(30, 50, 0.2)],             # 疲倦: very slow
        3: [(4, 10, 0.8)],              # 疼痛: fast intense bursts
        4: [(10, 20, 0.4)],             # 安抚: medium
        5: [(5, 40, 0.3)],              # 其他: wide range
    }

    bands = profiles[class_id]
    tempo_specs = rhythms[class_id]

    for i in range(n_samples):
        # STEP 1: Create spectral fingerprint
        # Boost designated bands by 3-8x vs baseline
        base = rng.normal(0, 0.3, (N_MFCC, TIME_FRAMES)).astype(np.float32)

        # Make designated bands 5-10x stronger
        for band in bands:
            intensity = rng.uniform(3.0, 8.0)
            # Add temporal texture within band
            texture = np.sin(2 * np.pi * rng.uniform(0.01, 0.05) * np.arange(TIME_FRAMES))
            base[band, :] += intensity * (0.5 + 0.5 * texture)

        # STEP 2: Apply temporal envelope
        n_modes = rng.randint(1, 3)
        for _ in range(n_modes):
            spec = tempo_specs[rng.randint(0, len(tempo_specs))]
            period = rng.randint(spec[0], spec[1] + 1)
            amp = spec[2] * rng.uniform(0.5, 1.5)
            phase = rng.randint(0, period)
            envelope = 1.0 + amp * np.sin(2 * np.pi * (np.arange(TIME_FRAMES) + phase) / period)
            # Apply to multiple MFCC bands
            start_band = rng.randint(0, N_MFCC - 6)
            base[start_band:start_band + 6, :] *= envelope

        # STEP 3: Add controlled noise
        noise_level = rng.uniform(0.1, 0.4)
        base += rng.normal(0, noise_level, base.shape).astype(np.float32)

        X[i] = base

    return X


def generate_synthetic_data(n_per_class=150):
    """Generate synthetic MFCC data for all 7 cry types."""
    all_X, all_y = [], []

    for cls_id in range(6):
        X_cls = _class_template(cls_id, n_per_class, seed=cls_id * 1000)
        all_X.append(X_cls)
        all_y.extend([cls_id] * n_per_class)

    X = np.concatenate(all_X, axis=0).astype(np.float32)
    y = np.array(all_y, dtype=np.int64)

    idx = np.random.RandomState(42).permutation(len(X))
    return X[idx], y[idx]


if __name__ == "__main__":
    X, y = generate_synthetic_data(150)
    print(f"Generated {len(X)} samples")
    for cls_id in range(6):
        mask = y == cls_id
        cls_mean = X[mask].mean(axis=(0, 2))
        top3 = np.argsort(-cls_mean)[:3]
        print(f"  Class {cls_id} ({OUR_CLASSES[cls_id]}): top MFCC bands = {top3.tolist()}")
