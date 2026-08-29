/**
 * Setu (सेतु) - Web Portal Client JavaScript
 * SIH26092 - Ministry of Social Justice & Empowerment
 */

let currentLang = "en";
let allSchemesCatalog = [];
let allHelpdesks = {};
let lastMatchResponse = null;
let currentFontSizeIndex = 1; // 0: 14px, 1: 16px, 2: 18.5px, 3: 21px
const fontSizes = ["14px", "16px", "18.5px", "21px"];

let userAuthToken = localStorage.getItem("setu_user_token") || null;
let currentUser = JSON.parse(localStorage.getItem("setu_user_info") || "null");
let pendingVerifyEmail = "";

// Expose globals for HTML inline event handlers
window.setLanguage = setLanguage;
window.togglePwdSlider = togglePwdSlider;
window.updateIncomeDisplay = updateIncomeDisplay;
window.handleMatchSubmit = handleMatchSubmit;
window.printChecklistSlip = printChecklistSlip;
window.downloadTextSlip = downloadTextSlip;
window.filterCatalog = filterCatalog;
window.renderHelpdeskDirectory = renderHelpdeskDirectory;
window.handleHeroCta = handleHeroCta;

// Auth Modal
window.openAuthModal = openAuthModal;
window.closeAuthModal = closeAuthModal;
window.switchAuthView = switchAuthView;
window.handleUserLogin = handleUserLogin;
window.handleUserSignup = handleUserSignup;
window.handleVerifyEmail = handleVerifyEmail;
window.handleForgotPassword = handleForgotPassword;
window.handleResetPassword = handleResetPassword;
window.handleUserLogout = handleUserLogout;
window.resendVerificationCode = resendVerificationCode;

