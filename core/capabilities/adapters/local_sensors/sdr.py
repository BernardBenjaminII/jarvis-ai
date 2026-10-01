"""RTL-SDR hardware adapter."""

from __future__ import annotations

import re
import shutil
import subprocess

from .models import SDRStatus


_DEVICE_RE = re.compile(
    r"0:\s+(?P<manufacturer>[^,\r\n]+),\s*"
    r"(?P<product>.*?),\s*SN:\s*(?P<serial>\S+)"
)

_TUNER_RE = re.compile(r"Found\s+(.+?)\s+tuner", re.IGNORECASE)
_SAMPLE_RE = re.compile(r"Sampling at\s+(\d+)\s+S/s", re.IGNORECASE)


def _parse_rtl_test_output(text: str) -> SDRStatus:
    lower = text.lower()

    device = _DEVICE_RE.search(text)
    tuner = _TUNER_RE.search(text)
    sample = _SAMPLE_RE.search(text)

    manufacturer = device.group("manufacturer").strip() if device else None
    product = device.group("product").strip() if device else None
    serial = device.group("serial").strip() if device else None
    tuner_name = tuner.group(1).strip() if tuner else None
    sample_rate = int(sample.group(1)) if sample else None

    if "usb_open error -3" in lower or "permission" in lower:
        return SDRStatus(
            state="permission_denied",
            available=True,
            manufacturer=manufacturer,
            product=product,
            serial=serial,
            tuner=tuner_name,
            sample_rate=sample_rate,
            detail="RTL-SDR detected but device permissions prevent access.",
        )

    if (
        "device or resource busy" in lower
        or "kernel driver is active" in lower
        or "claimed by second instance" in lower
    ):
        return SDRStatus(
            state="busy",
            available=True,
            manufacturer=manufacturer,
            product=product,
            serial=serial,
            tuner=tuner_name,
            sample_rate=sample_rate,
            detail="RTL-SDR is present but currently claimed by another driver or process.",
        )

    # rtl_test -t may return a non-zero exit code after tuner probing on
    # R820T-family devices. Presence of a usable tuner/sample stream is a
    # stronger readiness signal than the process exit code.
    if (
        "using device 0" in lower
        and tuner_name is not None
        and sample_rate is not None
    ):
        return SDRStatus(
            state="ready",
            available=True,
            manufacturer=manufacturer,
            product=product,
            serial=serial,
            tuner=tuner_name,
            sample_rate=sample_rate,
            detail="RTL-SDR hardware is accessible.",
        )

    if "found 0 device" in lower or "no supported devices found" in lower:
        return SDRStatus(
            state="unavailable",
            available=False,
            detail="No RTL-SDR device detected.",
        )

    return SDRStatus(
        state="error",
        available=device is not None,
        manufacturer=manufacturer,
        product=product,
        serial=serial,
        tuner=tuner_name,
        sample_rate=sample_rate,
        detail="RTL-SDR probe returned an unrecognized result.",
    )


def sdr_status(timeout: float = 8.0) -> SDRStatus:
    rtl_test = shutil.which("rtl_test")

    if rtl_test is None:
        return SDRStatus(
            state="unavailable",
            available=False,
            detail="rtl_test is not installed.",
        )

    try:
        result = subprocess.run(
            [rtl_test, "-t"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        text = ""
        if exc.stdout:
            text = (
                exc.stdout.decode(errors="replace")
                if isinstance(exc.stdout, bytes)
                else exc.stdout
            )

        parsed = _parse_rtl_test_output(text)

        # If rtl_test reached sampling before the timeout, hardware is usable.
        if parsed.state == "ready":
            return parsed

        return SDRStatus(
            state="error",
            available=parsed.available,
            manufacturer=parsed.manufacturer,
            product=parsed.product,
            serial=parsed.serial,
            tuner=parsed.tuner,
            sample_rate=parsed.sample_rate,
            detail="RTL-SDR probe timed out.",
        )
    except OSError as exc:
        return SDRStatus(
            state="error",
            available=False,
            detail=f"Unable to execute rtl_test: {exc}",
        )

    return _parse_rtl_test_output(result.stdout)
