import logging
from pathlib import Path

from .config_manager import ConfigManager
from .jianghu_logic import JianghuLogic
from .karma_service import KarmaService  # 👈 임포트 추가
from .lore_manager import LoreManager
from .martial_manager import MartialManager
from .project_manager import ProjectContext
from .technique_weaver import TechniqueWeaver


class StudioSystem:
    """[V20 Core Engine] 매니페스토 공정 전체를 기동하고 서비스를 관리하는 최상위 시스템"""

    def __init__(self, api_client=None) -> None:
        self.root = Path.cwd()
        self.config = ConfigManager()
        self.project = None

        # V20 핵심 서비스 레이어 (지연 로딩 방식)
        self.lore = None
        self.martial = None
        self.world = None
        self.techniques = None
        self.guard = None
        self.hud = None
        self.api_client = api_client  # main.py에서 주입받은 클라이언트를 할당

    def boot_v20_project(self, project_name: str) -> None:
        """[Phase 0] V20 지능 기동 및 시스템 복구"""
        logging.info(f"🚀 [Phase 0] 프로젝트 '{project_name}' V20 지능 기동 중...")

        # 1. 데이터 앵커링 엔진 기동 (ProjectContext)
        self.project = ProjectContext(project_name)

        # 2. 강호 물리 및 로어 서비스 연동
        self.lore = LoreManager(self.project)
        self.martial = MartialManager(self.project)
        self.world = JianghuLogic(self.project)
        self.techniques = TechniqueWeaver()
        # [V40] guard는 장르 선택 후 main_a.py에서 동적으로 초기화됨
        self.guard = None
        self.karma = KarmaService(self.project)  # 👈 서비스 기동

        logging.info(f"✅ [System] 모든 V20 서비스 계층이 프로젝트 '{project_name}'에 결착되었습니다.")

    def get_v20_orchestrator_config(self) -> dict:
        """[V25] 에이전트들이 참조할 시스템 통합 설정 반환 (누락 서비스 보완)"""
        return {
            "project": self.project,
            "api_client": self.api_client,
            "martial": self.martial,
            "world": self.world,
            "techniques": self.techniques,
            "guard": self.guard,
            "karma": self.karma,
            "models": self.config["models"],
        }

    def check_v20_readiness(self) -> dict:
        """[V25] SQL DB Anchors를 조회하여 각 공정의 완료 여부를 반환"""
        status = {"Stage 0 (Bible)": False, "Stage 1 (Volumes)": False, "Stage 2 (Arcs)": False}

        if not self.project or not hasattr(self.project, "db"):
            return status

        try:
            # [V70] DBManager safe API 사용 (직접 cursor 접근 제거)
            bible_data = self.project.db.load_anchor("bible")
            status["Stage 0 (Bible)"] = bool(bible_data)

            vols_data = self.project.db.load_anchor("volumes")
            status["Stage 1 (Volumes)"] = bool(vols_data)

            arcs_data = self.project.db.load_anchor("arcs")
            status["Stage 2 (Arcs)"] = bool(arcs_data)

        except Exception:
            # 테이블이 없거나 DB 연결 오류 시 False 유지
            pass

        return status
