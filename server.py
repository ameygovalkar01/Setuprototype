"""
server.py - FastAPI Backend Web Server for Setu (सेतु)
SIH26092 - Ministry of Social Justice & Empowerment
"""
import os
import json
import time
import secrets
import pandas as pd
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Header, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import schema
import security
import matcher
import admin
import users

app = FastAPI(
    title="Setu (सेतु) API",
    description="AI-Driven Scheme Matching Platform for Marginalized Entrepreneurs (SIH26092)",
    version="1.1.0"
)

# Admin active token store in-memory (Token -> {"created": timestamp, "last_active": timestamp})
ADMIN_SESSIONS: Dict[str, Dict[str, float]] = {}
SESSION_TTL_SECONDS = 15 * 60 # 15 minutes
LOGIN_FAILURES: Dict[str, Dict[str, Any]] = {} # IP -> {"attempts": count, "lockout_until": timestamp}

# Mount static files directory
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Pydantic models
class CitizenProfileRequest(BaseModel):
    category: str = "All"
    gender: str = "All-Any"
    is_pwd: bool = False
    pwd_percent: int = 0
    income: int = 0
    age: int = 25
    state: str = "All India"
    sector: str = "All"
    business_need: str = ""
    low_bandwidth: bool = False

class AdminLoginRequest(BaseModel):
    password: str

class UserSignupRequest(BaseModel):
    name: str
    email: str
    phone: str = ""
    password: str

class UserVerifyEmailRequest(BaseModel):
    email: str
    otp: str

