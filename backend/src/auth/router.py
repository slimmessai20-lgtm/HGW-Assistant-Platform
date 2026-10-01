from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.auth.models import LoginRequest, LoginResponse, UserOut
from src.auth.service import (
    authenticate_user, create_token, decode_token,
    get_all_users, create_user, delete_user, toggle_user_active,
    create_session, update_session_token_hash, end_session,
    update_password, verify_password,
)
from src.auth.db import get_connection
from pydantic import BaseModel
from typing import Optional, Literal
import jwt
import datetime
from slowapi import Limiter
from slowapi.util import get_remote_address
from src.config import SECRET_KEY, ALGORITHM

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


# ── helpers ──────────────────────────────────────────────────────────────────

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = decode_token(credentials.credentials)
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")


def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    return current_user


# ── endpoints ────────────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(body: LoginRequest, request: Request):
    user = authenticate_user(body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # ── 1. Create session row ────────────────────────────────────────────────
    ip_address = request.client.host if request.client else ""
    user_agent = request.headers.get("user-agent", "")
    session_id = create_session(user["id"], ip_address, user_agent)

    # ── 2. Build JWT with session_id embedded ────────────────────────────────
    token = create_token(user, session_id=session_id)

    # ── 3. Store token hash for traceability ────────────────────────────────
    update_session_token_hash(session_id, token)

    return LoginResponse(
        access_token=token,
        user=UserOut(
            id=user["id"],
            username=user["username"],
            full_name=user["full_name"],
            email=user.get("email"),
            role=user["role"],
            is_active=bool(user["is_active"]),
        )
    )


@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    """Mark the current session as ended."""
    session_id = current_user.get("session_id")
    if session_id:
        end_session(session_id)
    return {"message": "Déconnecté"}


@router.get("/me", response_model=UserOut)
def me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.post("/verify")
def verify_token(current_user: dict = Depends(get_current_user)):
    return {"valid": True, "user": current_user}


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password")
def change_password(body: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT password_hash FROM users WHERE id = %s", (current_user["sub"],))
            row = cur.fetchone()
    finally:
        conn.close()
    if not row or not verify_password(body.current_password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    update_password(int(current_user["sub"]), body.new_password)
    return {"message": "Password updated successfully"}


class ForgotPasswordRequest(BaseModel):
    email: str

@router.post("/forgot-password")
@limiter.limit("3/minute")
def forgot_password(body: ForgotPasswordRequest, request: Request):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username FROM users WHERE email = %s AND is_active = 1", (body.email,))
            user = cur.fetchone()
    finally:
        conn.close()

    if not user:
        # Prevent email enumeration by returning a generic success message
        return {"message": "If this email is registered, you will receive a password reset link shortly."}

    # Generate short-lived reset token
    payload = {
        "sub": str(user["id"]),
        "purpose": "password_reset",
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    }
    reset_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    # Send email
    from src.auth.service import send_reset_email
    reset_link = f"http://localhost:4200/auth/reset-password?token={reset_token}"
    success = send_reset_email(body.email, reset_link)

    # We still print it for the demo/debugging just in case the email fails
    print(f"\n[SECURITY] Password reset requested for {body.email}")
    print(f"[SECURITY] Magic Link: {reset_link}\n")

    if not success:
        return {"message": "Server could not send email due to configuration. Check console for the link."}

    return {"message": "If this email is registered, you will receive a password reset link shortly."}


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/reset-password")
@limiter.limit("5/minute")
def reset_password(body: ResetPasswordRequest, request: Request):
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    try:
        payload = jwt.decode(body.token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token purpose")
        user_id = int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Reset link has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid reset link")

    # Update the password
    update_password(user_id, body.new_password)
    
    # We could invalidate the token here (e.g., storing used tokens), 
    # but since it's short-lived, it's generally okay for a simple implementation.
    return {"message": "Your password has been successfully reset. You can now login."}


# ── admin: user management ───────────────────────────────────────────────────

@router.get("/users")
def list_users(_: dict = Depends(require_admin)):
    return get_all_users()


class CreateUserRequest(BaseModel):
    username: str
    password: str
    full_name: str
    email: Optional[str] = ""
    role: Literal["admin", "engineer", "general"] = "general"


@router.post("/users")
def add_user(body: CreateUserRequest, _: dict = Depends(require_admin)):
    try:
        create_user(body.username, body.password, body.full_name, body.email or "", body.role)
        return {"message": "Utilisateur créé avec succès"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats")
def get_stats(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Réservé aux administrateurs")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Total gateways
            cur.execute("SELECT COUNT(*) as total FROM gateways")
            total_gw = cur.fetchone()["total"]

            # Gateways par statut
            cur.execute("SELECT status, COUNT(*) as cnt FROM gateways GROUP BY status")
            by_status = {r["status"]: r["cnt"] for r in cur.fetchall()}

            # Gateways par marque
            cur.execute("SELECT COALESCE(brand,'Autre') as brand, COUNT(*) as cnt FROM gateways GROUP BY brand ORDER BY cnt DESC")
            by_brand = cur.fetchall()

            # Total users
            cur.execute("SELECT COUNT(*) as total FROM users")
            total_users = cur.fetchone()["total"]

            # Users par rôle
            cur.execute("SELECT role, COUNT(*) as cnt FROM users GROUP BY role")
            by_role = {r["role"]: r["cnt"] for r in cur.fetchall()}

            # Dernières entrées (5)
            cur.execute("""
                SELECT g.name, g.brand, g.status, g.created_at, u.full_name as creator
                FROM gateways g LEFT JOIN users u ON g.created_by = u.id
                ORDER BY g.created_at DESC LIMIT 5
            """)
            recent = cur.fetchall()
            for r in recent:
                if r.get("created_at"):
                    r["created_at"] = r["created_at"].isoformat()

            return {
                "total_gateways": total_gw,
                "by_status": by_status,
                "by_brand": by_brand,
                "total_users": total_users,
                "by_role": by_role,
                "recent_gateways": recent,
            }
    finally:
        conn.close()


@router.delete("/users/{user_id}")
def remove_user(user_id: int, _: dict = Depends(require_admin)):
    delete_user(user_id)
    return {"message": "Utilisateur supprimé"}


@router.patch("/users/{user_id}/toggle")
def toggle_user(user_id: int, active: bool, _: dict = Depends(require_admin)):
    toggle_user_active(user_id, active)
    return {"message": "Statut mis à jour"}


# ── account requests ─────────────────────────────────────────────────────────
from src.auth.service import (
    create_account_request, get_pending_account_requests, get_account_request,
    update_account_request_status, send_approval_email, send_rejection_email,
    generate_random_password
)

class RequestAccountRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    message: str
    role: str = "general"

@router.post("/request-account")
@limiter.limit("3/minute")
def request_account(body: RequestAccountRequest, request: Request):
    try:
        create_account_request(body.first_name, body.last_name, body.email, body.message, body.role)
        return {"message": "Demande envoyée avec succès."}
    except Exception as e:
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=400, detail="Une demande existe déjà pour cet email.")
        raise HTTPException(status_code=500, detail="Erreur lors de l'enregistrement de la demande.")

@router.get("/requests")
def list_account_requests(_: dict = Depends(require_admin)):
    return get_pending_account_requests()

@router.post("/requests/{req_id}/approve")
def approve_request(req_id: int, _: dict = Depends(require_admin)):
    req = get_account_request(req_id)
    if not req or req["status"] != "pending":
        raise HTTPException(status_code=404, detail="Demande introuvable ou déjà traitée.")
    
    # Create the user
    username = f"{req['first_name'].lower()}.{req['last_name'].lower()}"
    # check if username exists, if so append something
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                username = f"{username}{req_id}"
    finally:
        conn.close()

    raw_pwd = generate_random_password()
    try:
        # Pass the requested role when creating the user
        create_user(username, raw_pwd, f"{req['first_name']} {req['last_name']}", req["email"], req.get("role") or "general")
        update_account_request_status(req_id, "approved")
        
        # Send email
        send_approval_email(req["email"], req["first_name"], username, raw_pwd)
        return {"message": "Demande approuvée. L'utilisateur a été créé et un email a été envoyé."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/requests/{req_id}/reject")
def reject_request(req_id: int, _: dict = Depends(require_admin)):
    req = get_account_request(req_id)
    if not req or req["status"] != "pending":
        raise HTTPException(status_code=404, detail="Demande introuvable ou déjà traitée.")
    
    update_account_request_status(req_id, "rejected")
    send_rejection_email(req["email"], req["first_name"])
    return {"message": "Demande rejetée. Un email a été envoyé."}
