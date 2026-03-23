function wake(mac) {
    $.post("/wake", { mac: mac })
        .done(function () {
            closePage();
        })
        .fail(function () {
            alert("Wake Up fehlgeschlagen! Prüfe MAC.");
        });
}

function shutdown(ip, user, pass) {
    $.post("/shutdown", { ip: ip, user: user, password: pass })
        .done(function () {
            // nur wenn POST erfolgreich
            closePage();
        })
        .fail(function () {
            alert("Shutdown fehlgeschlagen! Prüfe IP, Benutzer, Passwort oder Rechte.");
        });
}

function closePage() {
    if (window.opener && !window.opener.closed) {
        window.opener.location.reload(true);
        window.close();
        return;
    }
    window.history.back();
}

function togglePassword() {
    const field = document.getElementById("sshPass");
    const checkbox = document.getElementById("showPassword");
    field.type = field.type === "password" ? "text" : "password";
    checkbox.checked = field.type === "text";
}
document.getElementById("showPassword").addEventListener("change", togglePassword);

function delete_device(ip) {
    if (confirm("Gerät wirklich löschen?")) {
        $.post("/delete_device", { ip: ip }, function () {
            // Wenn es ein opener-Fenster gibt (Popup)
            if (window.opener && !window.opener.closed) {
                try {
                    // reload des Opener-Fensters
                    window.opener.location.href = window.opener.location.pathname + '?t=' + Date.now();
                    // Popup schließen, wenn möglich
                    window.close();
                    return;
                } catch (e) {
                    console.log("Cannot close opener, fallback to reload");
                }
            }
            // Kein opener oder nicht closable -> einfach index.html laden
            window.location.href = '/?t=' + Date.now();
        });
    }
}

function saveChanges() {
    const ip = document.getElementById("device_ip").value;
    const name = document.getElementById("deviceName").value;
    const ssh_user = document.getElementById("sshUser").value;
    const ssh_pass = document.getElementById("sshPass").value;
    const saveBtn = event.target;
    saveBtn.disabled = true;
    saveBtn.textContent = 'Speichere...';

    $.post("/edit_device", {
        ip: ip,
        name: name,
        ssh_user: ssh_user,
        ssh_pass: ssh_pass
    }, function () {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Speichern ✓';
        if (window.opener && !window.opener.closed) {
            window.opener.location.href = window.opener.location.pathname + '?reload=' + Date.now();
            window.close();
        } else if (document.referrer) {
            window.location.href = document.referrer + '?t=' + Date.now();
        } else {
            window.location.href = '/';
        }
    }).fail(function () {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Speichern';
        alert('Fehler beim Speichern');
    });
}

document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { closePage(); }
});