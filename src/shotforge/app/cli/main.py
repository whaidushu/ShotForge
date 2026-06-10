from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from shotforge.comfyui import build_workflow_registry, discover_local_workflows
from shotforge.app.services.provider_service import ProviderService
from shotforge.config import get_settings
from shotforge.core.capability_catalog import build_capability_catalog
from shotforge.core.harness_audit import build_harness_audit
from shotforge.core.project_state import OutputLanguage, ProjectState
from shotforge.exporters import ExportManager
from shotforge.workflows.evaluation_workflow import load_project_state, run_evaluation_pipeline
from shotforge.workflows.effect_demo_workflow import DEFAULT_CASE_ID, list_effect_cases, run_effect_demo
from shotforge.workflows.design_workflow import run_design_pipeline
from shotforge.workflows.full_loop_workflow import run_full_loop_pipeline
from shotforge.workflows.iterative_redesign_workflow import run_iterative_redesign

app = typer.Typer(help="ShotForge evaluation-driven video workflow runtime")
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
        exporter.export_all(state)
    _print_summary(state)


@app.command("effect-demo")
def effect_demo(
    case_id: Annotated[
        str,
        typer.Argument(help="Effect demo case id."),
    ] = DEFAULT_CASE_ID,
    language: Annotated[
        OutputLanguage,
        typer.Option("--language", "-l", help="Output language: zh or en."),
    ] = "en",
    generator: Annotated[
        str,
        typer.Option("--generator", help="Generator provider id."),
    ] = "mock",
    style: Annotated[
        str | None,
        typer.Option("--style", help="Override case visual style."),
    ] = None,
) -> None:
    state = run_effect_demo(
        case_id,
        language=language,
        generator_provider_id=generator,
        style=style,
    )
    effect = state.metadata.get("effect_demo", {})
    comparison = effect.get("comparison", {})
    console.print(f"[bold]Effect demo[/bold] {effect.get('case_id', case_id)}")
    console.print(f"Run: {state.run_id}")
    console.print(
        f"Score: v1={comparison.get('v1_score')} "
        f"v2={comparison.get('v2_score')} "
        f"v3={comparison.get('v3_score')} "
        f"structured_delta={comparison.get('structured_delta')} "
        f"compensation_delta={comparison.get('compensation_delta')} "
        f"total_delta={comparison.get('score_delta')}"
    )
    paths = effect.get("paths", {})
    if paths.get("comparison_markdown"):
        console.print(f"Report: {Path(paths['comparison_markdown']).resolve()}")
    _print_summary(state)


@app.command("effect-cases")
def effect_cases() -> None:
    table = Table(title="ShotForge Effect Cases")
    table.add_column("Case")
    table.add_column("Title")
    table.add_column("Duration")
    table.add_column("Path", overflow="fold")
    for item in list_effect_cases():
        table.add_row(
            item["case_id"],
            item["title"],
            f"{item['duration_seconds']}s",
            item["path"],
        )
    console.print(table)


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

    console.print(f"[bold]ShotForge Runtime Evidence[/bold] {report['run_id']}")
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

    memory = Table(title="Memory Governance")
    memory.add_column("Agent")
    memory.add_column("Selected")
    memory.add_column("Promotion")
    memory.add_column("Reasons", overflow="fold")
    for item in report.get("memory_selections", []):
        memory.add_row(
            item["agent_name"],
            str(len(item.get("selected_memory_ids", []))),
            item.get("promotion_decision", "n/a"),
            ", ".join(item.get("reasons", [])) or "none",
        )
    console.print(memory)

    sandbox = Table(title="Sandbox Strategy")
    sandbox.add_column("Profile")
    sandbox.add_column("Decision")
    sandbox.add_column("Network")
    sandbox.add_column("Writes")
    sandbox.add_column("Reason", overflow="fold")
    for item in report.get("sandbox_policy_records", []):
        sandbox.add_row(
            item.get("profile_id", ""),
            item.get("decision", ""),
            str(item.get("allow_network", "")),
            str(item.get("allow_file_write", "")),
            item.get("reason", ""),
        )
    console.print(sandbox)

    mcp = Table(title="MCP Access")
    mcp.add_column("Operation")
    mcp.add_column("Target", overflow="fold")
    mcp.add_column("Status")
    mcp.add_column("Reason", overflow="fold")
    for item in report.get("mcp_access_records", []):
        mcp.add_row(
            item.get("operation", ""),
            item.get("target", "") or "n/a",
            item.get("status", ""),
            item.get("reason", ""),
        )
    console.print(mcp)


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


