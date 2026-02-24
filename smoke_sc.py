#!/usr/bin/env python
"""SC Smoke Test — smart_retrieval 활성화 후 Stage 4 에피소드 1개 생성.

실제 Gemini API를 호출합니다. 비용 ~$0.5~2, 소요 3~10분.
기존 프로젝트(테스트 원고__11, investment)에서 다음 1화 생성.

Usage:
    python smoke_sc.py
"""

import atexit
import builtins
import os
import sys
from pathlib import Path

# ── 인터랙션 차단: input() → 자동 응답 ──
_original_input = builtins.input
_auto_state = {"target_ep": "999"}  # 프로젝트 부팅 후 실제 값으로 갱신


def _auto_input(prompt=""):
    if "몇 화까지" in prompt:
        resp = _auto_state["target_ep"]
    elif any(k in prompt for k in ("1.", "2.", "선택")):
        resp = "1"
    else:
        resp = "y"
    print(f"[AUTO] {prompt.strip()} → '{resp}'")
    return resp


builtins.input = _auto_input

# ── validation.yaml 임시 패치: SC 활성화 ──
YAML_PATH = Path("config/settings/validation.yaml")
_yaml_backup = YAML_PATH.read_text(encoding="utf-8")
_patched = _yaml_backup
for key in ["enabled", "stage2_enabled", "stage4_enabled", "director_enabled"]:
    _patched = _patched.replace(f"  {key}: false", f"  {key}: true")
YAML_PATH.write_text(_patched, encoding="utf-8")
print("[SC-SMOKE] smart_retrieval 전체 활성화 완료")


def _restore_yaml():
    YAML_PATH.write_text(_yaml_backup, encoding="utf-8")
    print("[SC-SMOKE] validation.yaml 원복 완료")


atexit.register(_restore_yaml)

# ── 로그 캡처: [SC] 패턴 수집 ──
_sc_logs: list[str] = []


