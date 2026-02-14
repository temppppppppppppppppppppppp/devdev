"""[Phase 4C-4] Stage3 DI 컨텍스트 — 속성·콜백 의존 주입"""


class Stage3Context:
    """Stage3Orchestrator의 DI 컨텍스트.

    [4C-4a] 필수 2종: ui, current_project
    [4C-4b] 콜백 1종: get_protagonist_name
    """

    __slots__ = (
        "ui",
        "current_project",
        "get_protagonist_name",
    )

    def __init__(self, *, ui, current_project, get_protagonist_name=None):
        self.ui = ui
        self.current_project = current_project
        self.get_protagonist_name = get_protagonist_name

    @classmethod
    def from_app(cls, app):
        """SovereignApp에서 속성 추출"""
        return cls(
            ui=app.ui,
            current_project=app.current_project,
            get_protagonist_name=getattr(app, "_get_protagonist_name", None),
        )
