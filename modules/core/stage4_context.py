"""[Phase 4C-2a/2b] Stage4 DI 컨텍스트 — 속성 의존 주입"""


class Stage4Context:
    """Stage4Orchestrator의 DI 컨텍스트.

    [4C-2a] 필수 5종: ui, current_project, agents, sys, state_tracker
    [4C-2b] 확장 10종: memory, world_state, fact_ledger, character_voice,
            perf_timer, foreshadow_tracker, failure_learner, diversity_engine,
            semantic_plot_guard, selected_genre
    """

    __slots__ = (
        # [4C-2a] 필수 5종
        "ui",
        "current_project",
        "agents",
        "sys",
        "state_tracker",
        # [4C-2b] 확장 10종
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
        )