# ── 메인 ──
def main():
    from dotenv import load_dotenv

    load_dotenv(override=True)

    if not os.getenv("GOOGLE_API_KEY"):
        print("[SC-SMOKE] GOOGLE_API_KEY가 없습니다. .env를 확인하세요.")
        sys.exit(1)

    from main_a import SovereignApp

    app = SovereignApp()

    # ── 1. 장르 설정 (investment = 3번) ──
    from modules.core.constants import GenreTypes, HUDKeys

    app.selected_genre = {
        "name": f"{GenreTypes.get_name(GenreTypes.INVESTMENT)} (Investment)",
        "type": GenreTypes.INVESTMENT,
        "hud_key": HUDKeys.INVESTMENT_HUD_ROOT,
        "description": "금융 배경, 자본/투자 시스템, 기업/시장",
        "critical_keys": [
            "capital",
            "total_assets",
            "stocks",
            "reputation",
            "connections",
            "market_insight",
            "status",
        ],
    }
    print(f"[SC-SMOKE] 장르: {app.selected_genre['name']}")

    # ── 2. 프로젝트 부팅 ──
    PROJECT_NAME = "테스트 원고__11"

    project_env = Path(f"projects/{PROJECT_NAME}/.env")
    if project_env.exists():
        load_dotenv(project_env, override=True)
        import google.genai as genai

        from modules.core.system import StudioSystem

        new_key = os.getenv("GOOGLE_API_KEY")
        if new_key:
            app.sys = StudioSystem(api_client=genai.Client(api_key=new_key))
            from modules.domain.agents.base_agent import BaseAgent

            BaseAgent._keys_initialized = False
            BaseAgent._current_key_idx = 0
            BaseAgent._context_caches.clear()
            BaseAgent._init_api_keys()

    _genre_type = app.selected_genre.get("type", "wuxia") if isinstance(getattr(app, "selected_genre", None), dict) else "wuxia"
    app.sys.boot_v20_project(PROJECT_NAME, genre=_genre_type)
    app.current_project = app.sys.project
    app.current_project.genre = app.selected_genre

    from modules.core.prompt_loader import PromptLoader

    PromptLoader().invalidate_cache()

    # 장르 정보 검증 (불일치 시 자동 'y' 응답)
    stored_genre = app.current_project.db.load_anchor("genre_info")
    if stored_genre:
        if stored_genre.get("type") != app.selected_genre["type"]:
            print(f"[SC-SMOKE] ⚠️ 장르 불일치: stored={stored_genre.get('type')}, selected={app.selected_genre['type']}")

    # ── 3. HUD + Guard + VecMemory ──
    from modules.core.genre_guards import create_genre_guard
    from modules.core.genre_hud_manager import create_hud_manager
    from modules.core.vec_memory import VecMemory

    app.sys.hud = create_hud_manager(app.selected_genre["type"], app.current_project)
    app.sys.guard = create_genre_guard(app.selected_genre["type"])
    app.current_project.guard = app.sys.guard

    app.current_project.paths.memory.mkdir(parents=True, exist_ok=True)
    app.memory = VecMemory(
        api_key=os.getenv("GOOGLE_API_KEY", ""),
        ui_log=app.ui.log,
        conn=app.current_project.db.conn,
        lock=app.current_project.db._lock,
    )
    print(f"[SC-SMOKE] VecMemory operational: {app.memory.is_operational()}")

    # ── 4. 에이전트 초기화 ──
    if not app._attach_agents():
        print("[SC-SMOKE] 에이전트 초기화 실패!")
        sys.exit(1)
    print("[SC-SMOKE] 에이전트 초기화 완료")

    # ── 4.5 limit_mode 에피소드 제한 설정 ──
    next_ep = app.current_project.get_latest_episode_number() + 1
    _auto_state["target_ep"] = str(next_ep)
    print(f"[SC-SMOKE] 목표: {next_ep}화 1개만 생성 (limit_mode=True)")

    # ── 5. ui.log 래핑: [SC] 로그 캡처 ──
    _original_log = app.ui.log

    def _capturing_log(msg, *args, **kwargs):
        _original_log(msg, *args, **kwargs)
        if isinstance(msg, str) and "[SC" in msg:
            _sc_logs.append(msg)

    app.ui.log = _capturing_log

    # logging 모듈 [SC] 캡처
    import logging

    class SCLogHandler(logging.Handler):
        def emit(self, record):
            msg = self.format(record)
            if "[SC" in msg:
                _sc_logs.append(msg)

    _sc_handler = SCLogHandler()
    _sc_handler.setLevel(logging.DEBUG)
    # root logger 레벨을 DEBUG로 낮춰야 logging.info/debug 메시지가 핸들러에 도달
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().addHandler(_sc_handler)

    # ── 6. Stage 4 실행 (에피소드 1개) ──
    print("\n" + "=" * 60)
    print(f"[SC-SMOKE] Stage 4 시작 — 에피소드 {next_ep}화 생성")
    print("=" * 60 + "\n")

    try:
        app._stage_4_v2_chief_writer(limit_mode=True)
    except Exception as e:
        print(f"\n[SC-SMOKE] Stage 4 실행 중 오류: {e}")
        import traceback

        traceback.print_exc()

    # ── 7. 결과 리포트 ──
    print("\n" + "=" * 60)
    print("[SC-SMOKE] 결과 리포트")
    print("=" * 60)

    if _sc_logs:
        print(f"\n✅ [SC] 로그 {len(_sc_logs)}건 캡처됨:")
        for i, log in enumerate(_sc_logs[:30], 1):
            print(f"  {i:2d}. {log[:120]}")
        if len(_sc_logs) > 30:
            print(f"  ... 외 {len(_sc_logs) - 30}건")
    else:
        print("\n❌ [SC] 로그 0건 — SC 경로가 실행되지 않았을 수 있음")

    # 원고 확인
    last_ep = app.current_project.db.cursor.execute("SELECT MAX(ep_num) FROM manuscripts").fetchone()[0]
    print(f"\n최종 원고 에피소드: {last_ep}화")
    if last_ep and last_ep >= next_ep:
        print(f"✅ {next_ep}화 원고 생성 성공!")
    else:
        print(f"⚠️ {next_ep}화 원고 미생성 — Stage 4가 완료되지 않았을 수 있음")

    # cleanup
    logging.getLogger().removeHandler(_sc_handler)
    builtins.input = _original_input
    print("\n[SC-SMOKE] 완료.")


if __name__ == "__main__":
    main()
