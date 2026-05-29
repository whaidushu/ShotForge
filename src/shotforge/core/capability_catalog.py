from __future__ import annotations

from typing import Any

from shotforge.agents import build_default_agent_catalog
from shotforge.core.solution_playbook import SolutionPlaybookStore
from shotforge.generators import build_generator_catalog
from shotforge.llm.registry import build_llm_catalog


def build_capability_catalog() -> dict[str, Any]:
    generator_catalog = build_generator_catalog()
    llm_catalog = build_llm_catalog()
    playbooks = SolutionPlaybookStore().load()
    agent_catalog = build_default_agent_catalog()

    return {
        "agents": {
            "specs": [spec.model_dump(mode="json") for spec in agent_catalog.list()],
            "dependency_edges": agent_catalog.dependency_edges(),
        },
        "agent_harness": {
            "state_management": "ProjectState",
            "context_engineering": "ContextBuilder",
            "tool_orchestration": "SkillRegistry",
            "runtime": "AgentHarnessRuntime",
            "trace": "TraceLog",
            "versioning": "VersionManager",
        },
        "infra": {
            "mcp": [
                "knowledge.search",
                "runs.list",
                "runs.get_package",
                "runs.get_harness_audit",
            ],
            "sandbox": ["dry_run", "allowlisted_commands", "timeout", "working_dir"],
            "memory": ["jsonl_store", "tag_search", "source_run_id"],
            "knowledge_base": ["packaged_playbooks", "rubrics", "prompt_rules"],
        },
        "generator_providers": [
            _generator_provider_item(generator_catalog, provider_id)
            for provider_id in generator_catalog.list(available_only=False)
        ],
        "llm_providers": [
            {
                "model_name": model_name,
                "available": llm_catalog.is_available(model_name),
                "cost_mode": llm_catalog.get(model_name, require_available=False).cost_mode.value,
            }
            for model_name in llm_catalog.list(available_only=False)
        ],
        "playbooks": [playbook.model_dump(mode="json") for playbook in playbooks],
        "export_formats": [
            "json",
            "csv",
            "markdown",
            "manifest",
            "trace",
            "run_summary",
            "evaluation_csv",
        ],
        "api_routes": [
            "POST /api/runs",
            "GET /api/runs/{run_id}",
            "GET /api/runs/{run_id}/harness",
            "GET /api/runs/{run_id}/readiness",
            "GET /api/runs/{run_id}/versions",
            "GET /api/runs/{run_id}/export/{format}",
            "GET /api/capabilities",
            "GET /api/health",
        ],
    }


def _generator_provider_item(catalog, provider_id: str) -> dict[str, Any]:
    provider = catalog.get(provider_id, require_available=False)
    return {
        "provider_id": provider.provider_id,
        "display_name": provider.display_name,
        "available": catalog.is_available(provider_id),
        "supports_real_generation": provider.supports_real_generation(),
        "capabilities": provider.capabilities().model_dump(mode="json"),
    }
