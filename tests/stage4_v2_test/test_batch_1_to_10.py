"""
Stage 4 V2 배치 테스트 - 1~10화 순차 생성
"""

import json
import os
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
from google import genai

from modules.core.constants import AIModels
from modules.core.db_manager import DBManager
from modules.domain.agents.chief_writer import ChiefWriter
from modules.domain.agents.director import Director
from modules.domain.agents.manuscript_validator import ManuscriptValidator


class TestProjectContext:
    """테스트용 프로젝트 컨텍스트"""

    def __init__(self, db_path):
        self.db = DBManager(db_path)
        self.master_bible = self.db.load_anchor("bible") or {}
        self._manuscripts = {}  # 생성된 원고 캐시

    @property
    def latest_state(self):
        state = self.db.get_latest_state()
        if not state:
            bible_root = self.master_bible.get("MasterBible", self.master_bible)
            return bible_root.get("MartialHUD", {})
        return state

    def get_manuscript(self, ep_num):
        """생성된 원고 조회 (DB 또는 캐시)"""
        if ep_num in self._manuscripts:
            return self._manuscripts[ep_num]
        return self.db.get_manuscript(ep_num)

    def save_manuscript_cache(self, ep_num, title, content):
        """원고 캐시 저장"""
        self._manuscripts[ep_num] = {"ep_num": ep_num, "title": title, "content": content}


