import nmap
from mac_vendor_lookup import MacLookup
from modules import device as d


def find_device(devices, ip, mac):
    for device in devices:
        if mac and device.get("mac") == mac:
            return device
        if not mac and device.get("ip") == ip:
            return device
    return None


def scan_network(subnet="10.10.10.0/24"):
    """
    Scannt das Netzwerk nach Geräten, erkennt neue IPs, aktualisiert bekannte MACs
    und verhindert Duplikate für Geräte ohne MAC.
    """
    nm = nmap.PortScanner()
    nm.scan(hosts=subnet, arguments='-sn')

    devices = d.load_devices()
    mac_lookup = MacLookup()
    updated = False

    for host in nm.all_hosts():
        ip = nm[host]['addresses'].get('ipv4')
        mac = nm[host]['addresses'].get('mac', '').upper() if 'mac' in nm[host]['addresses'] else None

        if not ip:
            continue

        existing = find_device(devices, ip, mac)

        if existing:
            # Falls gleiche MAC gefunden wurde, aber neue IP
            if mac and existing.get("ip") != ip:
                existing["ip"] = ip
                updated = True
            continue

        try:
            vendor = mac_lookup.lookup(mac) if mac else "Unknown"
        except Exception:
            vendor = "Unknown"

        new_device = {
            "name": vendor,
            "ip": ip,
            "mac": mac if mac else "Unknown",
            "ssh_user": "",
            "ssh_pass": ""
        }

        devices.append(new_device)
        updated = True

    if updated:
        d.save_devices(devices)