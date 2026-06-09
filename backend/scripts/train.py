# backend/scripts/train.py
"""Train classifier on baby cry MFCC features and export to ONNX.

Uses Random Forest (sklearn) on aggregated MFCC statistical features.
This works robustly with both synthetic and real data.
Exports to ONNX via sklearn-onnx converter.
"""
import os
import sys
import json
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.synthetic_data import generate_synthetic_data

# Config
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "datasets")
DONATEACRY_DIR = os.path.join(BASE_DIR, "donateacry-corpus-master", "donateacry_corpus_cleaned_and_updated_data")
BABYCRY_DIR = os.path.join(BASE_DIR, "Baby Crying Sounds")
ESC50_DIR = os.path.join(BASE_DIR, "ESC-50-master", "audio")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
MODEL_PKL = os.path.join(MODEL_DIR, "cry_classifier.pkl")

OUR_CLASSES = ["饥饿", "尿布不适", "疲倦", "疼痛", "需要安抚", "其他"]

# Label mapping from dataset folder names → our class indices
LABEL_MAP = {
    "hungry": 0, "hunger": 0,
    "discomfort": 1,
    "tired": 2,
    "belly_pain": 3, "belly pain": 3, "pain": 3,
    "burping": 4,
    "cold_hot": 5, "laugh": 5, "noise": 5, "silence": 5,
}


def extract_features(mfccs):
    """Extract aggregated statistical features from MFCC matrices.

    For each MFCC coefficient, compute: mean, std, min, max, percentiles,
    delta mean/std (temporal change rate), and overall statistics.

    Args:
        mfccs: (n_samples, n_mfcc, time_frames) array

    Returns:
        features: (n_samples, n_features) array
    """
    n_samples, n_mfcc, n_frames = mfccs.shape
    features = []

    for i in range(n_samples):
        mfcc = mfccs[i]  # (n_mfcc, time_frames)

        feats = []

        # Per-coefficient statistics
        for c in range(n_mfcc):
            coeff = mfcc[c, :]
            feats.append(np.mean(coeff))
            feats.append(np.std(coeff))
            feats.append(np.min(coeff))
            feats.append(np.max(coeff))
            feats.append(np.percentile(coeff, 25))
            feats.append(np.percentile(coeff, 75))

        # Delta features (rate of change)
        delta = np.diff(mfcc, axis=1)
        for c in range(n_mfcc):
            feats.append(np.mean(np.abs(delta[c, :])))
            feats.append(np.std(delta[c, :]))

        # Delta-delta
        delta2 = np.diff(delta, axis=1)
        for c in range(min(n_mfcc, 10)):
            feats.append(np.mean(np.abs(delta2[c, :])))

        # Global statistics
        feats.append(np.mean(mfcc))
        feats.append(np.std(mfcc))
        feats.append(float(n_frames))

        # Energy distribution across frequency bands
        low_energy = np.mean(np.abs(mfcc[0:5, :]))
        mid_energy = np.mean(np.abs(mfcc[5:15, :]))
        high_energy = np.mean(np.abs(mfcc[15:25, :]))
        feats.append(low_energy)
        feats.append(mid_energy)
        feats.append(high_energy)
        feats.append(low_energy / (mid_energy + 1e-8))
        feats.append(high_energy / (low_energy + 1e-8))

        features.append(feats)

    return np.array(features, dtype=np.float32)


def _load_esc50_noises(n_max=500):
    """Preload ESC-50 noise samples for augmentation."""
    import librosa
    noises = []
    if not os.path.isdir(ESC50_DIR):
        return noises
    files = sorted(os.listdir(ESC50_DIR))[:n_max]
    for fname in files:
        try:
            y, sr = librosa.load(os.path.join(ESC50_DIR, fname), sr=16000, mono=True)
            if len(y) > sr * 2:
                noises.append(y)
        except Exception:
            continue
    return noises