@app.command("comfyui-workflows")
def comfyui_workflows(
    root: Annotated[
        Path | None,
        typer.Option("--root", help="Optional local ComfyUI workflows directory."),
    ] = None,
) -> None:
    settings = get_settings()
    workflow_root = root or (Path(settings.comfyui_workflows_dir) if settings.comfyui_workflows_dir else None)
    registry = build_workflow_registry()
    described = registry.describe()
    described_ids = {item.workflow_id for item in described}

    table = Table(title="ComfyUI Workflows")
    table.add_column("Workflow ID")
    table.add_column("Source")
    table.add_column("Format")
    table.add_column("Callable")
    table.add_column("Nodes")
    table.add_column("Path", overflow="fold")
    for item in described:
        table.add_row(
            item.workflow_id,
            item.source,
            item.format,
            str(item.callable),
            str(item.node_count),
            str(item.path or ""),
        )

    if workflow_root:
        for item in discover_local_workflows(workflow_root):
            if item.workflow_id in described_ids:
                continue
            table.add_row(
                item.workflow_id,
                item.source,
                item.format,
                str(item.callable),
                str(item.node_count),
                str(item.path or ""),
            )
    console.print(table)
    console.print("Use API-format workflows as SHOTFORGE_COMFYUI_WORKFLOW_ID, or file:<path>.")


@app.command()
def doctor(
    deep: Annotated[
        bool,
        typer.Option("--deep/--basic", help="Run provider preflight checks as well as storage checks."),
    ] = False,
) -> None:
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
    if not deep:
        console.print("Run `shotforge doctor --deep` to check LLM, ComfyUI, workflow, and VLM readiness.")
        return

    provider_service = ProviderService()
    profile = provider_service.default_provider_profile()
    preflight = provider_service.preflight_provider_profile(profile)
    provider_table = Table(title=f"Provider Preflight: {profile.name}")
    provider_table.add_column("Check")
    provider_table.add_column("Status")
    provider_table.add_column("Detail", overflow="fold")
    for check in preflight["checks"]:
        provider_table.add_row(check["label"], check["status"], check["detail"])
    console.print(provider_table)

    workflow_table = Table(title="ComfyUI Workflow Discovery")
    workflow_table.add_column("Workflow")
    workflow_table.add_column("Source")
    workflow_table.add_column("Callable")
    workflow_table.add_column("Path", overflow="fold")
    workflow_status = provider_service.comfyui_workflow_status(profile.comfyui_workflows_dir)
    for workflow in workflow_status["workflows"][:12]:
        workflow_table.add_row(
            workflow["workflow_id"],
            workflow["source"],
            str(workflow["callable"]),
            workflow["path"],
        )
    console.print(workflow_table)
    console.print(f"Overall provider status: {preflight['status']}")


@app.command("web")
def web(
    host: Annotated[str, typer.Option("--host", help="Host interface to bind.")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", help="Port to bind.")] = 8000,
    reload: Annotated[
        bool,
        typer.Option("--reload/--no-reload", help="Reload the web app when source files change."),
    ] = False,
) -> None:
    import uvicorn

    console.print(f"Starting ShotForge Web at http://{host}:{port}")
    uvicorn.run("shotforge.app.web.app:app", host=host, port=port, reload=reload)


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
