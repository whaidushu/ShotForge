from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import AliasChoices, BaseModel, Field

from shotforge.core.schemas.observation import (
    FrameObservation,
    ObservationReport,
    SequenceObservation,  # noqa: F401 - re-exported for legacy imports
    ShotObservation,  # noqa: F401 - re-exported for legacy imports
)
from shotforge.core.runtime_models import (
    AgentContractReport,
    HarnessContextSnapshot,
    MCPAccessRecord,
    MemorySelectionRecord,
    SandboxPolicyRecord,
    StateTransitionRecord,
    ToolCallRecord,
    ToolOrchestrationRecord,
    WorkflowDecisionRecord,
)


ExportFormat = Literal[
    "json",
    "csv",
    "markdown",
    "evaluation_csv",
    "manifest",
    "package_view",
    "trace",
    "run_summary",
]
OutputLanguage = Literal["zh", "en"]
IssueSeverity = Literal["low", "medium", "high", "critical"]
GenerationStatus = Literal["mocked", "submitted", "running", "completed", "failed"]
ReadinessStatus = Literal["passed", "warning", "failed"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def local_run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M")


class CreativeIntent(BaseModel):
    premise: str = ""
    genre: str = "cinematic"
    audience: str = "general"
    mood: str = "dynamic"
    visual_style: str = "cinematic"
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CharacterSpec(BaseModel):
    character_id: str
    name: str
    role: str
    visual_traits: list[str] = Field(default_factory=list)
    behavior_notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SceneSpec(BaseModel):
    scene_id: str
    index: int
    title: str
    duration_seconds: int
    description: str
    emotional_goal: str
    key_visuals: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MotionSpec(BaseModel):
    shot_id: str
    camera: str
    subject_motion: str
    transition: str
    pacing: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ShotSpec(BaseModel):
    shot_id: str
    scene_id: str
    index: int
    title: str
    duration_seconds: int
    description: str
    shot_type: str
    key_visuals: list[str] = Field(default_factory=list)
    motion: MotionSpec | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AudioCue(BaseModel):
    shot_id: str
    music: str
    sound_design: list[str] = Field(default_factory=list)
    voiceover: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class StructuredPromptTemplate(BaseModel):
    character_identity: str = ""
    scene_constraints: str = ""
    physical_constraints: list[str] = Field(default_factory=list)
    action_sequence: str = ""
    emotional_direction: str = ""
    camera_direction: str = ""
    motion_direction: str = ""
    narrative_beat: str = ""
    style_constraints: str = ""
    success_criteria: list[str] = Field(default_factory=list)
    comfyui_params: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def render(self) -> str:
        parts = [
            self.character_identity,
            self.scene_constraints,
            "Physical constraints: " + "; ".join(self.physical_constraints)
            if self.physical_constraints
            else "",
            self.action_sequence,
            self.emotional_direction,
            self.camera_direction,
            self.motion_direction,
            self.narrative_beat,
            self.style_constraints,
        ]
        if self.success_criteria:
            parts.append("Success criteria: " + "; ".join(self.success_criteria))
        return " ".join(part.strip() for part in parts if part.strip())


class PromptItem(BaseModel):
    shot_id: str
    provider: str = "mock-video-model"
    prompt: str
    structured_template: StructuredPromptTemplate | None = None
    negative_prompt: str = "low quality, distorted anatomy, unreadable text, flicker"
    parameters: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PromptPackage(BaseModel):
    provider: str = "mock-video-model"
    prompts: list[PromptItem] = Field(default_factory=list)
    adapter_notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArchitectureComponent(BaseModel):
    name: str
    responsibility: str
    owner_agent: str
    skills: list[str] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IntegrationPoint(BaseModel):
    system: str
    interface: str
    data_contract: str
    status: Literal["mocked", "planned", "ready"] = "planned"
    metadata: dict[str, Any] = Field(default_factory=dict)


class POCSuccessCriterion(BaseModel):
    criterion_id: str
    metric: str
    target: str
    evaluation_method: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RolloutPhase(BaseModel):
    phase: str
    objective: str
    exit_criteria: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ValueMetric(BaseModel):
    name: str
    baseline: str
    target: str
    business_value: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SolutionArchitecture(BaseModel):
    industry: str
    scenario: str
    business_objective: str
    reference_customer: str = ""
    model_strategy: str
    agent_topology: list[str] = Field(default_factory=list)
    components: list[ArchitectureComponent] = Field(default_factory=list)
    integration_points: list[IntegrationPoint] = Field(default_factory=list)
    safety_controls: list[str] = Field(default_factory=list)
    poc_success_criteria: list[POCSuccessCriterion] = Field(default_factory=list)
    rollout_plan: list[RolloutPhase] = Field(default_factory=list)
    value_metrics: list[ValueMetric] = Field(default_factory=list)
    knowledge_assets: list[str] = Field(default_factory=list)
    scenario_patterns: list[str] = Field(default_factory=list)
    evaluation_metrics: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReadinessCheck(BaseModel):
    check_id: str
    category: str
    status: ReadinessStatus
    evidence: str
    required_for_pilot: bool = True
    remediation: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeliveryReadinessReport(BaseModel):
    report_id: str = Field(default_factory=lambda: f"ready_{uuid4().hex[:12]}")
    overall_status: ReadinessStatus
    checks: list[ReadinessCheck] = Field(default_factory=list)
    handoff_deliverables: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    risk_register: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GeneratedShotResult(BaseModel):
    shot_id: str
    prompt_id: str
    mock_video_uri: str
    duration_seconds: int
    observed_summary: str
    detected_elements: list[str] = Field(default_factory=list)
    motion_summary: str = ""
    audio_summary: str = ""
    quality_signals: dict[str, float] = Field(default_factory=dict)
    frame_observations: list[FrameObservation] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GeneratedResult(BaseModel):
    generated_result_id: str = Field(default_factory=lambda: f"gen_{uuid4().hex[:12]}")
    project_id: str
    run_id: str
    version: int
    provider: str = "mock"
    status: GenerationStatus = "mocked"
    created_at: datetime = Field(default_factory=utc_now)
    shots: list[GeneratedShotResult] = Field(default_factory=list)
    artifact_refs: list[str] = Field(default_factory=list)
    observation_report_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DimensionScore(BaseModel):
    dimension_id: str
    label: str
    score: float = Field(ge=0, le=1)
    weight: float = 1.0
    rationale: str
    related_shot_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Issue(BaseModel):
    issue_id: str = Field(default_factory=lambda: f"issue_{uuid4().hex[:12]}")
    severity: IssueSeverity
    dimension_id: str
    dimension_label: str
    shot_id: str | None = None
    description: str
    evidence: str
    suspected_cause: str
    correction_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScoreCard(BaseModel):
    overall_score: float = Field(ge=0, le=1)
    dimension_scores: list[DimensionScore] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvaluationReport(BaseModel):
    evaluation_id: str = Field(default_factory=lambda: f"eval_{uuid4().hex[:12]}")
    version_id: int
    target_version: int
    generated_result_id: str
    created_at: datetime = Field(default_factory=utc_now)
    score_card: ScoreCard
    issues: list[Issue] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    suggested_focus: list[str] = Field(default_factory=list)
    rubric_id: str = "baseline_v1"
    metadata: dict[str, Any] = Field(default_factory=dict)


class VerificationCheck(BaseModel):
    check_id: str
    label: str
    status: Literal["passed", "warning", "failed"]
    evidence: str = ""
    shot_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class VerificationReport(BaseModel):
    verification_id: str = Field(default_factory=lambda: f"verify_{uuid4().hex[:12]}")
    version_id: int
    generated_result_id: str
    created_at: datetime = Field(default_factory=utc_now)
    checks: list[VerificationCheck] = Field(default_factory=list)
    summary: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class DimensionDelta(BaseModel):
    dimension_id: str
    label: str
    before_score: float = Field(ge=0, le=1)
    after_score: float = Field(ge=0, le=1)
    delta: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScoreDelta(BaseModel):
    score_delta_id: str = Field(default_factory=lambda: f"score_delta_{uuid4().hex[:12]}")
    from_version: int
    to_version: int
    before_evaluation_id: str
    after_evaluation_id: str
    overall_before: float = Field(ge=0, le=1)
    overall_after: float = Field(ge=0, le=1)
    overall_delta: float
    dimension_deltas: list[DimensionDelta] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RegressionCheck(BaseModel):
    regression_check_id: str = Field(default_factory=lambda: f"regression_{uuid4().hex[:12]}")
    from_version: int
    to_version: int
    resolved_issue_ids: list[str] = Field(default_factory=list)
    remaining_issue_ids: list[str] = Field(default_factory=list)
    new_issue_ids: list[str] = Field(default_factory=list)
    status: Literal["improved", "mixed", "regressed", "unchanged"]
    summary: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConvergenceStep(BaseModel):
    step_id: str = Field(default_factory=lambda: f"conv_step_{uuid4().hex[:12]}")
    from_version: int
    to_version: int
    score_delta_id: str | None = None
    regression_check_id: str | None = None
    overall_delta: float = 0.0
    status: Literal["improved", "mixed", "regressed", "unchanged"]
    stop_reason: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class CorrectionPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: f"plan_{uuid4().hex[:12]}")
    source_evaluation_id: str
    target_issue_ids: list[str] = Field(default_factory=list)
    correction_strategy: str
    selected_agent: str
    affected_fields: list[str] = Field(default_factory=list)
    expected_improvement: dict[str, float] = Field(default_factory=dict)
    risk: str = ""
    priority: int = 100
    status: Literal["planned", "applied", "skipped"] = "planned"
    metadata: dict[str, Any] = Field(default_factory=dict)