def run_batch_test(start_ep: int = 1, end_ep: int = 10):
    """배치 테스트 실행"""
    print("\n" + "=" * 70)
    print(f"🎬 Stage 4 V2 배치 테스트 - {start_ep}~{end_ep}화")
    print(f"   시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 환경 설정
    test_dir = os.path.dirname(__file__)
    env_path = os.path.join(test_dir, "project", ".env")
    load_dotenv(env_path)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        load_dotenv(os.path.join(ROOT, ".env"))
        api_key = os.getenv("GOOGLE_API_KEY")

    client = genai.Client(api_key=api_key)

    # 프로젝트 컨텍스트
    db_path = os.path.join(test_dir, "project", "project_data.db")
    context = TestProjectContext(db_path)

    # 에이전트 초기화
    chief_writer = ChiefWriter(context=context, client=client, model_tier=AIModels.STAGE4_FIXED_WRITER_MODEL)
    manuscript_validator = ManuscriptValidator(context=context)
    director = Director(context=context, client=client, model_tier="gemini-2.5-pro")

    # 결과 저장
    results = []
    result_dir = os.path.join(test_dir, "results")
    os.makedirs(result_dir, exist_ok=True)

    total_start = time.time()

    for ep_num in range(start_ep, end_ep + 1):
        # Blueprint 확인
        blueprint = context.db.get_blueprint(ep_num)
        if not blueprint:
            print(f"\n⚠️ {ep_num}화 Blueprint 없음 - 스킵")
            results.append({"ep": ep_num, "status": "SKIP", "reason": "No blueprint"})
            continue

        print(f"\n{'=' * 60}")
        print(f"📝 제{ep_num}화 생성 시작")
        print(f"{'=' * 60}")

        ep_start = time.time()

        # 이전 원고
        prev_manuscript = ""
        prev_ending = ""
        if ep_num > 1:
            prev_ms = context.get_manuscript(ep_num - 1)
            if prev_ms:
                prev_manuscript = prev_ms.get("content", "")
                prev_ending = prev_manuscript[-500:] if prev_manuscript else ""

        # Arc 정보
        arc_no = (ep_num - 1) // 5 + 1
        arc_pos = ((ep_num - 1) % 5) + 1
        arc_data = context.db.load_anchor(f"arc_{arc_no:03d}")
        arc_tactical = arc_data.get("tactical_doc", "") if arc_data else ""

        # HUD
        hud_state = context.latest_state
        hud_report = json.dumps(hud_state, ensure_ascii=False) if hud_state else ""

        # 면담 루프 (최대 3회)
        final_manuscript = None
        final_title = None
        director_feedback = ""

        for interview in range(3):
            print(f"   🎭 [{interview + 1}차 면담] 앙상블 생성 중...")

            try:
                if interview == 0:
                    candidates = chief_writer.generate_ensemble(
                        ep_num=ep_num,
                        blueprint=blueprint,
                        prev_manuscript=prev_manuscript,
                        hud_report=hud_report,
                        arc_doc=arc_tactical,
                        master_bible=context.master_bible,
                        style_guide="",
                        genre_name="무협",
                    )
                else:
                    candidates = chief_writer.regenerate_with_feedback(
                        ep_num=ep_num,
                        blueprint=blueprint,
                        prev_manuscript=prev_manuscript,
                        hud_report=hud_report,
                        arc_doc=arc_tactical,
                        master_bible=context.master_bible,
                        style_guide="",
                        director_feedback=director_feedback,
                        previous_attempt={},
                        attempt_number=interview + 1,
                        genre_name="무협",
                    )

                # 후보 요약
                for c in candidates:
                    ms_len = len(c.get("manuscript", ""))
                    strategy = c.get("strategy_name", c.get("strategy", "?"))
                    print(f"      • {strategy}: {ms_len}자")

                # Python 검증
                validation_results = manuscript_validator.validate_all_candidates(
                    candidates=candidates, blueprint=blueprint, prev_manuscript=prev_manuscript, hud_report=hud_report
                )

                # Director 면담
                director_result = director.select_and_judge_ensemble(
                    ep_num=ep_num,
                    candidates=candidates,
                    validation_results=validation_results,
                    blueprint=blueprint,
                    previous_ending=prev_ending,
                    arc_pos=arc_pos,
                    total_eps=5,
                    retry_count=interview,
                )

                verdict = director_result.get("verdict", "REJECT")
                score = director_result.get("score", 0)
                selected = director_result.get("selected", "A")

                print(f"   📊 판정: {verdict} (점수: {score}, 선택: {selected})")

                if verdict == "PASS":
                    selected_candidate = director_result.get("selected_candidate", {})
                    final_manuscript = selected_candidate.get("manuscript", "")
                    final_title = selected_candidate.get("title", f"제{ep_num}화")
                    break
                else:
                    feedback = director_result.get("feedback", {})
                    action_items = director_result.get("action_items", [])
                    director_feedback = "\n".join(action_items) if action_items else str(feedback)

            except Exception as e:
                print(f"   ❌ 에러: {str(e)[:100]}")
                continue

        ep_elapsed = time.time() - ep_start

        if final_manuscript:
            # 저장
            result_file = os.path.join(result_dir, f"ep_{ep_num:04d}.txt")
            with open(result_file, "w", encoding="utf-8") as f:
                f.write(f"# {final_title}\n\n{final_manuscript}")

            # 캐시에 저장 (다음 화 참조용)
            context.save_manuscript_cache(ep_num, final_title, final_manuscript)

            results.append(
                {
                    "ep": ep_num,
                    "status": "PASS",
                    "title": final_title,
                    "length": len(final_manuscript),
                    "score": score,
                    "time": round(ep_elapsed, 1),
                }
            )
            print(f"   ✅ 저장 완료: {len(final_manuscript)}자, {ep_elapsed:.1f}초")
        else:
            results.append({"ep": ep_num, "status": "FAIL", "time": round(ep_elapsed, 1)})
            print("   ❌ 3번 모두 REJECT")

    # 최종 결과
    total_elapsed = time.time() - total_start

    print("\n" + "=" * 70)
    print("📊 최종 결과")
    print("=" * 70)

    pass_count = sum(1 for r in results if r.get("status") == "PASS")
    fail_count = sum(1 for r in results if r.get("status") == "FAIL")
    skip_count = sum(1 for r in results if r.get("status") == "SKIP")

    print(f"   • 성공: {pass_count}개")
    print(f"   • 실패: {fail_count}개")
    print(f"   • 스킵: {skip_count}개")
    print(f"   • 총 소요: {total_elapsed / 60:.1f}분")

    print("\n상세 결과:")
    for r in results:
        if r.get("status") == "PASS":
            print(f"   {r['ep']:2d}화: ✅ PASS | {r['length']:,}자 | 점수 {r['score']} | {r['time']}초")
        elif r.get("status") == "FAIL":
            print(f"   {r['ep']:2d}화: ❌ FAIL | {r['time']}초")
        else:
            print(f"   {r['ep']:2d}화: ⏭️ SKIP | {r.get('reason', '')}")

    # 결과 JSON 저장
    summary_file = os.path.join(result_dir, "batch_result.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "start_ep": start_ep,
                "end_ep": end_ep,
                "total_time": round(total_elapsed, 1),
                "pass_count": pass_count,
                "fail_count": fail_count,
                "skip_count": skip_count,
                "results": results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n📁 결과 저장: {summary_file}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=2, help="Start episode")
    parser.add_argument("--end", type=int, default=10, help="End episode")
    args = parser.parse_args()

    run_batch_test(args.start, args.end)
