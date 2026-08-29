# Setu (सेतु) — AI-Driven Scheme Matching for Marginalized Entrepreneurs

**Smart India Hackathon Problem Statement SIH26092**  
*Ministry of Social Justice & Empowerment (MoSJE), Government of India*

---

## 📌 Executive Summary

**Setu (सेतु — "Bridge")** is a secure, privacy-first affirmative scheme discovery platform that bridges marginalized and vulnerable entrepreneurs (SC, ST, OBC, Divyangjan/PwD, EWS, DNT, Women, Minorities) to government concessional credit, capital subsidies, toolkits, and incubation schemes.

Designed from the ground up under **Defense-in-Depth and Least Privilege** principles, Setu treats sensitive demographic data (caste, disability, income) with absolute confidentiality: **Zero persistence of citizen PII**.

---

## 🏛️ Guiding Security & Privacy Architecture

1. **Zero Citizen PII Retention (Stateless Matching)**  
   - Citizen intake form inputs live **strictly in temporary memory (`st.session_state`)** for the active session.
   - Demographic inputs (caste, disability %, annual family income) **never touch disk, database clients, or log files**.
   
2. **Least Privilege & Role-Based Isolation**  
   - The public Citizen Matcher and Scheme Explorer operate strictly in **read-only mode**.
   - Only authenticated administrators can modify `schemes.csv` through validated atomic operations.

3. **Two-Stage Explainable Recommendation Engine**  
   - **Stage 1 (Deterministic Filtering)**: Pure pandas boolean vector masking on caste, income caps (`-1` = uncapped), age bounds, state coverage, gender, and certified disability status.
   - **Stage 2 (Semantic Affinity Ranking)**: Cosine similarity via `sentence-transformers` (`all-MiniLM-L6-v2`) cached once in memory via `@st.cache_resource`, with automatic TF-IDF fallback in **Low-Bandwidth Mode**.
   - **Explainability Over Black-Box**: Every recommendation provides plain-language justification bullets (e.g. *"✓ Income ₹1.5L ≤ Cap ₹3.0L"*, *"✓ Dedicated Divyangjan quota"*).

4. **Secured Administrative Layer**  
   - **Bcrypt Passwords (Cost factor = 12)** stored in `.env`, never in code or plaintext.
   - **Rate Limiting**: Failed login attempts trigger exponential cooldowns to block brute-forcing.
   - **Inactivity Timeout**: Admin sessions expire automatically after 15 minutes of inactivity.
   - **Atomic Writes**: `schemes.csv` updates use a write-to-temp-then-rename (`os.replace`) strategy to prevent partial/corrupted writes.
   - **Strict Bulk Ingestion**: CSV uploads are validated row-by-row against `schema.py` and fail closed (rejects whole batch on any invalid field).

5. **Input Sanitization & URL Defense**  
   - All free-text fields are stripped of HTML/script/control characters using `bleach.clean(tags=[], strip=True)`.
   - External URLs enforce `https://`, reject IP literals/embedded credentials, and validate against authorized government domains (`.gov.in`, `.nic.in`, `.org.in`).

---

## 📂 Project Architecture

```
setu-scheme-matcher/
├── app.py                 # Multi-tab UI: Citizen Matcher / Catalog Explorer / Admin Portal
├── matcher.py             # Rule-based filter + semantic ranking + explainability engine
├── admin.py               # Admin auth, session timeout, rate limiting, atomic CRUD, bulk ingest
├── security.py            # Sanitization, bcrypt hashing, URL validation, non-PII audit logging
├── schema.py              # Single source of truth: column types, allow-lists, delimiter (|)
├── generate_hash.py       # Helper CLI to generate bcrypt hashes for .env
├── requirements.txt       # Pinned dependencies
├── .env.example           # Environment template
├── .env                   # Local configuration (not committed in production)
├── data/
│   ├── schemes.csv        # Pre-seeded database of 12 real central welfare schemes
│   └── help_desks.json    # Static directory of state nodal facilitation centers
├── logs/
│   └── audit.log          # Non-PII administrative event audit trail
└── tests/
    └── test_core.py       # Automated test suite (Sanitization, URL, Matcher, Admin)
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (Python 3.11, 3.12, 3.13, 3.14 supported)
- `pip` package manager

### 2. Installation

Clone or navigate to the project directory:
```bash
cd setu-scheme-matcher
```

Install dependencies:
```bash
python3 -m pip install -r requirements.txt
```

### 3. Environment & Admin Credentials Setup

Generate a secure Bcrypt hash for your administrator password:
```bash
python3 generate_hash.py
```
*(Enter your chosen password, e.g., `MyGovAdminPassword2026!`)*

Copy `.env.example` to `.env` and paste the generated hash:
```bash
cp .env.example .env
```
Ensure your `.env` contains:
```ini
ADMIN_PASSWORD_HASH="$2b$12$..."
APP_ENV=development
```
*(Note: A default demo password `SetuAdmin@2026!#` is pre-configured for evaluation).*

