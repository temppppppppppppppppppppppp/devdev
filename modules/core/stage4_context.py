"""[Phase 4C-2a/2b/2c] Stage4 DI 컨텍스트 — 속성·콜백 의존 주입"""


class Stage4Context:
    """Stage4Orchestrator의 DI 컨텍스트.

    [4C-2a] 필수 5종: ui, current_project, agents, sys, state_tracker
    [4C-2b] 확장 11종: memory, world_state, fact_ledger, character_voice,
            perf_timer, foreshadow_tracker, failure_learner, diversity_engine,
            semantic_plot_guard, selected_genre, quality_dashboard
    [4C-2c] 콜백 7종: get_int_input, build_item_acquisition_timeline,
            load_narrative_summaries, get_protagonist_name,
            generate_narrative_summary, flush_audit_buffer, safe_commit
    """

    __slots__ = (
        # [4C-2a] 필수 5종
        "ui",
        "current_project",
        "agents",
        "sys",
        "state_tracker",
        # [4C-2b] 확장 11종
        "memory",
        "world_state",
        "fact_ledger",
        "character_voice",
        "perf_timer",
        "foreshadow_tracker",
        "failure_learner",
        "diversity_engine",
        "semantic_plot_guard",
        "selected_genre",
        "quality_dashboard",
        "pacing_analyzer",
        # [4C-2c] 콜백 7종
        "get_int_input",
        "build_item_acquisition_timeline",
        "load_narrative_summaries",
        "get_protagonist_name",
        "generate_narrative_summary",
        "flush_audit_buffer",
        "safe_commit",
    )

    def __init__(
        self,
        *,
        ui,
        current_project,
        agents,
        sys,
        state_tracker,
        # [4C-2b] 확장 — 모두 optional (None 허용)
        memory=None,
        world_state=None,
        fact_ledger=None,
        character_voice=None,
        perf_timer=None,
        foreshadow_tracker=None,
        failure_learner=None,
        diversity_engine=None,
        semantic_plot_guard=None,
        selected_genre=None,
        quality_dashboard=None,
        pacing_analyzer=None,
        # [4C-2c] 콜백 — 모두 optional (None 허용)
        get_int_input=None,
        build_item_acquisition_timeline=None,
        load_narrative_summaries=None,
        get_protagonist_name=None,
        generate_narrative_summary=None,
        flush_audit_buffer=None,
        safe_commit=None,
    ):
        self.ui = ui
        self.current_project = current_project
        self.agents = agents
        self.sys = sys
        self.state_tracker = state_tracker
        self.memory = memory
        self.world_state = world_state
        self.fact_ledger = fact_ledger
        self.character_voice = character_voice
        self.perf_timer = perf_timer
        self.foreshadow_tracker = foreshadow_tracker
        self.failure_learner = failure_learner
        self.diversity_engine = diversity_engine
        self.semantic_plot_guard = semantic_plot_guard
        self.selected_genre = selected_genre
        self.quality_dashboard = quality_dashboard
        self.pacing_analyzer = pacing_analyzer
        self.get_int_input = get_int_input
        self.build_item_acquisition_timeline = build_item_acquisition_timeline
        self.load_narrative_summaries = load_narrative_summaries
        self.get_protagonist_name = get_protagonist_name
        self.generate_narrative_summary = generate_narrative_summary
        self.flush_audit_buffer = flush_audit_buffer
        self.safe_commit = safe_commit

    @classmethod
    def from_app(cls, app):
        """SovereignApp에서 전체 속성 추출"""
        return cls(
            ui=app.ui,
            current_project=app.current_project,
            agents=app.agents,
            sys=app.sys,
            state_tracker=getattr(app, "state_tracker", None),
            memory=getattr(app, "memory", None),
            world_state=getattr(app, "world_state", None),
            fact_ledger=getattr(app, "fact_ledger", None),
            character_voice=getattr(app, "character_voice", None),
            perf_timer=getattr(app, "perf_timer", None),
            foreshadow_tracker=getattr(app, "foreshadow_tracker", None),
            failure_learner=getattr(app, "failure_learner", None),
            diversity_engine=getattr(app, "diversity_engine", None),
            semantic_plot_guard=getattr(app, "semantic_plot_guard", None),
            selected_genre=getattr(app, "selected_genre", None),
            quality_dashboard=getattr(app, "quality_dashboard", None),
            pacing_analyzer=getattr(app, "pacing_analyzer", None),
            get_int_input=getattr(app, "_get_int_input", None),
            build_item_acquisition_timeline=getattr(app, "_build_item_acquisition_timeline", None),
            load_narrative_summaries=getattr(app, "_load_narrative_summaries", None),
            get_protagonist_name=getattr(app, "_get_protagonist_name", None),
            generate_narrative_summary=getattr(app, "_generate_narrative_summary", None),
            flush_audit_buffer=getattr(app, "_flush_audit_buffer", None),
            safe_commit=getattr(app, "_safe_commit", None),
        )
