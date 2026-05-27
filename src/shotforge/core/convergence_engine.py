from __future__ import annotations

from dataclasses import dataclass

from shotforge.core.project_state import ConvergenceStep, ProjectState


@dataclass(frozen=True)
class StopCondition:
    reason: str
    should_stop: bool = False


@dataclass(frozen=True)
class ConvergencePolicy:
    max_iterations: int = 3
    min_delta: float = 0.005
    stop_on_unchanged: bool = True
    stop_on_regression: bool = False
    stop_on_score_plateau: bool = False
    stop_when_all_tracked_issues_resolved: bool = False


class ConvergenceEngine:
    _MEANINGFUL_FIELD_PREFIXES = (
        "characters[",
        "scenes[",
        "shots[",
        "prompt_package.prompts[",
        "audio_cues[",
    )

    def __init__(
        self,
        max_iterations: int = 3,
        min_delta: float = 0.005,
        stop_on_regression: bool = False,
        use_early_stop: bool = False,
        policy: ConvergencePolicy | None = None,
    ):
        self.policy = policy or ConvergencePolicy(
            max_iterations=max_iterations,
            min_delta=min_delta,
            stop_on_regression=stop_on_regression,
            stop_on_score_plateau=use_early_stop,
            stop_when_all_tracked_issues_resolved=use_early_stop,
        )

    def evaluate_stop_condition(self, state: ProjectState, iteration_index: int) -> StopCondition:
        if not state.score_deltas or not state.regression_checks:
            return StopCondition(reason="no_re_evaluation_yet", should_stop=False)
        latest_delta = state.score_deltas[-1]
        latest_regression = state.regression_checks[-1]
        if self.policy.stop_on_unchanged and not self._has_meaningful_design_changes(state):
            return StopCondition(reason="design_package_unchanged", should_stop=True)
        if iteration_index >= self.policy.max_iterations:
            return StopCondition(reason="selected_iterations_reached", should_stop=True)
        if self.policy.stop_on_regression and latest_regression.status == "regressed":
            return StopCondition(reason="regression_detected", should_stop=True)
        if self.policy.stop_on_score_plateau and abs(latest_delta.overall_delta) < self.policy.min_delta:
            return StopCondition(reason="score_delta_below_threshold", should_stop=True)
        if (
            self.policy.stop_when_all_tracked_issues_resolved
            and not latest_regression.remaining_issue_ids
            and not latest_regression.new_issue_ids
        ):
            return StopCondition(reason="all_tracked_issues_resolved", should_stop=True)
        return StopCondition(reason="continue", should_stop=False)

    def record_step(self, state: ProjectState, stop_condition: StopCondition) -> ConvergenceStep:
        score_delta = state.score_deltas[-1]
        regression_check = state.regression_checks[-1]
        step = ConvergenceStep(
            from_version=score_delta.from_version,
            to_version=score_delta.to_version,
            score_delta_id=score_delta.score_delta_id,
            regression_check_id=regression_check.regression_check_id,
            overall_delta=score_delta.overall_delta,
            status=regression_check.status,
            stop_reason=stop_condition.reason if stop_condition.should_stop else "",
            metadata={
                "resolved_issue_count": len(regression_check.resolved_issue_ids),
                "remaining_issue_count": len(regression_check.remaining_issue_ids),
                "new_issue_count": len(regression_check.new_issue_ids),
                "meaningful_change_count": self._meaningful_change_count(state),
            },
        )
        state.convergence_steps.append(step)
        state.metadata["convergence_summary"] = {
            "latest_version": state.version,
            "step_count": len(state.convergence_steps),
            "latest_status": regression_check.status,
            "latest_overall_delta": score_delta.overall_delta,
            "stop_reason": step.stop_reason,
            "policy": {
                "max_iterations": self.policy.max_iterations,
                "min_delta": self.policy.min_delta,
                "stop_on_unchanged": self.policy.stop_on_unchanged,
                "stop_on_regression": self.policy.stop_on_regression,
                "stop_on_score_plateau": self.policy.stop_on_score_plateau,
                "stop_when_all_tracked_issues_resolved": self.policy.stop_when_all_tracked_issues_resolved,
            },
        }
        state.touch()
        return step

    def _has_meaningful_design_changes(self, state: ProjectState) -> bool:
        if not state.version_diffs:
            return True
        latest_diff = state.version_diffs[-1]
        if latest_diff.changed_shots or latest_diff.changed_prompts or latest_diff.changed_audio_cues:
            return True
        return any(
            change.path.startswith(self._MEANINGFUL_FIELD_PREFIXES)
            for change in latest_diff.field_changes
        )

    def _meaningful_change_count(self, state: ProjectState) -> int:
        if not state.version_diffs:
            return 0
        latest_diff = state.version_diffs[-1]
        paths = {
            change.path
            for change in latest_diff.field_changes
            if change.path.startswith(self._MEANINGFUL_FIELD_PREFIXES)
        }
        paths.update(f"shots[{shot_id}]" for shot_id in latest_diff.changed_shots)
        paths.update(f"prompt_package.prompts[{shot_id}]" for shot_id in latest_diff.changed_prompts)
        paths.update(f"audio_cues[{shot_id}]" for shot_id in latest_diff.changed_audio_cues)
        return len(paths)
