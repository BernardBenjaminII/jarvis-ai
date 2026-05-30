import subprocess
import shutil
import re
import ipaddress
import json
import os

DEVICE_DB = "known_devices.json"
# ------------------------
# STATUS LOG (LIVE FEED)
# ------------------------
STATUS_LOG = []
MAX_LOG = 50


def push_status(message):
    STATUS_LOG.append(message)

    if len(STATUS_LOG) > MAX_LOG:
        STATUS_LOG.pop(0)

# ------------------------
# CORE EXECUTION
# ------------------------
def run(cmd, timeout=20):
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            text=True,
            capture_output=True,
            timeout=timeout
        )
        output = result.stdout.strip() or result.stderr.strip()
        return output if output else "[OK] Command completed."
    except subprocess.TimeoutExpired:
        return f"[TIMEOUT] {cmd}"
    except Exception as e:
        return f"[ERROR] {e}"


def command_exists(cmd):
    return shutil.which(cmd) is not None


# ------------------------
# NETWORK DETECTION
# ------------------------
def get_active_subnet():
    output = run("ip -br addr")

    for line in output.splitlines():
        parts = line.split()

        if len(parts) >= 3:
            iface = parts[0]
            state = parts[1]
            ip_info = parts[2]

            if state == "UP" and iface != "lo":
                match = re.search(r'(\d+\.\d+\.\d+\.\d+/\d+)', ip_info)
                if match:
                    return match.group(1)

    return None


def get_scan_range():
    subnet = get_active_subnet()

    if subnet:
        network = ipaddress.ip_network(subnet, strict=False)

        if network.is_loopback or network.is_link_local:
            return "192.168.1.0/24"

        return str(network)

    return "192.168.1.0/24"


# ------------------------
# DEVICE TRACKING
# ------------------------
def load_known_devices():
    if not os.path.exists(DEVICE_DB):
        return {}
    with open(DEVICE_DB, "r") as f:
        return json.load(f)


def save_known_devices(devices):
    with open(DEVICE_DB, "w") as f:
        json.dump(devices, f, indent=2)


def extract_hosts(scan_output):
    hosts = []

    current_ip = None
    hostname = None
    vendor = None

    for line in scan_output.splitlines():

        if "Nmap scan report for" in line:
            parts = line.split("for")[1].strip()

            if "(" in parts:
                hostname = parts.split("(")[0].strip()
                current_ip = parts.split("(")[1].replace(")", "").strip()
            else:
                hostname = None
                current_ip = parts.strip()

        elif "MAC Address:" in line:
            vendor = line.split("(")[-1].replace(")", "").strip()

            # finalize this host entry
            if current_ip:
                hosts.append({
                    "ip": current_ip,
                    "hostname": hostname,
                    "vendor": vendor
                })

                current_ip = None
                hostname = None
                vendor = None

    return hosts

def fingerprint_device(ip):
    result = run(f"nmap -O -sT -Pn --max-retries 1 --host-timeout 4s {ip}")

    os_guess = "Unknown OS"
    open_ports = []

    for line in result.splitlines():
        if "Running:" in line or "OS details" in line:
            os_guess = line.strip()

        if "/tcp" in line and "open" in line:
            port = line.split()[0]
            open_ports.append(port)

    ports = ", ".join(open_ports) if open_ports else "No open ports"

    return f"{os_guess} | Ports: {ports}"


def alert_new_device(ip, label):
    return f"🚨 NEW DEVICE ALERT: {ip} → {label}"

def track_devices(scan_output):
    known = load_known_devices()
    hosts = extract_hosts(scan_output)

    output = []
    alerts = []
    self_ip = run("hostname -I").split()[0]

    for host in hosts:
        ip = host["ip"]
        hostname = host["hostname"]
        vendor = host["vendor"]

        label = "Unknown Device"

        if ip.endswith(".1"):
            label = "Gateway / Router"

        if hostname:
            label = hostname

        if vendor:
            label += f" ({vendor})"

        if ip == self_ip:
            label = "This Device (JARVIS)"

        is_new = ip not in known

        if is_new:
            known[ip] = label
            alerts.append(f"🚨 NEW DEVICE ALERT: {ip} → {label}")

        fingerprint = fingerprint_device(ip)

        prefix = "🚨 NEW" if is_new else "🧠 KNOWN"

        output.append(f"{prefix}: {ip} → {label}")
        output.append(f"   🔍 {fingerprint}")

    save_known_devices(known)

    final_output = []

    # ✅ ALWAYS show status
    if alerts:
        final_output.append("🚨 NEW DEVICES DETECTED 🚨")
        final_output.extend(alerts)
        final_output.append("")
    else:
        final_output.append("✅ No new devices detected")
        final_output.append("")

    # ✅ ALWAYS show devices
    final_output.extend(output)

    result = "\n".join(final_output)

    push_status(result)

    return result