// Bilingual Dictionary
const I18N = {
    en: {
        nav_subtitle: "AI-Driven Welfare Scheme & Credit Discovery",
        nav_matcher: "Scheme Matcher",
        nav_explorer: "Scheme Explorer",
        nav_helpdesk: "Nodal Helpdesks",
        nav_privacy: "Privacy Contract",
        btn_login_signup: "Login / Sign Up",
        hero_pill: "Smart India Hackathon • Problem SIH26092",
        hero_title: "Empowering Marginalized Entrepreneurs Across India",
        hero_desc: "Intelligent, explainable scheme discovery connecting Scheduled Castes, Scheduled Tribes, OBCs, Divyangjan (PwD), Women, and Minorities to affirmative credit, capital subsidies, toolkits, and incubation.",
        btn_find_schemes: "Find My Eligible Schemes",
        btn_browse_catalog: "Browse All Schemes",
        privacy_badge_text: "Stateless In-Memory Matching:",
        privacy_badge_sub: "Zero Citizen Demographic PII is stored on disk or databases.",
        stat_schemes: "Central & State Welfare Schemes",
        stat_support: "Max Financial Support Available",
        stat_privacy: "Confidential & Explainable Rules",
        stat_states: "States & Union Territories Covered",
        matcher_header: "Entrepreneur Eligibility Assessment",
        matcher_sub: "Complete your demographic and enterprise parameters. All fields are processed in temporary RAM only.",
        lbl_category: "Social Category / Caste Group *",
        lbl_gender: "Gender Identity",
        lbl_age: "Applicant Age (Years)",
        lbl_pwd: "Are you a Person with Disability (Divyangjan / PwD)?",
        lbl_pwd_pct: "Certified Disability Percentage: ",
        lbl_income: "Annual Family Income (Rs.): ",
        lbl_state: "State / UT",
        lbl_sector: "Business Sector / Trade Domain",
        lbl_business_need: "Business Requirement / Purpose (AI Semantic Search):",
        ph_business_need: "E.g., I want to purchase automatic tailoring & embroidery machines for an apparel manufacturing micro-enterprise in Pune.",
        lbl_low_bw: "Low-Bandwidth Mode (Fast keyword indexing, minimal data transfer)",
        btn_evaluate: "Evaluate My Eligible Schemes",
        empty_title: "Ready to Find Your Scheme Matches",
        empty_desc: "Select your category, income, and business profile on the left and click Evaluate My Eligible Schemes to view matching welfare programs.",
        loading_text: "Analyzing eligibility criteria and calculating AI semantic match scores...",
        btn_print_slip: "Print Slip",
        checklist_header: "Universal Document Checklist",
        checklist_sub: "Consolidated documents required across your matched schemes:",
        btn_download_slip: "Download Summary (.txt)",
        btn_print: "Print Document Slip",
        helpdesk_card_title: "Nearest State Facilitation Center",
        explorer_title: "National Welfare Schemes Catalog",
        explorer_sub: "Search and filter affirmative government entrepreneurship credit & subsidy schemes.",
        ph_search_catalog: "Search by scheme name, ministry, or keyword...",
        locator_title: "State Nodal Facilitation Directory",
        locator_sub: "Direct contacts for State SC/ST Corporations, MSME DFOs, and Divyangjan Welfare desks.",
        lbl_select_state_desk: "Select Your State / UT:",
        privacy_contract_title: "The Setu Privacy & Security Contract"
    },
    hi: {
        nav_subtitle: "कल्याणकारी योजना सेतु",
        nav_matcher: "नागरिक योजना सेतु",
        nav_explorer: "योजना कैटलॉग",
        nav_helpdesk: "नोडल सुविधा केंद्र",
        nav_privacy: "गोपनीयता अनुबंध",
        btn_login_signup: "लॉग इन / रजिस्टर",
        hero_pill: "स्मार्ट इंडिया हैकाथॉन • समस्या SIH26092",
        hero_title: "भारत के वंचित एवं दिव्यांग उद्यमियों का सशक्तिकरण",
        hero_desc: "अनुसूचित जाति, अनुसूचित जनजाति, पिछड़ा वर्ग, दिव्यांगजन, महिलाओं एवं अल्पसंख्यकों को सरकारी सहायता से जोड़ने वाला सेतु।",
        btn_find_schemes: "पात्र योजनाएं खोजें",
        btn_browse_catalog: "सभी योजनाएं देखें",
        privacy_badge_text: "शून्य व्यक्तिगत डेटा भंडारण:",
        privacy_badge_sub: "नागरिक विवरण केवल तात्कालिक मेमोरी में प्रोसेस होता है।",
        stat_schemes: "कल्याणकारी सरकारी योजनाएं",
        stat_support: "अधिकतम वित्तीय सहायता",
        stat_privacy: "पारदर्शी नियम व गोपनीयता",
        stat_states: "सभी राज्य एवं केंद्र शासित प्रदेश",
        matcher_header: "उद्यमी पात्रता मूल्यांकन",
        matcher_sub: "अपनी श्रेणी, आय व व्यवसाय का विवरण भरें।",
        lbl_category: "सामाजिक श्रेणी / वर्ग *",
        lbl_gender: "लिंग",
        lbl_age: "आवेदक की आयु (वर्ष)",
        lbl_pwd: "क्या आप दिव्यांग (Divyangjan / PwD) हैं?",
        lbl_pwd_pct: "प्रमाणित दिव्यांगता प्रतिशत: ",
        lbl_income: "वार्षिक पारिवारिक आय (रु.): ",
        lbl_state: "राज्य / केंद्र शासित प्रदेश",
        lbl_sector: "व्यवसाय क्षेत्र / उद्योग",
        lbl_business_need: "व्यावसायिक आवश्यकता (एआई सर्च):",
        ph_business_need: "उदा. मैं परिधान निर्माण हेतु आधुनिक मशीनें खरीदना चाहता हूँ।",
        lbl_low_bw: "कम बैंडविड्थ मोड",
        btn_evaluate: "मेरी पात्र योजनाएं खोजें",
        empty_title: "पात्रता जांच के लिए तैयार",
        empty_desc: "बाईं ओर अपनी श्रेणी व आय चुनें और उपयुक्त योजनाएं देखें।",
        loading_text: "नियमों का मूल्यांकन व एआई मैच स्कोर की गणना की जा रही है...",
        btn_print_slip: "पर्ची प्रिंट करें",
        checklist_header: "आवश्यक दस्तावेज चेकलिस्ट",
        checklist_sub: "आपकी सभी चयनित योजनाओं के लिए आवश्यक समेकित दस्तावेज:",
        btn_download_slip: "सारांश डाउनलोड करें (.txt)",
        btn_print: "दस्तावेज पर्ची प्रिंट करें",
        helpdesk_card_title: "निकटतम राज्य नोडल सुविधा केंद्र",
        explorer_title: "राष्ट्रीय कल्याणकारी योजना कैटलॉग",
        explorer_sub: "सरकारी उद्यम ऋण एवं सब्सिडी योजनाओं की विस्तृत खोज करें।",
        ph_search_catalog: "योजना, मंत्रालय या कीवर्ड द्वारा खोजें...",
        locator_title: "राज्य नोडल सुविधा निर्देशिका",
        locator_sub: "राज्य अनुसूचित जाति/जनजाति निगम व सहायता केंद्र।",
        lbl_select_state_desk: "अपना राज्य चुनें:",
        privacy_contract_title: "सेतु गोपनीयता एवं सुरक्षा अनुबंध"
    }
};

