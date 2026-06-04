import subprocess

def run_command(command):
    try:
        result = subprocess.check_output(
            command,
            shell=True,
            stderr=subprocess.STDOUT,
            text=True
        )
        return result.strip()
    except subprocess.CalledProcessError as e:
        return f"[COMMAND ERROR]\n{e.output}"
