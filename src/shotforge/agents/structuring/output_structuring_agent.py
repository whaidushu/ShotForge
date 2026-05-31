from __future__ import annotations

from shotforge.core.project_state import CorrectionOperation, CorrectionPatch, ProjectState
from shotforge.core.trace_log import TraceLog
from shotforge.core.version_diff import VersionDiffBuilder
from shotforge.core.version_manager import VersionManager


class OutputStructuringAgent:
    def structure(
        self,
        state: ProjectState,
        patches: list[CorrectionPatch],
        reason: str = "redesign",
    ) -> ProjectState:
        with TraceLog(state).span("output_structuring_agent", patch_count=len(patches)):
            next_state = VersionManager().fork_next_version(state, reason=reason)
            next_state.correction_patches.extend(patches)
            skipped_duplicates = 0
            for patch in patches:
                unique_operations, duplicate_count = self._dedupe_operations(patch.operations)
                skipped_duplicates += duplicate_count
                for operation in unique_operations:
                    self._apply_operation(next_state, operation)
                self._mark_plan_applied(next_state, patch.plan_id)
            resolved_issue_ids = sorted(
                {
                    issue_id
                    for patch in patches
                    for issue_id in self._plan_issue_ids(next_state, patch.plan_id)
                }
            )
            next_state.issue_history = [
                issue for issue in next_state.issue_history if issue.issue_id not in resolved_issue_ids
            ]
            diff = VersionDiffBuilder().build(
                state,
                next_state,
                explanation=self._explanation(state, next_state, patches),
            )
            diff.resolved_issues = resolved_issue_ids
            diff.metadata["patch_ids"] = [patch.patch_id for patch in patches]
            next_state.version_diffs.append(diff)
            next_state.metadata["redesign_result"] = {
                "from_version": state.version,
                "to_version": next_state.version,
                "patch_count": len(patches),
                "operation_count": sum(len(patch.operations) for patch in patches),
                "skipped_duplicate_operation_count": skipped_duplicates,
                "resolved_issue_count": len(resolved_issue_ids),
                "diff_id": diff.diff_id,
            }
            next_state.metadata["next_version_preview"] = {
                "current_version": state.version,
                "next_version": next_state.version,
                "parent_version": next_state.metadata.get("parent_version"),
                "fork_reason": next_state.metadata.get("fork_reason"),
            }
            next_state.touch()
            return next_state

    def _apply_operation(self, state: ProjectState, operation: CorrectionOperation) -> None:
        if operation.operation_type == "append_shot_description":
            shot = next(item for item in state.shots if item.shot_id == operation.target_id)
            shot.description = self._append(shot.description, str(operation.value))
            return
        if operation.operation_type == "append_motion_subject":
            shot = next(item for item in state.shots if item.shot_id == operation.target_id)
            if shot.motion is not None:
                shot.motion.subject_motion = self._append(
                    shot.motion.subject_motion,
                    str(operation.value),
                )
            return
        if operation.operation_type == "append_motion_camera":
            shot = next(item for item in state.shots if item.shot_id == operation.target_id)
            if shot.motion is not None:
                shot.motion.camera = self._append(shot.motion.camera, str(operation.value))
            return
        if operation.operation_type == "append_prompt_text":
            prompt = next(
                item for item in state.prompt_package.prompts if item.shot_id == operation.target_id
            )
            prompt.prompt = self._append(prompt.prompt, str(operation.value))
            return
        if operation.operation_type == "append_negative_prompt":
            prompt = next(
                item for item in state.prompt_package.prompts if item.shot_id == operation.target_id
            )
            prompt.negative_prompt = self._append_comma_list(
                prompt.negative_prompt,
                str(operation.value),
            )
            return
        if operation.operation_type == "append_structured_template_text":
            prompt = next(
                item for item in state.prompt_package.prompts if item.shot_id == operation.target_id
            )
            if prompt.structured_template is not None:
                field_name = operation.field_path.rsplit(".", 1)[-1]
                current = getattr(prompt.structured_template, field_name, "")
                if isinstance(current, str):
                    setattr(prompt.structured_template, field_name, self._append(current, str(operation.value)))
            return
        if operation.operation_type == "append_structured_template_list":
            prompt = next(
                item for item in state.prompt_package.prompts if item.shot_id == operation.target_id
            )
            if prompt.structured_template is not None:
                field_name = operation.field_path.rsplit(".", 1)[-1]
                current = getattr(prompt.structured_template, field_name, None)
                if isinstance(current, list):
                    values = operation.value if isinstance(operation.value, list) else [str(operation.value)]
                    for value in values:
                        text = str(value).strip()
                        if text and text not in current:
                            current.append(text)
            return
        if operation.operation_type == "append_scene_description":
            scene = next(item for item in state.scenes if item.scene_id == operation.target_id)
            scene.description = self._append(scene.description, str(operation.value))
            return
        if operation.operation_type == "append_scene_emotional_goal":
            scene = next(item for item in state.scenes if item.scene_id == operation.target_id)
            scene.emotional_goal = self._append(scene.emotional_goal, str(operation.value))
            return
        if operation.operation_type == "append_audio_sound_design":
            cue = next(item for item in state.audio_cues if item.shot_id == operation.target_id)
            values = operation.value if isinstance(operation.value, list) else [str(operation.value)]
            for value in values:
                text = str(value)
                if text not in cue.sound_design:
                    cue.sound_design.append(text)
            return
        if operation.operation_type == "append_character_behavior":
            character = next(
                item for item in state.characters if item.character_id == operation.target_id
            )
            value = str(operation.value)
            if value not in character.behavior_notes:
                character.behavior_notes.append(value)

    def _dedupe_operations(
        self,
        operations: list[CorrectionOperation],
    ) -> tuple[list[CorrectionOperation], int]:
        seen: set[tuple[str, str, str, str]] = set()
        unique = []
        for operation in operations:
            key = (
                operation.operation_type,
                operation.target_id,
                operation.field_path,
                str(operation.value),
            )
            if key in seen:
                continue
            seen.add(key)
            unique.append(operation)
        return unique, len(operations) - len(unique)

    def _mark_plan_applied(self, state: ProjectState, plan_id: str) -> None:
        for plan in state.correction_plans:
            if plan.plan_id == plan_id:
                plan.status = "applied"

    def _plan_issue_ids(self, state: ProjectState, plan_id: str) -> list[str]:
        for plan in state.correction_plans:
            if plan.plan_id == plan_id:
                return plan.target_issue_ids
        return []

    def _append(self, current: str, note: str) -> str:
        if not note:
            return current
        if note in current:
            return current
        return f"{current} {note}".strip()

    def _append_comma_list(self, current: str, note: str) -> str:
        existing = [part.strip() for part in current.split(",") if part.strip()]
        additions = [part.strip() for part in note.split(",") if part.strip()]
        for addition in additions:
            if addition not in existing:
                existing.append(addition)
        return ", ".join(existing)

    def _explanation(
        self,
        before: ProjectState,
        after: ProjectState,
        patches: list[CorrectionPatch],
    ) -> str:
        return (
            f"Structured redesign from v{before.version} to v{after.version} using "
            f"{len(patches)} correction patches."
        )