document.addEventListener("DOMContentLoaded", () => {
    initAccessibility();
    initPillListeners();
    updateUserNavAndGate();
    loadHelpdeskDirectory();
});

function showToast(msg, duration = 6000) {
    const toast = document.getElementById("toast-notification");
    if (!toast) return;
    toast.innerHTML = msg;
    toast.style.display = "flex";
    setTimeout(() => {
        toast.style.display = "none";
    }, duration);
}

function initAccessibility() {
    const decBtn = document.getElementById("btn-font-dec");
    const resetBtn = document.getElementById("btn-font-reset");
    const incBtn = document.getElementById("btn-font-inc");
    const contrastBtn = document.getElementById("btn-contrast");

    function applyFontSize(index) {
        currentFontSizeIndex = Math.max(0, Math.min(index, fontSizes.length - 1));
        document.documentElement.style.fontSize = fontSizes[currentFontSizeIndex];
        
        [decBtn, resetBtn, incBtn].forEach(b => {
            if (b) b.classList.remove("active");
        });
        if (currentFontSizeIndex === 0 && decBtn) decBtn.classList.add("active");
        if (currentFontSizeIndex === 1 && resetBtn) resetBtn.classList.add("active");
        if (currentFontSizeIndex >= 2 && incBtn) incBtn.classList.add("active");
    }

    if (decBtn) decBtn.addEventListener("click", () => applyFontSize(currentFontSizeIndex - 1));
    if (resetBtn) resetBtn.addEventListener("click", () => applyFontSize(1));
    if (incBtn) incBtn.addEventListener("click", () => applyFontSize(currentFontSizeIndex + 1));
    if (contrastBtn) {
        contrastBtn.addEventListener("click", () => {
            document.body.classList.toggle("high-contrast");
            contrastBtn.classList.toggle("active");
        });
    }
}

function setLanguage(lang) {
    currentLang = lang;
    document.querySelectorAll(".lang-btn").forEach(b => b.classList.remove("active"));
    const activeBtn = document.getElementById("lang-" + lang);
    if (activeBtn) activeBtn.classList.add("active");

    const dict = I18N[lang] || I18N["en"];
    document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (dict[key]) el.innerText = dict[key];
    });
    document.querySelectorAll("[data-i18n-ph]").forEach(el => {
        const key = el.getAttribute("data-i18n-ph");
        if (dict[key]) el.placeholder = dict[key];
    });
}

function initPillListeners() {
    document.querySelectorAll(".cat-pill").forEach(pill => {
        pill.addEventListener("click", () => {
            document.querySelectorAll(".cat-pill").forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            const radio = pill.querySelector("input");
            if (radio) radio.checked = true;
        });
    });
}

function togglePwdSlider(chk) {
    const box = document.getElementById("pwd-pct-container");
    if (box) box.style.display = chk.checked ? "block" : "none";
}

function updateIncomeDisplay(val) {
    const num = parseInt(val) || 0;
    const el = document.getElementById("income-val");
    if (el) el.innerText = "₹" + num.toLocaleString("en-IN");
}

function handleHeroCta() {
    if (currentUser && userAuthToken) {
        const el = document.getElementById("matcher");
        if (el) el.scrollIntoView({ behavior: "smooth" });
    } else {
        openAuthModal("login");
    }
}

