/**
 * Setu (सेतु) - Dedicated Admin Page JavaScript
 * SIH26092 - Ministry of Social Justice & Empowerment
 */

let adminToken = sessionStorage.getItem("setu_admin_token") || null;
let allSchemes = [];

window.handleAdminPageLogin = handleAdminPageLogin;
window.handleAdminPageLogout = handleAdminPageLogout;
window.switchAdmTab = switchAdmTab;
window.filterAdminTable = filterAdminTable;
window.deleteSchemeRow = deleteSchemeRow;
window.handleSaveNewScheme = handleSaveNewScheme;
window.handlePageBulkUpload = handlePageBulkUpload;
window.exportSchemesCSV = exportSchemesCSV;

document.addEventListener("DOMContentLoaded", () => {
    if (adminToken) {
        verifySessionAndLoad();
    } else {
        showLoginScreen();
    }
});

function showLoginScreen() {
    document.getElementById("admin-login-screen").style.display = "block";
    document.getElementById("admin-dash-screen").style.display = "none";
}

function showDashScreen() {
    document.getElementById("admin-login-screen").style.display = "none";
    document.getElementById("admin-dash-screen").style.display = "block";
    loadSchemesTable();
}

async function verifySessionAndLoad() {
    try {
        const resp = await fetch("/api/admin/verify", {
            headers: { "x-admin-token": adminToken }
        });
        if (resp.ok) {
            showDashScreen();
        } else {
            adminToken = null;
            sessionStorage.removeItem("setu_admin_token");
            showLoginScreen();
        }
    } catch {
        showLoginScreen();
    }
}

async function handleAdminPageLogin(e) {
    e.preventDefault();
    const pwd = document.getElementById("adm-page-pwd").value;
    const errBox = document.getElementById("adm-page-error");
    errBox.style.display = "none";

    try {
        const resp = await fetch("/api/admin/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ password: pwd })
        });
        const data = await resp.json();
        if (resp.ok && data.success) {
            adminToken = data.token;
            sessionStorage.setItem("setu_admin_token", data.token);
            showDashScreen();
        } else {
            errBox.innerText = data.detail || "Invalid administrative credentials.";
            errBox.style.display = "block";
        }
    } catch (err) {
        errBox.innerText = "Error: " + err.message;
        errBox.style.display = "block";
    }
}

async function handleAdminPageLogout() {
    if (adminToken) {
        await fetch("/api/admin/logout", {
            method: "POST",
            headers: { "x-admin-token": adminToken }
        });
    }
    adminToken = null;
    sessionStorage.removeItem("setu_admin_token");
    showLoginScreen();
}

function switchAdmTab(tabName) {
    document.querySelectorAll(".admin-tab").forEach(t => t.classList.remove("active"));
    ["manage", "add", "bulk", "audit"].forEach(t => {
        const el = document.getElementById("admpage-tab-" + t);
        if (el) el.style.display = (t === tabName) ? "block" : "none";
    });
    if (window.event && window.event.target) window.event.target.classList.add("active");

    if (tabName === "manage") loadSchemesTable();
    if (tabName === "audit") loadAuditTrail();
}

async function loadSchemesTable() {
    const tbody = document.querySelector("#adm-full-table tbody");
    if (!tbody) return;
    tbody.innerHTML = "<tr><td colspan='7'>Loading database schemes...</td></tr>";

    try {
        const resp = await fetch("/api/schemes");
        const data = await resp.json();
        if (data.success) {
            allSchemes = data.schemes;
            document.getElementById("adm-scheme-count").innerText = allSchemes.length;
            renderTableRows(allSchemes);
        }
    } catch (err) {
        tbody.innerHTML = "<tr><td colspan='7' style='color:red;'>Failed to load schemes: " + err.message + "</td></tr>";
    }
}

