#!/usr/bin/env python3
"""
ONTO Enterprise Security Hardening Module

Critical patches for enterprise readiness:
1. Safe logging (no secrets)
2. Rate limiting
3. Report tamper resistance
4. Request validation
"""

import hashlib
import hmac
import time
from datetime import datetime
from functools import wraps
from typing import Dict, Any, Optional
import json
import logging

# ============================================================
# SAFE LOGGING
# ============================================================

SAFE_LOG_FIELDS = {
    "evaluation_id",
    "model_name", 
    "organization",
    "timestamp",
    "status",
    "n_samples",
    "risk_level",
}

REDACTED_FIELDS = {
    "api_key",
    "model_endpoint",
    "credentials",
    "password",
    "secret",
    "token",
    "authorization",
}

def safe_log(data: Dict[str, Any], level: str = "info") -> Dict[str, Any]:
    """
    Log only safe fields, redact secrets.
    NEVER log customer credentials or model endpoints.
    """
    safe_data = {}
    
    for key, value in data.items():
        key_lower = key.lower()
        
        # Skip redacted fields entirely
        if any(redact in key_lower for redact in REDACTED_FIELDS):
            safe_data[key] = "[REDACTED]"
            continue
        
        # Include only safe fields, or sanitize
        if key in SAFE_LOG_FIELDS:
            safe_data[key] = value
        elif isinstance(value, dict):
            safe_data[key] = safe_log(value, level)
        elif isinstance(value, str) and len(value) > 100:
            safe_data[key] = f"{value[:50]}...[truncated]"
        else:
            safe_data[key] = value
    
    # Log based on level
    logger = logging.getLogger("onto.enterprise")
    log_func = getattr(logger, level, logger.info)
    log_func(json.dumps(safe_data, default=str))
    
    return safe_data


class SecureLogger:
    """Enterprise-grade logging with automatic redaction"""
    
    def __init__(self, name: str = "onto.enterprise"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Structured JSON handler
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '{"time": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}'
        ))
        self.logger.addHandler(handler)
    
    def info(self, msg: str, **kwargs):
        self.logger.info(json.dumps({"msg": msg, **safe_log(kwargs)}))
    
    def warning(self, msg: str, **kwargs):
        self.logger.warning(json.dumps({"msg": msg, **safe_log(kwargs)}))
    
    def error(self, msg: str, **kwargs):
        self.logger.error(json.dumps({"msg": msg, **safe_log(kwargs)}))
    
    def audit(self, action: str, user_id: str, resource: str, **kwargs):
        """Audit log for compliance"""
        self.logger.info(json.dumps({
            "audit": True,
            "action": action,
            "user_id": user_id,
            "resource": resource,
            "timestamp": datetime.utcnow().isoformat(),
            **safe_log(kwargs),
        }))


# ============================================================
# RATE LIMITING
# ============================================================

class RateLimiter:
    """
    Simple in-memory rate limiter.
    Production: use Redis for distributed limiting.
    """
    
    def __init__(self):
        self.requests: Dict[str, list] = {}
        
        # Tier limits (requests per minute)
        self.limits = {
            "pilot": 5,
            "starter": 20,
            "pro": 100,
            "enterprise": 500,
        }
    
    def check(self, api_key: str, tier: str) -> tuple[bool, Optional[str]]:
        """
        Check if request is allowed.
        Returns (allowed, error_message)
        """
        now = time.time()
        window = 60  # 1 minute
        
        # Get limit for tier
        limit = self.limits.get(tier, 5)
        
        # Clean old requests
        if api_key not in self.requests:
            self.requests[api_key] = []
        
        self.requests[api_key] = [
            ts for ts in self.requests[api_key] 
            if now - ts < window
        ]
        
        # Check limit
        if len(self.requests[api_key]) >= limit:
            return False, f"Rate limit exceeded. {limit} requests per minute for {tier} tier."
        
        # Record request
        self.requests[api_key].append(now)
        return True, None
    
    def get_remaining(self, api_key: str, tier: str) -> int:
        """Get remaining requests in current window"""
        limit = self.limits.get(tier, 5)
        current = len(self.requests.get(api_key, []))
        return max(0, limit - current)


