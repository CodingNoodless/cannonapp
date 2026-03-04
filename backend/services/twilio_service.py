"""
Twilio WhatsApp Service - Send WhatsApp messages via Twilio
"""

import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)


class TwilioService:
    """Handles WhatsApp messaging via Twilio"""

    def __init__(self):
        self._client = None

    def _get_client(self):
        """Lazy-load Twilio client so missing credentials don't crash startup"""
        if self._client is None:
            if not settings.twilio_account_sid or not settings.twilio_auth_token:
                raise RuntimeError("Twilio credentials not configured")
            from twilio.rest import Client
            self._client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        return self._client

    def _format_phone(self, phone: str) -> str:
        """Ensure number is in whatsapp:+XXXXXXXXXXX format"""
        phone = phone.strip()
        if not phone.startswith("whatsapp:"):
            if not phone.startswith("+"):
                phone = "+" + phone
            phone = f"whatsapp:{phone}"
        return phone

    async def send_whatsapp(self, to_phone: str, message: str) -> bool:
        """
        Send a WhatsApp message to a phone number.
        Returns True on success, False on failure (never raises — so it doesn't break the main flow).
        """
        if not to_phone:
            return False
        try:
            client = self._get_client()
            client.messages.create(
                from_=settings.twilio_whatsapp_from,
                to=self._format_phone(to_phone),
                body=message
            )
            logger.info(f"WhatsApp sent to {to_phone}")
            return True
        except Exception as e:
            logger.error(f"WhatsApp send failed to {to_phone}: {e}")
            return False

    async def send_welcome(self, phone: str, email: str) -> bool:
        """Welcome message sent after successful signup"""
        name = email.split("@")[0].capitalize()
        message = (
            f"👋 Welcome to *Cannon*, {name}!\n\n"
            f"You're now part of the Cannon community — the #1 looksmaxxing platform.\n\n"
            f"🎯 Complete your first face scan to get your personal analysis and score.\n\n"
            f"Let's get started! 🚀"
        )
        return await self.send_whatsapp(phone, message)

    async def send_scan_complete(self, phone: str, email: str, overall_score: Optional[float]) -> bool:
        """Notification sent after a face scan analysis completes"""
        name = email.split("@")[0].capitalize()
        score_text = f"*{overall_score:.1f}/10*" if overall_score is not None else "ready"
        message = (
            f"✅ Hey {name}, your Cannon face scan is complete!\n\n"
            f"📊 Your overall score: {score_text}\n\n"
            f"Open the Cannon app to see your full analysis, breakdown, and personalised recommendations. 💪"
        )
        return await self.send_whatsapp(phone, message)


# Singleton instance
twilio_service = TwilioService()