function renderTableRows(schemes) {
    const tbody = document.querySelector("#adm-full-table tbody");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (schemes.length === 0) {
        tbody.innerHTML = "<tr><td colspan='7' style='text-align:center; color:#64748B;'>No schemes found.</td></tr>";
        return;
    }

    schemes.forEach(s => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><code>${s.scheme_id}</code></td>
            <td><strong>${s.scheme_name}</strong></td>
            <td>${s.sponsoring_body}</td>
            <td><code>${s.category}</code></td>
            <td>${s.benefit_amount}</td>
            <td><span class="doc-pill">${s.benefit_type}</span></td>
            <td>
                <button class="btn btn-outline btn-sm" onclick="deleteSchemeRow('${s.scheme_id}')" style="color:#DC2626; border-color:#DC2626; padding:3px 8px;">Delete</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function filterAdminTable() {
    const q = document.getElementById("adm-table-search").value.toLowerCase().trim();
    const filtered = allSchemes.filter(s => {
        return !q || (s.scheme_name || "").toLowerCase().includes(q) ||
                     (s.scheme_id || "").toLowerCase().includes(q) ||
                     (s.sponsoring_body || "").toLowerCase().includes(q) ||
                     (s.category || "").toLowerCase().includes(q);
    });
    renderTableRows(filtered);
}

async function deleteSchemeRow(schemeId) {
    if (!confirm(`Are you sure you want to delete scheme ${schemeId}? This will atomically update schemes.csv.`)) return;
    try {
        const resp = await fetch(`/api/admin/scheme/${schemeId}`, {
            method: "DELETE",
            headers: { "x-admin-token": adminToken }
        });
        if (resp.ok) {
            alert(`Scheme ${schemeId} deleted successfully.`);
            loadSchemesTable();
        } else {
            alert("Delete failed.");
        }
    } catch (err) {
        alert("Error: " + err.message);
    }
}

async function handleSaveNewScheme(e) {
    e.preventDefault();
    const payload = {
        scheme_id: document.getElementById("form-sid").value.trim(),
        scheme_name: document.getElementById("form-sname").value.trim(),
        sponsoring_body: document.getElementById("form-sbody").value.trim(),
        category: document.getElementById("form-cat").value.split("|").map(x => x.trim()),
        eligible_gender: ["All"],
        pwd_only: false,
        min_income: 0,
        max_income: -1,
        min_age: 18,
        max_age: 70,
        states: ["All India"],
        sector: ["All"],
        benefit_type: document.getElementById("form-btype").value,
        benefit_amount: document.getElementById("form-bamt").value.trim(),
        subsidy_percentage: 0.0,
        description: document.getElementById("form-desc").value.trim(),
        required_documents: document.getElementById("form-docs").value.split("|").map(x => x.trim()),
        official_url: document.getElementById("form-url").value.trim(),
        contact_info: document.getElementById("form-contact").value.trim(),
        is_edit: false
    };

    try {
        const resp = await fetch("/api/admin/scheme", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "x-admin-token": adminToken
            },
            body: JSON.stringify(payload)
        });
        const data = await resp.json();
        if (resp.ok) {
            alert("Scheme added atomically to database!");
            switchAdmTab("manage");
        } else {
            alert("Error: " + JSON.stringify(data.detail));
        }
    } catch (err) {
        alert("Request error: " + err.message);
    }
}

async function handlePageBulkUpload() {
    const fileInput = document.getElementById("adm-page-csv");
    const msgDiv = document.getElementById("adm-page-bulk-msg");
    if (!fileInput.files || fileInput.files.length === 0) {
        alert("Please select a CSV file.");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    msgDiv.innerHTML = "<p>Validating schema constraints...</p>";

    try {
        const resp = await fetch("/api/admin/bulk-upload", {
            method: "POST",
            headers: { "x-admin-token": adminToken },
            body: formData
        });
        const data = await resp.json();
        if (resp.ok) {
            msgDiv.innerHTML = `<p style="color:#059669; font-weight:700;">✅ ${data.message}</p>`;
            loadSchemesTable();
        } else {
            msgDiv.innerHTML = `<p style="color:#DC2626; font-weight:700;">❌ Ingestion Rejected:</p><pre style="color:#DC2626; font-size:0.85rem;">${JSON.stringify(data.detail, null, 2)}</pre>`;
        }
    } catch (err) {
        msgDiv.innerHTML = `<p style="color:#DC2626;">Error: ${err.message}</p>`;
    }
}

async function loadAuditTrail() {
    const pre = document.getElementById("adm-page-audit-pre");
    if (!pre) return;
    pre.innerText = "Loading audit records...";
    try {
        const resp = await fetch("/api/admin/audit-logs", {
            headers: { "x-admin-token": adminToken }
        });
        const data = await resp.json();
        if (data.success) {
            pre.innerText = (data.logs && data.logs.length > 0) ? data.logs.join("") : "No audit entries recorded yet.";
        }
    } catch (err) {
        pre.innerText = "Error loading logs: " + err.message;
    }
}

function exportSchemesCSV() {
    window.location.href = "/api/admin/export";
}
