from __future__ import annotations

from typing import Protocol

from shotforge.core.project_state import ProjectState


class ReviewRefineProvider(Protocol):
    def review(self, state: ProjectState) -> list[str]:
        """Return human or model review notes for a generated package."""

    def refine(self, state: ProjectState, notes: list[str]) -> ProjectState:
        """Apply review notes to create the next package version."""


class NoopReviewRefineProvider:
    def review(self, state: ProjectState) -> list[str]:
        return state.review_notes

    def refine(self, state: ProjectState, notes: list[str]) -> ProjectState:
        state.review_notes.extend(notes)
        state.touch()
        return state
