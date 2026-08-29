"""
tests/test_core.py - Comprehensive Unit & Security Tests for Setu Core Engine
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import io
import time
import pandas as pd
import numpy as np

import schema
import security
import matcher
import admin

def test_sanitization():
    # Test script and style tag stripping
    raw_xss = "<script>alert(1)</script>Hello<b>World</b>"
    cleaned = security.sanitize_text(raw_xss)
    assert "<script>" not in cleaned
    assert "alert(1)" in cleaned or "Hello" in cleaned
    assert "<b>" not in cleaned
    assert "World" in cleaned
    
    # Test control character removal
    raw_ctrl = "Test\x00String\x1fWith\x08Controls"
    cleaned_ctrl = security.sanitize_text(raw_ctrl)
    assert "\x00" not in cleaned_ctrl
    assert "\x1f" not in cleaned_ctrl

def test_url_validation():
    # Valid HTTPS URLs
    ok, url = security.validate_url("https://www.standupmitra.in/Home")
    assert ok is True
    assert url == "https://www.standupmitra.in/Home"
    
    # Invalid Scheme
    ok, _ = security.validate_url("http://insecure-site.com")
    assert ok is False
    
    # Dangerous protocols
    ok, _ = security.validate_url("javascript:alert(1)")
    assert ok is False
    
    ok, _ = security.validate_url("data:text/html,<script>alert(1)</script>")
    assert ok is False
    
    # IP literal rejection
    ok, _ = security.validate_url("https://192.168.1.1/admin")
    assert ok is False
    
    # Embedded credentials rejection
    ok, _ = security.validate_url("https://admin:pass@portal.gov.in")
    assert ok is False

def test_password_hashing():
    pwd = "GovAdminSecret2026!"
    hashed = security.hash_password(pwd)
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert security.verify_password(pwd, hashed) is True
    assert security.verify_password("WrongPassword", hashed) is False

def test_schema_validation():
    valid_row = {
        "scheme_id": "TEST-001",
        "scheme_name": "Test Affirmative Scheme",
        "sponsoring_body": "Ministry of Social Justice",
        "category": "SC|ST",
        "eligible_gender": "All|Female",
        "pwd_only": False,
        "min_income": 0,
        "max_income": 300000,
        "min_age": 18,
        "max_age": 65,
        "states": "All India",
        "sector": "Manufacturing|Services",
        "benefit_type": "Loan",
        "benefit_amount": "Up to Rs 10 Lakhs",
        "subsidy_percentage": 15.0,
        "description": "Test scheme description for SC/ST artisans and manufacturers.",
        "required_documents": "Aadhaar Card|Caste Certificate",
        "official_url": "https://nsfdc.nic.in",
        "contact_info": "1800-11-0301"
    }
    is_valid, errors = schema.validate_scheme_row(valid_row)
    assert is_valid is True
    assert len(errors) == 0
    
    # Invalid category
    invalid_cat_row = dict(valid_row)
    invalid_cat_row["category"] = "UnknownCategory"
    is_valid, errors = schema.validate_scheme_row(invalid_cat_row)
    assert is_valid is False
    assert any("category" in e.lower() for e in errors)
    
    # Invalid income range
    invalid_inc_row = dict(valid_row)
    invalid_inc_row["min_income"] = 500000
    invalid_inc_row["max_income"] = 200000
    is_valid, errors = schema.validate_scheme_row(invalid_inc_row)
    assert is_valid is False

def test_matcher_deterministic_and_explainability():
    df = admin.load_schemes_dataframe()
    assert not df.empty, "Pre-seeded schemes should not be empty"
    
    # Test SC Female Entrepreneur profile
    profile_sc_female = {
        "category": "SC",
        "gender": "Female",
        "is_pwd": False,
        "pwd_percent": 0,
        "income": 120000,
        "age": 28,
        "state": "Maharashtra",
        "sector": "Artisans & Crafts",
        "business_need": "I run a handloom weaving unit and want concessional credit for purchasing raw materials and tools."
    }
    
    matches = matcher.match_schemes(
        user_profile=profile_sc_female,
        schemes_df=df,
        embedding_model=None,
        low_bandwidth_mode=True
    )
    
    assert len(matches) > 0
    # Verify Stand-Up India or NSFDC or Mahila Samriddhi are among matches
    scheme_ids = [m["scheme_id"] for m in matches]
    assert "SETU-001" in scheme_ids or "SETU-002" in scheme_ids or "SETU-010" in scheme_ids
    
    top_match = matches[0]
    assert "qualification_reasons" in top_match
    assert len(top_match["qualification_reasons"]) >= 2
    assert top_match["match_score"] >= 65
    
    # Test PwD only scheme filter
    profile_pwd = {
        "category": "General",
        "gender": "Male",
        "is_pwd": True,
        "pwd_percent": 60,
        "income": 200000,
        "age": 35,
        "state": "Delhi",
        "sector": "Services",
        "business_need": "Setting up an IT services kiosk."
    }
    pwd_matches = matcher.match_schemes(
        user_profile=profile_pwd,
        schemes_df=df,
        embedding_model=None,
        low_bandwidth_mode=True
    )
    pwd_ids = [m["scheme_id"] for m in pwd_matches]
    assert "SETU-007" in pwd_ids, "NHFDC scheme must match certified PwD applicant"

def test_document_checklist_aggregation():
    sample_matches = [
        {
            "scheme_name": "Scheme A",
            "match_score": 90,
            "required_documents": ["Aadhaar Card", "Caste Certificate", "DPR"]
        },
        {
            "scheme_name": "Scheme B",
            "match_score": 85,
            "required_documents": ["Aadhaar Card", "Income Certificate", "DPR"]
        }
    ]
    checklist = matcher.aggregate_document_checklist(sample_matches)
    doc_dict = {item["document_name"]: item["required_by_count"] for item in checklist}
    assert doc_dict["Aadhaar Card"] == 2
    assert doc_dict["DPR"] == 2
    assert doc_dict["Caste Certificate"] == 1
    assert doc_dict["Income Certificate"] == 1

def test_admin_rate_limiting_and_session():
    state = {}
    
    # Test initial state
    is_ok, _ = admin.check_login_rate_limit(state)
    assert is_ok is True
    
    # Trigger 5 failed attempts
    for _ in range(5):
        admin.record_failed_login(state)
        
    is_ok, msg = admin.check_login_rate_limit(state)
    assert is_ok is False
    assert "rate limit" in msg.lower() or "wait" in msg.lower()
    
    # Successful login resets
    admin.record_successful_login(state)
    assert state["is_admin"] is True
    assert admin.verify_admin_session(state) is True
    
    # Inactivity timeout simulation
    state["admin_last_active"] = time.time() - (20 * 60) # 20 minutes ago
    assert admin.verify_admin_session(state) is False
    assert state.get("is_admin") is False

def test_bulk_csv_validation():
    state = {"is_admin": True, "admin_last_active": time.time()}
    
    # Valid CSV
    valid_csv = b"""scheme_id,scheme_name,sponsoring_body,category,eligible_gender,pwd_only,min_income,max_income,min_age,max_age,states,sector,benefit_type,benefit_amount,subsidy_percentage,description,required_documents,official_url,contact_info
