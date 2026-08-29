"""
app.py - Setu (सेतु): AI-Driven Scheme Matching for Marginalized Entrepreneurs
SIH26092 - Ministry of Social Justice & Empowerment
"""
import os
import json
import time
import pandas as pd
import streamlit as st

import schema
import security
import matcher
import admin

st.set_page_config(
    page_title="Setu (सेतु) — Scheme Matching Platform",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 50%, #047857 100%);
        padding: 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .main-header h1 {
        color: white !important;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .main-header p {
        color: #E2E8F0 !important;
        font-size: 1.05rem;
        margin: 0;
    }
    .badge-privacy {
        display: inline-block;
        background-color: rgba(255, 255, 255, 0.18);
        border: 1px solid rgba(255, 255, 255, 0.35);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        color: #F8FAFC;
        margin-top: 10px;
    }
    .scheme-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 5px solid #1E40AF;
        border-radius: 8px;
        padding: 18px 20px;
        margin-bottom: 18px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .scheme-card-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0F172A;
    }
    .scheme-card-body {
        font-size: 0.95rem;
        color: #475569;
        margin-top: 6px;
    }
    .match-badge {
        background-color: #ECFDF5;
        color: #047857;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 6px;
        border: 1px solid #A7F3D0;
        font-size: 0.9rem;
    }
    .reason-box {
        background-color: #F8FAFC;
        border-left: 3px solid #0D9488;
        padding: 10px 14px;
        border-radius: 4px;
        font-size: 0.9rem;
        margin-top: 10px;
        color: #334155;
    }
    .doc-pill {
        display: inline-block;
        background-color: #EFF6FF;
        color: #1D4ED8;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        margin-right: 6px;
        margin-bottom: 4px;
        border: 1px solid #DBEAFE;
    }
    .stButton>button {
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

I18N = {
    "en": {
        "title": "Setu (सेतु)",
        "subtitle": "AI-Driven Welfare Scheme & Concessional Credit Matching for Marginalized Entrepreneurs",
        "badge_privacy": "🔒 Zero Citizen PII Retention — Stateless & In-Memory Matching Engine",
        "tab_matcher": "🔍 Citizen Scheme Matcher",
        "tab_explorer": "📚 Scheme Explorer",
        "tab_admin": "⚙️ Admin Portal",
        "intake_header": "Entrepreneur Profile (Optional fields can be skipped)",
        "category_label": "Social Category / Caste Group",
        "gender_label": "Gender Identity",
        "pwd_label": "Divyangjan / Person with Disability (PwD)?",
        "pwd_pct_label": "Disability Percentage (%)",
        "income_label": "Annual Household Income (₹)",
        "age_label": "Applicant Age (Years)",
        "state_label": "State / Union Territory",
        "sector_label": "Business Domain / Trade Sector",
        "need_label": "Describe your business idea or financial requirement:",
        "need_placeholder": "E.g., I want to establish a small handloom & apparel production unit in rural Pune and need capital for modern sewing machines.",
        "btn_match": "🚀 Find Eligible Schemes",
        "results_header": "Eligible Government Schemes Found",
        "match_score": "Match Score",
        "why_qualify": "Why You Qualify (Explainable Transparency)",
        "docs_needed": "Required Documentation Checklist",
        "official_apply": "Apply on Official Portal",
        "contact": "Nodal Contact",
        "no_matches": "No schemes matched your exact constraints. Try adjusting the category, income or sector criteria.",
        "nearest_helpdesk": "📍 Nearest State Nodal Facilitation Center",
        "download_summary": "📥 Download Match Summary & Document Checklist",
        "low_bw_toggle": "⚡ Low-Bandwidth Mode (Keyword-only matcher, instant load)",
        "lang_toggle": "Language / भाषा"
    },
    "hi": {
        "title": "सेतु (Setu)",
        "subtitle": "वंचित एवं दिव्यांग उद्यमियों के लिए एआई-संचालित कल्याणकारी योजना एवं रियायती ऋण सेतु",
        "badge_privacy": "🔒 शून्य व्यक्तिगत डेटा भंडारण — पूर्णतः सुरक्षित व तात्कालिक मैचिंग",
        "tab_matcher": "🔍 नागरिक योजना सेतु",
        "tab_explorer": "📚 योजना खोज (कैटलॉग)",
        "tab_admin": "⚙️ प्रशासन पोर्टल",
        "intake_header": "उद्यमी विवरण (अनावश्यक विवरण छोड़ सकते हैं)",
        "category_label": "सामाजिक श्रेणी / वर्ग",
        "gender_label": "लिंग",
        "pwd_label": "क्या आप दिव्यांग (PwD) हैं?",
        "pwd_pct_label": "दिव्यांगता प्रतिशत (%)",
        "income_label": "वार्षिक पारिवारिक आय (₹)",
        "age_label": "आवेदक की आयु (वर्ष)",
        "state_label": "राज्य / केंद्र शासित प्रदेश",
        "sector_label": "व्यवसाय क्षेत्र / उद्योग",
        "need_label": "अपनी व्यावसायिक आवश्यकता या कार्य का संक्षिप्त विवरण दें:",
        "need_placeholder": "उदा. मैं पारंपरिक हथकरघा एवं सिलाई इकाई स्थापित करने हेतु मशीनरी व कार्यशील पूंजी ऋण चाहता हूँ।",
        "btn_match": "🚀 उपयुक्त योजनाएं खोजें",
        "results_header": "आपके लिए उपयुक्त सरकारी योजनाएं",
        "match_score": "पात्रता स्कोर",
        "why_qualify": "आप क्यों पात्र हैं (स्पष्ट नियम आधार)",
        "docs_needed": "आवश्यक दस्तावेज चेकलिस्ट",
        "official_apply": "आधिकारिक पोर्टल पर आवेदन करें",
        "contact": "नोडल संपर्क",
        "no_matches": "दी गई जानकारी के अनुसार कोई योजना नहीं मिली। कृपया आय या श्रेणी विवरण में बदलाव करें।",
        "nearest_helpdesk": "📍 राज्य नोडल सुविधा केंद्र",
        "download_summary": "📥 पात्रता व दस्तावेज पर्ची डाउनलोड करें",
        "low_bw_toggle": "⚡ कम बैंडविड्थ मोड (तेज कीवर्ड मिलान)",
        "lang_toggle": "Language / भाषा"
    }
}

@st.cache_resource(show_spinner="Loading AI Embedding Engine (all-MiniLM-L6-v2)...")
def load_cached_transformer():
    return matcher.get_sentence_transformer_model()

@st.cache_data(show_spinner=False)
def load_cached_helpdesks():
    path = os.path.join(os.path.dirname(__file__), "data", "help_desks.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/india-circular.png", width=64)
    st.title("Setu • सेतु")
    st.caption("Smart India Hackathon — SIH26092\nMinistry of Social Justice & Empowerment")
    st.divider()
    lang_choice = st.radio("Language / भाषा", ["English", "हिन्दी"], index=0)
    lang_code = "hi" if lang_choice == "हिन्दी" else "en"
    T = I18N[lang_code]
    low_bandwidth = st.checkbox(T["low_bw_toggle"], value=False, help="Uses fast token indexing instead of downloading/running large neural embeddings.")
    st.divider()
    st.markdown("### 🛡️ Privacy Contract")
    st.info("**Zero PII Stored**: Your caste, income, disability, and business details are processed strictly in temporary RAM. No user inputs are saved to disk, databases, or tracking logs.")

st.markdown(f"""
<div class="main-header">
    <h1>{T["title"]}</h1>
    <p>{T["subtitle"]}</p>
    <div class="badge-privacy">{T["badge_privacy"]}</div>
</div>
""", unsafe_allow_html=True)

tab_matcher, tab_explorer, tab_admin = st.tabs([T["tab_matcher"], T["tab_explorer"], T["tab_admin"]])
schemes_df = admin.load_schemes_dataframe()
help_desks = load_cached_helpdesks()
embedding_model = None if low_bandwidth else load_cached_transformer()

# TAB 1: Citizen Scheme Matcher
with tab_matcher:
    st.subheader(T["intake_header"])
    with st.form("citizen_intake_form", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            cat_options = [c for c in schema.ALLOWED_CATEGORIES if c != "All"]
            user_cat = st.selectbox(T["category_label"], cat_options, index=0)
            user_gender = st.selectbox(T["gender_label"], ["All-Any", "Female", "Male", "Transgender"], index=0)
        with c2:
            is_pwd = st.selectbox(T["pwd_label"], ["No", "Yes"], index=0) == "Yes"
            pwd_pct = 40
            if is_pwd:
                pwd_pct = st.slider(T["pwd_pct_label"], min_value=40, max_value=100, value=50, step=5)
            user_age = st.number_input(T["age_label"], min_value=18, max_value=75, value=28, step=1)
        with c3:
            user_income = st.number_input(T["income_label"], min_value=0, max_value=2500000, value=150000, step=25000, help="Family annual income. Set to 0 if none.")
            user_state = st.selectbox(T["state_label"], schema.STATES_AND_UTS, index=0)
        c4, c5 = st.columns([1, 2])
        with c4:
            user_sector = st.selectbox(T["sector_label"], schema.ALLOWED_SECTORS, index=0)
        with c5:
            user_need = st.text_area(T["need_label"], placeholder=T["need_placeholder"], height=90)
        submit_button = st.form_submit_button(T["btn_match"], use_container_width=True, type="primary")

    if submit_button or st.session_state.get("last_matched_results"):
        if submit_button:
            user_profile = {
                "category": user_cat,
                "gender": user_gender,
                "is_pwd": is_pwd,
                "pwd_percent": pwd_pct if is_pwd else 0,
                "income": user_income,
                "age": user_age,
                "state": user_state,
                "sector": user_sector,
                "business_need": user_need
            }
            matched_list = matcher.match_schemes(
                user_profile=user_profile,
                schemes_df=schemes_df,
                embedding_model=embedding_model,
                low_bandwidth_mode=low_bandwidth
            )
            st.session_state["last_matched_results"] = matched_list
            st.session_state["last_matched_profile"] = user_profile
        else:
            matched_list = st.session_state.get("last_matched_results", [])
            user_profile = st.session_state.get("last_matched_profile", {})
        st.divider()
        if not matched_list:
            st.warning(T["no_matches"])
        else:
            st.subheader(f"🎯 {T['results_header']} ({len(matched_list)})")
            top_col1, top_col2 = st.columns([2, 1])
            with top_col1:
                for scheme in matched_list:
                    score = scheme["match_score"]
                    sname = scheme["scheme_name"]
                    sbody = scheme["sponsoring_body"]
                    bamt = scheme["benefit_amount"]
                    desc = scheme["description"]
                    reasons = scheme["qualification_reasons"]
                    docs = scheme["required_documents"]
                    url = scheme["official_url"]
                    contact = scheme["contact_info"]
                    st.markdown(f"""
                    <div class="scheme-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span class="scheme-card-title">{sname}</span>
                            <span class="match-badge">{score}% Match</span>
                        </div>
                        <div style="color:#2563EB; font-weight:600; font-size:0.9rem; margin-top:2px;">🏛️ {sbody}</div>
                        <div class="scheme-card-body">{desc}</div>
                        <div style="margin-top:12px; font-size:0.9rem;">
                            <strong>💰 Financial Benefit:</strong> <span style="color:#047857; font-weight:600;">{bamt}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander(f"💡 {T['why_qualify']} ({len(reasons)} rules matched)", expanded=True):
                        for r in reasons:
                            st.markdown(f"- {r}")
                    with st.expander(f"📄 {T['docs_needed']}", expanded=False):
                        doc_html = "".join([f"<span class='doc-pill'>✓ {d}</span>" for d in docs])
                        st.markdown(doc_html, unsafe_allow_html=True)
                    act_col1, act_col2 = st.columns([1, 1])
                    with act_col1:
                        if scheme["url_is_safe"] and url:
                            st.link_button(f"🔗 {T['official_apply']}", url, use_container_width=True)
                        else:
                            st.button(f"⚠️ {T['official_apply']} (Offline Submission)", disabled=True, use_container_width=True)
                    with act_col2:
                        st.caption(f"📞 **{T['contact']}:** {contact}")
                    st.write("")
            with top_col2:
                st.markdown("### 📋 Universal Document Checklist")
                st.caption("Consolidated documents required across all your matched schemes:")
                checklist = matcher.aggregate_document_checklist(matched_list)
                checklist_text_lines = [
                    "=== SETU SCHEME MATCH SUMMARY ===",
                    f"Category: {user_profile.get('category')} | Income: Rs.{user_profile.get('income')} | State: {user_profile.get('state')}",
                    f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                    "\n--- TOP MATCHED SCHEMES ---"
                ]
                for i, s in enumerate(matched_list, 1):
                    checklist_text_lines.append(f"{i}. {s['scheme_name']} ({s['match_score']}% Match)")
                    checklist_text_lines.append(f"   Benefit: {s['benefit_amount']}")
                    checklist_text_lines.append(f"   Portal: {s['official_url']}")
                checklist_text_lines.append("\n--- REQUIRED DOCUMENT CHECKLIST ---")
                for item in checklist:
                    doc_name = item["document_name"]
                    count = item["required_by_count"]
                    st.checkbox(f"**{doc_name}** (Needed for {count} schemes)", value=False, key=f"chk_{doc_name}")
                    checklist_text_lines.append(f"[ ] {doc_name} (Required by: {', '.join(item['required_by_schemes'])})")
                st.divider()
                checklist_download_str = "\n".join(checklist_text_lines)
                st.download_button(
                    label=T["download_summary"],
                    data=checklist_download_str,
                    file_name=f"Setu_Scheme_Summary_{time.strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                st.divider()
                st.markdown(f"### {T['nearest_helpdesk']}")
                selected_state = user_profile.get("state", "National")
                desk_info = help_desks.get(selected_state, help_desks.get("National", {}))
                if desk_info:
                    st.info(
                        f"**🏛️ {desk_info.get('nodal_body')}**\n\n"
                        f"📍 **Address:** {desk_info.get('address')}\n\n"
                        f"📞 **Helpline:** {desk_info.get('toll_free')}\n\n"
                        f"✉️ **Email:** {desk_info.get('email')}\n\n"
                        f"💼 **Services:** {desk_info.get('services')}"
                    )

# TAB 2: Scheme Explorer
with tab_explorer:
    st.subheader("📚 National Welfare Schemes Catalog")
    st.caption("Read-only verified directory of central and state affirmative entrepreneurship schemes.")
    fe_col1, fe_col2, fe_col3 = st.columns(3)
    with fe_col1:
        search_query = st.text_input("🔍 Search by scheme name, keyword, or ministry:", placeholder="e.g. Mudra, Vishwakarma, Handicrafts...")
    with fe_col2:
        filter_cat = st.selectbox("Filter by Target Group:", ["All Categories"] + schema.ALLOWED_CATEGORIES)
    with fe_col3:
        filter_benefit = st.selectbox("Filter by Benefit Type:", ["All Types"] + schema.ALLOWED_BENEFIT_TYPES)
    filtered_df = schemes_df.copy()
    if search_query.strip():
        q = security.sanitize_text(search_query).lower()
        filtered_df = filtered_df[
            filtered_df["scheme_name"].str.lower().str.contains(q, na=False) |
            filtered_df["description"].str.lower().str.contains(q, na=False) |
            filtered_df["sponsoring_body"].str.lower().str.contains(q, na=False)
        ]
    if filter_cat != "All Categories":
        filtered_df = filtered_df[
            filtered_df["category"].apply(lambda x: filter_cat in schema.parse_multi_field(x) or "All" in schema.parse_multi_field(x))
        ]
    if filter_benefit != "All Types":
        filtered_df = filtered_df[filtered_df["benefit_type"] == filter_benefit]
    st.markdown(f"Showing **{len(filtered_df)}** registered schemes:")
    for _, row in filtered_df.iterrows():
        with st.container():
            st.markdown(f"### {row['scheme_name']}")
            st.markdown(f"**🏛️ Sponsoring Ministry/Body:** {row['sponsoring_body']} | **Category:**  | **Type:** ")
            st.write(row["description"])
            c_info1, c_info2 = st.columns([2, 1])
            with c_info1:
                st.markdown(f"**💰 Benefit Details:** {row['benefit_amount']}")
                st.markdown(f"**📄 Required Documents:** {', '.join(schema.parse_multi_field(row['required_documents']))}")
            with c_info2:
                is_safe, url = security.validate_url(row["official_url"])
                if is_safe and url:
                    st.link_button("🔗 Visit Official Portal", url, use_container_width=True)
                else:
                    st.caption("Link unavailable / Offline")
            st.divider()

# TAB 3: Admin Portal
with tab_admin:
    st.subheader("⚙️ Setu Administration Portal")
    st.caption("Restricted access for authorized MoSJE & Scheme Administrators. Requires Bcrypt authentication.")
    is_authenticated = admin.verify_admin_session(st.session_state)
    if not is_authenticated:
        st.markdown("#### 🔐 Administrator Login")
        is_allowed, rate_msg = admin.check_login_rate_limit(st.session_state)
        if not is_allowed:
            st.error(rate_msg)
        else:
            with st.form("admin_login_form"):
                admin_password = st.text_input("Admin Master Password:", type="password")
                login_submitted = st.form_submit_button("Unlock Admin Dashboard", type="primary")
                if login_submitted:
                    expected_hash = admin.get_admin_password_hash()
                    if not expected_hash:
                        st.error("ADMIN_PASSWORD_HASH is not configured in .env. Please run generate_hash.py first.")
                    elif security.verify_password(admin_password, expected_hash):
                        admin.record_successful_login(st.session_state)
                        st.success("Authentication successful! Access granted.")
                        st.rerun()
                    else:
                        admin.record_failed_login(st.session_state)
                        st.error("Invalid admin credentials. This attempt has been audited.")
    else:
        admin_col1, admin_col2 = st.columns([3, 1])
        with admin_col1:
            st.success("✅ Logged in with Admin privileges. (Auto-session timeout: 15 mins)")
        with admin_col2:
            if st.button("🚪 Logout Admin", type="secondary", use_container_width=True):
                admin.logout_admin(st.session_state)
                st.rerun()
        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Active Schemes", len(schemes_df))
        m2.metric("Social Groups Supported", len(schema.ALLOWED_CATEGORIES) - 1)
        m3.metric("Sectors Covered", len(schema.ALLOWED_SECTORS) - 1)
        m4.metric("Data Storage Model", "Atomic CSV + In-Memory")
        st.divider()
        subtab_manage, subtab_add, subtab_bulk, subtab_audit, subtab_export = st.tabs([
            "📋 Manage Schemes",
            "➕ Add Scheme",
            "📤 Bulk CSV Ingest",
            "📜 Audit Trail",
            "💾 Export Database"
        ])
        with subtab_manage:
            st.markdown("#### Existing Scheme Registry")
            st.dataframe(
                schemes_df[["scheme_id", "scheme_name", "sponsoring_body", "category", "benefit_type", "benefit_amount"]],
                use_container_width=True
            )
            st.markdown("##### Edit or Delete a Scheme")
            selected_id = st.selectbox("Select Scheme ID to manage:", schemes_df["scheme_id"].tolist() if not schemes_df.empty else [])
            if selected_id:
                row_data = schemes_df[schemes_df["scheme_id"] == selected_id].iloc[0].to_dict()
                with st.form("edit_scheme_form"):
                    st.markdown(f"**Editing: {row_data.get('scheme_name')} ({selected_id})**")
                    e_name = st.text_input("Scheme Name:", value=row_data.get("scheme_name", ""))
                    e_body = st.text_input("Sponsoring Body:", value=row_data.get("sponsoring_body", ""))
                    e_cat = st.multiselect("Target Categories:", schema.ALLOWED_CATEGORIES, default=schema.parse_multi_field(row_data.get("category", "")))
                    e_gender = st.multiselect("Eligible Genders:", schema.ALLOWED_GENDERS, default=schema.parse_multi_field(row_data.get("eligible_gender", "")))
                    e_pwd = st.checkbox("Divyangjan / PwD Only Scheme?", value=schema.parse_bool(row_data.get("pwd_only", False)))
                    e_c1, e_c2, e_c3 = st.columns(3)
                    with e_c1:
                        e_min_inc = st.number_input("Min Income (₹):", value=int(row_data.get("min_income", 0)), step=10000)
                        e_max_inc = st.number_input("Max Income (₹, -1=uncapped):", value=int(row_data.get("max_income", -1)), step=50000)
                    with e_c2:
                        e_min_age = st.number_input("Min Age:", value=int(row_data.get("min_age", 18)), min_value=14, max_value=100)
                        e_max_age = st.number_input("Max Age:", value=int(row_data.get("max_age", 70)), min_value=18, max_value=120)
                    with e_c3:
                        cur_btype = row_data.get("benefit_type", "Loan")
                        btype_idx = schema.ALLOWED_BENEFIT_TYPES.index(cur_btype) if cur_btype in schema.ALLOWED_BENEFIT_TYPES else 0
                        e_btype = st.selectbox("Benefit Type:", schema.ALLOWED_BENEFIT_TYPES, index=btype_idx)
                        e_sub = st.number_input("Subsidy %:", value=float(row_data.get("subsidy_percentage", 0.0)), min_value=0.0, max_value=100.0)
                    e_states = st.multiselect("States:", schema.STATES_AND_UTS, default=schema.parse_multi_field(row_data.get("states", "All India")))
                    e_sector = st.multiselect("Sectors:", schema.ALLOWED_SECTORS, default=schema.parse_multi_field(row_data.get("sector", "All")))
                    e_bamount = st.text_input("Benefit Amount Summary:", value=row_data.get("benefit_amount", ""))
                    e_desc = st.text_area("Detailed Description:", value=row_data.get("description", ""), height=100)
                    e_docs = st.multiselect("Required Documents:", schema.STANDARD_DOCUMENTS, default=[d for d in schema.parse_multi_field(row_data.get("required_documents", "")) if d in schema.STANDARD_DOCUMENTS])
                    e_url = st.text_input("Official Portal URL:", value=row_data.get("official_url", ""))
                    e_contact = st.text_input("Contact Info / Helpline:", value=row_data.get("contact_info", ""))
                    e_submit = st.form_submit_button("💾 Save Changes Atomically", type="primary")
                    if e_submit:
                        updated_dict = {
                            "scheme_id": selected_id,
                            "scheme_name": e_name,
                            "sponsoring_body": e_body,
                            "category": e_cat,
                            "eligible_gender": e_gender,
                            "pwd_only": e_pwd,
                            "min_income": e_min_inc,
                            "max_income": e_max_inc,
                            "min_age": e_min_age,
                            "max_age": e_max_age,
                            "states": e_states,
                            "sector": e_sector,
                            "benefit_type": e_btype,
                            "benefit_amount": e_bamount,
                            "subsidy_percentage": e_sub,
                            "description": e_desc,
                            "required_documents": e_docs,
                            "official_url": e_url,
                            "contact_info": e_contact
                        }
                        ok, errs = admin.save_scheme_entry(updated_dict, is_edit=True, session_state=st.session_state)
                        if ok:
                            st.success(f"Scheme {selected_id} updated successfully!")
                            st.rerun()
                        else:
                            for err in errs:
                                st.error(err)
                if st.button(f"🗑️ Delete Scheme {selected_id}", type="secondary"):
                    ok, msg = admin.delete_scheme_entry(selected_id, st.session_state)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        with subtab_add:
            st.markdown("#### ➕ Create New Scheme Entry")
            with st.form("create_scheme_form"):
                n_c1, n_c2 = st.columns(2)
                with n_c1:
                    n_id = st.text_input("Scheme ID (e.g. SETU-013):", placeholder="SETU-XXX")
                    n_name = st.text_input("Scheme Name:")
                    n_body = st.text_input("Sponsoring Ministry / Body:")
                with n_c2:
                    n_cat = st.multiselect("Target Categories:", schema.ALLOWED_CATEGORIES, default=["SC", "ST"])
                    n_gender = st.multiselect("Eligible Genders:", schema.ALLOWED_GENDERS, default=["All"])
                    n_pwd = st.checkbox("Divyangjan / PwD Only Scheme?", value=False)
                n_c3, n_c4, n_c5 = st.columns(3)
                with n_c3:
                    n_min_inc = st.number_input("Min Income (₹):", value=0, step=10000, key="n_min_inc")
                    n_max_inc = st.number_input("Max Income (₹, -1 for uncapped):", value=-1, step=50000, key="n_max_inc")
                with n_c4:
                    n_min_age = st.number_input("Min Age:", value=18, min_value=14, max_value=100, key="n_min_age")
                    n_max_age = st.number_input("Max Age:", value=70, min_value=18, max_value=120, key="n_max_age")
                with n_c5:
                    n_btype = st.selectbox("Benefit Type:", schema.ALLOWED_BENEFIT_TYPES, index=0, key="n_btype")
                    n_sub = st.number_input("Subsidy %:", value=0.0, min_value=0.0, max_value=100.0, key="n_sub")
                n_states = st.multiselect("States:", schema.STATES_AND_UTS, default=["All India"], key="n_states")
                n_sector = st.multiselect("Sectors:", schema.ALLOWED_SECTORS, default=["All"], key="n_sector")
                n_bamount = st.text_input("Benefit Amount Summary (e.g., Loans up to ₹10 Lakhs @ 5%):")
                n_desc = st.text_area("Detailed Scheme Description:", height=100)
                n_docs = st.multiselect("Required Documents:", schema.STANDARD_DOCUMENTS, default=["Aadhaar Card", "Bank Account Statement (6 Months)"], key="n_docs")
                n_url = st.text_input("Official HTTPS Portal URL:", placeholder="https://...")
                n_contact = st.text_input("Helpline / Contact Information:")
                n_submit = st.form_submit_button("🚀 Create Scheme Atomically", type="primary")
                if n_submit:
                    new_scheme_dict = {
                        "scheme_id": n_id,
                        "scheme_name": n_name,
                        "sponsoring_body": n_body,
                        "category": n_cat,
                        "eligible_gender": n_gender,
                        "pwd_only": n_pwd,
                        "min_income": n_min_inc,
                        "max_income": n_max_inc,
                        "min_age": n_min_age,
                        "max_age": n_max_age,
                        "states": n_states,
                        "sector": n_sector,
                        "benefit_type": n_btype,
                        "benefit_amount": n_bamount,
                        "subsidy_percentage": n_sub,
                        "description": n_desc,
                        "required_documents": n_docs,
                        "official_url": n_url,
                        "contact_info": n_contact
                    }
                    ok, errs = admin.save_scheme_entry(new_scheme_dict, is_edit=False, session_state=st.session_state)
                    if ok:
                        st.success(f"Scheme {n_id} created successfully!")
                        st.rerun()
                    else:
                        for err in errs:
                            st.error(err)
        with subtab_bulk:
            st.markdown("#### 📤 Bulk Scheme Ingestion (Strict Schema Validation)")
            st.caption("Upload a standard CSV of schemes. Fails closed: any validation error will reject the whole batch to preserve database integrity.")
            uploaded_file = st.file_uploader("Choose a CSV file (Max 5MB / 2,000 rows):", type=["csv"])
            if uploaded_file is not None:
                file_bytes = uploaded_file.read()
                if st.button("Validate and Ingest Batch", type="primary"):
                    ok, messages, count = admin.validate_and_ingest_bulk_csv(file_bytes, uploaded_file.name, st.session_state)
                    if ok:
                        st.success(f"✅ {messages[0]}")
                        st.rerun()
                    else:
                        st.error("❌ Bulk Ingestion Failed. Violations detected:")
                        for msg in messages:
                            st.markdown(f"- ")
        with subtab_audit:
            st.markdown("#### 📜 System Audit Trail (Non-PII Admin Actions)")
            st.caption("Strict zero-citizen-PII compliance: Only administrative and authentication lifecycle events are logged.")
            logs = security.read_recent_audit_logs(limit=40)
            if logs:
                st.code("".join(logs), language="text")
            else:
                st.info("No audit log records found yet.")
        with subtab_export:
            st.markdown("#### 💾 Export Clean Scheme Registry")
            st.caption("Download the current schemes database in validated CSV format (contains zero citizen demographic data).")
            csv_data = schemes_df.to_csv(index=False, columns=schema.SCHEME_COLUMNS)
            st.download_button(
                label="📥 Download schemes.csv",
                data=csv_data,
                file_name=f"schemes_export_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                type="primary"
            )
