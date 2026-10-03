"""Built-in receive-only RF task profiles."""

from __future__ import annotations


PROFILES = {
    "adsb": {
        "name": "ADS-B Aircraft",
        "description":
            "1090 MHz Mode-S / ADS-B receive task.",
        "frequency_hz": 1_090_000_000,
        "sample_rate": 2_048_000,
        "gain": "auto",
    },

    "fm": {
        "name": "FM Broadcast",
        "description":
            "Wide-FM broadcast radio with local audio.",
        "frequency_hz": 100_000_000,
        "sample_rate": 2_048_000,
        "audio_rate_hz": 32_000,
        "gain": "auto",
    },

    "am": {
        "name": "AM Broadcast",
        "description":
            "Medium-wave AM broadcast using Q-branch direct sampling.",
        "frequency_hz": 999_000,
        "sample_rate": 24_000,
        "audio_rate_hz": 24_000,
        "gain": "auto",
    },

    "rf_scan": {
        "name": "RF Spectrum Scan",
        "description":
            "Sweep a selected RF range using rtl_power.",
        "scan_start_hz": 88_000_000,
        "scan_stop_hz": 108_000_000,
        "scan_bin_hz": 25_000,
        "gain": "auto",
    },

    "manual": {
        "name": "Manual Receiver",
        "description":
            "Manual frequency and modulation control.",
        "frequency_hz": 100_000_000,
        "sample_rate": 2_048_000,
        "gain": "auto",
    },
}
