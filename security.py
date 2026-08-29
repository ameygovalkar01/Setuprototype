"""
security.py - Security, Sanitization, Password Hashing, URL Validation & Audit Logging
"""
import os
import re
import ipaddress
from urllib.parse import urlparse
from datetime import datetime, timezone
from typing import Tuple, Optional
import bleach
import bcrypt

LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
AUDIT_LOG_FILE = os.path.join(LOGS_DIR, "audit.log")

os.makedirs(LOGS_DIR, exist_ok=True)

TRUSTED_GOV_DOMAINS = [
    "gov.in",
    "nic.in",
    "org.in",
    "mygov.in",
    "standupmitra.in",
    "udyamregistration.gov.in",
    "pmvishwakarma.gov.in",
    "nsfdc.nic.in",
    "nstfdc.tribal.gov.in",
    "nbcfdc.gov.in",
    "nhfdc.nic.in",
    "kviconline.gov.in",
    "mudra.org.in",
    "sidbi.in",
    "vcfsc.in",
    "nskfdc.nic.in",
    "nmdfc.org"
]

def sanitize_text(value: Optional[str]) -> str:
    """
    Strips script/style tags, HTML tags, null bytes, and non-printable control characters.
    Uses bleach with zero permitted tags + regex sanitization.
    """
    if value is None:
        return ""
    raw = str(value)
    
    # Strip non-printable ASCII control characters and null bytes
    cleaned = "".join(ch for ch in raw if ord(ch) >= 32 or ch in ("\n", "\r", "\t"))
    cleaned = bleach.clean(cleaned, tags=[], attributes={}, strip=True)
    return cleaned.strip()

def is_ip_address(host: str) -> bool:
    """Returns True if host is an IPv4 or IPv6 address literal."""
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False

def validate_url(url: Optional[str], enforce_gov_domain: bool = False) -> Tuple[bool, str]:
    """
    Validates a URL against strict security requirements:
    1. Scheme must be https.
    2. Rejects embedded credentials.
    3. Rejects IP-literal destinations and localhost.
    4. Rejects dangerous schemes.
    5. Optionally verifies domain against trusted government domains.
    Returns (is_valid, safe_url_or_reason).
    """
    if not url or not isinstance(url, str):
        return (False, "Empty or invalid URL")
        
    url = url.strip()
    
    if re.match(r"^(javascript|data|vbscript|file):", url, re.IGNORECASE):
        return (False, "Forbidden URL scheme")
        
    try:
        parsed = urlparse(url)
    except Exception as e:
        return (False, f"Malformed URL: {str(e)}")
        
    if parsed.scheme.lower() != "https":
        return (False, "URL must use HTTPS protocol")
        
    if not parsed.netloc:
        return (False, "Missing host in URL")
        
    if parsed.username or parsed.password or "@" in parsed.netloc:
        return (False, "Embedded credentials not allowed")
        
    host = parsed.hostname.lower() if parsed.hostname else ""
    if not host:
        return (False, "Invalid hostname")
        
    if is_ip_address(host) or host in ("localhost", "127.0.0.1", "0.0.0.0"):
        return (False, "IP literals and localhost are prohibited")
        
    if enforce_gov_domain:
        is_trusted = any(host == d or host.endswith("." + d) for d in TRUSTED_GOV_DOMAINS)
        if not is_trusted:
            return (False, f"Domain '{host}' is not in trusted government allow-list")
            
    return (True, url)

def hash_password(raw_password: str) -> str:
    """Hashes a plaintext password using bcrypt with work factor 12."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(raw_password.encode("utf-8"), salt).decode("utf-8")

def verify_password(raw_password: str, hashed_str: str) -> bool:
    """Safely verifies a plaintext password against a stored bcrypt hash."""
    if not raw_password or not hashed_str:
        return False
    try:
        return bcrypt.checkpw(raw_password.encode("utf-8"), hashed_str.encode("utf-8"))
    except Exception:
        return False

def log_audit_event(action: str, detail: str, admin_user: str = "admin_session"):
    """
    Logs administrative actions to a secure local audit log.
    CRITICAL PRIVACY GUARANTEE: Never log citizen demographic or search data.
    Only administrative actions (login, add_scheme, edit_scheme, delete_scheme, bulk_upload, export)
    are permitted to enter this audit trail.
    """
    sanitized_action = sanitize_text(action)
    sanitized_detail = sanitize_text(detail)
    sanitized_admin = sanitize_text(admin_user)
    
    timestamp = datetime.now(timezone.utc).isoformat()
    log_entry = f"[{timestamp}] [USER:{sanitized_admin}] [ACTION:{sanitized_action}] {sanitized_detail}\n"
    
    try:
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Warning: Failed to write audit log: {e}")

def read_recent_audit_logs(limit: int = 50) -> list:
    """Reads recent audit log lines for admin view."""
    if not os.path.exists(AUDIT_LOG_FILE):
        return []
    try:
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f_in:
            lines = f_in.readlines()
        return lines[-limit:][::-1]
    except Exception:
        return []

