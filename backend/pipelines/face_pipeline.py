"""
Face Recognition Pipeline for SnapClass Attendance System.
Uses dlib facial landmarks, 128-dimensional face descriptor embeddings,
and Scikit-Learn Support Vector Classification (SVC) with Euclidean distance matching.
All core algorithms, parameters, and math preserved identically from original logic.
"""
from functools import lru_cache
import numpy as np
from sklearn.svm import SVC

# Database import
from backend.db import get_all_students

# Lazy / Safe imports for dlib and face_recognition_models
try:
    import dlib
    import face_recognition_models
    DLIB_AVAILABLE = True
except Exception as e:
    DLIB_AVAILABLE = False
    print(f"[FacePipeline Warning] Dlib or face_recognition_models import issue: {e}")


@lru_cache(maxsize=1)
def load_dlib_models():
    """
    Loads and caches dlib frontal face detector, 68-point shape predictor,
    and ResNet face recognition model.
    """
    if not DLIB_AVAILABLE:
        raise RuntimeError("dlib and face_recognition_models must be installed.")
    
    detector = dlib.get_frontal_face_detector()
    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location()
    )
    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )
    return detector, sp, facerec


def get_face_embeddings(image_np: np.ndarray):
    """
    Extracts 128-dimensional face embedding vectors for every detected face in an image.
    """
    if not DLIB_AVAILABLE:
        return []
    
    detector, sp, facerec = load_dlib_models()
    faces = detector(image_np, 1)

    encodings = []
    for face in faces:
        shape = sp(image_np, face)
        face_descriptor = facerec.compute_face_descriptor(image_np, shape, 1)  # 128 embedding
        encodings.append(np.array(face_descriptor))
    return encodings


# Module-level cache for trained classifier model
_trained_model_cache = None


def get_trained_model():
    """
    Retrieves or fits the linear SVM classifier on all registered students' face embeddings.
    """
    global _trained_model_cache
    if _trained_model_cache is not None:
        return _trained_model_cache

    X = []
    y = []

    student_db = get_all_students()
    if not student_db:
        return None

    for student in student_db:
        embedding = student.get('face_embedding')
        if embedding:
            X.append(np.array(embedding))
            y.append(student.get('student_id'))

    if len(X) == 0:
        return None

    clf = SVC(kernel='linear', probability=True, class_weight='balanced')
    try:
        clf.fit(X, y)
    except ValueError:
        pass

    _trained_model_cache = {'clf': clf, 'X': X, 'y': y}
    return _trained_model_cache


def train_classifier():
    """
    Clears cache and retrains the classifier with updated students in database.
    """
    global _trained_model_cache
    _trained_model_cache = None
    model_data = get_trained_model()
    return bool(model_data)


def predict_attendance(class_image_np: np.ndarray):
    """
    Scans a classroom photo, extracts face embeddings, performs SVM prediction,
    and applies Euclidean distance resemblance threshold (0.6) to prevent false positives.
    Returns:
        detected_student: dict of {student_id: True}
        all_students: list of all student IDs trained
        num_faces: number of faces found in the image
    """
    encodings = get_face_embeddings(class_image_np)
    detected_student = {}

    model_data = get_trained_model()
    if not model_data:
        return detected_student, [], len(encodings)

    clf = model_data['clf']
    X_train = model_data['X']
    y_train = model_data['y']

    all_students = sorted(list(set(y_train)))

    for encoding in encodings:
        if len(all_students) >= 2:
            predicted_id = int(clf.predict([encoding])[0])
        else:
            predicted_id = int(all_students[0])

        student_embedding = X_train[y_train.index(predicted_id)]
        best_match_score = np.linalg.norm(student_embedding - encoding)
        resemblance_threshold = 0.6

        if best_match_score <= resemblance_threshold:
            detected_student[predicted_id] = True

    return detected_student, all_students, len(encodings)