class RedesignPlan(BaseModel):
    redesign_plan_id: str = Field(default_factory=lambda: f"redesign_{uuid4().hex[:12]}")
    source_evaluation_id: str
    target_layer_id: str
    target_layer_index: int
    fix_issue_ids: list[str] = Field(default_factory=list)
    protect_fields: list[str] = Field(default_factory=list)
    defer_issue_ids: list[str] = Field(default_factory=list)
    rationale: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class CorrectionOperation(BaseModel):
    operation_type: Literal[
        "append_shot_description",
        "append_motion_subject",
        "append_motion_camera",
        "append_prompt_text",
        "append_negative_prompt",
        "append_structured_template_text",
        "append_structured_template_list",
        "append_scene_description",
        "append_scene_emotional_goal",
        "append_audio_sound_design",
        "append_character_behavior",
    ]
    target_id: str
    field_path: str
    value: Any
    rationale: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class CorrectionPatch(BaseModel):
    patch_id: str = Field(default_factory=lambda: f"patch_{uuid4().hex[:12]}")
    plan_id: str
    agent_name: str
    target_version: int
    operations: list[CorrectionOperation] = Field(default_factory=list)
    rationale: str = ""
    expected_effect: str = ""
    risk: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class FieldChange(BaseModel):
    path: str
    before: Any = None
    after: Any = None
    change_type: Literal["added", "removed", "modified"]
    metadata: dict[str, Any] = Field(default_factory=dict)


