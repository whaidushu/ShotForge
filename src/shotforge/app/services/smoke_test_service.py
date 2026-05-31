from __future__ import annotations

import os
from typing import Any

from shotforge.app.services.provider_runtime import ProviderRuntimeService
from shotforge.config import get_settings
from shotforge.exporters import ExportManager
from shotforge.workflows.full_loop_workflow import run_full_loop_pipeline


class SmokeTestService:
    def __init__(self, runtime_service: ProviderRuntimeService | None = None) -> None:
        self.runtime_service = runtime_service or ProviderRuntimeService()

    def run_internal_test_chain(self) -> dict[str, Any]:
        snapshot = {key: os.environ.get(key) for key in self.runtime_service.ENV_KEYS}
        try:
            os.environ["SHOTFORGE_LLM_PROVIDER"] = "mock"
            os.environ["SHOTFORGE_LLM_MODEL"] = "mock"
            os.environ["SHOTFORGE_EVALUATOR_MODE"] = "mock"
            get_settings.cache_clear()
            state = run_full_loop_pipeline(
                idea="Internal deployment smoke test for ShotForge pipeline",
                style="cinematic",
                duration_seconds=6,
                language="en",
                rubric_id="baseline_v1",
                generator_provider_id="mock",
            )
            ExportManager().export_all(state)
            return {
                "status": "passed",
                "failed": 0,
                "warnings": 0,
                "checks": [
                    {
                        "check_id": "internal_pipeline",
                        "label": "Internal pipeline",
                        "status": "passed",
                        "detail": f"Design, generation, evaluation, and export completed: {state.run_id}",
                    }
                ],
                "run_id": state.run_id,
                "run_url": f"/?run_id={state.run_id}&language=en",
            }
        except Exception as exc:
            return {
                "status": "failed",
                "failed": 1,
                "warnings": 0,
                "checks": [
                    {
                        "check_id": "internal_pipeline",
                        "label": "Internal pipeline",
                        "status": "failed",
                        "detail": str(exc),
                    }
                ],
            }
        finally:
            self.runtime_service.restore_env(snapshot)
