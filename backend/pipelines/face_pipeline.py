"""
Face recognition pipeline wrapper.
Delegates to backend.face_recognition for backward compatibility.
"""
from backend.face_recognition import (
    load_dlib_models,
    get_face_embeddings,
    get_trained_model,
    train_classifier,
    predict_attendance,
)

__all__ = [
    "load_dlib_models",
    "get_face_embeddings",
    "get_trained_model",
    "train_classifier",
    "predict_attendance",
]