### 4. Run Automated Test Suite

Verify all security filters, schema validations, and matching logic:
```bash
python3 tests/test_core.py
```

### 5. Launch the Web Portal / Website

Start the production web server (FastAPI + Modern HTML5/CSS3/JS Web Application):
```bash
python3 -m uvicorn server:app --reload --port 8000
```
Open your browser at **`http://localhost:8000`** to access the complete responsive government web portal.

*(Alternative Streamlit view is also available via: `streamlit run app.py`)*


---

## 🌐 Key Features & UI Walkthrough

| Feature | Description |
|---|---|
| 🔍 **Citizen Matcher** | Interactive intake with real-time matching, match % badges, and detailed eligibility criteria. |
| 💡 **Reasoning Transparency** | "Why You Qualify" breakdown showing exact matching social, financial, age, and sector rules. |
| 📋 **Universal Checklist** | Dynamic consolidated checklist of all required documents (Caste Cert, DPR, UDID, etc.). |
| 📥 **Downloadable Summary** | Export plain-text slip with matches and checklists to take to physical district offices. |
| 🌐 **Bilingual Support** | Instant toggle between **English** and **हिन्दी (Hindi)**. |
| ⚡ **Low-Bandwidth Mode** | Bypasses heavy neural models in favor of lightweight token indexing for 2G/3G connections. |
| 📍 **Static Helpdesk Directory** | Instant lookup of state-level MSME DFOs, SC/ST corporations, and Divyangjan welfare centers. |
| 📚 **Scheme Explorer** | Filterable public directory across ministries, benefits (loans, grants, subsidies), and target groups. |
| ⚙️ **Admin Portal** | Secure scheme management with live table editing, atomic creation, deletion, CSV bulk upload, and audit logs. |

---

## 📦 Pre-Seeded Schemes in `data/schemes.csv`

1. **Stand-Up India Scheme** — SC/ST & Women, greenfield loans ₹10L–₹1 Crore.
2. **NSFDC Term Loan Scheme** — SC entrepreneurs, income ≤ ₹3 Lakhs, loans up to ₹50 Lakhs.
3. **NSTFDC Adivasi Mahila Sashaktikaran Yojana (AMSY)** — ST women micro-credit up to ₹2 Lakhs @ 4%.
4. **PM Vishwakarma Yojana** — 18 artisan trades, ₹15,000 toolkit grant + collateral-free loans up to ₹3 Lakhs @ 5%.
5. **Venture Capital Fund for SC (VCF-SC)** — SC tech startups & industry, equity up to ₹15 Crores.
6. **NBCFDC General Term Loan** — OBC & DNT entrepreneurs, income ≤ ₹3 Lakhs, loans up to ₹15 Lakhs.
7. **NHFDC Self-Employment Scheme for Divyangjan** — Certified PwD (≥40%), soft credit up to ₹25 Lakhs.
8. **Prime Minister Employment Generation Programme (PMEGP)** — 35% margin money subsidy for special categories.
9. **Pradhan Mantri MUDRA Yojana (PMMY)** — Micro-enterprises, Shishu/Kishore/Tarun loans up to ₹20 Lakhs.
10. **NSFDC Mahila Samriddhi Yojana** — SC women micro-credit up to ₹1.4 Lakhs @ 4%.
11. **NSKFDC Term Loan** — Safai Karamcharis & manual scavengers rehabilitation loans up to ₹15 Lakhs.
12. **NMDFC Virasat Scheme** — Minority craftspersons and artisans credit up to ₹10 Lakhs.

---

## 🛡️ Production Readiness & Deployment Disclaimer

> [!IMPORTANT]
> **Prototype Scope**: This implementation is an engineered prototype for the Smart India Hackathon.
> For enterprise production deployment under MoSJE / National Informatics Centre (NIC):
> - **Storage**: Migrate `schemes.csv` to PostgreSQL / Cloud SQL with Row-Level Security (RLS) and automated read replicas.
> - **Secrets Management**: Transition `.env` to AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault.
> - **Authentication**: Integrate Gov SSO (Jan Parichay / MeriPehchaan OAuth2/OIDC) for administrative access.
> - **Transport Security**: Enforce TLS 1.3 with HSTS headers via Reverse Proxy (NGINX / Cloudflare).
> - **WAF**: Deploy AWS WAF or Cloud Armor to defend against Layer 7 DDoS and rate abuse.

---

## 📄 License & Attribution

Developed for **Smart India Hackathon (SIH26092)**.  
Ministry of Social Justice & Empowerment, Government of India.
