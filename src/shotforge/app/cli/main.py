from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from shotforge.config import get_settings
from shotforge.core.capability_catalog import build_capability_catalog
from shotforge.core.harness_audit import build_harness_audit
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
def audit(
    package_json: Annotated[Path, typer.Argument(help="Path to a generated package.json file.")]
) -> None:
    state = ProjectState.model_validate_json(package_json.read_text(encoding="utf-8"))
    report = build_harness_audit(state)

    console.print(f"[bold]ShotForge Harness Audit[/bold] {report['run_id']}")
    readiness = report.get("readiness") or {}
    solution = report.get("solution") or {}
    policies = report.get("policies") or {}

    summary = Table(title="Run Evidence")
    summary.add_column("Area")
    summary.add_column("Value", overflow="fold")
    summary.add_row("Version", str(report["version"]))
    summary.add_row("Readiness", str(readiness.get("overall_status", "n/a")))
    summary.add_row("Industry", str(solution.get("industry", "n/a")))
    summary.add_row("Scenario", str(solution.get("scenario", "n/a")))
    summary.add_row("Knowledge assets", ", ".join(solution.get("knowledge_assets", [])) or "n/a")
    summary.add_row("MCP tools", ", ".join(policies.get("mcp_tool_names", [])) or "n/a")
    console.print(summary)

    contexts = Table(title="Agent Contexts")
    contexts.add_column("Agent")
    contexts.add_column("Role", overflow="fold")
    contexts.add_column("Sources")
    contexts.add_column("Chars")
    for item in report["contexts"]:
        agent_spec = item.get("metadata", {}).get("agent_spec", {})
        contexts.add_row(
            item["agent_name"],
            str(agent_spec.get("role", "")),
            str(item["source_count"]),
            str(item["char_count"]),
        )
    console.print(contexts)

    tools = Table(title="Tool Calls")
    tools.add_column("Tool")
    tools.add_column("Status")
    tools.add_column("Scope")
    for item in report["tool_calls"]:
        tools.add_row(item["tool_name"], item["status"], item["permission_scope"])
    console.print(tools)

    tool_plans = Table(title="Tool Orchestration")
    tool_plans.add_column("Requested")
    tool_plans.add_column("Selected")
    tool_plans.add_column("Status")
    tool_plans.add_column("Schema")
    tool_plans.add_column("Fallback")
    for item in report.get("tool_orchestration", []):
        tool_plans.add_row(
            item["requested_tool"],
            item["selected_tool"],
            item["status"],
            item["schema_status"],
            str(item["fallback_used"]),
        )
    console.print(tool_plans)

    transitions = Table(title="State Transitions")
    transitions.add_column("Agent")
    transitions.add_column("Status")
    transitions.add_column("Changed Fields", overflow="fold")
    transitions.add_column("Issues", overflow="fold")
    for item in report["state_transitions"]:
        transitions.add_row(
            item["agent_name"],
            item["invariant_status"],
            ", ".join(item["changed_fields"]) or "none",
            ", ".join(item["invariant_issues"]) or "none",
        )
    console.print(transitions)

    contracts = Table(title="Agent Contracts")
    contracts.add_column("Agent")
    contracts.add_column("Pre")
    contracts.add_column("Post")
    contracts.add_column("Missing", overflow="fold")
    for item in report.get("agent_contracts", []):
        missing = ", ".join(item.get("missing_inputs", []) + item.get("missing_outputs", []))
        contracts.add_row(
            item["agent_name"],
            item["precondition_status"],
            item["postcondition_status"],
            missing or "none",
        )
    console.print(contracts)

    decisions = Table(title="Workflow Decisions")
    decisions.add_column("Agent")
    decisions.add_column("Decision")
    decisions.add_column("Next")
    decisions.add_column("Reason", overflow="fold")
    for item in report.get("workflow_decisions", []):
        decisions.add_row(
            item["agent_name"],
            item["decision"],
            str(item.get("next_agent") or "none"),
            item.get("reason", ""),
        )
    console.print(decisions)


@app.command()
def capabilities() -> None:
    catalog = build_capability_catalog()
    console.print("[bold]ShotForge Capability Catalog[/bold]")

    summary = Table(title="Summary")
    summary.add_column("Area")
    summary.add_column("Count")
    summary.add_row("Agents", str(len(catalog["agents"]["specs"])))
    summary.add_row("Generator providers", str(len(catalog["generator_providers"])))
    summary.add_row("LLM providers", str(len(catalog["llm_providers"])))
    summary.add_row("Playbooks", str(len(catalog["playbooks"])))
    summary.add_row("Export formats", str(len(catalog["export_formats"])))
    console.print(summary)

    providers = Table(title="Generator Providers")
    providers.add_column("Provider")
    providers.add_column("Available")
    providers.add_column("Real Generation")
    for item in catalog["generator_providers"]:
        providers.add_row(
            item["provider_id"],
            str(item["available"]),
            str(item["supports_real_generation"]),
        )
    console.print(providers)

    routes = Table(title="API Routes")
    routes.add_column("Route")
    for route in catalog["api_routes"]:
        routes.add_row(route)
    console.print(routes)


@app.command()
def doctor() -> None:
    settings = get_settings()
    table = Table(title="ShotForge Doctor")
    table.add_column("Check")
    table.add_column("Value", overflow="fold")
    table.add_column("Status")
    checks = {
        "storage_root": settings.storage_root,
        "runs_dir": settings.runs_dir,
        "versions_dir": settings.versions_dir,
        "knowledge_base_path": settings.knowledge_base_path,
        "memory_store_path": settings.memory_store_path,
    }
    for name, path in checks.items():
        exists = path.exists()
        table.add_row(name, str(path), "ok" if exists or name.endswith("_path") else "missing")
    console.print(table)


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
