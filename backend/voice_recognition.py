"""
SnapClass Attendance System - Optimized Voice Recognition Pipeline
===================================================================
Provides high-accuracy speaker identification and classroom audio attendance
scanning using Librosa MFCC feature extraction and Cosine Similarity verification.

Pipeline Architecture:
----------------------
1. Audio Preprocessing:
   - Mono conversion & 16kHz resampling (standardized acoustic sampling).
   - Peak volume normalization via librosa.util.normalize.
   - Silence trimming & background noise suppression (librosa.effects.trim).
   - Pre-emphasis filtering (boosts vocal formants, suppresses room low-end).

2. Feature Extraction:
   - 20-band Mel-Frequency Cepstral Coefficients (MFCCs).
   - 1st-order Delta (velocity) and 2nd-order Delta-Delta (acceleration) dynamics.
   - Statistical aggregation across time: temporal mean & standard deviation.
   - L2 unit hypersphere normalization (||v|| = 1.0).

3. Speaker Matching & Attendance:
   - Cosine similarity verification between student voice embeddings.
   - High-confidence verification threshold (0.85) to eliminate false positives.
   - Bulk classroom audio segmentation for multi-student roll-call scanning.

Supabase Storage:
-----------------
The 120-dimensional L2-normalized embedding vector is stored as a JSON float array
in the 'students.voice_embedding' column.
"""
import io
import logging
from typing import Dict, Optional, Tuple, List, Sequence
import numpy as np
import soundfile as sf
import librosa

logger = logging.getLogger(__name__)

# Default recognition threshold to minimize false positives
DEFAULT_VOICE_THRESHOLD = 0.85
TARGET_SAMPLE_RATE = 16000


# ==============================================================================
# 1. AUDIO PREPROCESSING UTILITIES
# ==============================================================================
def load_audio_to_mono_16k(audio_bytes: bytes, target_sr: int = TARGET_SAMPLE_RATE) -> np.ndarray:
    """
    Decodes raw audio bytes (WAV, MP3, OGG, FLAC) into a single-channel (mono)
    16kHz float32 NumPy array.
    
    Args:
        audio_bytes: Raw audio byte buffer from HTTP request or file.
        target_sr: Desired output sampling rate (default 16000 Hz).
        
    Returns:
        1D float32 NumPy array of normalized audio samples.
    """
    if not audio_bytes or len(audio_bytes) == 0:
        raise ValueError("Audio buffer is empty.")

    buffer = io.BytesIO(audio_bytes)

    try:
        # First attempt: high-performance soundfile decoder
        data, sr = sf.read(buffer)
        if data.ndim > 1:
            data = np.mean(data, axis=1)  # Downmix stereo to mono
        if sr != target_sr:
            data = librosa.resample(data.astype(np.float32), orig_sr=sr, target_sr=target_sr)
        return data.astype(np.float32)
    except Exception as sf_err:
        logger.debug(f"Soundfile decoder fallback to librosa.load: {sf_err}")
        buffer.seek(0)
        y, _ = librosa.load(buffer, sr=target_sr, mono=True)
        return y.astype(np.float32)


def preprocess_audio_signal(
    audio: np.ndarray,
    top_db: float = 20.0,
    pre_emphasis_coeff: float = 0.97
) -> np.ndarray:
    """
    Performs volume normalization, silence trimming, and pre-emphasis filtering.
    
    Args:
        audio: 1D audio sample array.
        top_db: Decibels below peak to treat as silence (default 20 dB).
        pre_emphasis_coeff: First-order high-pass filter coefficient (default 0.97).
        
    Returns:
        Preprocessed 1D float32 audio array.
    """
    if len(audio) == 0:
        return audio

    # 1. Trim silence: Strip non-speech dead air from boundaries
    trimmed, _ = librosa.effects.trim(audio, top_db=top_db)
    if len(trimmed) > 0:
        audio = trimmed

    # 2. Pre-emphasis filter: Amplifies high-frequency vocal formants & balances spectrum
    if len(audio) > 1:
        audio = np.append(audio[0], audio[1:] - pre_emphasis_coeff * audio[:-1])

    # 3. Peak Volume Normalization: Scale amplitude uniformly to [-1.0, 1.0]
    audio = librosa.util.normalize(audio)

    return audio.astype(np.float32)


