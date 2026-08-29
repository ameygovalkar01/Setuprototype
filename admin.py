"""
admin.py - Secure Administration Module: Auth, Session Guards, Atomic CRUD & Bulk Ingestion
"""
import os
import io
import time
import tempfile
import pandas as pd
from typing import Tuple, List, Dict, Any, Optional
from dotenv import load_dotenv

import schema
import security

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
SCHEMES_FILE = os.path.join(DATA_DIR, 'schemes.csv')
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB limit
MAX_UPLOAD_ROWS = 2000
SESSION_TIMEOUT_SECONDS = 15 * 60  # 15 minutes
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_COOLDOWN_SECONDS = 60

def get_admin_password_hash() -> Optional[str]:
    """Fetches the admin password hash securely from the environment."""
    return os.getenv('ADMIN_PASSWORD_HASH')

def check_login_rate_limit(session_state: dict) -> Tuple[bool, str]:
    """
    Enforces in-session rate limiting on admin authentication attempts.
    Returns (is_allowed, error_message).
    """
    now = time.time()
    failed_count = session_state.get('admin_failed_attempts', 0)
    lockout_until = session_state.get('admin_lockout_until', 0)
    
    if now < lockout_until:
        remaining = int(lockout_until - now)
        return (False, f"Too many failed attempts. Rate limit active. Please wait {remaining}s.")
        
    return (True, "")

def record_failed_login(session_state: dict):
    """Increments failed login counter and sets lockout timestamp if threshold exceeded."""
    session_state['admin_failed_attempts'] = session_state.get('admin_failed_attempts', 0) + 1
    if session_state['admin_failed_attempts'] >= MAX_LOGIN_ATTEMPTS:
        session_state['admin_lockout_until'] = time.time() + LOCKOUT_COOLDOWN_SECONDS
        security.log_audit_event('AUTH_LOCKOUT', f'Admin login locked out for {LOCKOUT_COOLDOWN_SECONDS}s due to consecutive failures.')

def record_successful_login(session_state: dict):
    """Resets failure counters and sets active admin session timestamp."""
    session_state['admin_failed_attempts'] = 0
    session_state['admin_lockout_until'] = 0
    session_state['is_admin'] = True
    session_state['admin_last_active'] = time.time()
    security.log_audit_event('AUTH_SUCCESS', 'Admin successfully authenticated.')

def verify_admin_session(session_state: dict) -> bool:
    """
    Guard clause: Re-checks that the user is authenticated and the session has not timed out.
    Times out automatically after 15 minutes of inactivity.
    """
    if not session_state.get('is_admin', False):
        return False
        
    last_active = session_state.get('admin_last_active', 0)
    now = time.time()
    if now - last_active > SESSION_TIMEOUT_SECONDS:
        # Session expired
        session_state['is_admin'] = False
        session_state.pop('admin_last_active', None)
        security.log_audit_event('AUTH_TIMEOUT', 'Admin session expired due to inactivity.')
        return False
        
    # Update activity timestamp
    session_state['admin_last_active'] = now
    return True

def logout_admin(session_state: dict):
    """Explicitly destroys the admin session."""
    session_state['is_admin'] = False
    session_state.pop('admin_last_active', None)
    security.log_audit_event('AUTH_LOGOUT', 'Admin logged out.')

def load_schemes_dataframe() -> pd.DataFrame:
    """
    Loads and validates the schemes CSV from disk.
    Returns a pandas DataFrame.
    """
    if not os.path.exists(SCHEMES_FILE):
        return pd.DataFrame(columns=schema.SCHEME_COLUMNS)
    try:
        df = pd.read_csv(SCHEMES_FILE, dtype=str, keep_default_na=False)
        # Ensure all standard columns are present
        for col in schema.SCHEME_COLUMNS:
            if col not in df.columns:
                df[col] = ''
        return df
    except Exception as e:
        print(f"Error reading schemes file: {e}")
        return pd.DataFrame(columns=schema.SCHEME_COLUMNS)