BULK-001,Bulk Test Scheme,MoSJE,SC|ST,All,False,0,300000,18,65,All India,Manufacturing,Loan,Loans up to 5 Lakhs,0.0,Test description for bulk scheme,Aadhaar Card|Caste Certificate,https://nsfdc.nic.in,1800-11-0301
"""
    
    # Test invalid CSV with bad category
    invalid_csv = b"""scheme_id,scheme_name,sponsoring_body,category,eligible_gender,pwd_only,min_income,max_income,min_age,max_age,states,sector,benefit_type,benefit_amount,subsidy_percentage,description,required_documents,official_url,contact_info
BULK-002,Bad Scheme,MoSJE,InvalidCat,All,False,0,300000,18,65,All India,Manufacturing,Loan,Loans up to 5 Lakhs,0.0,Description,Aadhaar Card,https://nsfdc.nic.in,1800-11-0301
"""
    
    ok, errors, count = admin.validate_and_ingest_bulk_csv(invalid_csv, "invalid.csv", state)
    assert ok is False
    assert len(errors) > 0
    assert any("categor" in e.lower() for e in errors)

if __name__ == "__main__":
    print("Running test suite directly...")
    test_sanitization()
    test_url_validation()
    test_password_hashing()
    test_schema_validation()
    test_matcher_deterministic_and_explainability()
    test_document_checklist_aggregation()
    test_admin_rate_limiting_and_session()
    test_bulk_csv_validation()
    print("All 7 core test suites passed successfully!")
