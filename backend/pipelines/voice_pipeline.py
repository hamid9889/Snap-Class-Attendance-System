"""
Voice recognition pipeline wrapper.
Delegates to backend.voice_recognition for backward compatibility.
"""
from backend.voice_recognition import (
    load_audio_to_mono_16k,
    preprocess_audio_signal,
    extract_mfcc_embedding,
    get_voice_embedding,
    compute_cosine_similarity,
    identify_speaker,
    process_bulk_audio,
    DEFAULT_VOICE_THRESHOLD,
)

__all__ = [
    "load_audio_to_mono_16k",
    "preprocess_audio_signal",
    "extract_mfcc_embedding",
    "get_voice_embedding",
    "compute_cosine_similarity",
    "identify_speaker",
    "process_bulk_audio",
    "DEFAULT_VOICE_THRESHOLD",
]
