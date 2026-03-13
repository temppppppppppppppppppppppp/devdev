"""[Phase 4C-3] Stage2 DI 컨텍스트 — 속성·콜백 의존 주입"""

import inspect
import weakref


def _make_sync_callback(app_ref):
    """[S-04] weakref 기반 sync 콜백 — 람다 순환 참조 방지."""

    def _sync(key, cache=None):
        app = app_ref()
        if app is None:
            return
        setattr(app, "_cumulative_state_cache_key", key)
        if cache is not None:
            setattr(app, "_cumulative_state_cache", cache)

    return _sync


_RETRY_FEEDBACK_CALLBACK_SPECS = {
    "generate_structured_arc_feedback": {
        "tier": "optional_with_fallback",
        "fallbacks": (("_feedback_system", "generate_structured_arc_feedback"),),
    },
    "generate_reverse_feedback_stage3_to_2": {
        "tier": "optional_with_fallback",
        "fallbacks": (("_feedback_system", "generate_reverse_feedback_stage3_to_2"),),
    },
    "generate_reverse_feedback_stage4_to_2": {
        "tier": "optional_with_fallback",
        "fallbacks": (("_feedback_system", "generate_reverse_feedback_stage4_to_2"),),
    },
    "build_strong_kind_feedback": {
        "tier": "optional_with_fallback",
        "fallbacks": (("_feedback_system", "build_strong_kind_feedback"),),
    },
    "build_minimal_arc_context": {
        "tier": "optional_with_fallback",
        "fallbacks": (("_feedback_system", "build_minimal_arc_context"),),
    },
    "build_focused_context": {
        "tier": "optional_with_fallback",
        "fallbacks": (("_feedback_system", "build_focused_context"),),
    },
    "analyze_rejection_pattern_v60": {
        "tier": "required",
        "fallbacks": (),
    },
    "get_adaptive_feedback_intensity": {
        "tier": "optional_with_fallback",
        "fallbacks": (("_feedback_system", "get_adaptive_feedback_intensity"),),
    },
    "generate_arc_context_v60": {
        "tier": "optional_with_fallback",
        "fallbacks": (("_prompt_builder", "generate_arc_context_v60"),),
    },
}


def _safe_getattr(obj, name, default=None):
    if obj is None:
        return default
    try:
        inspect.getattr_static(obj, name)
    except AttributeError:
        return default
    try:
        return getattr(obj, name)
    except AttributeError:
        return default


def _resolve_retry_feedback_callback(app, callback_name: str):
    direct_name = f"_{callback_name}"
    callback = _safe_getattr(app, direct_name, None)
    if callable(callback):
        return callback

    spec = _RETRY_FEEDBACK_CALLBACK_SPECS.get(callback_name, {})
    for container_name, method_name in spec.get("fallbacks", ()):
        container = _safe_getattr(app, container_name, None)
        method = _safe_getattr(container, method_name, None)
        if callable(method):
            return method
    return None


def _build_retry_feedback_contract(app):
    callbacks = {}
    contract = {}
    missing = {
        "required": [],
        "optional_with_fallback": [],
        "observability_only": [],
    }

    for callback_name, spec in _RETRY_FEEDBACK_CALLBACK_SPECS.items():
        contract[callback_name] = spec["tier"]
        resolved = _resolve_retry_feedback_callback(app, callback_name)
        callbacks[callback_name] = resolved
        if not callable(resolved):
            missing[spec["tier"]].append(callback_name)

    return callbacks, contract, missing


