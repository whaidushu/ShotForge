from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FrameObservation(BaseModel):
    frame_index: int
    timestamp_seconds: float | None = None
    frame_path: str = ""
    detected_elements: list[str] = Field(default_factory=list)
    face_identity: str = ""
    action_summary: str = ""
    style_summary: str = ""
    color_summary: str = ""
    source: str = "heuristic"
    confidence: float = Field(default=0.45, ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ShotObservation(BaseModel):
    observation_id: str = Field(default_factory=lambda: f"shot_obs_{uuid4().hex[:12]}")
    shot_id: str
    generated_result_id: str
    version: int
    observer_id: str
    summary: str = ""
    frame_observations: list[FrameObservation] = Field(default_factory=list)
    detected_elements: list[str] = Field(default_factory=list)
    action_summary: str = ""
    confidence: float = Field(default=0.45, ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SequenceObservation(BaseModel):
    sequence_id: str = Field(default_factory=lambda: f"seq_obs_{uuid4().hex[:12]}")
    generated_result_id: str
    version: int
    shot_ids: list[str] = Field(default_factory=list)
    element_continuity_score: float | None = Field(default=None, ge=0, le=1)
    action_continuity_score: float | None = Field(default=None, ge=0, le=1)
    identity_continuity_score: float | None = Field(default=None, ge=0, le=1)
    transition_notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ObservationReport(BaseModel):
    report_id: str = Field(default_factory=lambda: f"obs_{uuid4().hex[:12]}")
    project_id: str
    run_id: str
    version: int
    generated_result_id: str
    created_at: datetime = Field(default_factory=utc_now)
    observer_id: str
    shot_observations: list[ShotObservation] = Field(default_factory=list)
    sequence_observations: list[SequenceObservation] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