// --- Gating & User Profile Navigation ---
function updateUserNavAndGate() {
    const navBox = document.getElementById("user-auth-box");
    const matcherGate = document.getElementById("matcher-gate-card");
    const matcherUnlocked = document.getElementById("matcher-unlocked-content");
    const explorerGate = document.getElementById("explorer-gate-card");
    const explorerUnlocked = document.getElementById("explorer-unlocked-content");

    if (currentUser && userAuthToken) {
        // Authenticated State -> Unlock Features
        if (navBox) {
            navBox.innerHTML = "<div style='display:flex; align-items:center; gap:12px;'><span style='font-weight:700; color:#1E3A8A; font-size:1rem;'>👤 " + currentUser.name + "</span><button class='btn btn-outline btn-sm' onclick='handleUserLogout()' style='padding:5px 12px;'>Logout</button></div>";
        }
        if (matcherGate) matcherGate.style.display = "none";
        if (matcherUnlocked) matcherUnlocked.style.display = "grid";
        if (explorerGate) explorerGate.style.display = "none";
        if (explorerUnlocked) explorerUnlocked.style.display = "block";

        loadCatalogSchemes();
    } else {
        // Unauthenticated State -> Lock Features behind Gate
        if (navBox) {
            navBox.innerHTML = "<button class='btn btn-primary btn-sm' onclick='openAuthModal(\"login\")'>👤 <span>Login / Sign Up</span></button>";
        }
        if (matcherGate) matcherGate.style.display = "block";
        if (matcherUnlocked) matcherUnlocked.style.display = "none";
        if (explorerGate) explorerGate.style.display = "block";
        if (explorerUnlocked) explorerUnlocked.style.display = "none";
    }
}

function openAuthModal(view) {
    const modal = document.getElementById("auth-modal");
    if (modal) modal.style.display = "flex";
    switchAuthView(view || "login");
}

function closeAuthModal() {
    const modal = document.getElementById("auth-modal");
    if (modal) modal.style.display = "none";
}

function switchAuthView(view) {
    const views = ["login", "signup", "verify", "forgot", "reset"];
    views.forEach(v => {
        const el = document.getElementById("view-auth-" + v);
        if (el) el.style.display = (v === view) ? "block" : "none";
    });
}

async function handleUserSignup(e) {
    e.preventDefault();
    const name = document.getElementById("usr-reg-name").value.trim();
    const email = document.getElementById("usr-reg-email").value.trim();
    const phone = document.getElementById("usr-reg-phone").value.trim();
    const password = document.getElementById("usr-reg-pwd").value;
    const errBox = document.getElementById("usr-signup-error");
    if (errBox) errBox.style.display = "none";

    try {
        const resp = await fetch("/api/auth/signup", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, phone, password })
        });
        const data = await resp.json();
        if (resp.ok && data.success) {
            pendingVerifyEmail = email;
            document.getElementById("verify-email-display").innerText = email;
            const otpInp = document.getElementById("usr-verify-otp");
            if (otpInp) {
                otpInp.value = "";
                otpInp.focus();
            }
            switchAuthView("verify");
        } else {
            if (errBox) {
                errBox.innerText = data.detail || "Signup failed.";
                errBox.style.display = "block";
            }
        }
    } catch (err) {
        if (errBox) {
            errBox.innerText = "Network error: " + err.message;
            errBox.style.display = "block";
        }
    }
}

async function handleVerifyEmail(e) {
    e.preventDefault();
    const otp = document.getElementById("usr-verify-otp").value.trim();
    const errBox = document.getElementById("usr-verify-error");
    if (errBox) errBox.style.display = "none";

    try {
        const resp = await fetch("/api/auth/verify-email", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: pendingVerifyEmail, otp })
        });
        const data = await resp.json();
        if (resp.ok && data.success) {
            userAuthToken = data.data.token;
            currentUser = data.data.user;
            localStorage.setItem("setu_user_token", userAuthToken);
            localStorage.setItem("setu_user_info", JSON.stringify(currentUser));
            updateUserNavAndGate();
            closeAuthModal();
            showToast("✅ Welcome, <strong>" + currentUser.name + "</strong>! Your portal is unlocked.");
        } else {
            if (errBox) {
                errBox.innerText = data.detail || "Invalid code.";
                errBox.style.display = "block";
            }
        }
    } catch (err) {
        if (errBox) {
            errBox.innerText = "Error: " + err.message;
            errBox.style.display = "block";
        }
    }
}

