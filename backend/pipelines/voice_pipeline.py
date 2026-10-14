"""
Voice Recognition Pipeline for SnapClass Attendance System.
Uses Resemblyzer d-vector voice embeddings and librosa audio preprocessing.
Speaker identification is performed via cosine similarity (dot product of normalized embeddings).
All core algorithms, parameters (sample rate 16000, top_db=30, threshold=0.65), and logic preserved.
"""
from functools import lru_cache
import io
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Safe / Lazy imports for voice analysis dependencies
try:
    import librosa
    from resemblyzer import VoiceEncoder, preprocess_wav
    VOICE_AVAILABLE = True
except Exception as e:
    VOICE_AVAILABLE = False
    logger.warning(f"[VoicePipeline Warning] librosa or resemblyzer not loaded: {e}")


@lru_cache(maxsize=1)
def load_voice_encoder():
    """
    Loads and caches the Resemblyzer deep learning voice encoder model in memory.
    """
    if not VOICE_AVAILABLE:
        raise RuntimeError("librosa and resemblyzer must be installed.")
    return VoiceEncoder()


def get_voice_embedding(audio_bytes: bytes):
    """
    Generates a 256-dimensional d-vector voice embedding from audio bytes.
    """
    try:
        if not VOICE_AVAILABLE:
            logger.error("Voice pipeline dependencies unavailable.")
            return None

        encoder = load_voice_encoder()
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
        wav = preprocess_wav(audio)
        embedding = encoder.embed_utterance(wav)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Voice recognition error in get_voice_embedding: {e}")
        return None


def identify_speaker(new_embedding, candidates_dict: dict, threshold: float = 0.65):
    """
    Identifies a speaker by computing cosine similarity against candidate voice embeddings.
    Returns:
        (best_student_id, best_score)
    """
    if new_embedding is None or not candidates_dict:
        return None, 0.0

    best_sid = None
    best_score = -1.0

    for sid, stored_embedding in candidates_dict.items():
        if stored_embedding:
            similarity = float(np.dot(new_embedding, stored_embedding))
            if similarity > best_score:
                best_score = similarity
                best_sid = sid

    if best_score >= threshold:
        return best_sid, best_score

    return None, best_score


def process_bulk_audio(audio_bytes: bytes, candidates_dict: dict, threshold: float = 0.65):
    """
    Splits continuous classroom recording into speech segments based on silence detection (top_db=30),
    generates voice embeddings for segments >= 0.5 seconds, and matches against registered candidates.
    Returns:
        identified_results: dict mapping {student_id: highest_match_score}
    """
    try:
        if not VOICE_AVAILABLE:
            logger.error("Voice pipeline dependencies unavailable.")
            return {}

        encoder = load_voice_encoder()
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
        segments = librosa.effects.split(audio, top_db=30)

        identified_results = {}

        for start, end in segments:
            # Skip very short audio snippets (< 0.5s)
            if (end - start) < sr * 0.5:
                continue

            segment_audio = audio[start:end]
            wav = preprocess_wav(segment_audio)
            embedding = encoder.embed_utterance(wav)

            sid, score = identify_speaker(embedding, candidates_dict, threshold)
            if sid:
                if sid not in identified_results or score > identified_results[sid]:
                    identified_results[sid] = round(score, 4)

        return identified_results
    except Exception as e:
        logger.error(f"Bulk voice process error: {e}")
        return {}
