# backend/app/services/cry_classifier.py
from __future__ import annotations

import numpy as np

CRY_TYPES = [
    "饥饿",
    "尿布不适",
    "疲倦",
    "疼痛",
    "需要安抚",
    "出牙",
    "其他",
]


class CryClassifier:
    """Placeholder CNN classifier for baby cry recognition.

    MVP: Returns random predictions with controlled confidence.
    Will be replaced with a real PyTorch/ONNX model.
    """

    def __init__(self, model_path: str = ""):
        self._labels = CRY_TYPES

    def predict(self, mfcc: np.ndarray) -> list[dict]:
        """Predict cry types from MFCC features.

        Args:
            mfcc: MFCC feature matrix (n_mfcc, time_frames)

        Returns:
            Sorted list of {type, confidence} descending by confidence.
        """
        n = len(self._labels)
        raw = np.random.dirichlet(np.ones(n) * 0.5)
        boost_idx = np.random.randint(0, n)
        raw[boost_idx] *= 3
        probs = raw / raw.sum()

        results = [
            {"type": self._labels[i], "confidence": round(float(probs[i]), 4)}
            for i in range(n)
        ]
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results


classifier = CryClassifier()