async function handleUserLogin(e) {
    e.preventDefault();
    const email = document.getElementById("usr-login-email").value.trim();
    const password = document.getElementById("usr-login-pwd").value;
    const errBox = document.getElementById("usr-login-error");
    if (errBox) errBox.style.display = "none";

    try {
        const resp = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        const data = await resp.json();
        if (resp.ok && data.success) {
            userAuthToken = data.data.token;
            currentUser = data.data.user;
            localStorage.setItem("setu_user_token", userAuthToken);
            localStorage.setItem("setu_user_info", JSON.stringify(currentUser));
            updateUserNavAndGate();
            closeAuthModal();
            showToast("✅ Welcome back, <strong>" + currentUser.name + "</strong>! Scheme matching is active.");
        } else if (resp.status === 403 && data.requires_verification) {
            pendingVerifyEmail = email;
            document.getElementById("verify-email-display").innerText = email;
            const otpInp = document.getElementById("usr-verify-otp");
            if (otpInp) {
                otpInp.value = "";
                otpInp.focus();
            }
            switchAuthView("verify");
        } else {
            if (errBox) {
                errBox.innerText = data.detail || "Invalid email or password.";
                errBox.style.display = "block";
            }
        }
    } catch (err) {
        if (errBox) {
            errBox.innerText = "Error: " + err.message;
            errBox.style.display = "block";
        }
    }
}

async function handleForgotPassword(e) {
    e.preventDefault();
    const email = document.getElementById("usr-forgot-email").value.trim();
    const errBox = document.getElementById("usr-forgot-error");
    if (errBox) errBox.style.display = "none";

    try {
        const resp = await fetch("/api/auth/forgot-password", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email })
        });
        const data = await resp.json();
        if (resp.ok && data.success) {
            pendingVerifyEmail = email;
            const otpInp = document.getElementById("usr-reset-otp");
            if (otpInp) otpInp.value = "";
            switchAuthView("reset");
        } else {
            if (errBox) {
                errBox.innerText = data.detail || "Failed to send reset code.";
                errBox.style.display = "block";
            }
        }
    } catch (err) {
        if (errBox) {
            errBox.innerText = "Error: " + err.message;
            errBox.style.display = "block";
        }
    }
}

async function handleResetPassword(e) {
    e.preventDefault();
    const otp = document.getElementById("usr-reset-otp").value.trim();
    const new_password = document.getElementById("usr-reset-pwd").value;
    const errBox = document.getElementById("usr-reset-error");
    if (errBox) errBox.style.display = "none";

    try {
        const resp = await fetch("/api/auth/reset-password", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: pendingVerifyEmail, otp, new_password })
        });
        const data = await resp.json();
        if (resp.ok && data.success) {
            showToast("✅ Password reset successfully. Please log in with your new password.");
            switchAuthView("login");
        } else {
            if (errBox) {
                errBox.innerText = data.detail || "Password reset failed.";
                errBox.style.display = "block";
            }
        }
    } catch (err) {
        if (errBox) {
            errBox.innerText = "Error: " + err.message;
            errBox.style.display = "block";
        }
    }
}

function handleUserLogout() {
    userAuthToken = null;
    currentUser = null;
    localStorage.removeItem("setu_user_token");
    localStorage.removeItem("setu_user_info");
    updateUserNavAndGate();
    showToast("You have been signed out. Please sign in to access schemes.");
}

