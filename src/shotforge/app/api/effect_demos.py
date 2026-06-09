from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from shotforge.app.api.schemas import EffectDemoRequest, EffectDemoResponse
from shotforge.app.errors import runtime_error_payload
from shotforge.workflows.effect_demo_workflow import (
    list_effect_cases,
    load_effect_comparison,
    run_effect_demo,
)


def build_effect_demo_router() -> APIRouter:
    router = APIRouter(prefix="/api/effect-demos", tags=["effect-demos"])

    @router.get("")
    def list_cases() -> dict[str, Any]:
        return {"cases": list_effect_cases()}

    @router.post("/{case_id}", response_model=EffectDemoResponse)
    def create_effect_demo(case_id: str, payload: EffectDemoRequest) -> EffectDemoResponse:
        try:
            state = run_effect_demo(
                case_id,
                language=payload.language,
                generator_provider_id=payload.generator_provider_id,
                style=payload.style,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=503, detail=runtime_error_payload(exc)) from exc
        effect_demo = state.metadata.get("effect_demo", {})
        return EffectDemoResponse(
            project_id=state.project_id,
            run_id=state.run_id,
            version=state.version,
            case_id=str(effect_demo.get("case_id", case_id)),
            comparison=effect_demo.get("comparison", {}),
            exports={artifact.format: artifact.path for artifact in state.exports},
            state=state,
        )

    @router.get("/{run_id}/comparison")
    def get_effect_comparison(run_id: str) -> dict[str, Any]:
        try:
            return load_effect_comparison(run_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return router

