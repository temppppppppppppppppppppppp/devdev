# -*- coding: utf-8 -*-
"""
[V60.80] Stage 3 Production Test - 실전 동일 환경
목표: 제1화~제10화 (Arc 1-2) Blueprint 생성
"""

import os
import sys
import io

import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

SOURCE_PROJECT = PROJECT_ROOT / "projects" / "팽가 망나니 가문 재건"
TEST_DIR = Path(__file__).parent


class ProductionContext:
    """실전 동일 ProjectContext"""

    def __init__(self, db_path: Path, config_root: Path):
        self.db_path = db_path
        self.config_root = config_root

        # DB 로드
        self._load_from_db()

        # Config 로드
        self._load_configs()

        # 런타임 저장소
        self._blueprints = {}
        self._manuscripts = {}

    def _load_from_db(self):
        """DB에서 모든 데이터 로드 (실전 동일)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Bible
        cursor.execute("SELECT data FROM anchors WHERE key = 'bible'")
        row = cursor.fetchone()
        self.bible = json.loads(row[0]) if row else {}

        # Arcs (DB만 사용, txt 안 씀!)
        cursor.execute("SELECT data FROM anchors WHERE key = 'arcs'")
        row = cursor.fetchone()
        self.arcs = json.loads(row[0]) if row else []

        # Encyclopedia
        cursor.execute("SELECT * FROM encyclopedia")
        rows = cursor.fetchall()
        self.encyclopedia = {row[0]: row[1] if len(row) > 1 else None for row in rows}

        # Genre Info
        cursor.execute("SELECT data FROM anchors WHERE key = 'genre_info'")
        row = cursor.fetchone()
        self.genre_info = json.loads(row[0]) if row else {}

        conn.close()

        # MasterBible 추출
        self.master_bible = self.bible.get('MasterBible', {})
        self.martial_hud = self.master_bible.get('MartialHUD', {})
        self.world_state = self.master_bible.get('WorldState', {})
        self.asset_library = self.master_bible.get('AssetLibrary', {})

        # 주인공 정보
        protagonist_data = self.martial_hud.get('Protagonist', {}).get('actual_truth', {})
        self.protagonist_name = protagonist_data.get('name', '주인공')

    def _load_configs(self):
        """Config JSON 로드"""
        self.configs = {}

        # settings.json
        settings_path = self.config_root / "settings.json"
        if settings_path.exists():
            with open(settings_path, 'r', encoding='utf-8') as f:
                self.configs['settings'] = json.load(f)

        # tone_presets.json
        tone_path = self.config_root / "tone_presets.json"
        if tone_path.exists():
            with open(tone_path, 'r', encoding='utf-8') as f:
                self.configs['tone_presets'] = json.load(f)

        # writer_rules.json
        writer_rules_path = self.config_root / "prompts" / "writer_rules.json"
        if writer_rules_path.exists():
            with open(writer_rules_path, 'r', encoding='utf-8') as f:
                self.configs['writer_rules'] = json.load(f)

        # architect_rules.json
        arch_rules_path = self.config_root / "prompts" / "architect_rules.json"
        if arch_rules_path.exists():
            with open(arch_rules_path, 'r', encoding='utf-8') as f:
                self.configs['architect_rules'] = json.load(f)

        # style_seeds (카카오 문체)
        style_path = self.config_root / "cash" / "style_seeds_final.txt"
        if style_path.exists():
            with open(style_path, 'r', encoding='utf-8') as f:
                self.configs['style_seeds'] = f.read()

    def get_blueprint(self, ep_num: int) -> Optional[Dict]:
        return self._blueprints.get(ep_num)

    def save_episode_blueprint(self, ep_num: int, blueprint: Dict):
        self._blueprints[ep_num] = blueprint

    def get_causal_history_summary(self) -> str:
        """인과 히스토리 요약 생성"""
        if not self._blueprints:
            return f"[서사 시작] 주인공 {self.protagonist_name}의 이야기가 시작됩니다."

        summaries = []
        for ep_num in sorted(self._blueprints.keys()):
            bp = self._blueprints[ep_num]
            title = bp.get('title', f'제{ep_num}화')
            ending = bp.get('ending_hook', '')[:100]
            summaries.append(f"제{ep_num}화 [{title}]: {ending}")

        return "\n".join(summaries[-5:])  # 최근 5개

    def get_arc_for_episode(self, ep_num: int) -> tuple:
        """에피소드에 해당하는 Arc 찾기"""
        for idx, arc in enumerate(self.arcs):
            ep_start = arc.get('ep_start', 0)
            ep_end = arc.get('ep_end', 0)
            if ep_start <= ep_num <= ep_end:
                return idx, arc
        return None, None


def setup_environment():
    """환경 설정"""
    print("=" * 70)
    print("[Setup] 실전 동일 환경 구성")
    print("=" * 70)

    env_path = SOURCE_PROJECT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"  [OK] .env")

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("  [FAIL] GOOGLE_API_KEY 없음")
        return False
    print(f"  [OK] API Key")
    return True


def print_context_summary(ctx: ProductionContext):
    """컨텍스트 요약 출력"""
    print("\n[Context] 로드된 데이터")
    print("-" * 50)
    print(f"  Bible: {len(json.dumps(ctx.bible)):,} bytes")
    print(f"  Arcs: {len(ctx.arcs)}개")
    print(f"  Encyclopedia: {len(ctx.encyclopedia)}개 항목")
    print(f"  주인공: {ctx.protagonist_name}")
    print(f"  Configs: {list(ctx.configs.keys())}")
    if 'style_seeds' in ctx.configs:
        print(f"  카카오 문체: {len(ctx.configs['style_seeds']):,} bytes")
    print("-" * 50)


def run_production_test(ctx: ProductionContext, target_episodes: List[int]):
    """실전 동일 테스트 실행"""
    print("\n" + "=" * 70)
    print(f"[Test] Stage 3 Production Test")
    print(f"       목표: 제{target_episodes[0]}화 ~ 제{target_episodes[-1]}화 ({len(target_episodes)}개)")
    print("=" * 70)

    from google import genai
    from modules.domain.agents.three_phase_blueprint_generator import ThreePhaseBlueprintGenerator
    from modules.domain.agents.director import Director

    # API 클라이언트
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    # 에이전트 (실전: gemini-2.5-flash 사용)
    three_phase = ThreePhaseBlueprintGenerator(ctx, client, model_tier="gemini-2.5-flash")
    director = Director(ctx, client, model_tier="gemini-2.5-flash")

    print(f"\n  [OK] 에이전트 생성")
    print(f"  [INFO] 모델: gemini-2.5-flash")

    # 결과 추적
    results = {
        "start_time": datetime.now().isoformat(),
        "target_episodes": target_episodes,
        "results": {},
        "summary": {"total": len(target_episodes), "pass": 0, "fail": 0}
    }

    prev_blueprint = None
    prev_blueprints = []

    for ep_num in target_episodes:
        # Arc 찾기
        arc_idx, arc_data = ctx.get_arc_for_episode(ep_num)
        if arc_data is None:
            print(f"\n  [SKIP] 제{ep_num}화 - Arc 없음")
            results["results"][ep_num] = {"status": "SKIP", "reason": "No Arc"}
            continue

        arc_no = arc_data.get('arc_no', arc_idx + 1)

        print(f"\n{'─' * 60}")
        print(f"  제{ep_num}화 (Arc {arc_no}) 생성 중...")
        print(f"{'─' * 60}")

        try:
            blueprint, pipeline_result = three_phase.generate(
                ep_num=ep_num,
                arc_data=arc_data,
                prev_blueprint=prev_blueprint,
                prev_blueprints=prev_blueprints[-5:] if prev_blueprints else None,
                max_retries=2,  # 총 3번 시도
                director=director,
                arc_idx=arc_idx
            )

            if blueprint and pipeline_result.get("final_verdict") == "PASS":
                results["summary"]["pass"] += 1
                results["results"][ep_num] = {
                    "status": "PASS",
                    "title": blueprint.get("title", "?"),
                    "scenes": len(blueprint.get("scene_breakdown", {})),
                    "length": len(blueprint.get("integrated_scenario", "")),
                    "retries": pipeline_result.get("retries", 0)
                }

                print(f"  [PASS] 제{ep_num}화 - {blueprint.get('title', '?')}")
                print(f"         씬: {len(blueprint.get('scene_breakdown', {}))}개, "
                      f"길이: {len(blueprint.get('integrated_scenario', ''))}자")

                # 다음 화를 위해 저장
                ctx.save_episode_blueprint(ep_num, blueprint)
                prev_blueprint = blueprint
                prev_blueprints.append(blueprint)

            else:
                results["summary"]["fail"] += 1
                results["results"][ep_num] = {
                    "status": "FAIL",
                    "verdict": pipeline_result.get("final_verdict", "?"),
                    "retries": pipeline_result.get("retries", 0)
                }
                print(f"  [FAIL] 제{ep_num}화 - {pipeline_result.get('final_verdict', '?')}")

        except Exception as e:
            results["summary"]["fail"] += 1
            results["results"][ep_num] = {"status": "ERROR", "error": str(e)[:200]}
            print(f"  [ERROR] 제{ep_num}화 - {str(e)[:100]}")
            import traceback
            traceback.print_exc()

    # 최종 요약
    results["end_time"] = datetime.now().isoformat()

    print("\n" + "=" * 70)
    print("[Result] 최종 결과")
    print("=" * 70)
    print(f"  총 시도: {results['summary']['total']}개")
    print(f"  성공: {results['summary']['pass']}개")
    print(f"  실패: {results['summary']['fail']}개")
    print(f"  성공률: {results['summary']['pass'] / results['summary']['total'] * 100:.1f}%")

    # Generator 통계
    if hasattr(three_phase, 'get_stats'):
        stats = three_phase.get_stats()
        print(f"\n  [Generator 통계]")
        print(f"    Phase 1: {stats.get('phase1_complete', 0)}회")
        print(f"    Phase 2: {stats.get('phase2_complete', 0)}회")
        print(f"    Phase 3 PASS: {stats.get('phase3_pass', 0)}회")
        print(f"    Phase 3 REJECT: {stats.get('phase3_reject', 0)}회")

    return results


def main():
    print("\n" + "=" * 70)
    print("  [V60.80] Stage 3 Production Test")
    print("  실전 동일 환경 - 제1화~제10화 Blueprint 생성")
    print("=" * 70)

    # 1. 환경 설정
    if not setup_environment():
        return

    # 2. 컨텍스트 로드 (DB만 사용!)
    ctx = ProductionContext(
        db_path=SOURCE_PROJECT / "project_data.db",
        config_root=PROJECT_ROOT / "config"
    )
    print_context_summary(ctx)

    # 3. 테스트 실행 (제1화~제10화)
    target_episodes = list(range(1, 11))  # 1~10화

    results = run_production_test(ctx, target_episodes)

    # 4. 결과 저장
    result_file = TEST_DIR / f"production_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n  [OK] 결과 저장: {result_file.name}")

    # 5. 성공한 Blueprint 저장
    if ctx._blueprints:
        bp_file = TEST_DIR / f"blueprints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(bp_file, 'w', encoding='utf-8') as f:
            json.dump(ctx._blueprints, f, ensure_ascii=False, indent=2, default=str)
        print(f"  [OK] Blueprint 저장: {bp_file.name}")

    print("\n" + "=" * 70)
    success_rate = results['summary']['pass'] / results['summary']['total'] * 100
    status = "SUCCESS" if success_rate >= 80 else "PARTIAL" if success_rate >= 50 else "FAILED"
    print(f"  테스트 완료! [{status}] 성공률: {success_rate:.1f}%")
    print("=" * 70)


if __name__ == "__main__":
    # Windows UTF-8 출력 설정 (pytest 수집 시 capture 파괴 방지)
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    main()
