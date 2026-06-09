from __future__ import annotations

import json
from pathlib import Path

from shotforge.core.harness_audit import build_harness_audit
from shotforge.core.project_state import ExportArtifact, ProjectState


def export_manifest(state: ProjectState, run_dir: Path) -> Path:
    path = run_dir / "manifest.json"
    audit = build_harness_audit(state)
    payload = {
        "project_id": state.project_id,
        "run_id": state.run_id,
        "version": state.version,
        "created_at": state.created_at.isoformat(),
        "updated_at": state.updated_at.isoformat(),
        "deliverables": [item.model_dump(mode="json") for item in state.exports],
        "solution": audit["solution"],
        "readiness": {
            "overall_status": audit["readiness"].get("overall_status"),
            "check_count": len(audit["readiness"].get("checks", [])),
            "next_actions": audit["readiness"].get("next_actions", []),
        },
        "audit_api": f"/api/runs/{state.run_id}/harness",
        "package_api": f"/api/runs/{state.run_id}",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _record(state, "manifest", path)
    return path


def export_trace(state: ProjectState, run_dir: Path) -> Path:
    path = run_dir / "trace.json"
    payload = {
        "project_id": state.project_id,
        "run_id": state.run_id,
        "trace_logs": [item.model_dump(mode="json") for item in state.trace_logs],
        "harness_audit": build_harness_audit(state),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _record(state, "trace", path)
    return path


def export_run_summary(state: ProjectState, run_dir: Path) -> Path:
    path = run_dir / "run_summary.md"
    audit = build_harness_audit(state)
    solution = state.solution_architecture
    readiness = state.delivery_readiness
    lines = [
        "# ShotForge Run Summary",
        "",
        f"- Project: `{state.project_id}`",
        f"- Run: `{state.run_id}`",
        f"- Version: `{state.version}`",
        f"- Idea: {state.user_idea}",
        f"- Shots: {len(state.shots)}",
        f"- Exports: {len(state.exports)}",
    ]
    if solution:
        lines.extend(
            [
                "",
                "## Solution",
                "",
                f"- Industry: {solution.industry}",
                f"- Scenario: {solution.scenario}",
                f"- Playbooks: {', '.join(solution.knowledge_assets)}",
                f"- Acceptance criteria: {len(solution.acceptance_criteria)}",
            ]
        )
    if readiness:
        lines.extend(
            [
                "",
                "## Delivery Readiness",
                "",
                f"- Overall status: {readiness.overall_status}",
                f"- Checks: {len(readiness.checks)}",
                f"- Next actions: {len(readiness.next_actions)}",
            ]
        )
        for action in readiness.next_actions:
            lines.append(f"  - {action}")
    lines.extend(
        [
            "",
            "## Harness Evidence",
            "",
            f"- Context snapshots: {len(audit['contexts'])}",
            f"- Tool calls: {len(audit['tool_calls'])}",
            f"- State transitions: {len(audit['state_transitions'])}",
            f"- Agent topology nodes: {len(audit['agent_topology']['nodes'])}",
            f"- Agent topology edges: {len(audit['agent_topology']['edges'])}",
        ]
    )
    lines.extend(
        [
            "",
            "## Audit",
            "",
            f"- Harness API: `/api/runs/{state.run_id}/harness`",
            f"- CLI: `shotforge audit {path.parent / 'package.json'}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    _record(state, "run_summary", path)
    return path


def _record(state: ProjectState, export_format: str, path: Path) -> None:
    state.exports = [item for item in state.exports if item.format != export_format]
    state.exports.append(ExportArtifact(format=export_format, path=str(path)))
    state.touch()
