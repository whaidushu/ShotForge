from __future__ import annotations

from pydantic import BaseModel, Field

from shotforge.core.project_state import (
    AudioCue,
    CharacterSpec,
    CorrectionPatch,
    CorrectionPlan,
    CreativeIntent,
    DeliveryReadinessReport,
    EvaluationReport,
    ExportArtifact,
    GeneratedResult,
    Issue,
    ObservationReport,
    ProjectState,
    RegressionCheck,
    ScoreDelta,
    SceneSpec,
    ShotSpec,
    SolutionArchitecture,
    TraceEvent,
    VerificationReport,
    VersionDiff,
    ConvergenceStep,
    PromptPackage,
    RedesignPlan,
)
from shotforge.core.runtime_models import ToolCallRecord, ToolOrchestrationRecord


class DesignPackage(BaseModel):
    creative_intent: CreativeIntent | None = None
    characters: list[CharacterSpec] = Field(default_factory=list)
    scenes: list[SceneSpec] = Field(default_factory=list)
    shots: list[ShotSpec] = Field(default_factory=list)
    audio_cues: list[AudioCue] = Field(default_factory=list)
    prompt_package: PromptPackage = Field(default_factory=PromptPackage)
    solution_architecture: SolutionArchitecture | None = None
    delivery_readiness: DeliveryReadinessReport | None = None


class GenerationPackage(BaseModel):
    generation_results: list[GeneratedResult] = Field(default_factory=list)


class ObservationPackage(BaseModel):
    observation_reports: list[ObservationReport] = Field(default_factory=list)


class EvaluationPackage(BaseModel):
    verification_reports: list[VerificationReport] = Field(default_factory=list)
    evaluation_reports: list[EvaluationReport] = Field(default_factory=list)
    issue_history: list[Issue] = Field(default_factory=list)


class IterationPackage(BaseModel):
    redesign_plans: list[RedesignPlan] = Field(default_factory=list)
    correction_plans: list[CorrectionPlan] = Field(default_factory=list)
    correction_patches: list[CorrectionPatch] = Field(default_factory=list)
    version_diffs: list[VersionDiff] = Field(default_factory=list)
    score_deltas: list[ScoreDelta] = Field(default_factory=list)
    regression_checks: list[RegressionCheck] = Field(default_factory=list)
    convergence_steps: list[ConvergenceStep] = Field(default_factory=list)
    versions: list[str] = Field(default_factory=list)


class RuntimePackage(BaseModel):
    exports: list[ExportArtifact] = Field(default_factory=list)
    trace_logs: list[TraceEvent] = Field(default_factory=list)
    tool_call_records: list[ToolCallRecord] = Field(default_factory=list)
    tool_orchestration_records: list[ToolOrchestrationRecord] = Field(default_factory=list)


class ProjectPackageView(BaseModel):
    project_id: str
    run_id: str
    version: int
    design: DesignPackage
    generation: GenerationPackage
    observation: ObservationPackage
    evaluation: EvaluationPackage
    iteration: IterationPackage
    runtime: RuntimePackage

    @classmethod
    def from_state(cls, state: ProjectState) -> ProjectPackageView:
        return cls(
            project_id=state.project_id,
            run_id=state.run_id,
            version=state.version,
            design=DesignPackage(
                creative_intent=state.creative_intent,
                characters=state.characters,
                scenes=state.scenes,
                shots=state.shots,
                audio_cues=state.audio_cues,
                prompt_package=state.prompt_package,
                solution_architecture=state.solution_architecture,
                delivery_readiness=state.delivery_readiness,
            ),
            generation=GenerationPackage(generation_results=state.generation_results),
            observation=ObservationPackage(observation_reports=state.observation_reports),
            evaluation=EvaluationPackage(
                verification_reports=state.verification_reports,
                evaluation_reports=state.evaluation_reports,
                issue_history=state.issue_history,
            ),
            iteration=IterationPackage(
                redesign_plans=state.redesign_plans,
                correction_plans=state.correction_plans,
                correction_patches=state.correction_patches,
                version_diffs=state.version_diffs,
                score_deltas=state.score_deltas,
                regression_checks=state.regression_checks,
                convergence_steps=state.convergence_steps,
                versions=state.versions,
            ),
            runtime=RuntimePackage(
                exports=state.exports,
                trace_logs=state.trace_logs,
                tool_call_records=state.tool_call_records,
                tool_orchestration_records=state.tool_orchestration_records,
            ),
        )