# ==============================================================================
# 2. ROBUST FEATURE EXTRACTION (MFCC + DELTAS)
# ==============================================================================
def extract_mfcc_embedding(
    audio: np.ndarray,
    sr: int = TARGET_SAMPLE_RATE,
    n_mfcc: int = 20
) -> Optional[np.ndarray]:
    """
    Extracts an L2-normalized 120-dimensional feature embedding vector from audio:
    - 20 MFCC means & 20 MFCC standard deviations (vocal tract envelope)
    - 20 Delta means & 20 Delta standard deviations (velocity dynamics)
    - 20 Delta-Delta means & 20 Delta-Delta standard deviations (acceleration dynamics)
    
    Args:
        audio: Preprocessed 16kHz mono audio array.
        sr: Sample rate (16000 Hz).
        n_mfcc: Number of Mel-frequency cepstral coefficients (default 20).
        
    Returns:
        L2-normalized 1D NumPy array of shape (120,), or None if audio is insufficient.
    """
    if audio is None or len(audio) < sr * 0.25:
        # Require at least 250ms of active speech for meaningful cepstral analysis
        return None

    try:
        # Compute MFCCs with 32ms window and 10ms hop
        mfcc = librosa.feature.mfcc(
            y=audio,
            sr=sr,
            n_mfcc=n_mfcc,
            n_fft=512,
            hop_length=160
        )

        # 1st-order Delta (spectral velocity)
        delta = librosa.feature.delta(mfcc)

        # 2nd-order Delta-Delta (spectral acceleration)
        delta2 = librosa.feature.delta(mfcc, order=2)

        # Aggregate temporal statistics across frames
        feature_vector = np.concatenate([
            np.mean(mfcc, axis=1),    # 20
            np.std(mfcc, axis=1),     # 20
            np.mean(delta, axis=1),   # 20
            np.std(delta, axis=1),    # 20
            np.mean(delta2, axis=1),  # 20
            np.std(delta2, axis=1)    # 20
        ]).astype(np.float32)         # Total: 120 dimensions

        # L2-normalize to unit hypersphere
        norm = float(np.linalg.norm(feature_vector))
        if norm > 0:
            feature_vector = feature_vector / norm
        else:
            return None

        return feature_vector
    except Exception as e:
        logger.error(f"Error computing MFCC features: {e}")
        return None


def get_voice_embedding(audio_bytes: bytes) -> Optional[List[float]]:
    """
    End-to-end extraction: converts raw audio bytes into an L2-normalized
    120-dimensional voice embedding list for Supabase storage and verification.
    
    Args:
        audio_bytes: Raw audio byte buffer from upload or recording.
        
    Returns:
        List of 120 floats representing the student's voice embedding, or None on error.
    """
    try:
        raw_audio = load_audio_to_mono_16k(audio_bytes, target_sr=TARGET_SAMPLE_RATE)
        clean_audio = preprocess_audio_signal(raw_audio)
        embedding = extract_mfcc_embedding(clean_audio, sr=TARGET_SAMPLE_RATE)
        if embedding is not None:
            return embedding.tolist()
        return None
    except Exception as e:
        logger.error(f"Failed to generate voice embedding: {e}")
        return None


# ==============================================================================
# 3. ACCURATE VOICE MATCHING (COSINE SIMILARITY & THRESHOLDING)
# ==============================================================================
def compute_cosine_similarity(vec1: Sequence[float], vec2: Sequence[float]) -> float:
    """
    Computes bounded cosine similarity between two embedding vectors:
        similarity = (u . v) / (||u|| * ||v||)
    
    Returns:
        Float similarity score in [-1.0, 1.0].
    """
    u = np.asarray(vec1, dtype=np.float32)
    v = np.asarray(vec2, dtype=np.float32)

    norm_u = float(np.linalg.norm(u))
    norm_v = float(np.linalg.norm(v))

    if norm_u == 0.0 or norm_v == 0.0:
        return 0.0

    dot_product = float(np.dot(u, v))
    similarity = dot_product / (norm_u * norm_v)
    return max(-1.0, min(1.0, similarity))


