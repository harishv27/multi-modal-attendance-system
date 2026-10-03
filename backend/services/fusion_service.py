def check_fallback_rules(face_score: float | None, fingerprint_score: float | None, palm_score: float | None, thresholds: dict) -> dict:
    """
    Implements fallback rules if some modalities fail or are missing.
    Returns {verified: bool, reason: str}
    """
    # 1. All three present
    if face_score is not None and fingerprint_score is not None and palm_score is not None:
        if face_score >= thresholds.get('FACE_THRESHOLD', 0.5) and fingerprint_score >= thresholds.get('FINGERPRINT_THRESHOLD', 0.75) and palm_score >= thresholds.get('PALM_THRESHOLD', 0.7):
            return {"verified": True, "reason": "All modalities matched"}
            
    # 2. Face + Fingerprint
    if face_score is not None and fingerprint_score is not None:
        if face_score >= thresholds.get('FACE_THRESHOLD', 0.5) and fingerprint_score >= thresholds.get('FINGERPRINT_THRESHOLD', 0.75):
            return {"verified": True, "reason": "Face and Fingerprint matched"}

    # 3. Face + Palm
    if face_score is not None and palm_score is not None:
        if face_score >= thresholds.get('FACE_THRESHOLD', 0.5) and palm_score >= thresholds.get('PALM_THRESHOLD', 0.7):
            return {"verified": True, "reason": "Face and Palm matched"}
            
    return {"verified": False, "reason": "Fallback rules not met"}

def fuse_scores(face_score: float | None, fingerprint_score: float | None, palm_score: float | None, weights: dict, thresholds: dict) -> dict:
    """
    Multi-modal score fusion.
    """
    scores = {}
    active_weights = {}
    
    if face_score is not None:
        scores['face'] = face_score
        active_weights['face'] = weights.get('FACE', 0.45)
        
    if fingerprint_score is not None:
        scores['fingerprint'] = fingerprint_score
        active_weights['fingerprint'] = weights.get('FINGERPRINT', 0.35)
        
    if palm_score is not None:
        scores['palm'] = palm_score
        active_weights['palm'] = weights.get('PALM', 0.20)
        
    if not scores:
        return {
            "fusion_score": 0.0,
            "decision": "rejected",
            "modalities_used": [],
            "individual_scores": {},
            "message": "No modalities provided"
        }
        
    # Normalize weights
    total_weight = sum(active_weights.values())
    if total_weight == 0:
        normalized_weights = {k: 1.0/len(active_weights) for k in active_weights}
    else:
        normalized_weights = {k: v/total_weight for k, v in active_weights.items()}
        
    # Calculate fusion score
    fusion_score = 0.0
    for mod in scores:
        fusion_score += scores[mod] * normalized_weights[mod]
        
    # Decision Logic
    fusion_threshold = thresholds.get('FUSION_THRESHOLD', 0.60)
    
    if fusion_score >= fusion_threshold:
        decision = "verified"
        message = "Successfully verified via fusion"
    else:
        # Check fallback rules
        fallback = check_fallback_rules(face_score, fingerprint_score, palm_score, thresholds)
        if fallback['verified']:
            decision = "verified"
            message = f"Verified via fallback: {fallback['reason']}"
        else:
            if fusion_score >= fusion_threshold - 0.1: # Marginally failed
                decision = "needs_review"
                message = "Verification score borderline, requires manual review"
            else:
                decision = "rejected"
                message = "Verification failed"
                
    return {
        "fusion_score": float(fusion_score),
        "decision": decision,
        "modalities_used": list(scores.keys()),
        "individual_scores": scores,
        "message": message
    }
