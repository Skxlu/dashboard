from flask import Blueprint, render_template, request
from modules import device as d


pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def index():
    devices = d.load_devices()
    return render_template("index.html", devices=devices)


@pages_bp.route("/details")
def details():
    ip = request.args.get("ip")
    devices = d.load_devices()
    device = next((dev for dev in devices if dev["ip"] == ip), None)

    if device is None:
        return f"Kein Gerät mit IP {ip} gefunden", 404

    return render_template("details.html", device=device)


@pages_bp.route("/systemctl")
def systemctl_page():
    return render_template("systemctl.html")


@pages_bp.route("/logs")
def logs_page():
    return render_template("logs.html")