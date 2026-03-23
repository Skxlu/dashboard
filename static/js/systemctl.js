
// ----------------------
// Accordion
// ----------------------
function toggleAccordion(el) {
    let box = document.getElementById("sshBox");

    if (box.style.display === "flex") {
        box.style.display = "none";
        el.classList.remove("active");
    } else {
        box.style.display = "flex";
        el.classList.add("active");
    }
}

// ----------------------
// Geräte laden
// ----------------------
function loadDevices() {
    fetch("/api/devices")
        .then(r => r.json())
        .then(data => {
            let select = document.getElementById("deviceSelect");

            // vorher leeren (wichtig bei reloads)
            select.innerHTML = '<option value="">Gerät auswählen...</option>';

            data.forEach(d => {
                let option = document.createElement("option");
                option.value = d.ip;
                option.textContent = d.name + " (" + d.ip + ")";
                select.appendChild(option);
            });
        });
}

// ----------------------
// Dropdown → IP übernehmen
// ----------------------
function selectDevice() {
    let select = document.getElementById("deviceSelect");
    let ipInput = document.getElementById("ip");

    if (select.value) {
        ipInput.value = select.value;
    }
}

// ----------------------
// Service Check
// ----------------------
function check() {
    let ip = document.getElementById("ip").value;
    let service = document.getElementById("service").value;
    let ssh_user = document.getElementById("ssh_user").value;
    let ssh_pass = document.getElementById("ssh_pass").value;

    fetch("/api/systemctl", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            ip: ip,
            service: service,
            ssh_user: ssh_user,
            ssh_pass: ssh_pass
        })
    })
        .then(r => r.json())
        .then(data => {

            document.getElementById("output").textContent =
                (data.output || "") + "\n" + (data.error || "");

            let indicator = document.getElementById("indicator");
            let statusText = document.getElementById("statusText");

            indicator.className = "indicator";

            if (data.output?.includes("active (running)")) {
                indicator.classList.add("running");
                statusText.textContent = "Läuft";
            }
            else if (data.output?.includes("inactive") || data.output?.includes("failed")) {
                indicator.classList.add("stopped");
                statusText.textContent = "Gestoppt";
            }
            else {
                indicator.classList.add("unknown");
                statusText.textContent = "Unbekannt";
            }

        })
        .catch(err => {
            document.getElementById("output").textContent = "Fehler: " + err;
        });
}

// ----------------------
// Beim Laden
// ----------------------
document.addEventListener("DOMContentLoaded", function () {
    loadDevices();
});