"""Single-owner receive-only SDR task manager."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
import subprocess
import threading
from typing import Any, BinaryIO

from .models import (
    RFStatus,
    RFTaskDescriptor,
    RFTaskRequest,
)
from .profiles import PROFILES
from .tasks.commands import (
    build_adsb,
    build_am,
    build_fm,
    build_manual,
    build_scan,
    executable,
)


class RFManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()

        self._process: subprocess.Popen | None = None
        self._audio_process: subprocess.Popen | None = None

        self._task: str | None = None
        self._config: dict[str, Any] = {}

        self._state = "idle"
        self._detail = "No RF task active."
        self._started_at: str | None = None

        self._output: deque[str] = deque(
            maxlen=80
        )

        self._reader_threads: list[
            threading.Thread
        ] = []

    # --------------------------------------------------------
    # Capabilities
    # --------------------------------------------------------

    def tasks(
        self,
    ) -> list[RFTaskDescriptor]:

        requirements = {
            "adsb": (
                "rtl_adsb",
                False,
            ),
            "fm": (
                "rtl_fm",
                True,
            ),
            "am": (
                "rtl_fm",
                True,
            ),
            "rf_scan": (
                "rtl_power",
                False,
            ),
            "manual": (
                "rtl_fm",
                True,
            ),
        }

        result: list[
            RFTaskDescriptor
        ] = []

        player = executable(
            "aplay"
        )

        for (
            task_id,
            profile,
        ) in PROFILES.items():

            command, needs_audio = (
                requirements[task_id]
            )

            path = executable(
                command
            )

            available = (
                path is not None
                and (
                    not needs_audio
                    or player is not None
                )
            )

            result.append(
                RFTaskDescriptor(
                    id=task_id,
                    name=profile["name"],
                    description=profile[
                        "description"
                    ],
                    available=available,
                    executable=path,
                )
            )

        return result

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    def _append(
        self,
        line: str,
    ) -> None:

        clean = line.rstrip()

        if not clean:
            return

        with self._lock:
            self._output.append(
                clean
            )

    def _reader_stream(
        self,
        stream: BinaryIO | None,
        prefix: str | None = None,
    ) -> None:

        if stream is None:
            return

        try:
            while True:
                raw = stream.readline()

                if not raw:
                    break

                if isinstance(
                    raw,
                    bytes,
                ):
                    clean = raw.decode(
                        "utf-8",
                        errors="replace",
                    ).rstrip()
                else:
                    clean = str(
                        raw
                    ).rstrip()

                if not clean:
                    continue

                if prefix:
                    clean = (
                        f"{prefix}: {clean}"
                    )

                self._append(
                    clean
                )

        except Exception as exc:
            self._append(
                f"reader error: {exc}"
            )

        finally:
            try:
                stream.close()
            except Exception:
                pass

    def _spawn_reader(
        self,
        stream: BinaryIO | None,
        prefix: str | None = None,
    ) -> None:

        thread = threading.Thread(
            target=self._reader_stream,
            args=(
                stream,
                prefix,
            ),
            daemon=True,
        )

        self._reader_threads.append(
            thread
        )

        thread.start()

    # --------------------------------------------------------
    # Command construction
    # --------------------------------------------------------

    def _build(
        self,
        task: str,
        config: dict[str, Any],
    ) -> tuple[str, list[str]]:

        if task == "adsb":
            return build_adsb(
                config
            )

        if task == "fm":
            return build_fm(
                config
            )

        if task == "am":
            return build_am(
                config
            )

        if task == "rf_scan":
            return build_scan(
                config
            )

        if task == "manual":
            return build_manual(
                config
            )

        raise RuntimeError(
            f"Unsupported RF task: {task}"
        )

    def _merged_config(
        self,
        request: RFTaskRequest,
    ) -> dict[str, Any]:

        config = dict(
            PROFILES.get(
                request.task,
                {},
            )
        )

        incoming = (
            request.model_dump(
                exclude_unset=True
            )
        )

        for key, value in (
            incoming.items()
        ):
            if value is not None:
                config[key] = value

        return config

    # --------------------------------------------------------
    # Audio
    # --------------------------------------------------------

    def _uses_audio(
        self,
        task: str,
        config: dict[str, Any],
    ) -> bool:

        if task in {
            "fm",
            "am",
        }:
            return True

        if task == "manual":
            return (
                config.get(
                    "modulation",
                    "fm",
                )
                in {
                    "fm",
                    "am",
                }
            )

        return False

    def _audio_rate(
        self,
        task: str,
        config: dict[str, Any],
    ) -> int:

        if task == "fm":
            return 32_000

        if task == "am":
            return 24_000

        if task == "manual":
            return 48_000

        return int(
            config.get(
                "audio_rate_hz",
                24_000,
            )
        )

    def _launch_audio(
        self,
        args: list[str],
        rate: int,
    ) -> None:

        player = executable(
            "aplay"
        )

        if not player:
            raise RuntimeError(
                "aplay is not installed"
            )

        source = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )

        if source.stdout is None:
            source.terminate()

            raise RuntimeError(
                "RF audio source did not "
                "provide stdout"
            )

        player_args = [
            player,
            "-q",
            "-t",
            "raw",
            "-f",
            "S16_LE",
            "-r",
            str(rate),
            "-c",
            "1",
        ]

        try:
            audio = subprocess.Popen(
                player_args,
                stdin=source.stdout,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                bufsize=0,
            )

        except Exception:
            source.terminate()
            source.wait(
                timeout=2
            )
            raise

        #
        # The audio child now owns the read
        # side of rtl_fm's stdout.
        #

        source.stdout.close()

        self._process = source
        self._audio_process = audio

        self._append(
            "Audio pipeline active: "
            f"rtl_fm -> aplay "
            f"({rate} Hz, mono)"
        )

        self._spawn_reader(
            source.stderr,
            "rtl_fm",
        )

        self._spawn_reader(
            audio.stderr,
            "aplay",
        )

    def _launch_normal(
        self,
        args: list[str],
    ) -> None:

        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
        )

        self._process = process
        self._audio_process = None

        self._spawn_reader(
            process.stdout
        )

    # --------------------------------------------------------
    # Process management
    # --------------------------------------------------------

    @staticmethod
    def _terminate(
        process: subprocess.Popen
        | None,
    ) -> None:

        if process is None:
            return

        if process.poll() is not None:
            return

        process.terminate()

        try:
            process.wait(
                timeout=3
            )

        except subprocess.TimeoutExpired:
            process.kill()

            try:
                process.wait(
                    timeout=2
                )
            except subprocess.TimeoutExpired:
                pass

    def start(
        self,
        request: RFTaskRequest,
    ) -> RFStatus:

        with self._lock:
            self.stop()

            self._state = "starting"
            self._detail = (
                f"Starting {request.task}"
            )

            self._output.clear()

            config = (
                self._merged_config(
                    request
                )
            )

            try:
                _exe, args = (
                    self._build(
                        request.task,
                        config,
                    )
                )

                if self._uses_audio(
                    request.task,
                    config,
                ):
                    rate = (
                        self._audio_rate(
                            request.task,
                            config,
                        )
                    )

                    config[
                        "audio_rate_hz"
                    ] = rate

                    self._launch_audio(
                        args,
                        rate,
                    )

                else:
                    self._launch_normal(
                        args
                    )

                self._task = (
                    request.task
                )

                self._config = config

                self._state = "running"

                self._started_at = (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )

                name = PROFILES[
                    request.task
                ]["name"]

                if self._uses_audio(
                    request.task,
                    config,
                ):
                    self._detail = (
                        f"{name} active · "
                        "audio playing"
                    )

                else:
                    self._detail = (
                        f"{name} active"
                    )

                return self.status()

            except Exception as exc:
                self._terminate(
                    self._process
                )

                self._terminate(
                    self._audio_process
                )

                self._process = None
                self._audio_process = None
                self._task = None
                self._config = {}

                self._state = "error"
                self._detail = str(
                    exc
                )

                self._started_at = None

                return self.status()

    def stop(
        self,
    ) -> RFStatus:

        with self._lock:
            source = self._process
            audio = (
                self._audio_process
            )

            if (
                source is None
                and audio is None
            ):
                self._state = "idle"
                self._task = None
                self._config = {}
                self._started_at = None
                self._detail = (
                    "No RF task active."
                )

                return self.status()

            self._state = "stopping"

            #
            # Stop source first so the audio
            # pipe receives EOF naturally.
            #

            self._terminate(
                source
            )

            self._terminate(
                audio
            )

            self._process = None
            self._audio_process = None

            self._task = None
            self._config = {}

            self._state = "idle"
            self._detail = (
                "RF task stopped."
            )

            self._started_at = None

            return self.status()

    # --------------------------------------------------------
    # Runtime health
    # --------------------------------------------------------

    def _refresh_process_state(
        self,
    ) -> None:

        source = self._process
        audio = (
            self._audio_process
        )

        #
        # Audio process died but rtl_fm is
        # still running: terminate rtl_fm so
        # we never leave the SDR orphaned.
        #

        if (
            source is not None
            and source.poll() is None
            and audio is not None
            and audio.poll() is not None
        ):
            code = (
                audio.returncode
            )

            self._terminate(
                source
            )

            self._process = None
            self._audio_process = None

            self._task = None
            self._config = {}

            self._state = "error"

            self._detail = (
                "Audio output exited "
                f"with code {code}"
            )

            self._started_at = None

            return

        if (
            source is not None
            and source.poll() is not None
        ):
            code = (
                source.returncode
            )

            completed_task = (
                self._task
            )

            if (
                audio is not None
                and audio.poll()
                is None
            ):
                self._terminate(
                    audio
                )

            self._process = None
            self._audio_process = None

            self._task = None
            self._config = {}
            self._started_at = None

            name = (
                PROFILES.get(
                    completed_task,
                    {},
                ).get(
                    "name",
                    "RF task",
                )
            )

            if code == 0:
                self._state = "idle"

                self._detail = (
                    f"{name} completed."
                )

            else:
                self._state = "error"

                self._detail = (
                    f"{name} exited "
                    f"with code {code}"
                )

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    def status(
        self,
    ) -> RFStatus:

        with self._lock:
            self._refresh_process_state()

            config = dict(
                self._config
            )

            process = (
                self._process
            )

            audio = (
                self._audio_process
            )

            audio_state: str | None = None
            audio_output: str | None = None

            if audio is not None:
                if audio.poll() is None:
                    audio_state = "playing"
                else:
                    audio_state = "error"

                audio_output = (
                    "system default audio"
                )

            elif (
                self._task
                in {
                    "fm",
                    "am",
                }
            ):
                audio_state = "off"

            executable_path = None

            if (
                process is not None
                and isinstance(
                    process.args,
                    list,
                )
                and process.args
            ):
                executable_path = str(
                    process.args[0]
                )

            return RFStatus(
                state=self._state,
                task=self._task,

                pid=(
                    process.pid
                    if process
                    else None
                ),

                frequency_hz=config.get(
                    "frequency_hz"
                ),

                sample_rate=config.get(
                    "sample_rate"
                ),

                gain=config.get(
                    "gain"
                ),

                scan_start_hz=config.get(
                    "scan_start_hz"
                ),

                scan_stop_hz=config.get(
                    "scan_stop_hz"
                ),

                scan_bin_hz=config.get(
                    "scan_bin_hz"
                ),

                audio_state=audio_state,

                audio_pid=(
                    audio.pid
                    if audio
                    else None
                ),

                audio_rate_hz=config.get(
                    "audio_rate_hz"
                ),

                audio_output=audio_output,

                started_at=(
                    self._started_at
                ),

                detail=self._detail,

                executable=(
                    executable_path
                ),

                output_tail=list(
                    self._output
                )[-20:],
            )


_RF_MANAGER = RFManager()


def get_rf_manager() -> RFManager:
    return _RF_MANAGER
