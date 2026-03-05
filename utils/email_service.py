"""
Email Service — sends transactional emails (welcome, alerts).
Uses SMTP so it works with any provider: Gmail, Outlook, SendGrid, etc.
Configure via .env — see .env.example for all variables.
"""
import smtplib
import ssl
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER", "")        # your Gmail / SMTP address
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")    # app password (not account pw)
FROM_NAME     = os.getenv("FROM_NAME", "PPW Password Manager")
FROM_EMAIL    = os.getenv("FROM_EMAIL", SMTP_USER)


# ── HTML Templates ────────────────────────────────────────────────────────────

def _welcome_html(username: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0f1117; color: #e2e8f0; margin: 0; padding: 0; }}
    .wrapper {{ max-width: 560px; margin: 40px auto; background: #1e2130; border-radius: 16px; overflow: hidden; }}
    .header {{ background: linear-gradient(135deg, #6c63ff 0%, #5a52e0 100%); padding: 40px 32px; text-align: center; }}
    .header h1 {{ margin: 0; font-size: 28px; color: #ffffff; }}
    .header p  {{ margin: 8px 0 0; color: #c4c0ff; font-size: 14px; }}
    .body {{ padding: 32px; }}
    .body h2 {{ color: #e2e8f0; font-size: 20px; margin-top: 0; }}
    .body p  {{ color: #a0aec0; line-height: 1.7; }}
    .feature {{ display: flex; align-items: flex-start; margin: 16px 0; }}
    .feature .icon {{ font-size: 22px; margin-right: 14px; min-width: 28px; }}
    .feature .text h3 {{ margin: 0 0 4px; color: #e2e8f0; font-size: 14px; }}
    .feature .text p  {{ margin: 0; color: #718096; font-size: 13px; }}
    .cta {{ text-align: center; margin: 28px 0 8px; }}
    .cta a {{ background: #6c63ff; color: #fff; padding: 12px 32px; border-radius: 8px;
              text-decoration: none; font-weight: 600; font-size: 15px; }}
    .footer {{ background: #13151f; padding: 20px 32px; text-align: center;
               color: #4a5568; font-size: 12px; }}
    .footer a {{ color: #6c63ff; text-decoration: none; }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <h1>🔐 Welcome to PPW</h1>
      <p>Your vault is ready. Your passwords are safe.</p>
    </div>
    <div class="body">
      <h2>Hey {username}, you're all set! 👋</h2>
      <p>
        Your account has been created and your personal vault is waiting.
        Everything you store is encrypted with <strong>AES-256-GCM</strong>
        — only you can unlock it with your master password.
      </p>

      <div class="feature">
        <div class="icon">🔐</div>
        <div class="text">
          <h3>Zero-knowledge encryption</h3>
          <p>Your master password is never stored. Not even we can read your data.</p>
        </div>
      </div>
      <div class="feature">
        <div class="icon">☁️</div>
        <div class="text">
          <h3>Cloud sync via MongoDB Atlas</h3>
          <p>Access your vault from any device — your data stays in your own Atlas cluster.</p>
        </div>
      </div>
      <div class="feature">
        <div class="icon">⚡</div>
        <div class="text">
          <h3>Password generator</h3>
          <p>Generate strong, unique passwords instantly from the Generator tab.</p>
        </div>
      </div>
      <div class="feature">
        <div class="icon">🛡</div>
        <div class="text">
          <h3>Security dashboard</h3>
          <p>See which passwords are weak or outdated — fix them before they become a problem.</p>
        </div>
      </div>

      <div class="cta">
        <a href="https://github.com/yourusername/PPW">Open PPW</a>
      </div>
    </div>
    <div class="footer">
      You received this email because you created a PPW account.<br>
      If you didn't do this, please <a href="mailto:{FROM_EMAIL}">contact us</a> immediately.
    </div>
  </div>
</body>
</html>
"""


def _welcome_text(username: str) -> str:
    return f"""Welcome to PPW, {username}!

Your vault is ready. Your passwords are safe.

Everything you store is encrypted with AES-256-GCM — only you can unlock
it with your master password. We never store your master password.

Features:
  🔐  Zero-knowledge encryption
  ☁️   Cloud sync via MongoDB Atlas
  ⚡  Password generator
  🛡   Security dashboard

Stay safe,
The PPW Team
"""


def _login_alert_html(username: str, timestamp: str, ip: str) -> str:
    return f"""
<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0f1117; color: #e2e8f0; }}
  .wrapper {{ max-width: 520px; margin: 40px auto; background: #1e2130; border-radius: 16px; overflow: hidden; }}
  .header {{ background: #ed8936; padding: 28px 32px; text-align: center; }}
  .header h1 {{ margin: 0; font-size: 22px; color: #fff; }}
  .body {{ padding: 28px 32px; }}
  .body p {{ color: #a0aec0; line-height: 1.7; }}
  .detail {{ background: #22263a; border-radius: 8px; padding: 14px 18px; margin: 16px 0; }}
  .detail span {{ color: #718096; font-size: 12px; display: block; }}
  .detail strong {{ color: #e2e8f0; font-size: 14px; }}
  .footer {{ background: #13151f; padding: 16px 32px; text-align: center; color: #4a5568; font-size: 12px; }}
</style></head><body>
<div class="wrapper">
  <div class="header"><h1>⚠️ New login detected</h1></div>
  <div class="body">
    <p>A new login was recorded for your PPW account <strong>{username}</strong>.</p>
    <div class="detail">
      <span>Time</span><strong>{timestamp}</strong>
    </div>
    <div class="detail">
      <span>IP address</span><strong>{ip or 'Unknown'}</strong>
    </div>
    <p>If this was you, no action is needed. If you don't recognise this login,
    change your master password immediately.</p>
  </div>
  <div class="footer">PPW Security Alert — you opted in to these notifications.</div>
</div></body></html>
"""


# ── Sender ────────────────────────────────────────────────────────────────────

def _send(to_email: str, subject: str, html: str, plain: str) -> tuple[bool, str]:
    """Internal send helper. Returns (success, error_message)."""
    if not SMTP_USER or not SMTP_PASSWORD:
        # Email not configured — silently skip (don't break registration)
        return True, "Email not configured — skipped"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg["To"]      = to_email

        msg.attach(MIMEText(plain, "plain", "utf-8"))
        msg.attach(MIMEText(html,  "html",  "utf-8"))

        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())

        return True, ""
    except Exception as e:
        return False, str(e)


# ── Public API ────────────────────────────────────────────────────────────────

def send_welcome_email(username: str, to_email: str) -> tuple[bool, str]:
    """Send welcome email after successful registration."""
    return _send(
        to_email=to_email,
        subject="🔐 Welcome to PPW — your vault is ready",
        html=_welcome_html(username),
        plain=_welcome_text(username),
    )


def send_login_alert(username: str, to_email: str,
                     timestamp: str, ip: Optional[str] = None) -> tuple[bool, str]:
    """Send login notification email."""
    return _send(
        to_email=to_email,
        subject="⚠️ PPW — new login detected",
        html=_login_alert_html(username, timestamp, ip or "Unknown"),
        plain=f"New login to your PPW account {username} at {timestamp} from {ip or 'Unknown'}.",
    )

