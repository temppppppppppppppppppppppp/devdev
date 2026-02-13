"""[Phase 4C-2a] Stage4 DI 파일럿 컨텍스트 — 상위 5종 의존 주입"""


class Stage4Context:
    """Stage4Orchestrator의 DI 파일럿 컨텍스트.

    파일럿 대상 5종: ui, current_project, agents, sys, state_tracker
    """

    __slots__ = ("ui", "current_project", "agents", "sys", "state_tracker")

    def __init__(self, *, ui, current_project, agents, sys, state_tracker):
        self.ui = ui
        self.current_project = current_project
        self.agents = agents
        self.sys = sys
        self.state_tracker = state_tracker

    @classmethod
    def from_app(cls, app):
        """SovereignApp에서 파일럿 5종 추출"""
        return cls(
            ui=app.ui,
            current_project=app.current_project,
            agents=app.agents,
            sys=app.sys,
            state_tracker=getattr(app, "state_tracker", None),
        )
