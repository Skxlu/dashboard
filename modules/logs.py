import os

def load_logs():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)
    with open(LOG_FILE) as f:
        return json.load(f)

def save_logs(logs):
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

def add_log(action, ip=None, info=""):
    logs = load_logs()

    logs.insert(0, {   # neueste oben
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "ip": ip or "-",
        "info": info
    })

    # Optional: max 200 Logs speichern
    logs = logs[:200]

    save_logs(logs)