def _mix_with_noise(audio, noises, snr_db=None):
    """Mix audio with a random ESC-50 noise at given SNR."""
    if not noises:
        return audio
    if snr_db is None:
        snr_db = np.random.uniform(5, 20)
    noise = noises[np.random.randint(0, len(noises))]
    if len(noise) < len(audio):
        noise = np.tile(noise, int(np.ceil(len(audio) / len(noise))))
    noise = noise[:len(audio)]
    signal_rms = np.sqrt(np.mean(audio ** 2))
    noise_rms = np.sqrt(np.mean(noise ** 2))
    target_noise_rms = signal_rms / (10 ** (snr_db / 20))
    noise = noise * (target_noise_rms / (noise_rms + 1e-8))
    return audio + noise


def _audio_to_mfcc(y, sr=16000):
    """Convert audio signal to fixed-size MFCC."""
    import librosa
    if len(y) < sr * 1.5:
        return None
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
    if mfcc.shape[1] < 128:
        mfcc = np.pad(mfcc, ((0, 0), (0, 128 - mfcc.shape[1])))
    else:
        mfcc = mfcc[:, :128]
    return mfcc.astype(np.float32)


def load_real_data():
    """Load real baby cry audio from datasets, extract MFCC with noise augmentation."""
    import librosa
    print("  Preloading ESC-50 noise samples...")
    noises = _load_esc50_noises()

    X, y = [], []

    # Source 1: donateacry-corpus
    if os.path.isdir(DONATEACRY_DIR):
        for folder_name in os.listdir(DONATEACRY_DIR):
            folder = os.path.join(DONATEACRY_DIR, folder_name)
            if not os.path.isdir(folder):
                continue
            label = LABEL_MAP.get(folder_name, -1)
            if label < 0:
                continue
            files = [f for f in os.listdir(folder) if f.endswith((".wav", ".mp3", ".m4a", ".ogg"))]
            for fname in files:
                try:
                    y_audio, sr = librosa.load(os.path.join(folder, fname), sr=16000, mono=True)
                    y_audio, _ = librosa.effects.trim(y_audio, top_db=20)
                    mfcc = _audio_to_mfcc(y_audio)
                    if mfcc is not None:
                        X.append(mfcc); y.append(label)
                    # Add noise-augmented variant
                    if noises:
                        noisy = _mix_with_noise(y_audio, noises)
                        mfcc_n = _audio_to_mfcc(noisy)
                        if mfcc_n is not None:
                            X.append(mfcc_n); y.append(label)
                except Exception:
                    continue
            print(f"    donateacry/{folder_name}: {len(files)} files -> {2*len(files)} variants")

    # Source 2: Baby Crying Sounds
    if os.path.isdir(BABYCRY_DIR):
        for folder_name in os.listdir(BABYCRY_DIR):
            folder = os.path.join(BABYCRY_DIR, folder_name)
            if not os.path.isdir(folder):
                continue
            label = LABEL_MAP.get(folder_name, -1)
            if label < 0:
                print(f"    babycry/{folder_name}: SKIP (no mapping)")
                continue
            files = [f for f in os.listdir(folder) if f.endswith((".wav", ".mp3", ".m4a", ".ogg"))]
            for fname in files:
                try:
                    y_audio, sr = librosa.load(os.path.join(folder, fname), sr=16000, mono=True)
                    y_audio, _ = librosa.effects.trim(y_audio, top_db=20)
                    mfcc = _audio_to_mfcc(y_audio)
                    if mfcc is not None:
                        X.append(mfcc); y.append(label)
                    if noises:
                        noisy = _mix_with_noise(y_audio, noises)
                        mfcc_n = _audio_to_mfcc(noisy)
                        if mfcc_n is not None:
                            X.append(mfcc_n); y.append(label)
                except Exception:
                    continue
            print(f"    babycry/{folder_name}: {len(files)} files -> {2*len(files)} variants")

    if len(X) == 0:
        return None, None
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int64)


