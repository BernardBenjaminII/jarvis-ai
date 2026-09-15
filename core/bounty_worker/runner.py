"""Internal POSIX process primitive; never expose argv to model/tool routing.

This is process lifecycle control, NOT an OS security sandbox.
Only the hardcoded fixture CLI uses it in R2.
"""
import os
import selectors
import signal
import subprocess
import time


def run_bounded(argv, *, timeout=5, output_limit=65536, cancel=None):
    if os.name != 'posix':
        raise RuntimeError('R2 runner requires POSIX process groups')
    if not 0 < timeout <= 30 or not 1 <= output_limit <= 1048576:
        raise ValueError('Invalid execution limits')
    if cancel is not None and cancel.is_set():
        return {'state': 'cancelled', 'output': '', 'bytes': 0, 'returncode': None}
    deadline = time.monotonic() + timeout
    process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, shell=False, start_new_session=True,
                               env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8'}, close_fds=True)
    output = bytearray()
    state = 'completed'
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    try:
        while True:
            if cancel is not None and cancel.is_set():
                state = 'cancelled'; break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                state = 'timeout'; break
            for key, _ in selector.select(min(.05, remaining)):
                chunk = os.read(key.fileobj.fileno(), min(65536, output_limit - len(output) + 1))
                if not chunk:
                    selector.unregister(key.fileobj)
                elif len(output) + len(chunk) > output_limit:
                    output.extend(chunk[:output_limit-len(output)])
                    state = 'output_limit'; break
                else:
                    output.extend(chunk)
            if state != 'completed':
                break
            if not selector.get_map() and process.poll() is not None:
                if process.returncode:
                    state = 'failed'
                break
    finally:
        # Also remove descendants that outlive the parent, including pipe holders.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        selector.close()
        process.stdout.close()
    return {'state': state, 'output': output.decode('utf-8', errors='replace'),
            'bytes': len(output), 'returncode': process.returncode}
