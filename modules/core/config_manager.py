
import os
from pathlib import Path

class ConfigManager:
    """[V20 Sovereign Config] 모델 티어 배정 및 프로젝트 경로 체계를 총괄 관리"""

    def __init__(self):
        self.root = Path.cwd()
        
        # 1. 프로젝트 폴더 생성
        self.projects_dir = self.root / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. [🔥 추가] 로그 폴더 생성 로직
        self.logs_dir = self.root / "logs" 
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 [System] 필수 경로 점검 완료: {self.logs_dir}")
        
        # [V60.24] 모든 모델을 Gemini 3로 통일
        # Stage 1~4: 모든 단계에서 Gemini 3 Pro 사용
        self.settings = {
            "models": {
                "analyst": "gemini-3-pro-preview",   # [V60.24] Gemini 3
                # [V65] architect 삭제 (레거시 에이전트 제거)
                "writer": "gemini-3-pro-preview",    # 7,000자 고해상도 집필
                "director": "gemini-3-pro-preview",  # [V60.24] Gemini 3
                "manager": "gemini-3-pro-preview",   # [V60.24] Gemini 3
                "editor": "gemini-3-pro-preview"     # [V60.24] Gemini 3

            },
            "limits": {
                "max_retries": 10,             # V20 매니페스토 기준 재시도 횟수
                "target_manuscript_length": 5000 # 목표 원고 자수
            }
        }

    def get_v20_project_paths(self, project_name):
        """V20 표준 폴더 구조 정의"""
        base = self.projects_dir / project_name
        return {
            'root': base,
            'config': base / "config",
            'db': base / "db",
            'drafts': base / "drafts",
            'logs': base / "logs",
            'blueprints': base / "blueprints", # Stage 3 설계도 폴더
            'memory': base / "chroma_db"
        }

    def get_model_for_agent(self, agent_role):
        return self.settings["models"].get(agent_role, "gemini-2.5-flash")

    def __getitem__(self, key): return self.settings[key]