// --- Scheme Matcher Form Handler ---
async function handleMatchSubmit(e) {
    e.preventDefault();
    const emptyState = document.getElementById("empty-state");
    const spinner = document.getElementById("loading-spinner");
    const matchesWrapper = document.getElementById("matches-wrapper");

    if (emptyState) emptyState.style.display = "none";
    if (spinner) spinner.style.display = "block";
    if (matchesWrapper) matchesWrapper.style.display = "none";

    const catRadio = document.querySelector("input[name='category']:checked");
    const category = catRadio ? catRadio.value : "SC";
    const genderEl = document.getElementById("inp-gender");
    const gender = genderEl ? genderEl.value : "All-Any";
    const age = parseInt(document.getElementById("inp-age") ? document.getElementById("inp-age").value : 28) || 28;
    const pwdChk = document.getElementById("inp-pwd");
    const isPwd = pwdChk ? pwdChk.checked : false;
    const pwdPct = isPwd ? (parseInt(document.getElementById("inp-pwd-pct") ? document.getElementById("inp-pwd-pct").value : 50) || 50) : 0;
    const income = parseInt(document.getElementById("inp-income") ? document.getElementById("inp-income").value : 0) || 0;
    const state = document.getElementById("inp-state") ? document.getElementById("inp-state").value : "All India";
    const sector = document.getElementById("inp-sector") ? document.getElementById("inp-sector").value : "All";
    const businessNeed = document.getElementById("inp-need") ? document.getElementById("inp-need").value : "";
    const lowBw = document.getElementById("inp-low-bw") ? document.getElementById("inp-low-bw").checked : false;

    const payload = {
        category: category,
        gender: gender,
        is_pwd: isPwd,
        pwd_percent: pwdPct,
        income: income,
        age: age,
        state: state,
        sector: sector,
        business_need: businessNeed,
        low_bandwidth: lowBw
    };

    try {
        const resp = await fetch("/api/match", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + userAuthToken
            },
            body: JSON.stringify(payload)
        });
        const data = await resp.json();
        if (spinner) spinner.style.display = "none";

        if (data.success && data.count > 0) {
            lastMatchResponse = { profile: payload, data: data };
            renderMatches(data.matches, data.count, payload.state);
            renderChecklist(data.checklist);
            renderHelpdeskBanner(payload.state);
            if (matchesWrapper) matchesWrapper.style.display = "block";
        } else {
            if (emptyState) {
                emptyState.style.display = "block";
                emptyState.innerHTML = "<div class='empty-icon'>⚠️</div><h3>No Exact Scheme Matches Found</h3><p>Try adjusting your category, income ceiling, or sector preferences to view broader welfare programs.</p>";
            }
        }
    } catch (err) {
        if (spinner) spinner.style.display = "none";
        if (emptyState) {
            emptyState.style.display = "block";
            emptyState.innerHTML = "<div class='empty-icon'>⚠️</div><h3>Service Error</h3><p>Failed to connect to matching engine: " + err.message + "</p>";
        }
    }
}

function renderMatches(matches, count, userState) {
    const countText = document.getElementById("matches-count-text");
    if (countText) countText.innerText = "🎯 " + count + " Eligible Government Schemes Found";

    const list = document.getElementById("scheme-cards-list");
    if (!list) return;
    list.innerHTML = "";

    matches.forEach(s => {
        const card = document.createElement("div");
        card.className = "scheme-result-card";

        const docPills = (s.required_documents || []).map(d => "<span class='doc-pill'>✓ " + d + "</span>").join("");
        const reasonsHtml = (s.qualification_reasons || []).map(r => "<li>" + r + "</li>").join("");

        const applyButtonHtml = s.url_is_safe && s.official_url 
            ? "<a href='" + s.official_url + "' target='_blank' rel='noopener noreferrer' class='btn btn-primary btn-sm'>🔗 Official Portal</a>"
            : "<button class='btn btn-secondary btn-sm' disabled>Offline Submission</button>";

        card.innerHTML = "<div class='scheme-header-row'><div><h3 class='scheme-name'>" + s.scheme_name + "</h3><div class='scheme-body-title'>🏛️ " + s.sponsoring_body + "</div></div><div class='match-badge'>" + s.match_score + "% Match</div></div><p class='scheme-desc'>" + s.description + "</p><div class='financial-box'><strong>💰 Benefit Details:</strong> " + s.benefit_amount + "</div><div class='reasons-box'><strong>💡 Why You Qualify:</strong><ul>" + reasonsHtml + "</ul></div><div style='font-size:0.85rem; font-weight:600; color:#334155; margin-bottom:4px;'>📄 Required Documents:</div><div class='doc-pills-row'>" + docPills + "</div><div class='scheme-actions'>" + applyButtonHtml + "<span style='font-size:0.82rem; color:#64748B;'>📞 Helpline: <strong>" + (s.contact_info || "Contact District Office") + "</strong></span></div>";
        list.appendChild(card);
    });
}

