from __future__ import annotations

import logging

import aiohttp
import orjson

from src.config import config

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


class EmailService:
    def __init__(self) -> None:
        self._api_key = config.BREVO_API_KEY
        self._sender_email = config.SMTP_EMAIL

    async def send_otp_email(self, to_email: str, otp: str, purpose: str = "verification") -> None:
        subject = f"Amantra - Your OTP for {purpose}"
        html = f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px;">
  <div style="max-width:480px;margin:auto;background:#fff;border-radius:8px;padding:32px;text-align:center;">
    <h2 style="color:#333;">Amantra</h2>
    <p style="color:#555;">Your OTP for <strong>{purpose}</strong> is:</p>
    <div style="font-size:32px;letter-spacing:8px;font-weight:bold;color:#4f46e5;margin:24px 0;">{otp}</div>
    <p style="color:#888;font-size:13px;">This code expires in 10 minutes. Do not share it with anyone.</p>
  </div>
</body>
</html>"""

        payload = {
            "sender": {"name": "Amantra", "email": self._sender_email},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html,
        }

        async with aiohttp.ClientSession() as session, session.post(
            BREVO_API_URL,
            headers={
                "api-key": self._api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            data=orjson.dumps(payload),
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status >= 400:
                body = await resp.text()
                logger.error("Brevo API error %d: %s", resp.status, body)
                raise RuntimeError(f"Brevo email failed ({resp.status}): {body}")
            logger.info("OTP email sent to %s via Brevo", to_email)
