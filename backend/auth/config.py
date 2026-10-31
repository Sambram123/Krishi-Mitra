"""
Krishi Mitra — Authentication Configuration
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Ensure environment is loaded
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"), override=False)

logger = logging.getLogger("krishi_auth")

APP_ENV = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).lower()
IS_PRODUCTION = APP_ENV in ("production", "prod")

JWT_SECRET = os.getenv("JWT_SECRET")

# Fail startup if JWT_SECRET is missing in production mode
if IS_PRODUCTION and not JWT_SECRET:
    raise RuntimeError("FATAL: JWT_SECRET environment variable is missing in production mode!")

if not JWT_SECRET:
    # Use deterministic fallback for development/testing only
    JWT_SECRET = "dev-insecure-secret-key-change-in-production-32bytes-min"
    if not IS_PRODUCTION:
        logger.warning("WARNING: JWT_SECRET not set; using development fallback secret.")

ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))
OTP_PROVIDER = os.getenv("OTP_PROVIDER", "console").lower()

# Rate limiting settings
OTP_EXPIRY_MINUTES = 5
OTP_MAX_ATTEMPTS = 5
RATE_LIMIT_PHONE_MAX = 5
RATE_LIMIT_IP_MAX = 10
RATE_LIMIT_WINDOW_SECONDS = 600  # 10 minutes


def assert_production_config():
    """Explicitly verify production requirements at server startup."""
    current_env = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development")).lower()
    secret = os.getenv("JWT_SECRET")
    if current_env in ("production", "prod") and not secret:
        raise RuntimeError("FATAL: JWT_SECRET environment variable is missing in production mode!")