# ------------------------
# NETWORK INFO
# ------------------------
def get_interfaces():
    return run("ip -br addr")


def get_routes():
    return run("ip route")


def get_dns():
    return run("resolvectl status 2>/dev/null || cat /etc/resolv.conf")


def ping_gateway():
    gateway = run("ip route | awk '/default/ {print $3; exit}'")
    if not gateway or gateway.startswith("["):
        return "[FAIL] No default gateway found."
    return run(f"ping -c 3 -W 2 {gateway}")


def ping_internet_ip():
    return run("ping -c 3 -W 2 1.1.1.1")


def ping_dns_name():
    return run("ping -c 3 -W 2 deb.debian.org")


def docker_status():
    if not command_exists("docker"):
        return "[INFO] Docker not installed."
    return run("systemctl is-active docker 2>/dev/null || docker info 2>&1 | head -20")


# ------------------------
# DIAGNOSIS
# ------------------------
def diagnose(internet, dns_test, gateway, docker):
    issues = []
    recommendations = []

    def add_issue(level, message, fix=None):
        issues.append((level, message))
        if fix:
            recommendations.append((level, fix))

    if "0% packet loss" not in gateway:
        add_issue("CRITICAL", "Cannot reach gateway", "Check WiFi")

    if "0% packet loss" not in internet:
        add_issue("CRITICAL", "No internet access", "Restart network")

    if "0% packet loss" not in dns_test:
        add_issue("WARNING", "DNS failing", "Run: fix dns")

    docker_lower = docker.lower()

    if "permission denied" in docker_lower:
        add_issue("WARNING", "Docker permission issue", "Fix docker group")

    elif "inactive" in docker_lower:
        add_issue("INFO", "Docker not running", "Start if needed")

    if not issues:
        add_issue("OK", "System healthy", "No action needed")

    return issues, recommendations


def format_section(title, content):
    return f"\n🔹 {title}\n" + "-" * 40 + f"\n{content.strip()}\n"


def format_issues(issues):
    icons = {"CRITICAL": "❌", "WARNING": "⚠️", "INFO": "ℹ️", "OK": "✅"}
    return "\n".join(f"{icons[l]} {l}: {m}" for l, m in issues)


def format_recommendations(recs):
    if not recs:
        return "No actions recommended"
    return "\n".join(f"- ({l}) {a}" for l, a in recs)


# ------------------------
# MAIN STATUS
# ------------------------
def network_status():
    interfaces = get_interfaces()
    routes = get_routes()
    dns = get_dns()
    gateway = ping_gateway()
    internet = ping_internet_ip()
    dns_test = ping_dns_name()
    docker = docker_status()

    issues, fixes = diagnose(internet, dns_test, gateway, docker)

    summary = "\n".join([
        "🌐 Internet: " + ("✅" if "0% packet loss" in internet else "❌"),
        "🧭 DNS: " + ("✅" if "0% packet loss" in dns_test else "❌"),
        "📡 Interface: " + ("✅" if "UP" in interfaces else "❌"),
        "🐳 Docker: " + ("⚠️" if "inactive" in docker.lower() else "✅")
    ])

    return (
        "🛡️ NETWORK GUARDIAN REPORT\n"
        + "=" * 50 + "\n\n"
        + summary + "\n\n"
        + format_section("Interfaces", interfaces)
        + format_section("Routes", routes)
        + format_section("DNS", dns)
        + format_section("Diagnosis", format_issues(issues))
        + format_section("Actions", format_recommendations(fixes))
    )


# ------------------------
# MAIN ENTRY
# ------------------------
def handle_network_guardian(query):
    q = query.lower()

    if "scan network" in q or "nmap" in q:
        subnet = get_scan_range()
        raw = run(f"nmap -sn -T4 --max-retries 1 --host-timeout 2s {subnet}")
        tracking = track_devices(raw)

        return (
            f"[SCAN RANGE: {subnet}]\n\n"
            f"{tracking}\n\n"
            f"{raw}"
        )

    if "network status" in q or "full network check" in q:
        return network_status()

    return "Network Guardian ready."
