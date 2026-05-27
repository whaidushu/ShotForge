from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from shotforge.core.project_state import OutputLanguage, ProjectState
from shotforge.exporters import ExportManager
from shotforge.workflows.evaluation_workflow import load_project_state, run_evaluation_pipeline
from shotforge.workflows.design_workflow import run_design_pipeline
from shotforge.workflows.full_loop_workflow import run_full_loop_pipeline
from shotforge.workflows.iterative_redesign_workflow import run_iterative_redesign

app = typer.Typer(help="ShotForge evaluation-driven agent harness")
console = Console()


def _print_summary(state: ProjectState) -> None:
    table = Table(title=f"ShotForge Run {state.run_id}")
    table.add_column("Shot")
    table.add_column("Title")
    table.add_column("Duration")
    table.add_column("Prompt", overflow="fold")
    for shot in state.shots:
        prompt = next(item for item in state.prompt_package.prompts if item.shot_id == shot.shot_id)
        table.add_row(shot.shot_id, shot.title, f"{shot.duration_seconds}s", prompt.prompt)
    console.print(table)
    console.print("\nExports:")
    for artifact in state.exports:
        console.print(f"- {artifact.format}: {Path(artifact.path).resolve()}")
    if state.evaluation_reports:
        report = state.evaluation_reports[-1]
        console.print(f"\nEvaluation: {report.score_card.overall_score:.2f}")
        for issue in report.issues[:8]:
            console.print(
                f"- [{issue.severity}] {issue.shot_id} {issue.dimension_label} "
                f"({issue.correction_type}): {issue.description}",
                markup=False,
            )


@app.command()
def design(
    idea: Annotated[str, typer.Argument(help="One-line AI video creative idea.")],
    style: Annotated[str, typer.Option("--style", "-s", help="Visual style.")] = "cinematic",
    duration: Annotated[
        int, typer.Option("--duration", "-d", help="Target duration in seconds.")
    ] = 24,
    language: Annotated[
        OutputLanguage,
        typer.Option("--language", "-l", help="Output language: zh or en."),
    ] = "zh",
) -> None:
    state = run_design_pipeline(
        idea=idea,
        style=style,
        duration_seconds=duration,
        language=language,
    )
    _print_summary(state)


@app.command()
def full_loop(
    idea: Annotated[str, typer.Argument(help="One-line AI video creative idea.")],
    style: Annotated[str, typer.Option("--style", "-s", help="Visual style.")] = "cinematic",
    duration: Annotated[
        int, typer.Option("--duration", "-d", help="Target duration in seconds.")
    ] = 24,
    language: Annotated[
        OutputLanguage,
        typer.Option("--language", "-l", help="Output language: zh or en."),
    ] = "zh",
    rubric: Annotated[str, typer.Option("--rubric", help="Evaluation rubric id.")] = "baseline_v1",
    generator: Annotated[
        str,
        typer.Option("--generator", help="Generator provider id."),
    ] = "mock",
    redesign: Annotated[
        bool,
        typer.Option("--redesign/--no-redesign", help="Run V2 iterative redesign after evaluation."),
    ] = False,
    max_iterations: Annotated[
        int,
        typer.Option("--max-iterations", help="Maximum redesign iterations."),
    ] = 3,
) -> None:
    state = run_full_loop_pipeline(
        idea=idea,
        style=style,
        duration_seconds=duration,
        language=language,
        rubric_id=rubric,
        generator_provider_id=generator,
    )
    if redesign:
        state = run_iterative_redesign(
            state,
            max_iterations=max_iterations,
            generator_provider_id=generator,
        )
        exporter = ExportManager()
        exporter.export_json(state)
        exporter.export_markdown(state)
        exporter.export_evaluation_csv(state)
    _print_summary(state)


@app.command()
def evaluate(
    package_json: Annotated[Path, typer.Argument(help="Path to a generated package.json file.")],
    rubric: Annotated[str, typer.Option("--rubric", help="Evaluation rubric id.")] = "baseline_v1",
    generator: Annotated[
        str,
        typer.Option("--generator", help="Generator provider id."),
    ] = "mock",
) -> None:
    state = load_project_state(package_json)
    run_evaluation_pipeline(state, rubric_id=rubric, generator_provider_id=generator, export=True)
    _print_summary(state)


@app.command()
def inspect(
    package_json: Annotated[Path, typer.Argument(help="Path to a generated package.json file.")]
) -> None:
    state = ProjectState.model_validate_json(package_json.read_text(encoding="utf-8"))
    _print_summary(state)


@app.command()
def run(
    idea: Annotated[str, typer.Argument(help="One-line AI video creative idea.")],
    style: Annotated[str, typer.Option("--style", "-s", help="Visual style.")] = "cinematic",
    duration: Annotated[
        int, typer.Option("--duration", "-d", help="Target duration in seconds.")
    ] = 24,
    language: Annotated[
        OutputLanguage,
        typer.Option("--language", "-l", help="Output language: zh or en."),
    ] = "zh",
) -> None:
    design(idea=idea, style=style, duration=duration, language=language)

__all__ = ["app"]
