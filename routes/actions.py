import paramiko
from flask import Blueprint, request, jsonify
from wakeonlan import send_magic_packet

from modules import scan as s
from modules import device as d
from modules import logs
from modules import shutdown as shutd


actions_bp = Blueprint("actions", __name__)


@actions_bp.route("/wake", methods=["POST"])
def wake():
    mac = request.form["mac"]
    send_magic_packet(mac)
    logs.add_log("WAKE", info=f"MAC: {mac}")
    return ("", 204)


@actions_bp.route("/shutdown", methods=["POST"])
def shutdown():
    ip = request.form["ip"]
    user = request.form["user"]
    password = request.form["password"]

    shutd.ssh_shutdown(ip, user, password)
    logs.add_log("SHUTDOWN", ip, f"user: {user}")
    return ("", 204)


@actions_bp.route("/scan", methods=["POST"])
def scan():
    s.scan_network()
    logs.add_log("SCAN", info="Netzwerk gescannt")
    return ("", 204)


@actions_bp.route("/edit_device", methods=["POST"])
def edit_device():
    ip = request.form["ip"]
    new_name = request.form["name"]
    new_user = request.form["ssh_user"]
    new_pass = request.form["ssh_pass"]

    devices = d.load_devices()

    for dev in devices:
        if dev["ip"] == ip:
            changes = []

            if dev["name"] != new_name:
                changes.append(f"name: '{dev['name']}' → '{new_name}'")
                dev["name"] = new_name

            if dev.get("ssh_user") != new_user:
                changes.append(f"user: '{dev.get('ssh_user')}' → '{new_user}'")
                dev["ssh_user"] = new_user

            if new_pass.strip():
                if dev.get("ssh_pass") != new_pass:
                    changes.append("password geändert")
                dev["ssh_pass"] = new_pass

            if changes:
                logs.add_log("EDIT", ip, " | ".join(changes))
            break

    d.save_devices(devices)
    return ("", 204)


@actions_bp.route("/delete_device", methods=["POST"])
def delete_device():
    ip = request.form["ip"]
    devices = d.load_devices()

    deleted_device = None
    for dev in devices:
        if dev["ip"] == ip:
            deleted_device = dev
            break

    devices = [dev for dev in devices if dev["ip"] != ip]
    d.save_devices(devices)

    if deleted_device:
        logs.add_log(
            "DELETE",
            ip,
            f"{deleted_device.get('name', 'Unbekannt')} entfernt (MAC: {deleted_device.get('mac', '-')})"
        )
    else:
        logs.add_log("DELETE", ip, "Gerät nicht gefunden")

    return ("", 204)


@actions_bp.route("/api/systemctl", methods=["POST"])
def systemctl_status():
    data = request.json
    service = data.get("service")
    ip = data.get("ip")
    ssh_user_input = data.get("ssh_user", "").strip()
    ssh_pass_input = data.get("ssh_pass", "").strip()

    devices = d.load_devices()
    device = next((dev for dev in devices if dev["ip"] == ip), None)

    if device:
        ssh_user = ssh_user_input if ssh_user_input else device.get("ssh_user")
        ssh_pass = ssh_pass_input if ssh_pass_input else device.get("ssh_pass")
    else:
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