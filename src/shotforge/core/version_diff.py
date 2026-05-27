from __future__ import annotations

from typing import Any

from shotforge.core.project_state import FieldChange, ProjectState, VersionDiff


class VersionDiffBuilder:
    def build(
        self,
        before: ProjectState,
        after: ProjectState,
        explanation: str = "",
    ) -> VersionDiff:
        field_changes = self._field_changes(before, after)
        return VersionDiff(
            from_version=before.version,
            to_version=after.version,
            changed_shots=self._changed_shots(before, after),
            changed_prompts=self._changed_prompts(before, after),
            changed_audio_cues=self._changed_audio_cues(before, after),
            resolved_issues=self._resolved_issues(before, after),
            new_issues=self._new_issues(before, after),
            field_changes=field_changes,
            explanation=explanation or f"Diff from v{before.version} to v{after.version}.",
            metadata={"field_change_count": len(field_changes)},
        )

    def _changed_shots(self, before: ProjectState, after: ProjectState) -> list[str]:
        before_map = {item.shot_id: item.model_dump(mode="json") for item in before.shots}
        after_map = {item.shot_id: item.model_dump(mode="json") for item in after.shots}
        return self._changed_keys(before_map, after_map)

    def _changed_prompts(self, before: ProjectState, after: ProjectState) -> list[str]:
        before_map = {
            item.shot_id: item.model_dump(mode="json") for item in before.prompt_package.prompts
        }
        after_map = {item.shot_id: item.model_dump(mode="json") for item in after.prompt_package.prompts}
        return self._changed_keys(before_map, after_map)

    def _changed_audio_cues(self, before: ProjectState, after: ProjectState) -> list[str]:
        before_map = {item.shot_id: item.model_dump(mode="json") for item in before.audio_cues}
        after_map = {item.shot_id: item.model_dump(mode="json") for item in after.audio_cues}
        return self._changed_keys(before_map, after_map)

    def _resolved_issues(self, before: ProjectState, after: ProjectState) -> list[str]:
        before_ids = {item.issue_id for item in before.issue_history}
        after_ids = {item.issue_id for item in after.issue_history}
        return sorted(before_ids - after_ids)

    def _new_issues(self, before: ProjectState, after: ProjectState) -> list[str]:
        before_ids = {item.issue_id for item in before.issue_history}
        after_ids = {item.issue_id for item in after.issue_history}
        return sorted(after_ids - before_ids)

    def _field_changes(self, before: ProjectState, after: ProjectState) -> list[FieldChange]:
        changes: list[FieldChange] = []
        changes.extend(self._character_field_changes(before, after))
        changes.extend(self._scene_field_changes(before, after))
        changes.extend(self._shot_field_changes(before, after))
        changes.extend(self._prompt_field_changes(before, after))
        changes.extend(self._audio_field_changes(before, after))
        if changes:
            return changes
        before_data = before.model_dump(mode="json")
        after_data = after.model_dump(mode="json")
        for key in ["version", "issue_history", "correction_plans", "correction_patches", "metadata"]:
            if before_data.get(key) != after_data.get(key):
                changes.append(self._field_change(key, before_data.get(key), after_data.get(key)))
        return changes

    def _character_field_changes(self, before: ProjectState, after: ProjectState) -> list[FieldChange]:
        before_map = {item.character_id: item for item in before.characters}
        after_map = {item.character_id: item for item in after.characters}
        changes: list[FieldChange] = []
        for character_id in sorted(set(before_map) | set(after_map)):
            before_character = before_map.get(character_id)
            after_character = after_map.get(character_id)
            if before_character is None or after_character is None:
                changes.append(
                    self._field_change(
                        f"characters[{character_id}]",
                        before_character.model_dump(mode="json") if before_character else None,
                        after_character.model_dump(mode="json") if after_character else None,
                    )
                )
                continue
            for field in ["name", "role", "visual_traits", "behavior_notes"]:
                before_value = getattr(before_character, field)
                after_value = getattr(after_character, field)
                if before_value != after_value:
                    changes.append(
                        self._field_change(
                            f"characters[{character_id}].{field}",
                            before_value,
                            after_value,
                        )
                    )
        return changes

    def _scene_field_changes(self, before: ProjectState, after: ProjectState) -> list[FieldChange]:
        before_map = {item.scene_id: item for item in before.scenes}
        after_map = {item.scene_id: item for item in after.scenes}
        changes: list[FieldChange] = []
        for scene_id in sorted(set(before_map) | set(after_map)):
            before_scene = before_map.get(scene_id)
            after_scene = after_map.get(scene_id)
            if before_scene is None or after_scene is None:
                changes.append(
                    self._field_change(
                        f"scenes[{scene_id}]",
                        before_scene.model_dump(mode="json") if before_scene else None,
                        after_scene.model_dump(mode="json") if after_scene else None,
                    )
                )
                continue
            for field in ["title", "description", "emotional_goal", "key_visuals"]:
                before_value = getattr(before_scene, field)
                after_value = getattr(after_scene, field)
                if before_value != after_value:
                    changes.append(
                        self._field_change(f"scenes[{scene_id}].{field}", before_value, after_value)
                    )
        return changes

    def _shot_field_changes(self, before: ProjectState, after: ProjectState) -> list[FieldChange]:
        before_map = {item.shot_id: item for item in before.shots}
        after_map = {item.shot_id: item for item in after.shots}
        changes: list[FieldChange] = []
        for shot_id in sorted(set(before_map) | set(after_map)):
            before_shot = before_map.get(shot_id)
            after_shot = after_map.get(shot_id)
            if before_shot is None or after_shot is None:
                changes.append(
                    self._field_change(
                        f"shots[{shot_id}]",
                        before_shot.model_dump(mode="json") if before_shot else None,
                        after_shot.model_dump(mode="json") if after_shot else None,
                    )
                )
                continue
            for field in ["title", "description", "shot_type", "key_visuals"]:
                before_value = getattr(before_shot, field)
                after_value = getattr(after_shot, field)
                if before_value != after_value:
                    changes.append(
                        self._field_change(f"shots[{shot_id}].{field}", before_value, after_value)
                    )
            if before_shot.motion or after_shot.motion:
                before_motion = before_shot.motion.model_dump(mode="json") if before_shot.motion else {}
                after_motion = after_shot.motion.model_dump(mode="json") if after_shot.motion else {}
                for field in ["camera", "subject_motion", "transition", "pacing"]:
                    if before_motion.get(field) != after_motion.get(field):
                        changes.append(
                            self._field_change(
                                f"shots[{shot_id}].motion.{field}",
                                before_motion.get(field),
                                after_motion.get(field),
                            )
                        )
        return changes

    def _prompt_field_changes(self, before: ProjectState, after: ProjectState) -> list[FieldChange]:
        before_map = {item.shot_id: item for item in before.prompt_package.prompts}
        after_map = {item.shot_id: item for item in after.prompt_package.prompts}
        changes: list[FieldChange] = []
        for shot_id in sorted(set(before_map) | set(after_map)):
            before_prompt = before_map.get(shot_id)
            after_prompt = after_map.get(shot_id)
            if before_prompt is None or after_prompt is None:
                changes.append(
                    self._field_change(
                        f"prompt_package.prompts[{shot_id}]",
                        before_prompt.model_dump(mode="json") if before_prompt else None,
                        after_prompt.model_dump(mode="json") if after_prompt else None,
                    )
                )
                continue
            for field in ["prompt", "structured_template", "negative_prompt", "parameters"]:
                before_value = getattr(before_prompt, field)
                after_value = getattr(after_prompt, field)
                if before_value != after_value:
                    changes.append(
                        self._field_change(
                            f"prompt_package.prompts[{shot_id}].{field}",
                            before_value,
                            after_value,
                        )
                    )
        return changes

    def _audio_field_changes(self, before: ProjectState, after: ProjectState) -> list[FieldChange]:
        before_map = {item.shot_id: item for item in before.audio_cues}
        after_map = {item.shot_id: item for item in after.audio_cues}
        changes: list[FieldChange] = []
        for shot_id in sorted(set(before_map) | set(after_map)):
            before_cue = before_map.get(shot_id)
            after_cue = after_map.get(shot_id)
            if before_cue is None or after_cue is None:
                changes.append(
                    self._field_change(
                        f"audio_cues[{shot_id}]",
                        before_cue.model_dump(mode="json") if before_cue else None,
                        after_cue.model_dump(mode="json") if after_cue else None,
                    )
                )
                continue
            for field in ["music", "sound_design", "voiceover"]:
                before_value = getattr(before_cue, field)
                after_value = getattr(after_cue, field)
                if before_value != after_value:
                    changes.append(
                        self._field_change(f"audio_cues[{shot_id}].{field}", before_value, after_value)
                    )
        return changes

    def _field_change(self, path: str, before: Any, after: Any) -> FieldChange:
        if before is None and after is not None:
            change_type = "added"
        elif before is not None and after is None:
            change_type = "removed"
        else:
            change_type = "modified"
        return FieldChange(path=path, before=before, after=after, change_type=change_type)

    def _changed_keys(self, before: dict[str, Any], after: dict[str, Any]) -> list[str]:
        return sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key))
