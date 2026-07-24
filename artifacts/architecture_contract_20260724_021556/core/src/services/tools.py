import datetime
import psutil
import socket
import subprocess
import os


# =========================
# 🧰 CORE TOOLS
# =========================

def get_cpu_info():
    return (
        f"CPU Usage: {psutil.cpu_percent()}%\n"
        f"Cores: {psutil.cpu_count(logical=False)} physical / {psutil.cpu_count()} threads\n"
        f"Frequency: {psutil.cpu_freq().current:.0f} MHz"
    )

def get_time():
    return f"Current time: {datetime.datetime.now()}"


def get_date():
    return f"Today's date: {datetime.date.today()}"


def get_identity():
    return "I am JARVIS, your personal assistant."


def get_system_status():
    return f"""
CPU: {psutil.cpu_percent()}%
RAM: {psutil.virtual_memory().percent}%
Disk: {psutil.disk_usage('/').percent}%
""".strip()


def get_ip():
    try:
        return f"Local IP: {socket.gethostbyname(socket.gethostname())}"
    except Exception as e:
        return str(e)


# =========================
# 💻 PROCESS TOOLS
# =========================

def list_processes():
    try:
        procs = [p.name() for p in psutil.process_iter()]
        return "\n".join(procs[:20])
    except Exception as e:
        return str(e)


def kill_process(name):
    try:
        for p in psutil.process_iter():
            if name.lower() in p.name().lower():
                p.kill()
                return f"Killed {p.name()}"
        return "Process not found"
    except Exception as e:
        return str(e)


# =========================
# 🌐 NETWORK TOOLS
# =========================

def scan_network():
    return subprocess.getoutput("arp -a")


def ping(host):
    return subprocess.getoutput(f"ping -c 1 {host}")


def get_network_status():
    try:
        ip_info = subprocess.getoutput("ip addr show")
        route_info = subprocess.getoutput("ip route")
        wifi_info = subprocess.getoutput("iwconfig 2>/dev/null")

        return f"""
=== NETWORK STATUS ===

--- ROUTES ---
{route_info}

--- WIFI ---
{wifi_info}

--- INTERFACES ---
{ip_info}
""".strip()

    except Exception as e:
        return str(e)


# =========================
# 📁 FILE TOOLS
# =========================

def find_file(name, path="."):
    results = []
    for root, dirs, files in os.walk(path):
        for f in files:
            if name.lower() in f.lower():
                results.append(os.path.join(root, f))
    return "\n".join(results[:10]) or "No files found"


def read_file(path):
    try:
        with open(path, "r") as f:
            return f.read()[:2000]
    except Exception as e:
        return str(e)


# =========================
# 🔒 SAFE COMMAND EXECUTION
# =========================

SAFE_COMMANDS = ["ls", "pwd", "whoami", "df", "uptime"]


def run_safe_command(command):
    parts = command.split()

    if not parts:
        return "No command provided"

    if parts[0] not in SAFE_COMMANDS:
        return "Command not allowed"

    try:
        result = subprocess.check_output(parts, text=True)
        return result[:1000]
    except Exception as e:
        return str(e)


# =========================
# 🧠 TOOL ROUTER
# =========================

def get_processor_info():
    try:
        return subprocess.getoutput("lscpu")
    except Exception as e:
        return str(e)


def get_cpu_usage():
    try:
        return subprocess.getoutput("top -bn1 | head -n 8")
    except Exception as e:
        return str(e)


def get_memory_info():
    try:
        return subprocess.getoutput("free -h")
    except Exception as e:
        return str(e)


def get_disk_info():
    try:
        return subprocess.getoutput("df -h")
    except Exception as e:
        return str(e)

def run_tool(command: str) -> str:
    q = command.lower().strip()

    # =========================
    # ⏱️ Time / Date
    # =========================
    if "time" in q:
        return get_time()

    if "date" in q:
        return get_date()

    # =========================
    # 🤖 Identity
    # =========================
    if "who are you" in q or "your identity" in q:
        return get_identity()

    # =========================
    # ⚙️ SYSTEM (HIGH PRIORITY)
    # =========================

    # Processor / CPU info (must come BEFORE process)
    if "processor" in q or "cpu info" in q or "cpu model" in q:
        return get_processor_info()

    if q in ["show cpu", "cpu", "show me cpu"]:
        return get_cpu_usage()

    # CPU usage
    if "cpu usage" in q or "cpu load" in q:
        return get_cpu_usage()

    # Memory
    if "memory" in q or "ram" in q:
        return get_memory_info()

    # Disk
    if "disk" in q or "storage" in q:
        return get_disk_info()
    # Network 
    if "network" in q or "wifi" in q or "internet" in q:
        return get_network_status()

    # General system status
    if "status" in q:
        return get_system_status()

    # =========================
    # 🌐 NETWORK
    # =========================
    if "ip" in q:
        return get_ip()

    if "scan network" in q or "network scan" in q:
        return scan_network()

    if q.startswith("ping"):
        target = q.replace("ping", "", 1).strip()
        return ping(target)

    # =========================
    # 💻 PROCESSES (STRICT MATCH)
    # =========================
    if q == "process" or "show processes" in q or "list processes" in q:
        return list_processes()

    if q.startswith("kill"):
        name = q.replace("kill", "", 1).strip()
        return kill_process(name)

    # =========================
    # 📁 FILES
    # =========================
    if q.startswith("find"):
        filename = q.replace("find", "", 1).strip()
        return find_file(filename)

    if q.startswith("read"):
        filepath = q.replace("read", "", 1).strip()
        return read_file(filepath)

    # =========================
    # 💻 SAFE COMMAND
    # =========================
    if q.startswith("run"):
        cmd = q.replace("run", "", 1).strip()
        return run_safe_command(cmd)

    return "[TOOL] No matching tool found."
