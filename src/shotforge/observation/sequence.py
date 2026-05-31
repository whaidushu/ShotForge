from __future__ import annotations

import re
from statistics import mean

from shotforge.core.project_state import GeneratedResult, SequenceObservation


class SequenceObservationBuilder:
    def build(self, generated_result: GeneratedResult) -> list[SequenceObservation]:
        if not generated_result.shots:
            return []
        return [
            SequenceObservation(
                generated_result_id=generated_result.generated_result_id,
                version=generated_result.version,
                shot_ids=[shot.shot_id for shot in generated_result.shots],
                element_continuity_score=self._continuity_score(
                    [
                        {
                            element
                            for frame in shot.frame_observations
                            for element in frame.detected_elements
                        }
                        for shot in generated_result.shots
                    ]
                ),
                action_continuity_score=self._text_continuity_score(
                    [
                        " ".join(frame.action_summary for frame in shot.frame_observations)
                        for shot in generated_result.shots
                    ]
                ),
                identity_continuity_score=self._identity_score(
                    [
                        frame.face_identity
                        for shot in generated_result.shots
                        for frame in shot.frame_observations
                        if frame.face_identity
                    ]
                ),
                transition_notes=[
                    f"{before.shot_id}->{after.shot_id}"
                    for before, after in zip(
                        generated_result.shots,
                        generated_result.shots[1:],
                        strict=False,
                    )
                ],
                metadata={"contract": "single_shot_now_sequence_ready"},
            )
        ]

    def _continuity_score(self, values: list[set[str]]) -> float | None:
        if len(values) < 2:
            return None
        scores = []
        for before, after in zip(values, values[1:], strict=False):
            if not before and not after:
                scores.append(1.0)
            elif not before or not after:
                scores.append(0.0)
            else:
                scores.append(len(before & after) / len(before | after))
        return round(mean(scores), 3) if scores else None

    def _text_continuity_score(self, values: list[str]) -> float | None:
        terms = [set(re.findall(r"[a-z][a-z0-9-]{2,}", value.lower())) for value in values]
        return self._continuity_score(terms)

    def _identity_score(self, identities: list[str]) -> float | None:
        if len(identities) < 2:
            return None
        return round(identities.count(identities[0]) / len(identities), 3)
