"""RF task models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RFTaskName = Literal[
    "adsb",
    "fm",
    "am",
    "rf_scan",
    "manual",
]


class RFTaskRequest(BaseModel):
    task: RFTaskName

    frequency_hz: int | None = None

    sample_rate: int = Field(
        default=2_048_000,
        ge=225_001,
        le=3_200_000,
    )

    gain: str | float = "auto"

    scan_start_hz: int | None = None
    scan_stop_hz: int | None = None

    scan_bin_hz: int = Field(
        default=25_000,
        ge=1_000,
    )

    modulation: Literal[
        "fm",
        "am",
        "raw",
    ] = "fm"


class RFTaskDescriptor(BaseModel):
    id: RFTaskName
    name: str
    description: str
    available: bool
    executable: str | None = None


class RFStatus(BaseModel):
    schema_id: str = "jarvis.rf.r2"

    state: Literal[
        "idle",
        "starting",
        "running",
        "stopping",
        "error",
    ]

    task: RFTaskName | None = None
    pid: int | None = None

    frequency_hz: int | None = None
    sample_rate: int | None = None
    gain: str | float | None = None

    scan_start_hz: int | None = None
    scan_stop_hz: int | None = None
    scan_bin_hz: int | None = None

    audio_state: str | None = None
    audio_pid: int | None = None
    audio_rate_hz: int | None = None
    audio_output: str | None = None

    started_at: str | None = None
    detail: str | None = None

    executable: str | None = None

    output_tail: list[str] = Field(
        default_factory=list
    )