function renderChecklist(checklist) {
    const container = document.getElementById("checklist-items");
    if (!container) return;
    container.innerHTML = "";

    (checklist || []).forEach(item => {
        const div = document.createElement("div");
        div.className = "chk-item";
        const safeId = item.document_name.replace(/\s+/g, "_");
        div.innerHTML = "<input type='checkbox' id='chk-" + safeId + "'><label for='chk-" + safeId + "'><strong>" + item.document_name + "</strong> <span style='font-size:0.8rem; color:#78350F;'>(Required for " + item.required_by_count + " schemes)</span></label>";
        container.appendChild(div);
    });
}

function renderHelpdeskBanner(stateName) {
    const desk = allHelpdesks[stateName] || allHelpdesks["National"] || {};
    const div = document.getElementById("helpdesk-details");
    if (!div) return;
    div.innerHTML = "<div style='font-size:1.05rem; font-weight:700; color:#1E293B; margin-bottom:6px;'>🏛️ " + (desk.nodal_body || "Central Welfare Desk") + "</div><div style='font-size:0.92rem; color:#475569; margin-bottom:6px;'>📍 <strong>Address:</strong> " + (desk.address || "Shastri Bhawan, New Delhi") + "</div><div style='font-size:0.92rem; color:#475569;'>📞 <strong>Helpline:</strong> " + (desk.toll_free || "1800-11-0301") + " | ✉️ <strong>Email:</strong> " + (desk.email || "support@gov.in") + "</div>";
}

function printChecklistSlip() {
    window.print();
}

function downloadTextSlip() {
    if (!lastMatchResponse) return;
    const profile = lastMatchResponse.profile;
    const data = lastMatchResponse.data;
    const lines = [
        "============================================================",
        "SETU (सेतु) — CITIZEN SCHEME ELIGIBILITY & DOCUMENT SLIP",
        "Ministry of Social Justice & Empowerment, Govt. of India",
        "============================================================",
        "Category: " + profile.category + " | Gender: " + profile.gender + " | State: " + profile.state,
        "Income: Rs." + profile.income.toLocaleString("en-IN") + " | Age: " + profile.age,
        "Generated: " + new Date().toLocaleString(),
        "\n--- TOP MATCHED SCHEMES ---"
    ];

    data.matches.forEach((s, idx) => {
        lines.push("\n" + (idx + 1) + ". " + s.scheme_name + " [" + s.match_score + "% Match]");
        lines.push("   Ministry/Body: " + s.sponsoring_body);
        lines.push("   Financial Support: " + s.benefit_amount);
        lines.push("   Portal URL: " + s.official_url);
    });

    lines.push("\n--- CONSOLIDATED DOCUMENT CHECKLIST ---");
    data.checklist.forEach(item => {
        lines.push("[ ] " + item.document_name + " (Required by: " + item.required_by_schemes.join(", ") + ")");
    });

    lines.push("\nPlease carry this checklist to your nearest District Industries Centre (DIC) or State SC/ST/OBC Corporation.");

    const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "Setu_Eligibility_Summary_" + Date.now() + ".txt";
    a.click();
    URL.revokeObjectURL(url);
}

async function loadCatalogSchemes() {
    try {
        const resp = await fetch("/api/schemes");
        const data = await resp.json();
        if (data.success) {
            allSchemesCatalog = data.schemes;
            renderCatalogGrid(allSchemesCatalog);
        }
    } catch (err) {
        console.error("Failed to load catalog schemes:", err);
    }
}

function filterCatalog() {
    const searchInput = document.getElementById("catalog-search");
    const q = (searchInput ? searchInput.value : "").toLowerCase().trim();
    const cat = document.getElementById("catalog-cat-filter") ? document.getElementById("catalog-cat-filter").value : "All";
    const btype = document.getElementById("catalog-type-filter") ? document.getElementById("catalog-type-filter").value : "All";

    const filtered = allSchemesCatalog.filter(s => {
        const matchQ = !q || (s.scheme_name || "").toLowerCase().includes(q) ||
                              (s.description || "").toLowerCase().includes(q) ||
                              (s.sponsoring_body || "").toLowerCase().includes(q);
        const matchCat = cat === "All" || (s.category || "").includes(cat) || (s.category || "").includes("All");
        const matchType = btype === "All" || s.benefit_type === btype;
        return matchQ && matchCat && matchType;
    });

    renderCatalogGrid(filtered);
}

