from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Nexus Hestia — Cosmic Buildings API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://cosmicbuildings.nexushestia.com",
        "http://cosmicbuildings.nexushestia.com",
        "https://www.cosmicbuildings.nexushestia.com",
        "http://www.cosmicbuildings.nexushestia.com",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_supabase() -> Client:
    url = os.environ["SUPABASE_URL"].strip().rstrip("/")
    if url.endswith("/rest/v1"):
        url = url[:-8]
    key = os.environ["SUPABASE_KEY"].strip()
    return create_client(url, key)

ADMIN_EMAILS = [
    "natasha.bajc@nexushestia.com",
    "natasha@natashabajc.com",
    "natashabajc@gmail.com",
]

PRE_APPROVED = [
    "natasha.bajc@nexushestia.com",
    "natasha@natashabajc.com",
    "natashabajc@gmail.com",
]

# ── MODELS ────────────────────────────────────────────────────────────────────

class AccessRequest(BaseModel):
    email: str

class CheckStream(BaseModel):
    stream_id: str
    stream_text: str
    domain_id: str
    checked: bool
    checked_by_email: str
    checked_by_name: str
    completion_pct: int = 100

class UpdatePct(BaseModel):
    stream_id: str
    completion_pct: int
    updated_by_email: str
    updated_by_name: str

class InviteRequest(BaseModel):
    email: str
    invited_by: str

class ApproveRequest(BaseModel):
    email: str
    action: str  # "approve" or "deny"
    admin_email: str

# ── AUTH HELPERS ──────────────────────────────────────────────────────────────

def require_admin(email: str):
    if email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")

