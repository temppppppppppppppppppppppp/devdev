"""[Phase 4C-4] Stage3 DI context: explicit attributes + callbacks."""


class Stage3Context:
    """Stage3Orchestrator DI 컨텍스트.

    [4C-4a] 필수 2종: ui, current_project
    [E-1a] 속성 7종: agents, sys, state_tracker, world_state, fact_ledger,
           preset_registry, selected_genre
    [E-1a] 콜백 10종: get_protagonist_name, audit_event, write_audit_summary,
           get_arc_context_for_episode, get_max_episode_from_manuscripts,
           get_int_input, safe_commit, validate_arc_data_fields,
           validate_blueprint_integrity, fix_entity_registry_protagonist
    """

    __slots__ = (
        # [필수 2종]
        "ui",
        "current_project",
        # [속성 7종]
        "agents",
        "sys",
        "state_tracker",
        "world_state",
        "fact_ledger",
        "adversarial_self_play",
        "preset_registry",
        "selected_genre",
        # [콜백 10종]
        "get_protagonist_name",
        "audit_event",
        "write_audit_summary",
        "get_arc_context_for_episode",
        "get_max_episode_from_manuscripts",
        "get_int_input",
        "safe_commit",
        "validate_arc_data_fields",
        "validate_blueprint_integrity",
        "fix_entity_registry_protagonist",
    )

    def __init__(
        self,
        *,
        ui,
        current_project,
        agents=None,
        sys=None,
        state_tracker=None,
        world_state=None,
        fact_ledger=None,
        adversarial_self_play=None,
        preset_registry=None,
        selected_genre=None,
        get_protagonist_name=None,
        audit_event=None,
        write_audit_summary=None,
        get_arc_context_for_episode=None,
        get_max_episode_from_manuscripts=None,
        get_int_input=None,
        safe_commit=None,
        validate_arc_data_fields=None,
        validate_blueprint_integrity=None,
        fix_entity_registry_protagonist=None,
    ):
        self.ui = ui
        self.current_project = current_project
        self.agents = agents
        self.sys = sys
        self.state_tracker = state_tracker
        self.world_state = world_state
        self.fact_ledger = fact_ledger
        self.adversarial_self_play = adversarial_self_play
        self.preset_registry = preset_registry
        self.selected_genre = selected_genre
        self.get_protagonist_name = get_protagonist_name
        self.audit_event = audit_event
        self.write_audit_summary = write_audit_summary
        self.get_arc_context_for_episode = get_arc_context_for_episode
        self.get_max_episode_from_manuscripts = get_max_episode_from_manuscripts
        self.get_int_input = get_int_input
        self.safe_commit = safe_commit
        self.validate_arc_data_fields = validate_arc_data_fields
        self.validate_blueprint_integrity = validate_blueprint_integrity
        self.fix_entity_registry_protagonist = fix_entity_registry_protagonist

    @classmethod
    def from_app(cls, app):
        """SovereignApp에서 속성 추출"""
        return cls(
            ui=app.ui,
            current_project=app.current_project,
            agents=app.agents,
            sys=app.sys,
            state_tracker=getattr(app, "state_tracker", None),
            world_state=getattr(app, "world_state", None),
            fact_ledger=getattr(app, "fact_ledger", None),
            adversarial_self_play=getattr(app, "adversarial_self_play", None),
            preset_registry=getattr(app, "preset_registry", None),
            selected_genre=getattr(app, "selected_genre", None),
            get_protagonist_name=getattr(app, "_get_protagonist_name", None),
            audit_event=getattr(app, "_audit_event", None),
            write_audit_summary=getattr(app, "_write_audit_summary", None),
            get_arc_context_for_episode=getattr(app, "_get_arc_context_for_episode", None),
            get_max_episode_from_manuscripts=getattr(app, "_get_max_episode_from_manuscripts", None),
            get_int_input=getattr(app, "_get_int_input", None),
            safe_commit=getattr(app, "_safe_commit", None),
            validate_arc_data_fields=getattr(app, "_validate_arc_data_fields", None),
            validate_blueprint_integrity=getattr(app, "_validate_blueprint_integrity", None),
            fix_entity_registry_protagonist=getattr(app, "_fix_entity_registry_protagonist", None),
        )
