from __future__ import annotations

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# local imports
from src.config import config


class EmailService:
    def __init__(self) -> None:
        self._smtp_email = config.SMTP_EMAIL
        self._smtp_password = config.SMTP_PASSWORD

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
        msg = MIMEMultipart("alternative")
        msg["From"] = self._smtp_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html, "html"))

        await aiosmtplib.send(
            msg,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=self._smtp_email,
            password=self._smtp_password,
        )
