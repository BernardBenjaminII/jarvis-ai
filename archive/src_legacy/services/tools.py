import datetime
import psutil
import socket
import subprocess
import os


# =========================
# 🧰 CORE TOOLS
# =========================

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

def run_tool(command: str) -> str:
    command = command.lower()

    # ⏱️ Time
    if "time" in command:
        return get_time()

    if "date" in command:
        return get_date()

    # 🤖 Identity
    if "who are you" in command:
        return get_identity()

    # ⚙️ System
    if "status" in command or "cpu" in command or "memory" in command:
        return get_system_status()

    # 🌐 Network
    if "ip" in command:
        return get_ip()

    if "scan network" in command:
        return scan_network()

    if "ping" in command:
        target = command.replace("ping", "").strip()
        return ping(target)

    # 💻 Processes
    if "process" in command:
        return list_processes()

    if "kill" in command:
        name = command.replace("kill", "").strip()
        return kill_process(name)

    # 📁 Files
    if "find" in command:
        filename = command.replace("find", "").strip()
        return find_file(filename)

    if "read" in command:
        filepath = command.replace("read", "").strip()
        return read_file(filepath)

    # 💻 Commands (SAFE ONLY)
    if command.startswith("run"):
        cmd = command.replace("run", "").strip()
        return run_safe_command(cmd)

    return "[TOOL] No matching tool found"
