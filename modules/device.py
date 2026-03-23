import os
import json
import paramiko
import platform
import subprocess


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEVICE_FILE = os.path.join(BASE_DIR, "devices.json")

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

