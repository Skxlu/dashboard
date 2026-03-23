import paramiko

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