class UserLoginRequest(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str

class SchemePayload(BaseModel):
    scheme_id: str
    scheme_name: str
    sponsoring_body: str
    category: List[str]
    eligible_gender: List[str]
    pwd_only: bool = False
    min_income: int = 0
    max_income: int = -1
    min_age: int = 18
    max_age: int = 70
    states: List[str]
    sector: List[str]
    benefit_type: str = "Loan"
    benefit_amount: str
    subsidy_percentage: float = 0.0
    description: str
    required_documents: List[str]
    official_url: str
    contact_info: str
    is_edit: bool = False

def get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "127.0.0.1"

def authenticate_admin_token(auth_token: Optional[str]) -> bool:
    if not auth_token:
        return False
    sess = ADMIN_SESSIONS.get(auth_token)
    if not sess:
        return False
    now = time.time()
    if now - sess["last_active"] > SESSION_TTL_SECONDS:
        del ADMIN_SESSIONS[auth_token]
        security.log_audit_event("WEB_AUTH_TIMEOUT", "Web Admin session expired due to inactivity.")
        return False
    sess["last_active"] = now
    return True

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Setu (सेतु) Web Portal</h1><p>Static index.html loading...</p>"

@app.get("/admin", response_class=HTMLResponse)
async def serve_admin():
    admin_path = os.path.join(STATIC_DIR, "admin.html")
    if os.path.exists(admin_path):
        with open(admin_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Setu Admin Portal</h1>"

@app.get("/api/schemes")
async def get_all_schemes():
    df = admin.load_schemes_dataframe()
    schemes = df.to_dict(orient="records")
    return {"success": True, "count": len(schemes), "schemes": schemes}

@app.get("/api/helpdesk")
async def get_helpdesks():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "help_desks.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return {"success": True, "data": json.load(f)}
        except Exception:
            return {"success": False, "data": {}}
    return {"success": False, "data": {}}

@app.post("/api/match")
async def match_citizen_profile(profile: CitizenProfileRequest):
    """
    Stateless Scheme Matching Engine (Zero Citizen PII Retention).
    Data processed strictly in-memory without saving to database or logging.
    """
    schemes_df = admin.load_schemes_dataframe()
    
    # Load model if not in low-bandwidth mode
    embedding_model = None
    if not profile.low_bandwidth:
        embedding_model = matcher.get_sentence_transformer_model()
        
    user_dict = {
        "category": security.sanitize_text(profile.category),
        "gender": security.sanitize_text(profile.gender),
        "is_pwd": profile.is_pwd,
        "pwd_percent": profile.pwd_percent,
        "income": profile.income,
        "age": profile.age,
        "state": security.sanitize_text(profile.state),
        "sector": security.sanitize_text(profile.sector),
        "business_need": security.sanitize_text(profile.business_need)
    }
    
    matched = matcher.match_schemes(
        user_profile=user_dict,
        schemes_df=schemes_df,
        embedding_model=embedding_model,
        low_bandwidth_mode=profile.low_bandwidth
    )
    
    checklist = matcher.aggregate_document_checklist(matched)
    
    return {
        "success": True,
        "count": len(matched),
        "matches": matched,
        "checklist": checklist
    }

# Citizen User Authentication Endpoints
@app.post("/api/auth/signup")
async def user_signup(req: UserSignupRequest):
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    ok, result = users.signup_user(req.name, req.email, req.phone, req.password)
    if not ok:
        raise HTTPException(status_code=400, detail=result)
    # result is the 6-digit OTP code
    return {
        "success": True, 
        "message": f"Verification code sent to {req.email}.",
        "otp": result,
        "demo_otp": result
    }

@app.post("/api/auth/verify-email")
async def user_verify_email(req: UserVerifyEmailRequest):
    ok, result = users.activate_user(req.email, req.otp)
    if not ok:
        raise HTTPException(status_code=400, detail=result)
    return {"success": True, "data": result}

@app.post("/api/auth/login")
async def user_login(req: UserLoginRequest):
    ok, result = users.login_user(req.email, req.password)
    if not ok:
        if isinstance(result, dict) and result.get("requires_verification"):
            return JSONResponse(status_code=403, content=result)
        raise HTTPException(status_code=401, detail=result)
    return {"success": True, "data": result}

@app.post("/api/auth/forgot-password")
async def user_forgot_password(req: ForgotPasswordRequest):
    ok, otp = users.request_password_reset(req.email)
    return {
        "success": True, 
        "message": f"Password reset code sent to {req.email}.",
        "otp": otp,
        "demo_otp": otp
    }

@app.post("/api/auth/reset-password")
async def user_reset_password(req: ResetPasswordRequest):
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")
    ok, msg = users.reset_password(req.email, req.otp, req.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}

@app.get("/api/auth/me")
async def user_get_me(authorization: Optional[str] = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    user = users.get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized.")
    return {"success": True, "user": {"name": user["name"], "email": user["email"], "phone": user["phone"]}}

# Admin Authentication & Management Endpoints
@app.post("/api/admin/login")
async def admin_login(payload: AdminLoginRequest, request: Request):
    ip = get_client_ip(request)
    now = time.time()
    
    # Rate limit check
    record = LOGIN_FAILURES.get(ip, {"attempts": 0, "lockout_until": 0})
    if now < record["lockout_until"]:
        remaining = int(record["lockout_until"] - now)
        raise HTTPException(status_code=429, detail=f"Rate limit active. Please retry in {remaining} seconds.")
        
    expected_hash = admin.get_admin_password_hash()
    if not expected_hash:
        raise HTTPException(status_code=500, detail="Admin password hash not configured in .env.")
        
    if security.verify_password(payload.password, expected_hash):
        # Successful login
        LOGIN_FAILURES[ip] = {"attempts": 0, "lockout_until": 0}
        token = secrets.token_hex(32)
        ADMIN_SESSIONS[token] = {"created": now, "last_active": now}
        security.log_audit_event("WEB_AUTH_SUCCESS", f"Admin authenticated from IP {ip}")
        return {"success": True, "token": token, "expires_in": SESSION_TTL_SECONDS}
    else:
        record["attempts"] += 1
        if record["attempts"] >= 5:
            record["lockout_until"] = now + 60
            security.log_audit_event("WEB_AUTH_LOCKOUT", f"IP {ip} locked out for 60s.")
        LOGIN_FAILURES[ip] = record
        security.log_audit_event("WEB_AUTH_FAIL", f"Failed admin password attempt from IP {ip}")
        raise HTTPException(status_code=401, detail="Invalid administrator credentials.")

@app.get("/api/admin/verify")
async def verify_session(x_admin_token: Optional[str] = Header(None)):
    if not authenticate_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Invalid or expired admin session token.")
    return {"success": True, "message": "Session valid."}

@app.post("/api/admin/logout")
async def admin_logout(x_admin_token: Optional[str] = Header(None)):
    if x_admin_token and x_admin_token in ADMIN_SESSIONS:
        del ADMIN_SESSIONS[x_admin_token]
        security.log_audit_event("WEB_AUTH_LOGOUT", "Admin session explicitly logged out.")
    return {"success": True, "message": "Logged out successfully."}

@app.post("/api/admin/scheme")
async def save_scheme(payload: SchemePayload, x_admin_token: Optional[str] = Header(None)):
    if not authenticate_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin session.")
        
    scheme_dict = {
        "scheme_id": payload.scheme_id,
        "scheme_name": payload.scheme_name,
        "sponsoring_body": payload.sponsoring_body,
        "category": payload.category,
        "eligible_gender": payload.eligible_gender,
        "pwd_only": payload.pwd_only,
        "min_income": payload.min_income,
        "max_income": payload.max_income,
        "min_age": payload.min_age,
        "max_age": payload.max_age,
        "states": payload.states,
        "sector": payload.sector,
        "benefit_type": payload.benefit_type,
        "benefit_amount": payload.benefit_amount,
        "subsidy_percentage": payload.subsidy_percentage,
        "description": payload.description,
        "required_documents": payload.required_documents,
        "official_url": payload.official_url,
        "contact_info": payload.contact_info
    }
    
    state = {"is_admin": True, "admin_last_active": time.time()}
    ok, errors = admin.save_scheme_entry(scheme_dict, is_edit=payload.is_edit, session_state=state)
    if not ok:
        raise HTTPException(status_code=400, detail={"errors": errors})
        
    return {"success": True, "message": f"Scheme {payload.scheme_id} committed atomically."}

@app.delete("/api/admin/scheme/{scheme_id}")
async def delete_scheme(scheme_id: str, x_admin_token: Optional[str] = Header(None)):
    if not authenticate_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin session.")
        
    state = {"is_admin": True, "admin_last_active": time.time()}
    ok, msg = admin.delete_scheme_entry(scheme_id, state)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}

@app.post("/api/admin/bulk-upload")
async def bulk_upload(file: UploadFile = File(...), x_admin_token: Optional[str] = Header(None)):
    if not authenticate_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin session.")
        
    file_bytes = await file.read()
    state = {"is_admin": True, "admin_last_active": time.time()}
    ok, messages, count = admin.validate_and_ingest_bulk_csv(file_bytes, file.filename, state)
    if not ok:
        raise HTTPException(status_code=400, detail={"errors": messages})
    return {"success": True, "message": messages[0], "count": count}

@app.get("/api/admin/audit-logs")
async def get_audit_logs(x_admin_token: Optional[str] = Header(None)):
    if not authenticate_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin session.")
    logs = security.read_recent_audit_logs(limit=50)
    return {"success": True, "logs": logs}

@app.get("/api/admin/export")
async def export_schemes(x_admin_token: Optional[str] = Header(None)):
    if not authenticate_admin_token(x_admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid admin session.")
    return FileResponse(admin.SCHEMES_FILE, filename="schemes_export.csv", media_type="text/csv")
