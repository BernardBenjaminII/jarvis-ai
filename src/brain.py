from src.core.environment import get_environment
from src.services.llm_service import query_llm
from src.services.tools import run_tool
from src.services.system_service import run_command
from src.memory import save_interaction, get_recent_context
from src.services.network_guardian import handle_network_guardian


# 🧠 PROMPT BUILDER
# 🧠 PROMPT BUILDER
def build_prompt(question, context, env_info=""):
    return f"""
You are JARVIS, a local AI assistant.

Rules:
- Answer only the user's latest query.
- Do not invent a conversation.
- Do not write "User:" or "JARVIS:" labels.
- Do not roleplay unless directly asked.
- Be brief, useful, and direct.
- If asked to run a tool, do not pretend. The system will run tools separately.

Environment:
{env_info}

Recent Context:
{context}

Latest User Query:
{question}

Direct Answer:
""".strip()

# 🛡️ SAFE COMMAND WHITELIST
ALLOWED_COMMANDS = [
    "ls", "pwd", "whoami", "cat",
    "ifconfig", "ip a", "ip route",
    "ping", "netstat", "ss",
    "ps", "top",
    "nmap", "iwconfig", "iw dev"
]


# 🖥️ Detect direct shell commands
def is_shell_command(question: str):
    q = question.strip()
    return any(q.startswith(cmd) for cmd in ALLOWED_COMMANDS)


# 🧠 Tool detection (non-shell utilities)
def should_use_tool(question: str):
    q = question.lower()

    tool_keywords = [
        "time", "date",
        "status", "cpu", "memory", "disk",
        "process", "kill",
        "read file", "search file"
    ]

    return any(k in q for k in tool_keywords)


# 🚀 MAIN BRAIN
def process_query(question, mode="local"):
    try:
        # 🔥 ENVIRONMENT AWARENESS
        env = get_environment()
        os_type = env["os"]
        capabilities = env["capabilities"]
        jarvis_mode = env["mode"]

        def prefix(source="core"):
            return f"[JARVIS: {os_type}/{jarvis_mode}/{source}]"

        print(f"[ENV] {os_type} | {jarvis_mode} | {capabilities}")

        context = get_recent_context()

        # 👋 BASIC GREETING SHORTCUT
        if question.strip().lower() in ["hello", "hi", "hey"]:
            result = "Hello. JARVIS is online."
            save_interaction(question, result)
            return f"{prefix('core')}\n{result}"

        # 🖥️ SYSTEM COMMAND
        if is_shell_command(question):
            result = run_command(question)
            save_interaction(question, result)
            return f"{prefix('system')}\n{result}"

        # 🛡️ NETWORK GUARDIAN
        if "network" in question.lower() or "scan" in question.lower():
            if "network_scanning" not in capabilities:
                return f"{prefix('core')} Network operations not supported on this system."

            result = handle_network_guardian(question)
            save_interaction(question, result)
            return f"{prefix('network-guardian')}\n{result}"

        # 🛠️ TOOL
        if should_use_tool(question):
            result = run_tool(question)
            save_interaction(question, result)
            return f"{prefix('tool')}\n{result}"

        # 🤖 LLM
        env_info = f"OS: {os_type}\nMode: {jarvis_mode}\nCapabilities: {', '.join(capabilities)}"

        prompt = build_prompt(question, context, env_info)

        response = query_llm(prompt, mode)
        save_interaction(question, response)

        return f"{prefix('llm')}\n{response}"

    except Exception as e:
        return f"[BRAIN ERROR] {str(e)}"
