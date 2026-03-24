from flask import Blueprint, jsonify, request
from modules import logs


logs_bp = Blueprint("logs", __name__)


@logs_bp.route("/api/logs/clear", methods=["POST"])
def clear_logs():
    logs.save_logs([])
    logs.add_log("CLEAR", info="Logs wurden gelöscht")
    return jsonify({"status": "ok"})


@logs_bp.route("/api/logs")
def api_logs():
    log_entries = logs.load_logs()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    start = (page - 1) * per_page
    end = start + per_page

    return jsonify({
        "logs": log_entries[start:end],
        "total": len(log_entries),
        "page": page,
        "pages": (len(log_entries) + per_page - 1) // per_page
    })