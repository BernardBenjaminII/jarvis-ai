OS_COMMANDS = {
    "Linux": {
        "cpu_info": "lscpu",
        "cpu_usage": "top -bn1 | head -n 5",
        "memory": "free -h",
        "disk": "df -h",
        "network_scan": "arp -a",
    },

    "Kali": {
        "cpu_info": "lscpu",
        "cpu_usage": "htop -b -n1 | head -n 10",
        "memory": "free -h",
        "network_scan": "arp -a",
    },

    "Ubuntu": {
        "cpu_info": "lscpu",
        "cpu_usage": "top -bn1 | grep 'Cpu(s)'",
        "memory": "free -h",
        "disk": "df -h",
    }
}
