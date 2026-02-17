"""[Phase 4C-3] Stage2 DI 컨텍스트 — 속성·콜백 의존 주입"""


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

    @classmethod
    def from_app(cls, app):
        """SovereignApp에서 전체 속성 추출"""
        return cls(
            ui=app.ui,
            current_project=app.current_project,
            agents=app.agents,
            sys=app.sys,
            state_tracker=getattr(app, "state_tracker", None),
            selected_genre=getattr(app, "selected_genre", None),
            preset_registry=getattr(app, "preset_registry", None),
            perf_timer=getattr(app, "perf_timer", None),
            semantic_plot_guard=getattr(app, "semantic_plot_guard", None),
            failure_learner=getattr(app, "failure_learner", None),
            memory=getattr(app, "memory", None),
            stage2_optimizer=getattr(app, "stage2_optimizer", None),
            arc_draft_validator=getattr(app, "arc_draft_validator", None),
            arc_corrector=getattr(app, "arc_corrector", None),
            constraint_compiler=getattr(app, "constraint_compiler", None),
            stage_rejection_history=getattr(app, "stage_rejection_history", None),
            pass_rate_monitor=getattr(app, "pass_rate_monitor", None),
            quality_dashboard=getattr(app, "quality_dashboard", None),
            quality_amplifier=getattr(app, "quality_amplifier", None),
            agent_intelligence=getattr(app, "agent_intelligence", None),
            constitutional_checker=getattr(app, "constitutional_checker", None),
            self_reflector=getattr(app, "self_reflector", None),
            use_arc_corrector=getattr(app, "use_arc_corrector", False),
            audit_event=getattr(app, "_audit_event", None),
            cumulative_state_cache=getattr(app, "_cumulative_state_cache", None),
            cumulative_state_cache_key=getattr(app, "_cumulative_state_cache_key", None),
            write_audit_summary=getattr(app, "_write_audit_summary", None),
            validate_arc_mapping=getattr(app, "_validate_arc_mapping", None),
            validate_arc_integrity=getattr(app, "_validate_arc_integrity", None),
            state_tracker_loaded_arcs=getattr(app, "_state_tracker_loaded_arcs", None),
            safe_commit_async=getattr(app, "_safe_commit_async", None),
            get_max_episode_from_manuscripts=getattr(app, "_get_max_episode_from_manuscripts", None),
            get_int_input=getattr(app, "_get_int_input", None),
            generate_structured_arc_feedback=getattr(app, "_generate_structured_arc_feedback", None),
            generate_reverse_feedback_stage3_to_2=getattr(app, "_generate_reverse_feedback_stage3_to_2", None),
            generate_reverse_feedback_stage4_to_2=getattr(app, "_generate_reverse_feedback_stage4_to_2", None),
            fix_entity_registry_protagonist=getattr(app, "_fix_entity_registry_protagonist", None),
            calculate_arc_from_episode=getattr(app, "_calculate_arc_from_episode", None),
            build_strong_kind_feedback=getattr(app, "_build_strong_kind_feedback", None),
            build_minimal_arc_context=getattr(app, "_build_minimal_arc_context", None),
            build_focused_context=getattr(app, "_build_focused_context", None),
            analyze_rejection_pattern_v60=getattr(app, "_analyze_rejection_pattern_v60", None),
            get_adaptive_feedback_intensity=getattr(app, "_get_adaptive_feedback_intensity", None),
            generate_arc_context_v60=getattr(app, "_generate_arc_context_v60", None),
            sync_cache_key_to_app=lambda key: setattr(app, "_cumulative_state_cache_key", key),
        )
