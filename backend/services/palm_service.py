"""
Palm Recognition Service
Uses MediaPipe Hands to extract 21 3D hand landmarks (63 features total).
MediaPipe is imported lazily (inside a factory function) so a missing or
broken mediapipe install does NOT crash the server at startup.

Matching uses cosine similarity between landmark feature vectors.
"""

import numpy as np
import base64
import io
from PIL import Image


# Module-level holder for the MediaPipe Hands instance (initialized once, lazily)
_hands_instance = None


def _get_hands():
    """
    Lazily initialize MediaPipe Hands.
    Runs once and caches the instance for reuse (it's expensive to create).
    """
    global _hands_instance
    if _hands_instance is None:
        try:
            import mediapipe as mp
            _hands_instance = mp.solutions.hands.Hands(
                static_image_mode=True,
                max_num_hands=1,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
        except Exception as e:
            raise RuntimeError(
                f"MediaPipe failed to initialize: {e}\n"
                "Run: pip install mediapipe"
            )
    return _hands_instance


def decode_image(image_bytes: bytes) -> np.ndarray:
    """Decode a base64 image (data URL or raw base64) into a numpy RGB array."""
    try:
        if isinstance(image_bytes, str):
            image_bytes = image_bytes.encode("utf-8")
        if image_bytes.startswith(b"data:image"):
            image_bytes = image_bytes.split(b",", 1)[1]
        decoded = base64.b64decode(image_bytes)
        image = Image.open(io.BytesIO(decoded)).convert("RGB")
        return np.array(image)
    except Exception as e:
        raise ValueError(f"Invalid image format: {e}")


def extract_palm_features(image_bytes: bytes) -> dict:
    """
    Detect a hand in the image and extract a 63-dimensional feature vector
    from 21 MediaPipe hand landmarks (x, y, z for each landmark).

    Auto-detects which hand (left/right) is shown. No enforcement — the caller
    stores whichever hand the user presented.

    Args:
        image_bytes: Raw bytes or base64-encoded image (data URL accepted).

    Returns:
        dict with keys:
            embedding  (list[float], length 63),
            quality_score (float),
            hand_side  (str — "left" or "right")

    Raises:
        ValueError: If no hand is detected in the image.
        RuntimeError: If MediaPipe is not available.
    """
    hands = _get_hands()
    image_array = decode_image(image_bytes)

    results = hands.process(image_array)

    if not results.multi_hand_landmarks:
        raise ValueError(
            "No palm/hand detected in the image. "
            "Please hold your open palm flat, facing the camera, "
            "and ensure good lighting."
        )

    landmarks = results.multi_hand_landmarks[0]

    # --- Auto-detect handedness ------------------------------------------------
    # react-webcam captures a MIRRORED screenshot (scaleX(-1) applied before
    # screenshot). MediaPipe labels from the camera perspective of that image.
    # Because the image is already mirrored, MediaPipe "Left" = user's Left
    # and MediaPipe "Right" = user's Right — no flip needed.
    detected_label = "right"   # safe default
    if results.multi_handedness:
        mp_label = results.multi_handedness[0].classification[0].label
        detected_label = mp_label.lower()   # "left" or "right" — no flip

    # --- Extract & normalise landmarks ----------------------------------------
    raw = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])  # (21,3)

    # Translate so wrist (landmark 0) is at origin
    wrist = raw[0]
    normalized = raw - wrist

    # Scale by distance from wrist to middle-finger MCP (landmark 9)
    span = np.linalg.norm(normalized[9])
    if span > 0:
        normalized = normalized / span

    embedding = normalized.flatten().tolist()   # 63 floats

    return {"embedding": embedding, "quality_score": 1.0, "hand_side": detected_label}




def compare_palms(stored_embedding: list, live_embedding: list, threshold: float) -> dict:
    """
    Compare two palm embeddings using cosine similarity.
    Cosine similarity = 1.0 means identical direction (same hand shape).

    Returns:
        dict: {match: bool, score: float}
    """
    try:
        stored = np.array(stored_embedding)
        live = np.array(live_embedding)

        norm_s = np.linalg.norm(stored)
        norm_l = np.linalg.norm(live)

        if norm_s == 0 or norm_l == 0:
            return {"match": False, "score": 0.0}

        score = float(np.dot(stored, live) / (norm_s * norm_l))
        # Clamp to [0, 1] — cosine can be negative for very different vectors
        score = max(0.0, score)
        match = score >= threshold

        return {"match": bool(match), "score": round(score, 4)}
    except Exception:
        return {"match": False, "score": 0.0}


def get_best_match(live_embedding: list, all_embeddings: list, threshold: float = 0.70) -> dict:
    """
    Find the best-matching student palm from enrolled templates.

    Args:
        live_embedding: The 63-float embedding from the live capture.
        all_embeddings: List of dicts, each with {student_id, embedding}.
        threshold: Minimum cosine similarity score to accept as a match.

    Returns:
        dict: {student_id, score, match}
    """
    best = {"student_id": None, "score": 0.0, "match": False}

    for entry in all_embeddings:
        result = compare_palms(entry["embedding"], live_embedding, threshold)
        if result["score"] > best["score"]:
            best["score"] = result["score"]
            best["student_id"] = entry["student_id"]
            best["match"] = result["match"]

    return best

def check_duplicate_palm(new_embedding: list, all_embeddings: list, duplicate_threshold: float = 0.95) -> dict:
    """
    Check if a newly captured palm is already enrolled under a different student.
    Uses a stricter threshold (0.95) than normal matching.

    Returns:
        dict: {is_duplicate: bool, existing_student_id: int|None, score: float}
    """
    best_score = 0.0
    existing_id = None

    for entry in all_embeddings:
        result = compare_palms(entry["embedding"], new_embedding, duplicate_threshold)
        if result["score"] > best_score:
            best_score = result["score"]
            if result["match"]:
                existing_id = entry["student_id"]

    return {
        "is_duplicate": existing_id is not None,
        "existing_student_id": existing_id,
        "score": round(best_score, 4)
    }