class Stage2Context:
    """Stage2Orchestrator의 DI 컨텍스트.

    [4C-3a] 필수 5종: ui, current_project, agents, sys, state_tracker
    [4C-3b] 확장 18종: selected_genre, preset_registry, perf_timer,
            semantic_plot_guard, failure_learner, memory,
            stage2_optimizer, arc_draft_validator, arc_corrector,
            constraint_compiler, stage_rejection_history,
            pass_rate_monitor, quality_dashboard, quality_amplifier,
            agent_intelligence, constitutional_checker, self_reflector,
            use_arc_corrector
    [4C-3c] 콜백 21종: audit_event, cumulative_state_cache,
            cumulative_state_cache_key, write_audit_summary,
            validate_arc_mapping, validate_arc_integrity,
            state_tracker_loaded_arcs, safe_commit_async,
            get_max_episode_from_manuscripts, get_int_input,
            generate_structured_arc_feedback,
            generate_reverse_feedback_stage3_to_2,
            generate_reverse_feedback_stage4_to_2,
            fix_entity_registry_protagonist,
            calculate_arc_from_episode,
            build_strong_kind_feedback, build_minimal_arc_context,
            build_focused_context, analyze_rejection_pattern_v60,
            get_adaptive_feedback_intensity, generate_arc_context_v60
    """

    __slots__ = (
        # [4C-3a] 필수 5종
        "ui",
        "current_project",
        "agents",
        "sys",
        "state_tracker",
        # [4C-3b] 확장 18종
        "selected_genre",
        "preset_registry",
        "perf_timer",
        "semantic_plot_guard",
        "failure_learner",
        "memory",
        "context_advisor",
        "stage2_optimizer",
        "arc_draft_validator",
        "arc_corrector",
        "constraint_compiler",
        "stage_rejection_history",
        "pass_rate_monitor",
        "quality_dashboard",
        "quality_amplifier",
        "agent_intelligence",
        "constitutional_checker",
        "self_reflector",
        "use_arc_corrector",
        "adversarial_self_play",
        # [4C-3c] 콜백 21종
        "audit_event",
        "cumulative_state_cache",
        "cumulative_state_cache_key",
        "write_audit_summary",
        "validate_arc_mapping",
        "validate_arc_integrity",
        "state_tracker_loaded_arcs",
        "safe_commit_async",
        "get_max_episode_from_manuscripts",
        "get_int_input",
        "generate_structured_arc_feedback",
        "generate_reverse_feedback_stage3_to_2",
        "generate_reverse_feedback_stage4_to_2",
        "fix_entity_registry_protagonist",
        "calculate_arc_from_episode",
        "build_strong_kind_feedback",
        "build_minimal_arc_context",
        "build_focused_context",
        "analyze_rejection_pattern_v60",
        "get_adaptive_feedback_intensity",
        "generate_arc_context_v60",
        # [Sweep3-D2] 캐시 키 동기화 콜백
        "sync_cache_key_to_app",
        # [MRF-T1] callback contract / missing ledger
        "retry_feedback_contract",
        "retry_feedback_missing_callbacks",
        # [LOG-1] 세션 로거
        "session_logger",
    )

    def __init__(
        self,
        *,
        ui,
        current_project,
        agents,
        sys,
        state_tracker,
        # [4C-3b] 확장 — 모두 optional
        selected_genre=None,
        preset_registry=None,
        perf_timer=None,
        semantic_plot_guard=None,
        failure_learner=None,
        memory=None,
        context_advisor=None,
        stage2_optimizer=None,
        arc_draft_validator=None,
        arc_corrector=None,
        constraint_compiler=None,
        stage_rejection_history=None,
        pass_rate_monitor=None,
        quality_dashboard=None,
        quality_amplifier=None,
        agent_intelligence=None,
        constitutional_checker=None,
        self_reflector=None,
        use_arc_corrector=False,
        adversarial_self_play=None,
        # [4C-3c] 콜백 — 모두 optional
        audit_event=None,
        cumulative_state_cache=None,
        cumulative_state_cache_key=None,
        write_audit_summary=None,
        validate_arc_mapping=None,
        validate_arc_integrity=None,
        state_tracker_loaded_arcs=None,
        safe_commit_async=None,
        get_max_episode_from_manuscripts=None,
        get_int_input=None,
        generate_structured_arc_feedback=None,
        generate_reverse_feedback_stage3_to_2=None,
        generate_reverse_feedback_stage4_to_2=None,
        fix_entity_registry_protagonist=None,
        calculate_arc_from_episode=None,
        build_strong_kind_feedback=None,
        build_minimal_arc_context=None,
        build_focused_context=None,
        analyze_rejection_pattern_v60=None,
        get_adaptive_feedback_intensity=None,
        generate_arc_context_v60=None,
        # [Sweep3-D2]
        sync_cache_key_to_app=None,
        retry_feedback_contract=None,
        retry_feedback_missing_callbacks=None,
        # [LOG-1]
        session_logger=None,
    ):
        self.ui = ui
        self.current_project = current_project
        self.agents = agents
        self.sys = sys
        self.state_tracker = state_tracker
        self.selected_genre = selected_genre
        self.preset_registry = preset_registry
        self.perf_timer = perf_timer
        self.semantic_plot_guard = semantic_plot_guard
        self.failure_learner = failure_learner
        self.memory = memory
        self.context_advisor = context_advisor
        self.stage2_optimizer = stage2_optimizer
        self.arc_draft_validator = arc_draft_validator
        self.arc_corrector = arc_corrector
        self.constraint_compiler = constraint_compiler
        self.stage_rejection_history = stage_rejection_history
        self.pass_rate_monitor = pass_rate_monitor
        self.quality_dashboard = quality_dashboard
        self.quality_amplifier = quality_amplifier
        self.agent_intelligence = agent_intelligence
        self.constitutional_checker = constitutional_checker
        self.self_reflector = self_reflector
        self.use_arc_corrector = use_arc_corrector
        self.adversarial_self_play = adversarial_self_play
        self.audit_event = audit_event
        self.cumulative_state_cache = cumulative_state_cache
        self.cumulative_state_cache_key = cumulative_state_cache_key
        self.write_audit_summary = write_audit_summary
        self.validate_arc_mapping = validate_arc_mapping
        self.validate_arc_integrity = validate_arc_integrity
        self.state_tracker_loaded_arcs = state_tracker_loaded_arcs
        self.safe_commit_async = safe_commit_async
        self.get_max_episode_from_manuscripts = get_max_episode_from_manuscripts
        self.get_int_input = get_int_input
        self.generate_structured_arc_feedback = generate_structured_arc_feedback
        self.generate_reverse_feedback_stage3_to_2 = generate_reverse_feedback_stage3_to_2
        self.generate_reverse_feedback_stage4_to_2 = generate_reverse_feedback_stage4_to_2
        self.fix_entity_registry_protagonist = fix_entity_registry_protagonist
        self.calculate_arc_from_episode = calculate_arc_from_episode
        self.build_strong_kind_feedback = build_strong_kind_feedback
        self.build_minimal_arc_context = build_minimal_arc_context
        self.build_focused_context = build_focused_context
        self.analyze_rejection_pattern_v60 = analyze_rejection_pattern_v60
        self.get_adaptive_feedback_intensity = get_adaptive_feedback_intensity
        self.generate_arc_context_v60 = generate_arc_context_v60
        self.sync_cache_key_to_app = sync_cache_key_to_app
        self.retry_feedback_contract = retry_feedback_contract or {
            name: spec["tier"] for name, spec in _RETRY_FEEDBACK_CALLBACK_SPECS.items()
        }
        self.retry_feedback_missing_callbacks = retry_feedback_missing_callbacks or {
            "required": [],
            "optional_with_fallback": [],
            "observability_only": [],
        }
        self.session_logger = session_logger

    @classmethod
    def from_app(cls, app):
        """SovereignApp에서 전체 속성 추출"""
        retry_callbacks, retry_contract, retry_missing = _build_retry_feedback_contract(app)
        return cls(
            ui=app.ui,
            current_project=app.current_project,
            agents=app.agents,
            sys=app.sys,
            state_tracker=_safe_getattr(app, "state_tracker", None),
            selected_genre=_safe_getattr(app, "selected_genre", None),
            preset_registry=_safe_getattr(app, "preset_registry", None),
            perf_timer=_safe_getattr(app, "perf_timer", None),
            semantic_plot_guard=_safe_getattr(app, "semantic_plot_guard", None),
            failure_learner=_safe_getattr(app, "failure_learner", None),
            memory=_safe_getattr(app, "memory", None),
            context_advisor=_safe_getattr(app, "context_advisor", None),
            stage2_optimizer=_safe_getattr(app, "stage2_optimizer", None),
            arc_draft_validator=_safe_getattr(app, "arc_draft_validator", None),
            arc_corrector=_safe_getattr(app, "arc_corrector", None),
            constraint_compiler=_safe_getattr(app, "constraint_compiler", None),
            stage_rejection_history=_safe_getattr(app, "stage_rejection_history", None),
            pass_rate_monitor=_safe_getattr(app, "pass_rate_monitor", None),
            quality_dashboard=_safe_getattr(app, "quality_dashboard", None),
            quality_amplifier=_safe_getattr(app, "quality_amplifier", None),
            agent_intelligence=_safe_getattr(app, "agent_intelligence", None),
            constitutional_checker=_safe_getattr(app, "constitutional_checker", None),
            self_reflector=_safe_getattr(app, "self_reflector", None),
            use_arc_corrector=_safe_getattr(app, "use_arc_corrector", False),
            adversarial_self_play=_safe_getattr(app, "adversarial_self_play", None),
            audit_event=_safe_getattr(app, "_audit_event", None),
            cumulative_state_cache=_safe_getattr(app, "_cumulative_state_cache", None),
            cumulative_state_cache_key=_safe_getattr(app, "_cumulative_state_cache_key", None),
            write_audit_summary=_safe_getattr(app, "_write_audit_summary", None),
            validate_arc_mapping=_safe_getattr(app, "_validate_arc_mapping", None),
            validate_arc_integrity=_safe_getattr(app, "_validate_arc_integrity", None),
            state_tracker_loaded_arcs=_safe_getattr(app, "_state_tracker_loaded_arcs", None),
            safe_commit_async=_safe_getattr(app, "_safe_commit_async", None),
            get_max_episode_from_manuscripts=_safe_getattr(app, "_get_max_episode_from_manuscripts", None),
            get_int_input=_safe_getattr(app, "_get_int_input", None),
            generate_structured_arc_feedback=retry_callbacks["generate_structured_arc_feedback"],
            generate_reverse_feedback_stage3_to_2=retry_callbacks["generate_reverse_feedback_stage3_to_2"],
            generate_reverse_feedback_stage4_to_2=retry_callbacks["generate_reverse_feedback_stage4_to_2"],
            fix_entity_registry_protagonist=_safe_getattr(app, "_fix_entity_registry_protagonist", None),
            calculate_arc_from_episode=_safe_getattr(app, "_calculate_arc_from_episode", None),
            build_strong_kind_feedback=retry_callbacks["build_strong_kind_feedback"],
            build_minimal_arc_context=retry_callbacks["build_minimal_arc_context"],
            build_focused_context=retry_callbacks["build_focused_context"],
            analyze_rejection_pattern_v60=retry_callbacks["analyze_rejection_pattern_v60"],
            get_adaptive_feedback_intensity=retry_callbacks["get_adaptive_feedback_intensity"],
            generate_arc_context_v60=retry_callbacks["generate_arc_context_v60"],
            sync_cache_key_to_app=_make_sync_callback(weakref.ref(app)),
            retry_feedback_contract=retry_contract,
            retry_feedback_missing_callbacks=retry_missing,
            session_logger=_safe_getattr(app, "_session_logger", None),
        )
