from __future__ import annotations

from functools import lru_cache
import json
from importlib.resources import files

from shotforge.core.project_state import CorrectionOperation, CorrectionPlan, Issue, ProjectState
from shotforge.i18n import get_translator


def target_shot_ids(state: ProjectState, plan: CorrectionPlan) -> list[str]:
    shot_ids = plan.metadata.get("shot_ids", [])
    if isinstance(shot_ids, list) and shot_ids:
        return [str(shot_id) for shot_id in shot_ids]
    issues = target_issues(state, plan)
    inferred = sorted({issue.shot_id for issue in issues if issue.shot_id})
    return inferred or [shot.shot_id for shot in state.shots[:1]]


def target_issues(state: ProjectState, plan: CorrectionPlan) -> list[Issue]:
    wanted = set(plan.target_issue_ids)
    return [issue for issue in state.issue_history if issue.issue_id in wanted]


def localized_note(
    language: str,
    key: str,
    plan: CorrectionPlan,
    issues: list[Issue],
) -> str:
    issue_summary = "; ".join(issue.description for issue in issues[:3])
    translator = get_translator()
    return _strategy_text(language, key) or translator.t(
        language,
        key,
        strategy=plan.correction_strategy,
        issues=issue_summary or "-",
    )


def operation(
    operation_type: str,
    target_id: str,
    field_path: str,
    value: str | list[str],
    rationale: str,
) -> CorrectionOperation:
    return CorrectionOperation(
        operation_type=operation_type,
        target_id=target_id,
        field_path=field_path,
        value=value,
        rationale=rationale,
    )


@lru_cache(maxsize=1)
def _strategy_book() -> dict:
    path = files("shotforge.knowledge").joinpath("correction_strategies.json")
    return json.loads(path.read_text(encoding="utf-8"))


def _strategy_text(language: str, key: str) -> str:
    prefix = "agents.correction."
    if not key.startswith(prefix):
        return ""
    parts = key.removeprefix(prefix).split(".")
    if len(parts) != 2:
        return ""
    correction_type, note_key = parts
    entry = _strategy_book().get("strategies", {}).get(correction_type, {})
    value = entry.get("notes", {}).get(note_key, {}).get(language)
    if isinstance(value, str):
        return value
    return ""
