# backend/app/services/cry_classifier.py
from __future__ import annotations

import os
import json
import pickle
from typing import Dict, List

import numpy as np

try:
    import onnxruntime as ort
except ImportError:
    ort = None

from app.config import settings

CRY_TYPES = ["饥饿", "尿布不适", "疲倦", "疼痛", "需要安抚", "其他"]


def _extract_mfcc_features(mfcc):
    n_mfcc, n_frames = mfcc.shape
    feats = []

    for c in range(n_mfcc):
        coeff = mfcc[c, :]
        feats.append(np.mean(coeff))
        feats.append(np.std(coeff))
        feats.append(np.min(coeff))
        feats.append(np.max(coeff))
        feats.append(np.percentile(coeff, 25))
        feats.append(np.percentile(coeff, 75))

    delta = np.diff(mfcc, axis=1)
    for c in range(n_mfcc):
        feats.append(np.mean(np.abs(delta[c, :])))
        feats.append(np.std(delta[c, :]))

    delta2 = np.diff(delta, axis=1)
    for c in range(min(n_mfcc, 10)):
        feats.append(np.mean(np.abs(delta2[c, :])))

    feats.append(np.mean(mfcc))
    feats.append(np.std(mfcc))
    feats.append(float(n_frames))

    low_energy = np.mean(np.abs(mfcc[0:5, :]))
    mid_energy = np.mean(np.abs(mfcc[5:15, :]))
    high_energy = np.mean(np.abs(mfcc[15:25, :]))
    feats.append(low_energy)
    feats.append(mid_energy)
    feats.append(high_energy)
    feats.append(low_energy / (mid_energy + 1e-8))
    feats.append(high_energy / (low_energy + 1e-8))

    return np.array(feats, dtype=np.float32)


class CryClassifier:
    def __init__(self, model_path: str = ""):
        model_path = model_path or settings.model_path
        self._labels = CRY_TYPES
        self._model_type = None
        self._session = None
        self._sklearn_model = None

        model_dir = os.path.dirname(model_path)
        label_map_path = os.path.join(model_dir, "labels.json")
        if os.path.exists(label_map_path):
            with open(label_map_path, "r", encoding="utf-8") as f:
                mapped = json.load(f)
                if len(mapped) == len(self._labels):
                    self._labels = mapped

        pkl_path = os.path.join(model_dir, "cry_classifier.pkl")
        if os.path.exists(pkl_path):
            with open(pkl_path, "rb") as f:
                self._sklearn_model = pickle.load(f)
            self._model_type = "sklearn"
        elif ort is not None and os.path.exists(model_path):
            self._session = ort.InferenceSession(model_path)
            self._model_type = "onnx"

    def predict(self, mfcc: np.ndarray) -> List[Dict]:
        if self._model_type == "sklearn":
            return self._predict_sklearn(mfcc)
        elif self._model_type == "onnx":
            return self._predict_onnx(mfcc)
        else:
            return self._random_predict()

    def status(self) -> Dict:
        return {
            "model_type": self._model_type or "random_fallback",
            "class_count": len(self._labels),
            "labels": self._labels,
            "sklearn_loaded": self._sklearn_model is not None,
            "onnxruntime_available": ort is not None,
            "onnx_loaded": self._session is not None,
        }

    def _predict_sklearn(self, mfcc: np.ndarray) -> List[Dict]:
        if mfcc.shape[1] < 128:
            mfcc = np.pad(mfcc, ((0, 0), (0, 128 - mfcc.shape[1])))
        else:
            mfcc = mfcc[:, :128]

        feats = _extract_mfcc_features(mfcc).reshape(1, -1)
        probs = self._sklearn_model.predict_proba(feats)[0]
        classes = self._sklearn_model.classes_

        results = []
        for i, cls_idx in enumerate(classes):
            idx = int(cls_idx)
            if idx < len(self._labels):
                results.append({
                    "type": self._labels[idx],
                    "confidence": round(float(probs[i]), 4),
                })
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results

    def _predict_onnx(self, mfcc: np.ndarray) -> List[Dict]:
        if mfcc.shape[1] < 128:
            mfcc = np.pad(mfcc, ((0, 0), (0, 128 - mfcc.shape[1])))
        else:
            mfcc = mfcc[:, :128]

        inp = mfcc[np.newaxis, np.newaxis, :, :].astype(np.float32)
        out = self._session.run(None, {"mfcc": inp})[0][0]

        probs = np.exp(out - out.max()) / np.exp(out - out.max()).sum()

        results = [
            {"type": self._labels[i], "confidence": round(float(probs[i]), 4)}
            for i in range(min(len(self._labels), len(probs)))
        ]
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results

    def _random_predict(self) -> List[Dict]:
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
