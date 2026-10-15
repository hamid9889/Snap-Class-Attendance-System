"""
SnapClass Attendance System - Face Recognition Pipeline
========================================================
Performs facial detection, 128-dimensional deep feature representation,
and Support Vector Machine (SVM) classification combined with Euclidean
distance verification to track classroom attendance from photos.

Key Components:
1. Dlib HOG frontal face detector (or 68-point shape predictor).
2. ResNet face recognition model (128-d descriptor).
3. Scikit-learn SVC with linear kernel.
4. Resemblance verification threshold (0.6) for false positive elimination.
"""
import logging
from functools import lru_cache
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from sklearn.svm import SVC

# Database import from Supabase utils
from backend.supabase_utils import get_all_students

logger = logging.getLogger(__name__)

# Safe / Lazy imports for dlib and face_recognition_models
try:
    import dlib
    import face_recognition_models
    DLIB_AVAILABLE = True
except Exception as e:
    DLIB_AVAILABLE = False
    logger.warning(f"[FaceRecognition Warning] dlib or face_recognition_models not loaded: {e}")


@lru_cache(maxsize=1)
def load_dlib_models():
    """
    Loads and caches dlib frontal face detector, 68-point shape predictor,
    and the ResNet face recognition descriptor model.
    """
    if not DLIB_AVAILABLE:
        raise RuntimeError(
            "Face recognition libraries (dlib, face_recognition_models) are not installed. "
            "Please install dependencies from requirements.txt."
        )

    detector = dlib.get_frontal_face_detector()
    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location()
    )
    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )
    return detector, sp, facerec


def get_face_embeddings(image_np: np.ndarray) -> List[np.ndarray]:
    """
    Extracts 128-dimensional face descriptor embeddings for every face detected in an image.
    
    Args:
        image_np (np.ndarray): RGB image as a NumPy array.
        
    Returns:
        List of 128-dimensional NumPy arrays representing each detected face.
    """
    if not DLIB_AVAILABLE:
        return []

    try:
        detector, sp, facerec = load_dlib_models()
        faces = detector(image_np, 1)

        encodings = []
        for face in faces:
            shape = sp(image_np, face)
            # Compute 128-d face descriptor vector
            face_descriptor = facerec.compute_face_descriptor(image_np, shape, 1)
            encodings.append(np.array(face_descriptor, dtype=np.float64))
        return encodings
    except Exception as e:
        logger.error(f"Error extracting face embeddings: {e}")
        return []


# In-memory cache for trained SVM classifier
_trained_model_cache: Optional[Dict[str, Any]] = None


def get_trained_model() -> Optional[Dict[str, Any]]:
    """
    Retrieves or fits the linear SVM classifier on all registered students' face embeddings.
    Caches the trained model in memory for high-performance inference.
    """
    global _trained_model_cache
    if _trained_model_cache is not None:
        return _trained_model_cache

    X = []
    y = []

    try:
        student_db = get_all_students()
    except Exception as e:
        logger.error(f"Database error while retrieving students for face model training: {e}")
        return None

    if not student_db:
        return None

    for student in student_db:
        embedding = student.get("face_embedding")
        student_id = student.get("student_id")
        if embedding and student_id is not None:
            X.append(np.array(embedding, dtype=np.float64))
            y.append(student_id)

    if len(X) == 0:
        return None

    clf = SVC(kernel="linear", probability=True, class_weight="balanced")
    try:
        clf.fit(X, y)
    except ValueError as e:
        logger.warning(f"SVM fitting skipped or failed: {e}")
        pass

    _trained_model_cache = {"clf": clf, "X": X, "y": y}
    return _trained_model_cache


def train_classifier() -> bool:
    """
    Clears cache and retrains the classifier with the latest students in Supabase.
    """
    global _trained_model_cache
    _trained_model_cache = None
    model_data = get_trained_model()
    return bool(model_data)


def predict_attendance(
    class_image_np: np.ndarray,
    resemblance_threshold: float = 0.6
) -> Tuple[Dict[int, bool], List[int], int]:
    """
    Scans a classroom photo, detects faces, extracts embeddings, performs SVM prediction,
    and validates Euclidean distance against the student's registered embedding.
    
    Args:
        class_image_np: RGB NumPy array of the classroom photograph.
        resemblance_threshold: Maximum allowable Euclidean distance (default 0.6).
        
    Returns:
        Tuple containing:
        - detected_student: Dict of {student_id: True} for recognized faces
        - all_students: List of all student IDs in the training model
        - num_faces: Number of faces detected in the image
    """
    encodings = get_face_embeddings(class_image_np)
    detected_student: Dict[int, bool] = {}

    model_data = get_trained_model()
    if not model_data:
        return detected_student, [], len(encodings)

    clf = model_data["clf"]
    X_train = model_data["X"]
    y_train = model_data["y"]

    all_students = sorted(list(set(y_train)))

    for encoding in encodings:
        if len(all_students) >= 2:
            predicted_id = int(clf.predict([encoding])[0])
        else:
            predicted_id = int(all_students[0])

        # Verify predicted student via Euclidean distance
        if predicted_id in y_train:
            student_embedding = X_train[y_train.index(predicted_id)]
            best_match_score = float(np.linalg.norm(student_embedding - encoding))

            if best_match_score <= resemblance_threshold:
                detected_student[predicted_id] = True

    return detected_student, all_students, len(encodings)