def log_audit(sb: Client, action: str, email: str, detail: str, stream_id: str = None, pct: int = None):
    sb.table("audit_log").insert({
        "action": action,
        "actor_email": email,
        "detail": detail,
        "stream_id": stream_id,
        "completion_pct": pct,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()

# ── ROUTES ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"service": "Nexus Hestia — Cosmic Buildings API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/test-supabase")
def test_supabase():
    try:
        sb = get_supabase()
        res = sb.table("stream_checks").select("count", count="exact").limit(1).execute()
        return {"ok": True, "details": "Successfully connected to Supabase!", "data": res.data}
    except Exception as e:
        import traceback
        return {"ok": False, "error_type": type(e).__name__, "error_message": str(e), "traceback": traceback.format_exc()}

# ── ACCESS ────────────────────────────────────────────────────────────────────

@app.post("/access/check")
def check_access(req: AccessRequest, sb: Client = Depends(get_supabase)):
    email = req.email.strip().lower()

    if email in PRE_APPROVED:
        log_audit(sb, "signin", email, f"Pre-approved sign-in")
        return {"granted": True, "role": "admin" if email in ADMIN_EMAILS else "viewer", "email": email}

    result = sb.table("users").select("*").eq("email", email).eq("approved", True).execute()
    if result.data:
        log_audit(sb, "signin", email, "Approved user sign-in")
        return {"granted": True, "role": result.data[0].get("role", "viewer"), "email": email}

    pending = sb.table("users").select("*").eq("email", email).eq("approved", False).execute()
    if pending.data:
        return {"granted": False, "reason": "pending", "message": "Access pending admin approval."}

    return {"granted": False, "reason": "not_found", "message": "No access. Request invite from natasha.bajc@nexushestia.com"}

# ── STREAMS ───────────────────────────────────────────────────────────────────

@app.get("/streams")
def get_streams(sb: Client = Depends(get_supabase)):
    result = sb.table("stream_checks").select("*").execute()
    return {"streams": result.data}

@app.post("/streams/check")
def check_stream(req: CheckStream, sb: Client = Depends(get_supabase)):
    existing = sb.table("stream_checks").select("*").eq("stream_id", req.stream_id).execute()

    payload = {
        "stream_id": req.stream_id,
        "stream_text": req.stream_text,
        "domain_id": req.domain_id,
        "checked": req.checked,
        "checked_by_email": req.checked_by_email,
        "checked_by_name": req.checked_by_name,
        "completion_pct": req.completion_pct,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if existing.data:
        sb.table("stream_checks").update(payload).eq("stream_id", req.stream_id).execute()
        action = "stream_updated"
    else:
        payload["created_at"] = datetime.now(timezone.utc).isoformat()
        sb.table("stream_checks").insert(payload).execute()
        action = "stream_checked"

    log_audit(sb, action, req.checked_by_email,
              f"{'Checked' if req.checked else 'Unchecked'}: {req.stream_text}",
              req.stream_id, req.completion_pct)

    return {"ok": True, "action": action}

@app.delete("/streams/{stream_id}")
def uncheck_stream(stream_id: str, email: str, name: str, sb: Client = Depends(get_supabase)):
    require_admin(email)
    stream = sb.table("stream_checks").select("stream_text").eq("stream_id", stream_id).execute()
    text = stream.data[0]["stream_text"] if stream.data else stream_id
    sb.table("stream_checks").delete().eq("stream_id", stream_id).execute()
    log_audit(sb, "stream_unchecked", email, f"Unchecked: {text}", stream_id)
    return {"ok": True}

# ── AUDIT LOG ─────────────────────────────────────────────────────────────────

@app.get("/audit")
def get_audit(limit: int = 100, sb: Client = Depends(get_supabase)):
    result = sb.table("audit_log").select("*").order("created_at", desc=True).limit(limit).execute()
    return {"log": result.data}

@app.delete("/audit")
def clear_audit(admin_email: str, sb: Client = Depends(get_supabase)):
    require_admin(admin_email)
    sb.table("audit_log").delete().neq("id", 0).execute()
    return {"ok": True}

# ── USERS / INVITES ───────────────────────────────────────────────────────────

@app.get("/users")
def get_users(admin_email: str, sb: Client = Depends(get_supabase)):
    require_admin(admin_email)
    result = sb.table("users").select("*").order("created_at", desc=True).execute()
    return {"users": result.data}

@app.post("/users/invite")
def invite_user(req: InviteRequest, sb: Client = Depends(get_supabase)):
    require_admin(req.invited_by)
    email = req.email.strip().lower()

    if email in PRE_APPROVED:
        return {"ok": False, "message": "Email already has access."}

    existing = sb.table("users").select("email").eq("email", email).execute()
    if existing.data:
        return {"ok": False, "message": "Email already in system."}

    sb.table("users").insert({
        "email": email,
        "role": "viewer",
        "approved": False,
        "invited_by": req.invited_by,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()

    log_audit(sb, "invite_sent", req.invited_by, f"Invited: {email}")
    # TODO: send email via SendGrid/Resend with magic link
    return {"ok": True, "message": f"Invite queued for {email}. Connect email provider to send link."}

@app.post("/users/approve")
def approve_user(req: ApproveRequest, sb: Client = Depends(get_supabase)):
    require_admin(req.admin_email)
    email = req.email.strip().lower()

    if req.action == "approve":
        sb.table("users").update({"approved": True, "role": "viewer"}).eq("email", email).execute()
        log_audit(sb, "user_approved", req.admin_email, f"Approved access: {email}")
        return {"ok": True, "message": f"{email} approved as viewer."}
    elif req.action == "deny":
        sb.table("users").delete().eq("email", email).execute()
        log_audit(sb, "user_denied", req.admin_email, f"Denied access: {email}")
        return {"ok": True, "message": f"{email} denied and removed."}
    else:
        raise HTTPException(status_code=400, detail="action must be 'approve' or 'deny'")

@app.delete("/users/{email}")
def remove_user(email: str, admin_email: str, sb: Client = Depends(get_supabase)):
    require_admin(admin_email)
    sb.table("users").delete().eq("email", email).execute()
    log_audit(sb, "user_removed", admin_email, f"Removed user: {email}")
    return {"ok": True}