class VersionDiff(BaseModel):
    diff_id: str = Field(default_factory=lambda: f"diff_{uuid4().hex[:12]}")
    from_version: int
    to_version: int
    changed_shots: list[str] = Field(default_factory=list)
    changed_prompts: list[str] = Field(default_factory=list)
    changed_audio_cues: list[str] = Field(default_factory=list)
    resolved_issues: list[str] = Field(default_factory=list)
    new_issues: list[str] = Field(default_factory=list)
    field_changes: list[FieldChange] = Field(default_factory=list)
    explanation: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExportArtifact(BaseModel):
    format: ExportFormat
    path: str


class TraceEvent(BaseModel):
    step: str
    status: Literal["started", "completed", "failed"]
    timestamp: datetime = Field(default_factory=utc_now)
    duration_ms: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectState(BaseModel):
    project_id: str = Field(default_factory=lambda: f"proj_{uuid4().hex[:12]}")
    run_id: str = Field(default_factory=local_run_id)
    version: int = 1
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    user_idea: str = Field(validation_alias=AliasChoices("user_idea", "idea"))
    style: str = "cinematic"
    language: OutputLanguage = "zh"
    duration_seconds: int = 24
    target_platform: str = "short-form"

    creative_intent: CreativeIntent | None = None
    characters: list[CharacterSpec] = Field(default_factory=list)
    scenes: list[SceneSpec] = Field(default_factory=list)
    shots: list[ShotSpec] = Field(default_factory=list)
    audio_cues: list[AudioCue] = Field(default_factory=list)
    prompt_package: PromptPackage = Field(default_factory=PromptPackage)
    solution_architecture: SolutionArchitecture | None = None
    delivery_readiness: DeliveryReadinessReport | None = None

    generation_results: list[GeneratedResult] = Field(default_factory=list)
    observation_reports: list[ObservationReport] = Field(default_factory=list)
    verification_reports: list[VerificationReport] = Field(default_factory=list)
    evaluation_reports: list[EvaluationReport] = Field(default_factory=list)
    issue_history: list[Issue] = Field(default_factory=list)
    redesign_plans: list[RedesignPlan] = Field(default_factory=list)
    correction_plans: list[CorrectionPlan] = Field(default_factory=list)
    correction_patches: list[CorrectionPatch] = Field(default_factory=list)
    version_diffs: list[VersionDiff] = Field(default_factory=list)
    score_deltas: list[ScoreDelta] = Field(default_factory=list)
    regression_checks: list[RegressionCheck] = Field(default_factory=list)
    convergence_steps: list[ConvergenceStep] = Field(default_factory=list)
    versions: list[str] = Field(default_factory=list)
    exports: list[ExportArtifact] = Field(default_factory=list)
    trace_logs: list[TraceEvent] = Field(default_factory=list)
    tool_call_records: list[ToolCallRecord] = Field(default_factory=list)
    tool_orchestration_records: list[ToolOrchestrationRecord] = Field(default_factory=list)
    harness_contexts: list[HarnessContextSnapshot] = Field(default_factory=list)
    state_transitions: list[StateTransitionRecord] = Field(default_factory=list)
    agent_contract_reports: list[AgentContractReport] = Field(default_factory=list)
    workflow_decisions: list[WorkflowDecisionRecord] = Field(default_factory=list)
    memory_selection_records: list[MemorySelectionRecord] = Field(default_factory=list)
    sandbox_policy_records: list[SandboxPolicyRecord] = Field(default_factory=list)
    mcp_access_records: list[MCPAccessRecord] = Field(default_factory=list)
    knowledge_refs: list[str] = Field(default_factory=list)
    memory_refs: list[str] = Field(default_factory=list)
    review_notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def motion_plan(self) -> list[MotionSpec]:
        return [shot.motion for shot in self.shots if shot.motion is not None]

    def touch(self) -> None:
        self.updated_at = utc_now()