function renderCatalogGrid(schemes) {
    const grid = document.getElementById("catalog-grid");
    if (!grid) return;
    grid.innerHTML = "";

    if (schemes.length === 0) {
        grid.innerHTML = "<p style='grid-column: 1/-1; text-align:center; color:#64748B; padding:30px 0;'>No schemes found matching your search filters.</p>";
        return;
    }

    schemes.forEach(s => {
        const card = document.createElement("div");
        card.className = "catalog-item-card";
        card.innerHTML = "<div><h3>" + s.scheme_name + "</h3><div style='color:#2563EB; font-size:0.9rem; font-weight:700; margin-bottom:8px;'>🏛️ " + s.sponsoring_body + "</div><p style='font-size:0.95rem; color:#475569; margin-bottom:14px;'>" + s.description + "</p><div style='font-size:0.92rem; margin-bottom:8px;'><strong>💰 Benefit:</strong> " + s.benefit_amount + "</div><div style='font-size:0.85rem; color:#64748B; margin-bottom:14px;'><strong>🎯 Target:</strong> <code>" + s.category + "</code> | <strong>Type:</strong> <code>" + s.benefit_type + "</code></div></div><div style='display:flex; justify-content:space-between; align-items:center; border-top:1px solid #E2E8F0; padding-top:12px;'><a href='" + s.official_url + "' target='_blank' rel='noopener noreferrer' class='btn btn-primary btn-sm'>🔗 Official Link</a><span style='font-size:0.8rem; color:#94A3B8;'>ID: " + s.scheme_id + "</span></div>";
        grid.appendChild(card);
    });
}

async function loadHelpdeskDirectory() {
    try {
        const resp = await fetch("/api/helpdesk");
        const data = await resp.json();
        if (data.success) {
            allHelpdesks = data.data;
            renderHelpdeskDirectory();
        }
    } catch (err) {
        console.error("Failed to load helpdesk directory:", err);
    }
}

function renderHelpdeskDirectory() {
    const stateSelect = document.getElementById("desk-state-select");
    const selectedState = stateSelect ? stateSelect.value : "National";
    const desk = allHelpdesks[selectedState] || allHelpdesks["National"] || {};
    const container = document.getElementById("desk-card-render");
    if (!container) return;

    container.innerHTML = "<div style='background:#FFFFFF; border:1.5px solid #E2E8F0; border-radius:12px; padding:24px; text-align:left; box-shadow:var(--shadow-card);'><h3 style='color:#1E3A8A; font-size:1.3rem; margin-bottom:10px;'>🏛️ " + (desk.nodal_body || "Nodal Authority") + "</h3><p style='font-size:1rem; margin-bottom:8px;'>📍 <strong>Office Address:</strong> " + (desk.address || "New Delhi") + "</p><p style='font-size:1rem; margin-bottom:8px;'>📞 <strong>Toll-Free Helpline:</strong> <strong style='color:#059669;'>" + (desk.toll_free || "1800-11-0301") + "</strong></p><p style='font-size:1rem; margin-bottom:8px;'>✉️ <strong>Email Desk:</strong> <a href='mailto:" + (desk.email || "support@gov.in") + "'>" + (desk.email || "support@gov.in") + "</a></p><p style='font-size:0.95rem; color:#64748B;'>💼 <strong>Facilitation Services:</strong> " + (desk.services || "Credit linkage and scheme counseling") + "</p></div>";
}

async function resendVerificationCode() {
    if (!pendingVerifyEmail) return;
    try {
        const resp = await fetch("/api/auth/forgot-password", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: pendingVerifyEmail })
        });
        showToast("📬 New verification email dispatched to " + pendingVerifyEmail);
    } catch (e) {
        showToast("Could not resend code. Please try again.");
    }
}
