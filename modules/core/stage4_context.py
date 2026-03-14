"""[Phase 4C-2a/2b/2c] Stage4 DI 컨텍스트 — 속성·콜백 의존 주입"""

import inspect

# [S-13] 조건부 모듈 8종 키 상수
_CONDITIONAL_MODULE_KEYS = (
    "pre_director_checklist",
    "confidence_calibrator",
    "prompt_weighter",
    "cross_verifier",
    "chain_of_verification",
    "adversarial_self_play",
    "tree_of_thoughts",
    "multi_agent_deliberation",
)


def _safe_getattr(obj, name: str, default=None):
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


class Stage4Context:
    """Stage4Orchestrator의 DI 컨텍스트.

    [4C-2a] 필수 5종: ui, current_project, agents, sys, state_tracker
    [4C-2b] 확장 13종: memory, world_state, fact_ledger, character_voice,
            perf_timer, foreshadow_tracker, failure_learner, diversity_engine,
            semantic_plot_guard, selected_genre, quality_dashboard,
            pacing_analyzer, pass_rate_monitor
    [S-13] 조건부 모듈 8종 → conditional_modules dict 통합
    [4C-2c] 콜백 12종: get_int_input, build_item_acquisition_timeline,
            load_narrative_summaries, get_protagonist_name, extract_npc_profiles,
            generate_narrative_summary, generate_writer_guidance_v60_8,
            enrich_director_result, audit_event, write_audit_summary,
            flush_audit_buffer, safe_commit
    """

    __slots__ = (
        # [4C-2a] 필수 5종
        "ui",
        "current_project",
        "agents",
        "sys",
        "state_tracker",
        # [4C-2b] 확장 13종
        "memory",
        "context_advisor",
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
        "pass_rate_monitor",
        "emotion_tracker",  # [TF7-P2-06] EmotionArcTracker 배선
        # [S-13] 조건부 모듈 8종 → 1 composite dict
        "conditional_modules",
        # [4C-2c] 직접 슬롯 콜백 7종
        "get_int_input",
        "build_item_acquisition_timeline",
        "load_narrative_summaries",
        "get_protagonist_name",
        "generate_narrative_summary",
        "flush_audit_buffer",
        "safe_commit",
        # [LOG-1] 세션 로거
        "session_logger",
        "_stage4_context_budget_meta",
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
        context_advisor=None,
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
        pass_rate_monitor=None,
        emotion_tracker=None,  # [TF7-P2-06]
        # [S-13] 조건부 모듈 8종 → composite dict
        conditional_modules=None,
        # [4C-2c] 콜백 — 모두 optional (None 허용)
        get_int_input=None,
        build_item_acquisition_timeline=None,
        load_narrative_summaries=None,
        get_protagonist_name=None,
        extract_npc_profiles=None,
        generate_narrative_summary=None,
        generate_writer_guidance_v60_8=None,
        enrich_director_result=None,
        audit_event=None,
        write_audit_summary=None,
        flush_audit_buffer=None,
        safe_commit=None,
        session_logger=None,
    ):
        self.ui = ui
        self.current_project = current_project
        self.agents = agents
        self.sys = sys
        self.state_tracker = state_tracker
        self.memory = memory
        self.context_advisor = context_advisor
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
        self.pass_rate_monitor = pass_rate_monitor
        self.emotion_tracker = emotion_tracker  # [TF7-P2-06]
        self.conditional_modules = conditional_modules or {}
        self._stage4_context_budget_meta = {}
        self.get_int_input = get_int_input
        self.build_item_acquisition_timeline = build_item_acquisition_timeline
        self.load_narrative_summaries = load_narrative_summaries
        self.get_protagonist_name = get_protagonist_name
        self.extract_npc_profiles = extract_npc_profiles
        self.generate_narrative_summary = generate_narrative_summary
        self.generate_writer_guidance_v60_8 = generate_writer_guidance_v60_8
        self.enrich_director_result = enrich_director_result
        self.audit_event = audit_event
        self.write_audit_summary = write_audit_summary
        self.flush_audit_buffer = flush_audit_buffer
        self.safe_commit = safe_commit
        self.session_logger = session_logger

    def get_module(self, name: str):
        """[S-13] 조건부 모듈 조회 헬퍼."""
        return self.conditional_modules.get(name)

    def _get_callback(self, name: str):
        callbacks = self._stage4_context_budget_meta.get("_callbacks")
        if not isinstance(callbacks, dict):
            return None
        return callbacks.get(name)

    def _set_callback(self, name: str, callback):
        callbacks = self._stage4_context_budget_meta.get("_callbacks")
        if callback is None:
            if isinstance(callbacks, dict):
                callbacks.pop(name, None)
                if not callbacks:
                    self._stage4_context_budget_meta.pop("_callbacks", None)
            return

        if not isinstance(callbacks, dict):
            callbacks = {}
            self._stage4_context_budget_meta["_callbacks"] = callbacks
        callbacks[name] = callback

    @property
    def extract_npc_profiles(self):
        return self._get_callback("extract_npc_profiles")

    @extract_npc_profiles.setter
    def extract_npc_profiles(self, callback):
        self._set_callback("extract_npc_profiles", callback)

    @property
    def generate_writer_guidance_v60_8(self):
        return self._get_callback("generate_writer_guidance_v60_8")

    @generate_writer_guidance_v60_8.setter
    def generate_writer_guidance_v60_8(self, callback):
        self._set_callback("generate_writer_guidance_v60_8", callback)

    @property
    def enrich_director_result(self):
        return self._get_callback("enrich_director_result")

    @enrich_director_result.setter
    def enrich_director_result(self, callback):
        self._set_callback("enrich_director_result", callback)

    @property
    def audit_event(self):
        return self._get_callback("audit_event")

    @audit_event.setter
    def audit_event(self, callback):
        self._set_callback("audit_event", callback)

    @property
    def write_audit_summary(self):
        return self._get_callback("write_audit_summary")

    @write_audit_summary.setter
    def write_audit_summary(self, callback):
        self._set_callback("write_audit_summary", callback)

    @classmethod
    def from_app(cls, app):
        """SovereignApp에서 전체 속성 추출"""
        # [S-13] 조건부 모듈 8종을 dict로 구성
        cm = {}
        for key in _CONDITIONAL_MODULE_KEYS:
            val = _safe_getattr(app, key, None)
            if val is not None:
                cm[key] = val

        return cls(
            ui=app.ui,
            current_project=app.current_project,
            agents=app.agents,
            sys=app.sys,
            state_tracker=_safe_getattr(app, "state_tracker", None),
            memory=_safe_getattr(app, "memory", None),
            context_advisor=_safe_getattr(app, "context_advisor", None),
            world_state=_safe_getattr(app, "world_state", None),
            fact_ledger=_safe_getattr(app, "fact_ledger", None),
            character_voice=_safe_getattr(app, "character_voice", None),
            perf_timer=_safe_getattr(app, "perf_timer", None),
            foreshadow_tracker=_safe_getattr(app, "foreshadow_tracker", None),
            failure_learner=_safe_getattr(app, "failure_learner", None),
            diversity_engine=_safe_getattr(app, "diversity_engine", None),
            semantic_plot_guard=_safe_getattr(app, "semantic_plot_guard", None),
            selected_genre=_safe_getattr(app, "selected_genre", None),
            quality_dashboard=_safe_getattr(app, "quality_dashboard", None),
            pacing_analyzer=_safe_getattr(app, "pacing_analyzer", None),
            pass_rate_monitor=_safe_getattr(app, "pass_rate_monitor", None),
            emotion_tracker=_safe_getattr(app, "emotion_tracker", None),
            conditional_modules=cm,
            get_int_input=_safe_getattr(app, "_get_int_input", None),
            build_item_acquisition_timeline=_safe_getattr(app, "_build_item_acquisition_timeline", None),
            load_narrative_summaries=_safe_getattr(app, "_load_narrative_summaries", None),
            get_protagonist_name=_safe_getattr(app, "_get_protagonist_name", None),
            extract_npc_profiles=_safe_getattr(app, "_extract_npc_profiles", None),
            generate_narrative_summary=_safe_getattr(app, "_generate_narrative_summary", None),
            generate_writer_guidance_v60_8=_safe_getattr(app, "_generate_writer_guidance_v60_8", None),
            enrich_director_result=_safe_getattr(app, "_enrich_director_result", None),
            audit_event=_safe_getattr(app, "_audit_event", None),
            write_audit_summary=_safe_getattr(app, "_write_audit_summary", None),
            flush_audit_buffer=_safe_getattr(app, "_flush_audit_buffer", None),
            safe_commit=_safe_getattr(app, "_safe_commit", None),
            session_logger=_safe_getattr(app, "_session_logger", None),
        )
