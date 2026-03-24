from flask import Blueprint, jsonify
from modules import device as d

devices_bp = Blueprint("devices", __name__)


@devices_bp.route("/status")
def status():
    devices = d.load_devices()

    for dev in devices:
        dev["status"] = "online" if d.is_online(dev) else "offline"

    return jsonify(devices)


@devices_bp.route("/api/devices")
def api_devices():
    devices = d.load_devices()
    return jsonify(devices)