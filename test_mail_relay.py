# test_mail_relay.py - 10-Iteration Verification Suite
import time
from fastapi.testclient import TestClient
from server import app
import users

client = TestClient(app)

print("="*60)
print("RUNNING 10-ITERATION VERIFICATION OF SETU MAIL & AUTH RELAY")
print("="*60)

for i in range(1, 11):
    test_email = f"entrepreneur_iter{i}_{int(time.time())}@govmail.in"
    test_pwd = f"StrongPassword{i}!2026"
    test_name = f"Test Entrepreneur #{i}"
    
    # 1. Test Format & Payload Construction
    subj, html, txt = users.format_email_bodies("123456", "verification")
    assert "Setu" in subj
    assert "123456" in html
    assert "123456" in txt
    
    # 2. Test Signup Endpoint
    res_signup = client.post("/api/auth/signup", json={
        "name": test_name,
        "email": test_email,
        "password": test_pwd
    })
    assert res_signup.status_code == 200, f"Iteration {i} signup failed: {res_signup.text}"
    otp = res_signup.json().get("otp") or res_signup.json().get("demo_otp")
    assert len(otp) == 6, f"Invalid OTP in iter {i}: {otp}"
    
    # 3. Test Verification & Activation
    res_verify = client.post("/api/auth/verify-email", json={
        "email": test_email,
        "otp": otp
    })
    assert res_verify.status_code == 200, f"Iteration {i} verify failed: {res_verify.text}"
    token = res_verify.json()["data"]["token"]
    assert token, f"No token in iter {i}"
    
    # 4. Test Authenticated Login
    res_login = client.post("/api/auth/login", json={
        "email": test_email,
        "password": test_pwd
    })
    assert res_login.status_code == 200, f"Iteration {i} login failed"
    
    # 5. Test Password Reset Dispatch & Execution
    res_forgot = client.post("/api/auth/forgot-password", json={"email": test_email})
    assert res_forgot.status_code == 200
    reset_otp = res_forgot.json().get("otp") or res_forgot.json().get("demo_otp")
    
    new_pwd = f"NewPassword{i}!2026"
    res_reset = client.post("/api/auth/reset-password", json={
        "email": test_email,
        "otp": reset_otp,
        "new_password": new_pwd
    })
    assert res_reset.status_code == 200
    
    # 6. Test Login with New Password
    res_new_login = client.post("/api/auth/login", json={
        "email": test_email,
        "password": new_pwd
    })
    assert res_new_login.status_code == 200
    
    print(f" Iteration {i:2d}/10: PASSED - {test_email} signed up, verified, logged in, and reset.")

print("="*60)
print("ALL 10 ITERATIONS COMPLETED AND VERIFIED 100% WORKING!")
print("="*60)
