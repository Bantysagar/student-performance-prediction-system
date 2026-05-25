const API_BASE = "http://127.0.0.1:8000";

const predictButton = document.getElementById("predictButton");
const resultBox = document.getElementById("resultBox");
const historyTableBody = document.getElementById("historyTableBody");
const clearHistoryButton = document.getElementById("clearHistoryButton");
const backendStatusDot = document.getElementById("backendStatusDot");
const backendStatusText = document.getElementById("backendStatusText");

function getRiskClass(riskLevel) {
    if (riskLevel === "Low") return "low";
    if (riskLevel === "Medium") return "medium";
    return "high";
}

function getStatusClass(status) {
    if (status === "Pass") return "pass";
    return "fail";
}

function saveLastResult(data) {
    localStorage.setItem("lastPredictionResult", JSON.stringify(data));
}

function loadLastResult() {
    const saved = localStorage.getItem("lastPredictionResult");

    if (!saved) return;

    try {
        const data = JSON.parse(saved);
        showResult(data);
    } catch {
        localStorage.removeItem("lastPredictionResult");
    }
}

async function checkBackendStatus() {
    try {
        const response = await fetch(`${API_BASE}/health`);

        if (!response.ok) {
            throw new Error("Backend health check failed.");
        }

        backendStatusDot.classList.remove("offline");
        backendStatusDot.classList.add("online");
        backendStatusText.textContent = "Backend Online";
    } catch {
        backendStatusDot.classList.remove("online");
        backendStatusDot.classList.add("offline");
        backendStatusText.textContent = "Backend Offline";
    }
}

function getInputValue(id) {
    return document.getElementById(id).value;
}

function getFormData() {
    return {
        student_name: getInputValue("studentName").trim(),
        study_hours: Number(getInputValue("studyHours")),
        attendance: Number(getInputValue("attendance")),
        previous_marks: Number(getInputValue("previousMarks")),
        assignments_completed: Number(getInputValue("assignmentsCompleted")),
        sleep_hours: Number(getInputValue("sleepHours")),
        internet_access: getInputValue("internetAccess"),
        extracurricular: getInputValue("extracurricular"),
    };
}

function validatePayload(payload) {
    if (!payload.student_name) {
        return "Please enter student name.";
    }

    if (payload.study_hours < 0 || payload.study_hours > 24) {
        return "Study hours must be between 0 and 24.";
    }

    if (payload.attendance < 0 || payload.attendance > 100) {
        return "Attendance must be between 0 and 100.";
    }

    if (payload.previous_marks < 0 || payload.previous_marks > 100) {
        return "Previous marks must be between 0 and 100.";
    }

    if (payload.assignments_completed < 0 || payload.assignments_completed > 10) {
        return "Assignments completed must be between 0 and 10.";
    }

    if (payload.sleep_hours < 0 || payload.sleep_hours > 24) {
        return "Sleep hours must be between 0 and 24.";
    }

    return null;
}

function showLoading() {
    resultBox.className = "result-box";
    resultBox.innerHTML = `
        <p><strong>Analyzing student profile...</strong></p>
        <div class="score">...</div>
        <p>Machine learning model is generating prediction.</p>
    `;
}

function showResult(data) {
    resultBox.className = "result-box";

    resultBox.innerHTML = `
        <p>Student: <strong>${data.student_name}</strong></p>

        <div class="score">${data.predicted_score}%</div>

        <p>
            <span class="pill ${getStatusClass(data.status)}">${data.status}</span>
            <span class="pill ${getRiskClass(data.risk_level)}">${data.risk_level} Risk</span>
        </p>

        <p>Prediction saved at: <strong>${data.created_at}</strong></p>
    `;
}

function showError(message) {
    resultBox.className = "error";
    resultBox.textContent = message;
}

async function submitPrediction() {
    const payload = getFormData();
    const validationError = validatePayload(payload);

    if (validationError) {
        showError(validationError);
        return;
    }

    predictButton.disabled = true;
    predictButton.textContent = "Generating Prediction...";
    showLoading();

    try {
        const response = await fetch(`${API_BASE}/predict`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Prediction failed.");
        }

        showResult(data);
        saveLastResult(data);
        await loadHistory();
    } catch (error) {
        showError(error.message);
    } finally {
        predictButton.disabled = false;
        predictButton.textContent = "Generate Prediction";
    }
}

async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE}/history`);
        const history = await response.json();

        if (!response.ok) {
            throw new Error("Could not load history.");
        }

        if (history.length === 0) {
            historyTableBody.innerHTML = `
                <tr>
                    <td colspan="6">No prediction history found.</td>
                </tr>
            `;
            return;
        }

        historyTableBody.innerHTML = history
            .map(
                (item) => `
                    <tr>
                        <td>${item.id}</td>
                        <td>${item.student_name}</td>
                        <td>${item.predicted_score}%</td>
                        <td>
                            <span class="pill ${getStatusClass(item.status)}">
                                ${item.status}
                            </span>
                        </td>
                        <td>
                            <span class="pill ${getRiskClass(item.risk_level)}">
                                ${item.risk_level}
                            </span>
                        </td>
                        <td>${item.created_at}</td>
                    </tr>
                `
            )
            .join("");
    } catch (error) {
        historyTableBody.innerHTML = `
            <tr>
                <td colspan="6">${error.message}</td>
            </tr>
        `;
    }
}

async function clearHistory() {
    const confirmed = confirm("Are you sure you want to clear all prediction history?");

    if (!confirmed) return;

    try {
        const response = await fetch(`${API_BASE}/history`, {
            method: "DELETE",
        });

        if (!response.ok) {
            throw new Error("Could not clear history.");
        }

        localStorage.removeItem("lastPredictionResult");

        resultBox.className = "empty-result";
        resultBox.innerHTML = `
            <div class="empty-icon">📈</div>
            <strong>No prediction generated yet</strong>
            <p>Enter student details and click Generate Prediction.</p>
        `;

        await loadHistory();
    } catch (error) {
        alert(error.message);
    }
}

predictButton.addEventListener("click", submitPrediction);
clearHistoryButton.addEventListener("click", clearHistory);

checkBackendStatus();
loadLastResult();
loadHistory();