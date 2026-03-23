function refreshStatus() {
    $.getJSON("/status", function (data) {
        let online = 0;

        data.forEach(function (d) {
            let id = d.ip.replace(/\./g, "_");
            let row = $("#row_" + id);
            let statusEl = $("#status_" + id);

            row.find("td").eq(0).text(d.name);
            row.find("td").eq(1).text(d.ip);

            let isMobile = window.innerWidth <= 768;

            if (isMobile) {
                statusEl.text("");
            } else {
                statusEl.text(d.status == "online" ? "Online" : "Offline");
            }

            statusEl.removeClass("online offline status")
                .addClass("status")
                .addClass(d.status == "online" ? "online" : "offline");

            if (d.status == "online") {
                online++;
            }
        });

        $("#counter").text("Online: " + online + " / " + data.length);
    });
}

function setButtonsDisabled(state) {
    document.querySelectorAll(".actions button").forEach(btn => {
        btn.disabled = state;
    });
}

function scanLAN() {
    const scanBtn = document.querySelector(".actions button");

    setButtonsDisabled(true);
    scanBtn.textContent = "Scanne...";

    $.post("/scan", {})
        .done(function () {
            location.reload();
        })
        .fail(function () {
            alert("Scan fehlgeschlagen");
            setButtonsDisabled(false);
            scanBtn.textContent = "Scan LAN";
        });
}

$(document).ready(function () {
    refreshStatus();
    setInterval(refreshStatus, 30000);
});

document.addEventListener('DOMContentLoaded', function () {
    const rows = document.querySelectorAll('#list tbody tr');

    rows.forEach(function (row) {
        row.addEventListener('click', function (e) {
            if (e.target.tagName.toLowerCase() === 'input') return;

            const ip = this.dataset.ip;
            const url = '/details?ip=' + encodeURIComponent(ip);

            if (window.innerWidth <= 768) {
                window.location.href = url;
            } else {
                window.open(url, 'deviceDetails', 'width=700,height=500,scrollbars=1,resizable=1');
            }
        });
    });
});
