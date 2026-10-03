import random
import base64
import uuid

# This is a simulated fingerprint service.
# In a real-world scenario, you would integrate a real SDK here (e.g., DigitalPersona, SecuGen).
# The real SDK would handle image capture, template extraction, and matching.

def enroll_fingerprint(image_bytes: bytes = None) -> dict:
    """
    Simulates fingerprint enrollment.
    Generates a random base64 string as a template.
    """
    # Simulate extraction process
    simulated_template = base64.b64encode(uuid.uuid4().bytes).decode('utf-8')
    return {
        "template": simulated_template,
        "quality_score": round(random.uniform(0.8, 1.0), 2)
    }

def verify_fingerprint(stored_template: str, live_scan: bytes = None, threshold: float = 0.75) -> dict:
    """
    Simulates fingerprint verification.
    """
    # Simulate matching process - we will return a realistic high score to simulate a match 
    # if it's the correct user in our simulated flow, but realistically we just randomly decide for simulation
    # Let's say if we call this, it means we 'found' the user in the mock UI and it's a match.
    simulated_score = round(random.uniform(0.75, 0.99), 2)
    match = simulated_score >= threshold
    
    return {
        "match": match,
        "score": simulated_score
    }

def get_best_match(live_scan: bytes, all_templates: list[dict], threshold: float = 0.75) -> dict:
    """
    Simulates 1:N fingerprint matching.
    """
    best_match = {"student_id": None, "score": 0.0, "match": False}
    
    # In simulation, we might randomly pick one or fail. 
    # For a deterministic demo, we might just assume the first one matches if we simulate a successful scan.
    # But since it's random simulation:
    if all_templates:
        # randomly pick a winner
        winner = random.choice(all_templates)
        simulated_score = round(random.uniform(0.75, 0.99), 2)
        best_match['student_id'] = winner['student_id']
        best_match['score'] = simulated_score
        best_match['match'] = simulated_score >= threshold
        
    return best_match
