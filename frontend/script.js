// Mocked backend for email resolution to subject mapping
const facultyEmailMap = {
    "smith@university.edu": { name: "Dr. Smith", subject: "Artificial Intelligence", pass: "pass123" },
    "johnson@university.edu": { name: "Prof. Johnson", subject: "Data Science", pass: "pass123" },
    "lee@university.edu": { name: "Dr. Lee", subject: "Computer Networks", pass: "pass123" },
    "atmakutitagore22@gmail.com": { name: "Prof. Tagore", subject: "Advanced Engineering", pass: "zoro22" }
};

let currentFaculty = null;
let currentSubject = null;

document.addEventListener("DOMContentLoaded", () => {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById("dateInput").value = today;
});

function login() {
    const email = document.getElementById("emailInput").value.toLowerCase().trim();
    const password = document.getElementById("passwordInput").value;

    if (!email || !password) {
        alert("Please enter both email and password.");
        return;
    }

    // Simulate auth & contextual data gathering
    const user = facultyEmailMap[email];
    if (user && user.pass !== password) {
        alert("Authentication Failed: Incorrect password.");
        return;
    }

    const actualUser = user || { name: email.split('@')[0].toUpperCase(), subject: "Software Engineering" };

    currentFaculty = actualUser.name;
    currentSubject = actualUser.subject;

    document.getElementById("facultyNameDisplay").innerText = currentFaculty;
    document.getElementById("subject").value = currentSubject;

    // Transition UI
    document.getElementById("loginView").classList.remove("active");
    setTimeout(() => {
        document.getElementById("loginView").style.display = "none";
        document.getElementById("dashboardView").classList.remove("hidden");
        setTimeout(() => {
            document.getElementById("dashboardView").classList.add("active");
            // Load Sheets automatically upon dashboard view
            fetchWorksheets();
        }, 50);
    }, 400);
}

function logout() {
    currentFaculty = null;
    currentSubject = null;

    document.getElementById("rolls").value = "";
    document.getElementById("status").className = "status-box hidden";
    document.getElementById("emailInput").value = "";
    document.getElementById("passwordInput").value = "";

    document.getElementById("dashboardView").classList.remove("active");
    setTimeout(() => {
        document.getElementById("dashboardView").classList.add("hidden");
        document.getElementById("loginView").style.display = "flex";
        setTimeout(() => {
            document.getElementById("loginView").classList.add("active");
        }, 50);
    }, 400);
}

async function startCalls() {
    pollResults();

    const subject = document.getElementById("subject").value;
    const department = document.getElementById("department").value;
    const section = document.getElementById("section").value;

    // ✅ FIXED YEAR EXTRACTION (IMPORTANT)
    const yearDropdown = document.getElementById("className");
    const year = yearDropdown.options[yearDropdown.selectedIndex].textContent.trim();

    const rollsInput = document.getElementById("rolls").value;

    const rolls = rollsInput
        .split(/\s|,|\n/)
        .filter(r => r.trim() !== "");

    if (rolls.length === 0) {
        showStatus("Error: Please enter at least one roll number.", "error");
        return;
    }

    const btn = document.getElementById("startCallsBtn");
    const btnText = btn.querySelector(".btn-text");
    const spinner = document.getElementById("callSpinner");

    btn.disabled = true;
    btnText.innerText = "Initiating...";
    spinner.classList.remove("hidden");
    document.getElementById("status").classList.add("hidden");

    // ✅ DEBUG (keep this for now)
    console.log("DEBUG PAYLOAD:", {
        subject,
        department,
        section,
        year,
        rolls
    });

    try {
        const response = await fetch("/start-calls", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                subject: subject,
                department: department,
                section: section,
                year: year,   // ✅ now guaranteed
                rolls: rolls
            })
        });

        const data = await response.json();

        if (data.results && data.results.length > 0) {
            let hasErrors = false;
            let statusText = "Transmission Results:\n";

            data.results.forEach(res => {
                statusText += `• ${res.roll}: ${res.status}\n`;
                if (res.status !== "Calling") hasErrors = true;
            });

            showStatus(statusText, hasErrors ? "error" : "success");
        } else {
            showStatus(data.message || "Operations completed.", "success");
        }

        setTimeout(fetchWorksheets, 2500);

    } catch (e) {
        showStatus("Network Failure: Could not reach the API.", "error");
    } finally {
        btn.disabled = false;
        btnText.innerText = "Initiate Calls";
        spinner.classList.add("hidden");
    }
}