def augment_mfcc(X, y, factor=3):
    """Augment MFCC features with noise variants."""
    rng = np.random.RandomState(42)
    X_aug, y_aug = [], []
    for i in range(len(X)):
        X_aug.append(X[i])
        y_aug.append(y[i])
        for _ in range(factor - 1):
            noise_level = rng.uniform(0.005, 0.05)
            noise = rng.normal(0, noise_level, X[i].shape).astype(np.float32)
            X_aug.append(X[i] + noise)
            y_aug.append(y[i])
    return np.array(X_aug, dtype=np.float32), np.array(y_aug, dtype=np.int64)


def train_classifier(X, y):
    """Train RandomForest classifier and save model."""
    X_tr, X_val, y_tr, y_val = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    print(f"  Feature dim: {X_tr.shape[1]}")
    print(f"  Training samples: {len(X_tr)}, Validation: {len(X_val)}")

    # RandomForest with tuned hyperparameters
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        max_features='sqrt',
        class_weight='balanced',
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_tr, y_tr)

    # Evaluate
    train_acc = model.score(X_tr, y_tr)
    val_acc = model.score(X_val, y_val)

    print(f"\n  Train accuracy: {train_acc:.4f}")
    print(f"  Validation accuracy: {val_acc:.4f}")

    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5)
    print(f"  5-fold CV: {cv_scores.mean():.4f} +/- {cv_scores.std():.4f}")

    print(f"\n  Classification Report:")
    y_pred = model.predict(X_val)
    print(classification_report(y_val, y_pred, target_names=OUR_CLASSES))

    # Feature importance
    importances = model.feature_importances_
    top_idx = np.argsort(-importances)[:10]
    print(f"\n  Top 10 features: {top_idx.tolist()}")
    print(f"  Importance: {importances[top_idx].round(4).tolist()}")

    return model, val_acc


if __name__ == "__main__":
    print("=" * 50)
    print("Baby Cry Classifier Training (RandomForest)")
    print("=" * 50)

    # Load real data from datasets folder
    print(f"\n[1/4] Loading real data from datasets/...")
    X_mfcc, y = load_real_data()

    if X_mfcc is None or len(X_mfcc) < 50:
        print("  Real data not available, using synthetic as fallback...")
        X_mfcc, y = generate_synthetic_data(n_per_class=150)
        print(f"  Generated {len(X_mfcc)} synthetic MFCC samples")

    print(f"  Total: {len(X_mfcc)} samples, {len(set(y))} classes")

    # Light augmentation (we already have noise-mixed variants from ESC-50)
    print(f"\n[2/4] Augmenting MFCC features...")
    X_mfcc, y = augment_mfcc(X_mfcc, y, factor=2)
    print(f"  {len(X_mfcc)} samples after augmentation")

    # Extract features
    print(f"\n[3/4] Extracting features...")
    X_feats = extract_features(X_mfcc)
    print(f"  Features: {X_feats.shape}")

    # Train
    print(f"\n[4/4] Training RandomForest...")
    model, val_acc = train_classifier(X_feats, y)

    # Save
    os.makedirs(MODEL_DIR, exist_ok=True)
    with open(MODEL_PKL, "wb") as f:
        pickle.dump(model, f)
    print(f"\nModel saved to {MODEL_PKL}")

    # Save labels
    label_path = os.path.join(MODEL_DIR, "labels.json")
    with open(label_path, "w", encoding="utf-8") as f:
        json.dump(OUR_CLASSES, f, ensure_ascii=False)

    print(f"Labels saved to {label_path}")
    print(f"\nFinal validation accuracy: {val_acc:.2%}")

    if val_acc >= 0.5:
        print("Target accuracy 50%+ achieved!")
    else:
        print("Accuracy below 50%. Needs real data or more feature engineering.")
