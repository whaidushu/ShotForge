from __future__ import annotations

import csv
from pathlib import Path

from shotforge.core.project_state import ExportArtifact, ProjectState


def export_evaluation_csv(state: ProjectState, run_dir: Path) -> Path:
    path = run_dir / "evaluation.csv"
    fieldnames = [
        "evaluation_id",
        "overall_score",
        "dimension_id",
        "dimension_label",
        "dimension_score",
        "issue_id",
        "severity",
        "shot_id",
        "correction_type",
        "description",
        "suspected_cause",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for report in state.evaluation_reports:
            if report.issues:
                for issue in report.issues:
                    dimension_score = next(
                        (
                            item.score
                            for item in report.score_card.dimension_scores
                            if item.dimension_id == issue.dimension_id
                        ),
                        "",
                    )
                    writer.writerow(
                        {
                            "evaluation_id": report.evaluation_id,
                            "overall_score": report.score_card.overall_score,
                            "dimension_id": issue.dimension_id,
                            "dimension_label": issue.dimension_label,
                            "dimension_score": dimension_score,
                            "issue_id": issue.issue_id,
                            "severity": issue.severity,
                            "shot_id": issue.shot_id,
                            "correction_type": issue.correction_type,
                            "description": issue.description,
                            "suspected_cause": issue.suspected_cause,
                        }
                    )
            else:
                writer.writerow(
                    {
                        "evaluation_id": report.evaluation_id,
                        "overall_score": report.score_card.overall_score,
                    }
                )
    state.exports = [item for item in state.exports if item.format != "evaluation_csv"]
    state.exports.append(ExportArtifact(format="evaluation_csv", path=str(path)))
    state.touch()
    return path