def atomic_write_schemes(df: pd.DataFrame, admin_user: str = "admin") -> Tuple[bool, str]:
    """
    Performs an atomic write to schemes.csv using write-temp-then-rename pattern.
    Ensures that concurrent readers never see corrupted or partial writes.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    temp_fd = None
    temp_path = None
    try:
        # Create temp file in the same directory to ensure same filesystem for os.replace
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            dir=DATA_DIR,
            delete=False,
            newline='',
            encoding='utf-8',
            suffix='.tmp'
        )
        temp_path = temp_file.name
        
        # Write clean dataframe
        df.to_csv(temp_file, index=False, columns=schema.SCHEME_COLUMNS)
        temp_file.flush()
        os.fsync(temp_file.fileno())
        temp_file.close()
        
        # Verify that temp file round-trips properly
        test_df = pd.read_csv(temp_path, dtype=str, keep_default_na=False)
        if len(test_df) != len(df):
            raise ValueError("Verification failed: written row count mismatch")
            
        # Atomic rename over target file
        os.replace(temp_path, SCHEMES_FILE)
        return (True, "Schemes successfully saved.")
    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        return (False, f"Atomic write failed: {str(e)}")

def save_scheme_entry(scheme_dict: Dict[str, Any], is_edit: bool, session_state: dict) -> Tuple[bool, List[str]]:
    """
    Validates, sanitizes, and commits a manual scheme entry atomically.
    """
    if not verify_admin_session(session_state):
        return (False, ["Unauthorized: Invalid or expired admin session."])
        
    # Sanitize all string fields
    sanitized = {}
    for k, v in scheme_dict.items():
        if isinstance(v, str):
            sanitized[k] = security.sanitize_text(v)
        elif isinstance(v, list):
            sanitized[k] = schema.join_multi_field([security.sanitize_text(str(x)) for x in v])
        else:
            sanitized[k] = v
            
    # Validate official URL
    url = sanitized.get('official_url', '')
    is_valid_url, url_msg = security.validate_url(url, enforce_gov_domain=False)
    if not is_valid_url:
        return (False, [f"Official URL Error: {url_msg}"])
        
    # Validate against schema rules
    is_valid_schema, errors = schema.validate_scheme_row(sanitized)
    if not is_valid_schema:
        return (False, errors)
        
    df = load_schemes_dataframe()
    scheme_id = sanitized['scheme_id']
    
    if is_edit:
        if scheme_id not in df['scheme_id'].values:
            return (False, [f"Scheme ID '{scheme_id}' not found for edit."])
        # Update row
        idx = df[df['scheme_id'] == scheme_id].index[0]
        for col in schema.SCHEME_COLUMNS:
            df.at[idx, col] = str(sanitized.get(col, ''))
        action = f"EDIT_SCHEME: {scheme_id} ({sanitized.get('scheme_name', '')})"
    else:
        if scheme_id in df['scheme_id'].values:
            return (False, [f"Scheme ID '{scheme_id}' already exists. Please choose a unique ID."])
        # Append row
        new_row = {col: str(sanitized.get(col, '')) for col in schema.SCHEME_COLUMNS}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        action = f"CREATE_SCHEME: {scheme_id} ({sanitized.get('scheme_name', '')})"
        
    success, write_msg = atomic_write_schemes(df)
    if success:
        security.log_audit_event('SAVE_SCHEME', action)
        return (True, [])
    else:
        return (False, [write_msg])

def delete_scheme_entry(scheme_id: str, session_state: dict) -> Tuple[bool, str]:
    """Deletes a scheme entry by scheme_id atomically."""
    if not verify_admin_session(session_state):
        return (False, "Unauthorized: Invalid or expired admin session.")
        
    df = load_schemes_dataframe()
    if scheme_id not in df['scheme_id'].values:
        return (False, f"Scheme ID '{scheme_id}' not found.")
        
    df = df[df['scheme_id'] != scheme_id].copy()
    success, write_msg = atomic_write_schemes(df)
    if success:
        security.log_audit_event('DELETE_SCHEME', f"Deleted scheme {scheme_id}")
        return (True, f"Scheme {scheme_id} deleted successfully.")
    else:
        return (False, write_msg)

def validate_and_ingest_bulk_csv(file_bytes: bytes, filename: str, session_state: dict) -> Tuple[bool, List[str], int]:
    """
    Validates uploaded CSV file against size, row limits, and column-by-column schema rules.
    Fails closed: Rejects entire batch if ANY row has validation errors.
    Returns (success, list_of_errors_or_messages, rows_ingested_count).
    """
    if not verify_admin_session(session_state):
        return (False, ["Unauthorized: Invalid or expired admin session."], 0)
        
    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        return (False, [f"File size exceeds maximum allowed limit of 5 MB ({len(file_bytes)} bytes)."], 0)
        
    try:
        csv_text = file_bytes.decode('utf-8')
    except UnicodeDecodeError:
        try:
            csv_text = file_bytes.decode('latin-1')
        except Exception:
            return (False, ["File is not a valid UTF-8 or text CSV file."], 0)
            
    try:
        uploaded_df = pd.read_csv(io.StringIO(csv_text), dtype=str, keep_default_na=False)
    except Exception as e:
        return (False, [f"CSV Parsing Error: {str(e)}"], 0)
        
    if len(uploaded_df) == 0:
        return (False, ["Uploaded CSV contains zero data rows."], 0)
        
    if len(uploaded_df) > MAX_UPLOAD_ROWS:
        return (False, [f"CSV exceeds maximum batch limit of {MAX_UPLOAD_ROWS} rows."], 0)
        
    # Verify required headers
    missing_headers = [c for c in schema.SCHEME_COLUMNS if c not in uploaded_df.columns]
    if missing_headers:
        return (False, [f"Missing required columns in CSV: {missing_headers}"], 0)
        
    batch_errors = []
    sanitized_rows = []
    seen_ids = set()
    
    for idx, row in uploaded_df.iterrows():
        row_num = idx + 2  # CSV line number
        row_dict = row.to_dict()
        
        # Sanitize text
        clean_row = {}
        for k, v in row_dict.items():
            clean_row[k] = security.sanitize_text(str(v))
            
        sid = clean_row.get('scheme_id', '').strip()
        if not sid:
            batch_errors.append(f"Row {row_num}: scheme_id cannot be empty.")
        elif sid in seen_ids:
            batch_errors.append(f"Row {row_num}: Duplicate scheme_id '{sid}' inside uploaded file.")
        else:
            seen_ids.add(sid)
            
        # Validate URL
        url = clean_row.get('official_url', '')
        url_ok, url_err = security.validate_url(url)
        if not url_ok:
            batch_errors.append(f"Row {row_num} (ID: {sid}): Invalid official_url - {url_err}")
            
        # Validate schema
        is_ok, errs = schema.validate_scheme_row(clean_row)
        if not is_ok:
            for err in errs:
                batch_errors.append(f"Row {row_num} (ID: {sid}): {err}")
                
        sanitized_rows.append(clean_row)
        
    if batch_errors:
        return (False, batch_errors, 0)
        
    # All rows valid -> replace / merge cleanly
    new_df = pd.DataFrame(sanitized_rows)[schema.SCHEME_COLUMNS]
    success, write_msg = atomic_write_schemes(new_df)
    
    if success:
        security.log_audit_event('BULK_INGEST', f"Bulk ingested {len(new_df)} schemes from {security.sanitize_text(filename)}")
        return (True, [f"Successfully validated and ingested {len(new_df)} schemes."], len(new_df))
    else:
        return (False, [write_msg], 0)
