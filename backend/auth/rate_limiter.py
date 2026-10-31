"""
Krishi Mitra — OTP Request Rate Limiter
Tracks request frequencies per phone number and IP address to mitigate abuse and SMS bombing.
"""

import time
import threading
from typing import Dict, List, Tuple
from backend.auth.config import (
    RATE_LIMIT_PHONE_MAX,
    RATE_LIMIT_IP_MAX,
    RATE_LIMIT_WINDOW_SECONDS,
)

_lock = threading.Lock()
_phone_timestamps: Dict[str, List[float]] = {}
_ip_timestamps: Dict[str, List[float]] = {}


def check_and_record_rate_limit(phone: str, ip: str) -> Tuple[bool, str]:
    """
    Checks if phone or IP has exceeded request limit within the sliding time window.
    Records request if allowed.
    Returns (is_allowed, error_message).
    """
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS

    with _lock:
        # Prune and check phone
        phone_times = [t for t in _phone_timestamps.get(phone, []) if t > cutoff]
        _phone_timestamps[phone] = phone_times
        if len(phone_times) >= RATE_LIMIT_PHONE_MAX:
            return False, "Too many OTP requests for this phone number. Please wait before requesting again."

        # Prune and check IP
        ip_times = [t for t in _ip_timestamps.get(ip, []) if t > cutoff]
        _ip_timestamps[ip] = ip_times
        if len(ip_times) >= RATE_LIMIT_IP_MAX:
            return False, "Too many OTP requests from your network. Please wait before requesting again."

        # Record this request
        phone_times.append(now)
        ip_times.append(now)
        return True, ""


def reset_rate_limits():
    """Resets rate limiting state (used for testing)."""
    with _lock:
        _phone_timestamps.clear()
        _ip_timestamps.clear()
