import bcrypt
import jwt
import datetime
import hashlib
from src.auth.db import get_connection
from src.config import SECRET_KEY, ALGORITHM, TOKEN_EXPIRE_HOURS


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(user: dict, session_id: int = None) -> str:
    payload = {
        "sub":      str(user["id"]),
        "username": user["username"],
        "role":     user["role"],
        "exp":      datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    if session_id:
        payload["session_id"] = session_id
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def authenticate_user(username: str, password: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE username = %s AND is_active = 1",
                (username,)
            )
            user = cursor.fetchone()
    finally:
        conn.close()

    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user


def get_all_users():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, full_name, email, role, is_active, created_at FROM users"
            )
            return cursor.fetchall()
    finally:
        conn.close()


def create_user(username: str, password: str, full_name: str, email: str, role: str):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (username, password_hash, full_name, email, role) VALUES (%s, %s, %s, %s, %s)",
                (username, hashed, full_name, email, role)
            )
        conn.commit()
    finally:
        conn.close()


def delete_user(user_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
    finally:
        conn.close()


def update_password(user_id: int, new_password: str):
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (hashed, user_id)
            )
        conn.commit()
    finally:
        conn.close()


def toggle_user_active(user_id: int, is_active: bool):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET is_active = %s WHERE id = %s",
                (1 if is_active else 0, user_id)
            )
        conn.commit()
    finally:
        conn.close()


# ── Session management ────────────────────────────────────────────────────────

def create_session(user_id: int, ip_address: str = '', user_agent: str = '') -> int:
    """Create a session row and return its id."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO sessions (user_id, token_hash, ip_address, user_agent)
                   VALUES (%s, %s, %s, %s)""",
                (user_id, '', ip_address, user_agent)
            )
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()


def update_session_token_hash(session_id: int, token: str):
    """Store a SHA-256 hash of the JWT in the session row."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sessions SET token_hash = %s WHERE id = %s",
                (token_hash, session_id)
            )
            conn.commit()
    finally:
        conn.close()


def touch_session(session_id: int):
    """Update last_active timestamp — call on each chat interaction."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sessions SET last_active = NOW() WHERE id = %s",
                (session_id,)
            )
            conn.commit()
    finally:
        conn.close()


def end_session(session_id: int):
    """Mark session as ended (on logout)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sessions SET ended_at = NOW() WHERE id = %s",
                (session_id,)
            )
            conn.commit()
    finally:
        conn.close()


def get_sessions_for_user(user_id: int) -> list:
    """Return all sessions for a user (admin view)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, created_at, last_active, ended_at, ip_address
                   FROM sessions WHERE user_id = %s ORDER BY created_at DESC""",
                (user_id,)
            )
            rows = cur.fetchall()
            for r in rows:
                for f in ("created_at", "last_active", "ended_at"):
                    if r.get(f):
                        r[f] = r[f].isoformat()
            return rows
    finally:
        conn.close()


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
import logging

logger = logging.getLogger(__name__)

def send_reset_email(to_email: str, reset_link: str) -> bool:
    """Send a password reset email using SMTP."""
    if not SMTP_USER or not SMTP_PASSWORD:
        logger.error("SMTP credentials not configured. Cannot send email.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Home Gateway - Password Reset Request"
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    text = f"Hello,\n\nPlease reset your password using the following link:\n{reset_link}\n\nIf you did not request this, please ignore this email."
    html = f"""\
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>Password Reset Request</h2>
        <p>Hello,</p>
        <p>We received a request to reset your password for your Home Gateway account.</p>
        <p>
            <a href="{reset_link}" style="display: inline-block; padding: 10px 20px; color: white; background-color: #007bff; text-decoration: none; border-radius: 5px;">
                Reset Password
            </a>
        </p>
        <p>If the button doesn't work, copy and paste this link into your browser:</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        <br>
        <p>If you did not request a password reset, please ignore this email.</p>
        <p>Best regards,<br>Home Gateway Team</p>
      </body>
    </html>
    """

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    msg.attach(part1)
    msg.attach(part2)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
        server.quit()
        logger.info(f"Password reset email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False

import secrets
import string

def send_approval_email(to_email: str, first_name: str, username: str, raw_password: str) -> bool:
    if not SMTP_USER or not SMTP_PASSWORD:
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Home Gateway - Account Approved!"
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    
    html = f"""\
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>Welcome to Home Gateway!</h2>
        <p>Hello {first_name},</p>
        <p>Your request for an account has been <strong>approved</strong> by the administrator.</p>
        <p>Here are your login credentials:</p>
        <ul>
            <li><strong>Username:</strong> {username}</li>
            <li><strong>Password:</strong> {raw_password}</li>
        </ul>
        <p>Please log in and change your password immediately.</p>
        <p>Best regards,<br>Home Gateway Team</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, "html"))
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        logger.error(f"Failed to send approval email: {e}")
        return False

def send_rejection_email(to_email: str, first_name: str) -> bool:
    if not SMTP_USER or not SMTP_PASSWORD:
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Home Gateway - Account Request Update"
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    
    html = f"""\
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>Account Request Update</h2>
        <p>Hello {first_name},</p>
        <p>We are sorry to inform you that your request for an account has been declined by the administrator at this time.</p>
        <p>If you believe this is an error, please contact your manager.</p>
        <p>Best regards,<br>Home Gateway Team</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, "html"))
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        logger.error(f"Failed to send rejection email: {e}")
        return False

def create_account_request(first_name: str, last_name: str, email: str, message: str, role: str = 'general') -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO account_requests (first_name, last_name, email, message, role) VALUES (%s, %s, %s, %s, %s)",
                (first_name, last_name, email, message, role)
            )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def get_pending_account_requests():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM account_requests WHERE status = 'pending' ORDER BY created_at DESC")
            rows = cur.fetchall()
            for r in rows:
                if r.get('created_at'):
                    r['created_at'] = r['created_at'].isoformat()
            return rows
    finally:
        conn.close()

def get_account_request(request_id: int):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM account_requests WHERE id = %s", (request_id,))
            return cur.fetchone()
    finally:
        conn.close()

def update_account_request_status(request_id: int, status: str):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE account_requests SET status = %s WHERE id = %s", (status, request_id))
        conn.commit()
    finally:
        conn.close()

def generate_random_password(length=12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for i in range(length))
