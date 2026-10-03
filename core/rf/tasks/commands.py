"""Safe receive-only RTL-SDR command builders."""

from __future__ import annotations

import shutil
from typing import Any


def executable(name: str) -> str | None:
    return shutil.which(name)


def gain_args(
    gain: str | float,
) -> list[str]:

    if (
        isinstance(gain, str)
        and gain.lower() == "auto"
    ):
        return []

    return [
        "-g",
        str(gain),
    ]


def build_adsb(
    config: dict[str, Any],
) -> tuple[str, list[str]]:

    exe = executable("rtl_adsb")

    if not exe:
        raise RuntimeError(
            "rtl_adsb is not installed"
        )

    args = [
        exe,
        "-V",
    ]

    return exe, args


def build_fm(
    config: dict[str, Any],
) -> tuple[str, list[str]]:

    exe = executable("rtl_fm")

    if not exe:
        raise RuntimeError(
            "rtl_fm is not installed"
        )

    frequency = int(
        config["frequency_hz"]
    )

    #
    # rtl_fm's wbfm preset performs the correct
    # broadcast-FM demodulation and produces
    # signed 16-bit mono PCM at 32 kHz.
    #

    args = [
        exe,
        "-f",
        str(frequency),
        "-M",
        "wbfm",
        "-",
    ]

    args[1:1] = gain_args(
        config.get("gain", "auto")
    )

    return exe, args


def build_am(
    config: dict[str, Any],
) -> tuple[str, list[str]]:

    exe = executable("rtl_fm")

    if not exe:
        raise RuntimeError(
            "rtl_fm is not installed"
        )

    frequency = int(
        config["frequency_hz"]
    )

    #
    # NESDR SMArt v5:
    # LF/MF/HF uses RTL2832 Q-branch direct sampling.
    #

    args = [
        exe,
        "-f",
        str(frequency),
        "-M",
        "am",
        "-s",
        "24000",
        "-r",
        "24000",
        "-E",
        "direct2",
        "-",
    ]

    args[1:1] = gain_args(
        config.get("gain", "auto")
    )

    return exe, args


def build_manual(
    config: dict[str, Any],
) -> tuple[str, list[str]]:

    exe = executable("rtl_fm")

    if not exe:
        raise RuntimeError(
            "rtl_fm is not installed"
        )

    frequency = int(
        config["frequency_hz"]
    )

    modulation = str(
        config.get(
            "modulation",
            "fm",
        )
    )

    mode = {
        "fm": "fm",
        "am": "am",
        "raw": "raw",
    }.get(
        modulation,
        "fm",
    )

    args = [
        exe,
        "-f",
        str(frequency),
        "-M",
        mode,
        "-s",
        "240000",
        "-r",
        "48000",
        "-",
    ]

    args[1:1] = gain_args(
        config.get("gain", "auto")
    )

    return exe, args


def build_scan(
    config: dict[str, Any],
) -> tuple[str, list[str]]:

    exe = executable(
        "rtl_power"
    )

    if not exe:
        raise RuntimeError(
            "rtl_power is not installed"
        )

    start = int(
        config["scan_start_hz"]
    )

    stop = int(
        config["scan_stop_hz"]
    )

    bin_hz = int(
        config["scan_bin_hz"]
    )

    if stop <= start:
        raise RuntimeError(
            "scan_stop_hz must be greater "
            "than scan_start_hz"
        )

    range_spec = (
        f"{start}:{stop}:{bin_hz}"
    )

    args = [
        exe,
        "-f",
        range_spec,
        "-i",
        "2",
    ]

    gain = config.get(
        "gain",
        "auto",
    )

    if not (
        isinstance(gain, str)
        and gain.lower() == "auto"
    ):
        args.extend(
            [
                "-g",
                str(gain),
            ]
        )

    args.append("-")

    return exe, args
