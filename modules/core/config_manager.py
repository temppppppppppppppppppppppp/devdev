
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
        
        # [V20 Master Model Tiers] 각 단계별 최적 모델 배정
        # Stage 1~2: 대량의 맥락 분석 (Gemini 3 Pro급 권장)
        # Stage 3~4: 고해상도 묘사 및 집필 (Gemini 2.5 Pro급 권장)
        self.settings = {
            "models": {
                "analyst": "gemini-2.5-pro",   # 전략/전술 설계 (고지능)
                "architect": "gemini-2.5-pro", # 초정밀 시나리오 설계
                "writer": "gemini-3-pro-preview",#"gemini-3-pro-preview",    # 7,000자 고해상도 집필
                "director": "gemini-2.5-flash",#"gemini-2.5-pro", # 빠른 품질 검수
                "manager": "gemini-2.5-flash",   # 인과 분석 및 데이터 박제
                "editor": "gemini-2.5-flash"   # 최후의 보루
                
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
        return self.settings["models"].get(agent_role, "gemini-1.5-flash")

    def __getitem__(self, key): return self.settings[key]
