import paramiko
from flask import Flask, render_template, request, jsonify
from wakeonlan import send_magic_packet

from modules import scan as s
from modules import device as d
from modules import logs
from modules import shutdown as shutd

app = Flask(__name__)

# ----------------------
# Flask Routen
# ----------------------
@app.route("/")
def index():
    devices = d.load_devices()
    return render_template("index.html", devices=devices)

#----------------------------------------------------------------------------------------------

@app.route("/status")
def status():
    devices = d.load_devices()
    for dev in devices:
        dev["status"] = "online" if d.is_online(dev) else "offline"
    return jsonify(devices)

#----------------------------------------------------------------------------------------------

@app.route("/wake", methods=["POST"])
def wake():
    mac = request.form["mac"]
    send_magic_packet(mac)
    logs.add_log("WAKE", info=f"MAC: {mac}")
    return ('', 204)

#----------------------------------------------------------------------------------------------

@app.route("/shutdown", methods=["POST"])
def shutdown():
    ip = request.form["ip"]
    user = request.form["user"]
    password = request.form["password"]
    shutd.ssh_shutdown(ip, user, password)
    logs.add_log("SHUTDOWN", ip, f"user: {user}")
    return ('', 204)

#----------------------------------------------------------------------------------------------

@app.route("/scan", methods=["POST"])
def scan():
    s.scan_network()
    logs.add_log("SCAN", info="Netzwerk gescannt")
    return ('', 204)

#----------------------------------------------------------------------------------------------

@app.route("/details")
def details():
    ip = request.args.get("ip")
    devices = d.load_devices()
    device = next((d for d in devices if d["ip"] == ip), None)
    if device is None:
        # Optional: 404 oder Fehlermeldung
        return f"Kein Gerät mit IP {ip} gefunden", 404
    return render_template("details.html", device=device)

#----------------------------------------------------------------------------------------------

@app.route("/api/devices")
def api_devices():
    devices = d.load_devices()
    return jsonify(devices)

#----------------------------------------------------------------------------------------------

@app.route("/edit_device", methods=["POST"])
def edit_device():
    ip = request.form["ip"]
    new_name = request.form["name"]
    new_user = request.form["ssh_user"]
    new_pass = request.form["ssh_pass"]

    devices = d.load_devices()

    for d in devices:
        if d["ip"] == ip:

            changes = []

            # Name
            if d["name"] != new_name:
                changes.append(f"name: '{d['name']}' → '{new_name}'")
                d["name"] = new_name

            # SSH User
            if d.get("ssh_user") != new_user:
                changes.append(f"user: '{d.get('ssh_user')}' → '{new_user}'")
                d["ssh_user"] = new_user

            # Passwort (nicht anzeigen!)
            if new_pass.strip():
                if d.get("ssh_pass") != new_pass:
                    changes.append("password geändert")
                    d["ssh_pass"] = new_pass

            # 🔥 Log nur wenn etwas geändert wurde
            if changes:
                logs.add_log("EDIT", ip, " | ".join(changes))

            break

    d.save_devices(devices)
    return ('', 204)

#----------------------------------------------------------------------------------------------

@app.route("/delete_device", methods=["POST"])
def delete_device():
    ip = request.form["ip"]
    devices = d.load_devices()

    deleted_device = None

    for d in devices:
        if d["ip"] == ip:
            deleted_device = d
            break

    # Gerät entfernen
    devices = [d for d in devices if d["ip"] != ip]
    d.save_devices(devices)

    # 🔥 Logging mit Name + MAC
    if deleted_device:
        logs.add_log(
            "DELETE",
            ip,
            f"{deleted_device.get('name','Unbekannt')} entfernt (MAC: {deleted_device.get('mac','-')})"
        )
    else:
        logs.add_log("DELETE", ip, "Gerät nicht gefunden")

    return ('', 204)

#----------------------------------------------------------------------------------------------

@app.route("/systemctl")
def systemctl_page():
    return render_template("systemctl.html")

@app.route("/api/systemctl", methods=["POST"])
def systemctl_status():
    data = request.json
    service = data.get("service")
    ip = data.get("ip")
    ssh_user_input = data.get("ssh_user", "").strip()
    ssh_pass_input = data.get("ssh_pass", "").strip()

    devices = d.load_devices()
    device = next((d for d in devices if d["ip"] == ip), None)

    if device:
        # Nimm user/pass aus devices.json, falls Frontend leer
        ssh_user = ssh_user_input if ssh_user_input else device.get("ssh_user")
        ssh_pass = ssh_pass_input if ssh_pass_input else device.get("ssh_pass")
    else:
        # Gerät nicht in devices.json, muss manuell User/Pass eingeben
        if not ssh_user_input or not ssh_pass_input:
            return jsonify({"error": "Device not found and no SSH credentials provided"})
        ssh_user = ssh_user_input
        ssh_pass = ssh_pass_input
    logs.add_log("SERVICE_CHECK", ip, f"Service: {service}")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=ssh_user, password=ssh_pass, timeout=5)

        command = f"systemctl status {service}.service"

        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        ssh.close()

        return jsonify({"output": output, "error": error})

    except Exception as e:
        return jsonify({"error": str(e)})

#----------------------------------------------------------------------------------------------

@app.route("/logs")
def logs_page():
    return render_template("logs.html")

@app.route("/api/logs/clear", methods=["POST"])
def clear_logs():
    logs.save_logs([])
    logs.add_log("CLEAR", info="Logs wurden gelöscht")
    return jsonify({"status": "ok"})

@app.route("/api/logs")
def api_logs():
    log = logs.load_logs()

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    start = (page - 1) * per_page
    end = start + per_page

    return jsonify({
        "logs": log[start:end],
        "total": len(log),
        "page": page,
        "pages": (len(log) + per_page - 1) // per_page
    })

#----------------------------------------------------------------------------------------------

if __name__ == "__main__":
    s.scan_network()
    app.run(host="0.0.0.0", port=5000)
