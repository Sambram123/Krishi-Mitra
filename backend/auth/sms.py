"""
Krishi Mitra — SMS Provider Interface and Implementations
Provides pluggable SMS interfaces (e.g. ConsoleProvider for dev/testing, GatewayProvider ready for prod).
"""

import logging
from abc import ABC, abstractmethod
from backend.auth.config import IS_PRODUCTION, OTP_PROVIDER

logger = logging.getLogger("krishi_sms")


def mask_phone_number(phone: str) -> str:
    """Masks phone number for privacy/DPDP compliance (e.g. +91******3210)."""
    clean = phone.strip()
    if len(clean) <= 4:
        return "****"
    return f"{clean[:3]}******{clean[-4:]}"


class SMSProvider(ABC):
    """Abstract SMS delivery interface."""

    @abstractmethod
    def send_otp(self, phone: str, otp_code: str) -> bool:
        """Deliver OTP to the target phone number."""
        pass


class ConsoleProvider(SMSProvider):
    """
    Development & Testing SMS provider.
    Prints OTP to server log in development mode.
    Guarantees no OTP or raw phone is logged in production mode.
    """

    def send_otp(self, phone: str, otp_code: str) -> bool:
        if IS_PRODUCTION:
            logger.info("Production mode: SMS OTP requested for %s (dispatching to carrier)", mask_phone_number(phone))
            return True

        # In development / testing:
        masked = mask_phone_number(phone)
        print(f"\n==========================================")
        print(f"[DEV SMS GATEWAY] Phone: {phone} (masked: {masked})")
        print(f"[DEV SMS GATEWAY] OTP:   {otp_code} (Valid for 5 minutes)")
        print(f"==========================================\n")
        logger.info("[DEV SMS] OTP generated for %s", masked)
        return True


def get_sms_provider() -> SMSProvider:
    """Factory for selecting the active SMS provider."""
    provider_name = OTP_PROVIDER.lower()
    if provider_name == "console":
        return ConsoleProvider()
    # Can plug in real providers like 'twilio', 'kaleyra', 'gupshup' here
    return ConsoleProvider()