def identify_speaker(
    new_embedding: Sequence[float],
    candidates_dict: Dict[int, List[float]],
    threshold: float = DEFAULT_VOICE_THRESHOLD
) -> Tuple[Optional[int], float]:
    """
    Matches a voice embedding against a dictionary of enrolled candidates using
    cosine similarity verification.
    
    Args:
        new_embedding: 120-d voice embedding of the captured audio.
        candidates_dict: Mapping of student_id -> 120-d voice embedding list from Supabase.
        threshold: Minimum cosine similarity score required for positive match (default 0.85).
        
    Returns:
        Tuple of (best_student_id or None, best_similarity_score).
    """
    if new_embedding is None or not candidates_dict:
        return None, 0.0

    best_sid = None
    best_score = -1.0

    new_emb_len = len(new_embedding)

    for sid, stored_embedding in candidates_dict.items():
        if not stored_embedding:
            continue
        
        # Validate dimensionality compatibility
        if len(stored_embedding) != new_emb_len:
            continue

        score = compute_cosine_similarity(new_embedding, stored_embedding)
        if score > best_score:
            best_score = score
            best_sid = sid

    if best_score >= threshold:
        return best_sid, best_score

    return None, best_score


def process_bulk_audio(
    audio_bytes: bytes,
    candidates_dict: Dict[int, List[float]],
    threshold: float = DEFAULT_VOICE_THRESHOLD
) -> Dict[int, float]:
    """
    Analyzes classroom lecture or roll-call recording:
    1. Resamples to 16kHz mono and normalizes recording volume.
    2. Splits audio stream into distinct speech segments based on silence detection.
    3. Trims, pre-emphasizes, and extracts MFCC embeddings for each active speech segment.
    4. Identifies enrolled students meeting the confidence threshold (>= 0.85).
    
    Args:
        audio_bytes: Raw classroom audio recording.
        candidates_dict: Mapping of {student_id: voice_embedding_list} for enrolled students.
        threshold: Verification threshold (default 0.85).
        
    Returns:
        Dict mapping {student_id: highest_confidence_score} for recognized students.
    """
    try:
        raw_audio = load_audio_to_mono_16k(audio_bytes, target_sr=TARGET_SAMPLE_RATE)
        if len(raw_audio) == 0:
            return {}

        # 1. Normalize recording volume
        norm_audio = librosa.util.normalize(raw_audio)

        # 2. Split continuous audio into active speech intervals (top_db=25)
        segments = librosa.effects.split(
            norm_audio,
            top_db=25,
            frame_length=1024,
            hop_length=256
        )

        # If no split detected (e.g. constant speech or low noise floor), evaluate full track
        if len(segments) == 0 and len(norm_audio) >= TARGET_SAMPLE_RATE * 0.25:
            segments = [(0, len(norm_audio))]

        identified_results: Dict[int, float] = {}

        for start, end in segments:
            # Skip very short audio snippets (< 0.35s) to eliminate transient room noise
            if (end - start) < TARGET_SAMPLE_RATE * 0.35:
                continue

            segment_raw = norm_audio[start:end]
            clean_segment = preprocess_audio_signal(segment_raw)
            segment_embedding = extract_mfcc_embedding(clean_segment, sr=TARGET_SAMPLE_RATE)

            if segment_embedding is None:
                continue

            sid, score = identify_speaker(segment_embedding, candidates_dict, threshold=threshold)
            if sid is not None:
                if sid not in identified_results or score > identified_results[sid]:
                    identified_results[sid] = round(score, 4)

        return identified_results
    except Exception as e:
        logger.error(f"Bulk voice process error: {e}")
        return {}

