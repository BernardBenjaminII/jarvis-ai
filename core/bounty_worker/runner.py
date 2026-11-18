"""Internal POSIX process primitive; never expose argv to model/tool routing.

This is process lifecycle control, NOT an OS security sandbox.
Only the hardcoded fixture CLI uses it in R2.
"""
import os
import selectors
import signal
import subprocess
import time


def run_bounded(
    argv,
    *,
    timeout=5,
    output_limit=65536,
    cancel=None,
    stdin_text=None,
):
    if os.name != 'posix':
        raise RuntimeError('R2 runner requires POSIX process groups')
    if not 0 < timeout <= 30 or not 1 <= output_limit <= 1048576:
        raise ValueError('Invalid execution limits')

    if stdin_text is not None:
        if not isinstance(stdin_text, str):
            raise ValueError('stdin_text must be text')

        stdin_bytes = stdin_text.encode('utf-8')

        # This runner only supports small fixed adapter inputs,
        # never arbitrary bulk process input.
        if len(stdin_bytes) > 4096:
            raise ValueError('stdin_text exceeds 4096 bytes')
    else:
        stdin_bytes = None

    if cancel is not None and cancel.is_set():
        return {'state': 'cancelled', 'output': '', 'bytes': 0, 'returncode': None}

    deadline = time.monotonic() + timeout

    process = subprocess.Popen(
        argv,
        stdin=(
            subprocess.PIPE
            if stdin_bytes is not None
            else subprocess.DEVNULL
        ),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=False,
        start_new_session=True,
        env={
            'PATH': '/usr/bin:/bin',
            'LANG': 'C.UTF-8',
        },
        close_fds=True,
    )

    output = bytearray()
    state = 'completed'
    selector = None
    input_offset = 0

    try:
        selector = selectors.DefaultSelector()

        os.set_blocking(process.stdout.fileno(), False)
        selector.register(
            process.stdout,
            selectors.EVENT_READ,
        )

        if stdin_bytes is not None:
            os.set_blocking(process.stdin.fileno(), False)

            if stdin_bytes:
                selector.register(
                    process.stdin,
                    selectors.EVENT_WRITE,
                )
            else:
                process.stdin.close()

        while True:
            if cancel is not None and cancel.is_set():
                state = 'cancelled'
                break

            remaining = deadline - time.monotonic()

            if remaining <= 0:
                state = 'timeout'
                break

            events = selector.select(min(0.05, remaining))

            for key, mask in events:
                if (
                    process.stdin is not None
                    and key.fileobj is process.stdin
                ):
                    try:
                        written = os.write(
                            process.stdin.fileno(),
                            stdin_bytes[input_offset:],
                        )
                    except BlockingIOError:
                        continue
                    except BrokenPipeError:
                        selector.unregister(process.stdin)
                        process.stdin.close()
                        continue

                    input_offset += written

                    if input_offset >= len(stdin_bytes):
                        selector.unregister(process.stdin)
                        process.stdin.close()

                elif mask & selectors.EVENT_READ:
                    try:
                        chunk = os.read(
                            key.fileobj.fileno(),
                            min(
                                65536,
                                output_limit - len(output) + 1,
                            ),
                        )
                    except BlockingIOError:
                        continue

                    if not chunk:
                        selector.unregister(key.fileobj)
                    elif len(output) + len(chunk) > output_limit:
                        output.extend(
                            chunk[:output_limit - len(output)]
                        )
                        state = 'output_limit'
                        break
                    else:
                        output.extend(chunk)

            if state != 'completed':
                break

            if process.poll() is not None:
                if (
                    process.stdin is not None
                    and not process.stdin.closed
                ):
                    try:
                        selector.unregister(process.stdin)
                    except KeyError:
                        pass
                    process.stdin.close()

                if not selector.get_map():
                    if process.returncode:
                        state = 'failed'
                    break

    finally:
        # Always clean up the isolated process group.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        finally:
            try:
                process.wait()
            finally:
                if selector is not None:
                    selector.close()

                process.stdout.close()

                if (
                    process.stdin is not None
                    and not process.stdin.closed
                ):
                    process.stdin.close()
    return {'state': state, 'output': output.decode('utf-8', errors='replace'),
            'bytes': len(output), 'returncode': process.returncode}
