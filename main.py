import json
import subprocess
import paramiko
from flask import Flask, render_template, request, jsonify
from wakeonlan import send_magic_packet
from mac_vendor_lookup import MacLookup
import nmap
import os
import platform
import datetime
from modules import logs

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEVICE_FILE = os.path.join(BASE_DIR, "devices.json")

# ----------------------
# Helferfunktionen
# ----------------------
def load_devices():
    if not os.path.exists(DEVICE_FILE):
        with open(DEVICE_FILE, "w") as f:
            json.dump([], f)
    with open(DEVICE_FILE) as f:
        return json.load(f)

def save_devices(devices):
    with open(DEVICE_FILE, "w") as f:
        json.dump(devices, f, indent=2)

def is_online(device):
    ip = device["ip"]
    ssh_user = device.get("ssh_user", "")
    ssh_pass = device.get("ssh_pass", "")
    
    if ssh_user and ssh_pass:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=ssh_user, password=ssh_pass, timeout=3)
            ssh.close()
            return True
        except:
            return False
    else:
        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", "1", "-w", "1000", ip]
        else:
            cmd = ["ping", "-c", "1", "-W", "1", ip]
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL)
        return result.returncode == 0

def ssh_shutdown(ip, user, password, os_type="windows"):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=user, password=password, timeout=5)
        if os_type.lower() == "windows":
            cmd = "shutdown /s /t 0"
        else:  # Linux
            cmd = f'echo "{password}" | sudo -S shutdown -h now'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        stdout.channel.recv_exit_status()
        ssh.close()
    except Exception as e:
        print("SSH Fehler:", e)

# ----------------------
# Netzwerk-Scan (für neue Geräte)
# ----------------------
def scan_network(subnet="10.10.10.0/24"):
    """
    Scannt das Netzwerk nach Geräten, erkennt neue IPs, aktualisiert bekannte MACs
    und verhindert Duplikate für Geräte ohne MAC.
    """
    nm = nmap.PortScanner()
    nm.scan(hosts=subnet, arguments='-sn')  # Ping-Scan
    devices = load_devices()
    mac_lookup = MacLookup()
    updated = False

    # Hilfsfunktion: finde Gerät anhand MAC oder IP
    def find_device(ip, mac):
        for d in devices:
            if mac and d.get("mac") == mac:
                return d
            if not mac and d.get("ip") == ip:
                return d
        return None

    for host in nm.all_hosts():
        ip = nm[host]['addresses'].get('ipv4')
        mac = nm[host]['addresses'].get('mac', '').upper() if 'mac' in nm[host]['addresses'] else None
        if not ip:
            continue

        existing = find_device(ip, mac)

        if existing:
            # Update IP, wenn MAC gleich aber IP geändert
            if mac and existing.get('ip') != ip:
                existing['ip'] = ip
                updated = True
            continue  # Gerät schon vorhanden, keine Duplikate

        # Neues Gerät
        try:
            vendor = mac_lookup.lookup(mac) if mac else "Unknown"
        except:
            vendor = "Unknown"

        new_device = {
            "name": f"{vendor}",
            "ip": ip,
            "mac": mac if mac else "Unknown",
            "ssh_user": "",
            "ssh_pass": ""
        }
        devices.append(new_device)
        updated = True

    if updated:
        save_devices(devices)

# ----------------------
# Flask Routen
# ----------------------
@app.route("/")
def index():
    devices = load_devices()
    return render_template("index.html", devices=devices)

#----------------------------------------------------------------------------------------------

@app.route("/status")
def status():
    devices = load_devices()
    for d in devices:
        d["status"] = "online" if is_online(d) else "offline"
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
    ssh_shutdown(ip, user, password)
    logs.add_log("SHUTDOWN", ip, f"user: {user}")
    return ('', 204)

#----------------------------------------------------------------------------------------------

@app.route("/scan", methods=["POST"])
def scan():
    scan_network()
    logs.add_log("SCAN", info="Netzwerk gescannt")
    return ('', 204)

#----------------------------------------------------------------------------------------------

@app.route("/details")
def details():
    ip = request.args.get("ip")
    devices = load_devices()
    device = next((d for d in devices if d["ip"] == ip), None)
    if device is None:
        # Optional: 404 oder Fehlermeldung
        return f"Kein Gerät mit IP {ip} gefunden", 404
    return render_template("details.html", device=device)

#----------------------------------------------------------------------------------------------

@app.route("/api/devices")
def api_devices():
    devices = load_devices()
    return jsonify(devices)

#----------------------------------------------------------------------------------------------

@app.route("/edit_device", methods=["POST"])
def edit_device():
    ip = request.form["ip"]
    new_name = request.form["name"]
    new_user = request.form["ssh_user"]
    new_pass = request.form["ssh_pass"]

    devices = load_devices()

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

    save_devices(devices)
    return ('', 204)

#----------------------------------------------------------------------------------------------

@app.route("/delete_device", methods=["POST"])
def delete_device():
    ip = request.form["ip"]
    devices = load_devices()

    deleted_device = None

    for d in devices:
        if d["ip"] == ip:
            deleted_device = d
            break

    # Gerät entfernen
    devices = [d for d in devices if d["ip"] != ip]
    save_devices(devices)

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

    devices = load_devices()
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
    scan_network()
    app.run(host="0.0.0.0", port=5001)
