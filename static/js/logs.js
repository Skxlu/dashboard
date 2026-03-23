let currentPage = 1;
const perPage = 20;
let totalPages = 1;

function clearLogs() {
    if (!confirm("Alle Logs wirklich löschen?")) {
        return;
    }

    fetch("/api/logs/clear", {
        method: "POST"
    })
        .then(r => r.json())
        .then(res => {
            if (res.error) {
                alert("Fehler: " + res.error);
                return;
            }

            currentPage = 1;   // zurück zur ersten Seite
            loadLogs();
        })
        .catch(err => {
            alert("Fehler beim Löschen: " + err);
        });
}

function badgeClass(action) {
    const allowed = ["WAKE", "SHUTDOWN", "EDIT", "DELETE", "SCAN", "SERVICE_CHECK", "ERROR"];
    return allowed.includes(action) ? action : "DEFAULT";
}

function escapeHtml(text) {
    return String(text ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function loadLogs() {
    fetch(`/api/logs?page=${currentPage}&per_page=${perPage}`)
        .then(r => r.json())
        .then(data => {
            const logs = data.logs || [];
            totalPages = data.pages || 1;

            const container = document.getElementById("logs");
            const counter = document.getElementById("logCounter");
            const pageInfo = document.getElementById("pageInfo");

            container.innerHTML = "";
            counter.textContent = "Einträge: " + (data.total || 0);
            pageInfo.textContent = `Seite ${data.page || 1} / ${data.pages || 1}`;

            if (!logs.length) {
                container.innerHTML = '<div class="empty">Keine Logs auf dieser Seite vorhanden.</div>';
                return;
            }

            logs.forEach(log => {
                const action = log.action || "UNKNOWN";

                const entry = document.createElement("div");
                entry.className = "log-entry";
                entry.innerHTML = `
          <div class="log-top">
            <div class="log-meta">
              <span class="badge ${badgeClass(action)}">${escapeHtml(action)}</span>
              <span class="log-time">${escapeHtml(log.time || "-")}</span>
              <span class="log-ip">${escapeHtml(log.ip || "-")}</span>
            </div>
          </div>
          <div class="log-info">${escapeHtml(log.info || "")}</div>
        `;

                container.appendChild(entry);
            });
        })
        .catch(err => {
            document.getElementById("logs").innerHTML =
                `<div class="empty">Fehler beim Laden der Logs.<br><br>${escapeHtml(err)}</div>`;
            document.getElementById("logCounter").textContent = "Fehler";
            document.getElementById("pageInfo").textContent = "Seite -";
        });
}

function nextPage() {
    if (currentPage < totalPages) {
        currentPage++;
        loadLogs();
    }
}

function prevPage() {
    if (currentPage > 1) {
        currentPage--;
        loadLogs();
    }
}

document.addEventListener("DOMContentLoaded", function () {
    loadLogs();
});