def rate_limit(limiter: RateLimiter):
    """Decorator for rate limiting endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract customer from kwargs (set by auth middleware)
            customer = kwargs.get("customer", {})
            api_key = customer.get("api_key", "unknown")
            tier = customer.get("tier", "pilot")
            
            allowed, error = limiter.check(api_key, tier)
            if not allowed:
                from fastapi import HTTPException
                raise HTTPException(status_code=429, detail=error)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================
# REPORT INTEGRITY
# ============================================================

class ReportIntegrity:
    """
    Tamper-resistant report storage.
    Provides hash-based verification for compliance.
    """
    
    def __init__(self, secret_key: str = "onto-report-integrity-key"):
        self.secret_key = secret_key.encode()
    
    def compute_hash(self, report_data: Dict) -> str:
        """Compute HMAC-SHA256 hash of report"""
        canonical = json.dumps(report_data, sort_keys=True, default=str)
        return hmac.new(
            self.secret_key,
            canonical.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def sign_report(self, report_data: Dict) -> Dict:
        """Add integrity signature to report"""
        report_hash = self.compute_hash(report_data)
        return {
            **report_data,
            "_integrity": {
                "hash": report_hash,
                "algorithm": "HMAC-SHA256",
                "signed_at": datetime.utcnow().isoformat(),
            }
        }
    
    def verify_report(self, report_data: Dict) -> tuple[bool, str]:
        """Verify report hasn't been tampered with"""
        if "_integrity" not in report_data:
            return False, "Missing integrity signature"
        
        stored_hash = report_data["_integrity"]["hash"]
        
        # Remove integrity block for hash computation
        data_without_integrity = {
            k: v for k, v in report_data.items() 
            if k != "_integrity"
        }
        
        computed_hash = self.compute_hash(data_without_integrity)
        
        if hmac.compare_digest(stored_hash, computed_hash):
            return True, "Report integrity verified"
        else:
            return False, "Report has been modified"


# ============================================================
# INPUT VALIDATION
# ============================================================

def validate_predictions(predictions: list) -> tuple[bool, Optional[str]]:
    """
    Validate prediction format and content.
    Prevent injection and malformed data.
    """
    if not predictions:
        return False, "Predictions list is empty"
    
    if len(predictions) > 10000:
        return False, "Too many predictions (max 10000)"
    
    valid_labels = {"KNOWN", "UNKNOWN", "CONTRADICTION"}
    
    for i, pred in enumerate(predictions):
        # Check required fields
        if "id" not in pred:
            return False, f"Prediction {i}: missing 'id' field"
        if "label" not in pred:
            return False, f"Prediction {i}: missing 'label' field"
        if "confidence" not in pred:
            return False, f"Prediction {i}: missing 'confidence' field"
        
        # Validate types
        if not isinstance(pred["id"], str):
            return False, f"Prediction {i}: 'id' must be string"
        if pred["label"] not in valid_labels:
            return False, f"Prediction {i}: invalid label '{pred['label']}'"
        
        # Validate confidence
        conf = pred["confidence"]
        if not isinstance(conf, (int, float)):
            return False, f"Prediction {i}: 'confidence' must be numeric"
        if not 0 <= conf <= 1:
            return False, f"Prediction {i}: 'confidence' must be between 0 and 1"
        
        # Sanitize ID (prevent injection)
        if len(pred["id"]) > 100:
            return False, f"Prediction {i}: 'id' too long (max 100 chars)"
        if not pred["id"].replace("_", "").replace("-", "").isalnum():
            return False, f"Prediction {i}: 'id' contains invalid characters"
    
    return True, None


def sanitize_string(s: str, max_length: int = 200) -> str:
    """Sanitize string input"""
    if not isinstance(s, str):
        return ""
    # Remove control characters
    s = "".join(c for c in s if c.isprintable() or c in "\n\t")
    # Truncate
    return s[:max_length]


# ============================================================
# USAGE EXAMPLE
# ============================================================

if __name__ == "__main__":
    # Test safe logging
    logger = SecureLogger()
    logger.info("Evaluation started", 
        evaluation_id="eval_123",
        api_key="secret_key_here",  # Will be redacted
        model_name="gpt-4"
    )
    
    # Test rate limiter
    limiter = RateLimiter()
    for i in range(7):
        allowed, err = limiter.check("key_123", "pilot")
        print(f"Request {i+1}: {'allowed' if allowed else err}")
    
    # Test report integrity
    integrity = ReportIntegrity()
    report = {"model": "test", "risk_score": 75}
    signed = integrity.sign_report(report)
    print(f"Signed report: {signed}")
    
    valid, msg = integrity.verify_report(signed)
    print(f"Verification: {msg}")
    
    # Tamper and re-verify
    signed["risk_score"] = 10
    valid, msg = integrity.verify_report(signed)
    print(f"After tamper: {msg}")
