from __future__ import annotations

from shotforge.core.project_state import (
    runtime_language,
    GeneratedResult,
    ProjectState,
    VerificationCheck,
    VerificationReport,
)
from shotforge.core.trace_log import TraceLog


class VerificationAgent:
    def verify(self, state: ProjectState, generated_result: GeneratedResult) -> VerificationReport:
        with TraceLog(state).span("verification_agent"):
            checks: list[VerificationCheck] = []
            checks.extend(self._shot_coverage_checks(state, generated_result))
            checks.extend(self._prompt_link_checks(state, generated_result))
            checks.extend(self._duration_checks(state, generated_result))
            failed = len([check for check in checks if check.status == "failed"])
            warnings = len([check for check in checks if check.status == "warning"])
            report = VerificationReport(
                version_id=state.version,
                generated_result_id=generated_result.generated_result_id,
                checks=checks,
                summary=self._summary(runtime_language(state), failed, warnings, len(checks)),
                metadata={
                    "failed_count": failed,
                    "warning_count": warnings,
                    "passed_count": len(checks) - failed - warnings,
                },
            )
            state.verification_reports.append(report)
            state.touch()
            return report

    def _shot_coverage_checks(
        self,
        state: ProjectState,
        generated_result: GeneratedResult,
    ) -> list[VerificationCheck]:
        generated_ids = {shot.shot_id for shot in generated_result.shots}
        checks = []
        for shot in state.shots:
            passed = shot.shot_id in generated_ids
            checks.append(
                VerificationCheck(
                    check_id=f"shot_coverage:{shot.shot_id}",
                    label="shot coverage",
                    status="passed" if passed else "failed",
                    evidence=(
                        "generated shot exists"
                        if passed
                        else "generated result is missing the storyboard shot"
                    ),
                    shot_id=shot.shot_id,
                )
            )
        return checks

    def _prompt_link_checks(
        self,
        state: ProjectState,
        generated_result: GeneratedResult,
    ) -> list[VerificationCheck]:
        prompt_ids = {prompt.shot_id for prompt in state.prompt_package.prompts}
        checks = []
        for generated_shot in generated_result.shots:
            passed = generated_shot.prompt_id in prompt_ids
            checks.append(
                VerificationCheck(
                    check_id=f"prompt_link:{generated_shot.shot_id}",
                    label="prompt link",
                    status="passed" if passed else "failed",
                    evidence=(
                        "generated shot links to a prompt"
                        if passed
                        else "generated shot prompt_id has no prompt package match"
                    ),
                    shot_id=generated_shot.shot_id,
                )
            )
        return checks

    def _duration_checks(
        self,
        state: ProjectState,
        generated_result: GeneratedResult,
    ) -> list[VerificationCheck]:
        expected = {shot.shot_id: shot.duration_seconds for shot in state.shots}
        checks = []
        for generated_shot in generated_result.shots:
            expected_duration = expected.get(generated_shot.shot_id)
            passed = expected_duration == generated_shot.duration_seconds
            checks.append(
                VerificationCheck(
                    check_id=f"duration:{generated_shot.shot_id}",
                    label="duration match",
                    status="passed" if passed else "warning",
                    evidence=f"expected={expected_duration}, actual={generated_shot.duration_seconds}",
                    shot_id=generated_shot.shot_id,
                )
            )
        return checks

    def _summary(self, language: str, failed: int, warnings: int, total: int) -> str:
        if language == "zh":
            return f"验证完成：{total} 项检查，{failed} 项失败，{warnings} 项警告。"
        return f"Verification complete: {total} checks, {failed} failed, {warnings} warnings."