function showStatus(message, type) {
    const statusBox = document.getElementById("status");
    statusBox.innerText = message;
    statusBox.className = `status-box ${type}`;
}

// ---------------- TRANSCRIPT VIEWER ----------------

async function fetchWorksheets() {
    const listEl = document.getElementById("sheetList");
    try {
        const response = await fetch("/api/worksheets");
        const sheets = await response.json();

        listEl.innerHTML = ""; // clear loading

        if (!sheets || sheets.length === 0) {
            listEl.innerHTML = "<li class='loading-text'>No sheets found.</li>";
            return;
        }

        // Sort sheets descending assuming they contain dates (YYYY-MM-DD...)
        sheets.sort((a, b) => b.title.localeCompare(a.title));

        sheets.forEach(sheet => {
            const li = document.createElement("li");
            li.innerText = sheet.title;
            li.onclick = () => loadSheetData(sheet.title, li);
            listEl.appendChild(li);
        });

    } catch (e) {
        listEl.innerHTML = "<li class='loading-text' style='color:red;'>Failed to load network routes.</li>";
    }
}

async function loadSheetData(title, listItemElement) {
    // UI Highlights
    document.querySelectorAll(".sheet-list li").forEach(li => li.classList.remove("active-sheet"));
    if (listItemElement) listItemElement.classList.add("active-sheet");

    document.getElementById("tablePlaceholder").classList.add("hidden");
    const table = document.getElementById("transcriptTable");
    const spinner = document.getElementById("tableSpinner");
    const tbody = document.getElementById("transcriptBody");

    table.classList.add("hidden");
    spinner.classList.remove("hidden");
    tbody.innerHTML = "";

    try {
        const response = await fetch(`/api/worksheets/${encodeURIComponent(title)}`);
        const data = await response.json();

        if (!data || data.length === 0) {
            document.getElementById("tablePlaceholder").innerText = "No records found in this transcript.";
            document.getElementById("tablePlaceholder").classList.remove("hidden");
            spinner.classList.add("hidden");
            return;
        }

        data.forEach(row => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${row.roll || 'N/A'}</strong></td>
                <td><span class="${getColorForReason(row.reason)}">${row.reason || 'Pending'}</span></td>
                <td><small>${row.transcript || '—'}</small></td>
            `;
            tbody.appendChild(tr);
        });

        spinner.classList.add("hidden");
        table.classList.remove("hidden");
    } catch (e) {
        spinner.classList.add("hidden");
        document.getElementById("tablePlaceholder").innerText = "Error loading transcript data.";
        document.getElementById("tablePlaceholder").classList.remove("hidden");
    }
}

function getColorForReason(reason) {
    if (!reason) return "status-text pending";
    const r = reason.toString().toUpperCase();
    if (r.includes('SICK')) return 'status-text sick';
    if (r.includes('TRAVEL')) return 'status-text travel';
    if (r.includes('FUNCTION')) return 'status-text fn';
    return 'status-text pending';
}



function pollResults() {

    setInterval(async () => {

        const res = await fetch("/results");
        const data = await res.json();

        const rows = document.querySelectorAll("#resultsTable tbody tr");

        rows.forEach(row => {
            const roll = row.children[0].innerText;

            if (data[roll]) {
                row.children[1].innerText = data[roll].status;
                row.children[2].innerText = data[roll].reason;
            }
        });

    }, 3000); // every 3 seconds
}