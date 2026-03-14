"""
[Phase 4C-1b] Stage01Helpers — SovereignApp의 Stage 0/1 로직 캡슐화

원본: main_a.py (4개 메서드, ~616줄)
  - _phase_0_recovery  (L1994-2139, 146줄) [4C-1b-a]
  - _extend_blocks     (L2347-2429, 83줄)  [4C-1b-a]
  - _stage_0_extended  (L2141-2345, 205줄) [4C-1b-b]
  - _stage_1_volumes   (L2431-2612, 182줄) [4C-1b-b]

패턴: self.app = SovereignApp 인스턴스 (Stage2/3/4 Orchestrator와 동일)
"""

import json
import logging
import re

from modules.core.project_support import (
    EXTERNAL_POV_INSERT_POLICY_OPTIONS,
    INCARNATION_TYPE_OPTIONS,
    POV_OPTIONS,
    WORLD_ORIGIN_OPTIONS,
    default_external_pov_insert_policy,
    resolve_external_pov_insert_policy_choice,
    resolve_indexed_menu_choice,
)


class Stage01Helpers:
    """
    [Phase 4C-1b] SovereignApp의 Stage 0 / Stage 1 로직 캡슐화

    패턴: self.app = SovereignApp 인스턴스
    """

    def __init__(self, app) -> None:
        self.app = app

    @staticmethod
    def _prompt_with_ui(app, prompt_text: str, **context) -> str:
        ui = getattr(app, "ui", None)
        if hasattr(type(ui), "prompt"):
            return ui.prompt(prompt_text, component="Stage0", stage="stage0", **context)
        try:
            return input(prompt_text)
        except (EOFError, KeyboardInterrupt, ValueError):
            return ""

    @classmethod
    def _pause_with_ui(cls, app, prompt_text: str = "\n[Enter] 메뉴로 돌아가기", **context) -> None:
        try:
            cls._prompt_with_ui(app, prompt_text, **context)
        except (EOFError, KeyboardInterrupt, ValueError):
            pass

    @staticmethod
    def validate_volume_boundaries(vol_data, vol_idx):
        """권 전략 문서의 미래 권 누수와 비정상 payload를 검증한다."""
        if not isinstance(vol_data, dict):
            return {
                "status": "REJECT",
                "reason": "권 설계 결과 구조가 유효하지 않습니다.",
                "feedback": "dict 형태의 권 설계 결과를 다시 생성하십시오.",
            }

        strategy = vol_data.get("strategy_doc", "")
        if isinstance(strategy, (dict, list)):
            strategy = json.dumps(strategy, ensure_ascii=False)
        elif strategy is None:
            return {
                "status": "REJECT",
                "reason": "strategy_doc가 비어 있습니다.",
                "feedback": "권 전략 문서를 문자열 또는 JSON 직렬화 가능한 구조로 다시 생성하십시오.",
            }
        elif not isinstance(strategy, str):
            return {
                "status": "REJECT",
                "reason": f"strategy_doc 타입이 지원되지 않습니다: {type(strategy).__name__}",
                "feedback": "strategy_doc를 문자열 또는 JSON 직렬화 가능한 구조로 다시 생성하십시오.",
            }

        future_mentions = re.findall(r"제\s*(\d+)\s*권", strategy)
        for mention in future_mentions:
            try:
                mention_vol = int(mention)
            except ValueError:
                continue
            if mention_vol > vol_idx:
                return {
                    "status": "REJECT",
                    "reason": f"미래 권({mention}권) 정보 누수 감지",
                    "feedback": f"제 {vol_idx}권 설계에서 {mention}권 내용을 언급하지 마십시오.",
                }

        future_keywords = ["이후", "다음 권", "훗날", "나중에", "앞으로"]
        future_count = sum(strategy.count(kw) for kw in future_keywords)
        if future_count > 3:
            return {
                "status": "WARNING",
                "reason": f"미래 지향 표현 과다 ({future_count}회)",
                "feedback": "현재 권의 사건에만 집중하십시오.",
            }

        return {"status": "PASS"}

    # ─────────────────────────────────────────────────────────────
    # [4C-1b-a] _phase_0_recovery
    # ─────────────────────────────────────────────────────────────
    def phase_0_recovery(self):
        """[V60.95] Phase 0: 프로젝트 설정 서브메뉴 (원본 main_a.py L1994)"""
        app = self.app

        app.ui.log("\n⚙️ Phase 0: S-Grade 데이터 주권 동기화 가동...")

        # [V40] 장르 정보 표시
        if app.selected_genre:
            app.ui.log(f"📌 현재 장르: {app.selected_genre['name']} ({app.selected_genre['type']})")

        # [V60.95] Stage 0 서브메뉴
        from modules.core.spinners import STAGE0_AVAILABLE

        app.ui.log("\n" + "=" * 50)
        app.ui.log("  📚 Stage 0 - 프로젝트 설정")
        app.ui.log("=" * 50)
        app.ui.log("\n  [1] 기존 방식 - Bible/Treatment 파일 선택")
        if STAGE0_AVAILABLE:
            app.ui.log("  [2] 🆕 컨셉 → Bible 생성 (AI 확장)")
            app.ui.log("  [3] 🔄 역설계 - 기존 원고에서 Bible/스타일 추출")
            app.ui.log("  [4] 📥 Bible JSON 임포트")
            app.ui.log("  [5] 📈 Block 확장 - 기존 Treatment에 블록 추가")
            app.ui.log("  [6] 🎨 스타일 레퍼런스 분석 - 참조 원고에서 문체 DNA 추출")
            app.ui.log("  [7] 🛡 작품가드 설정 (선택)")
        app.ui.log("\n  [0] 취소")

        try:
            p0_choice = self._prompt_with_ui(app, "\n  선택 (기본: 1): ", prompt_id="stage0_phase0_choice").strip()
        except (EOFError, KeyboardInterrupt, ValueError):
            p0_choice = "1"

        if p0_choice == "0":
            app.ui.log("❌ Stage 0이 취소되었습니다.")
            return
        elif p0_choice == "2" and STAGE0_AVAILABLE:
            self.stage_0_extended(mode=1)
            return
        elif p0_choice == "3" and STAGE0_AVAILABLE:
            self.stage_0_extended(mode=2)
            return
        elif p0_choice == "4" and STAGE0_AVAILABLE:
            self.stage_0_extended(mode=3)
            return
        elif p0_choice == "5" and STAGE0_AVAILABLE:
            self.stage_0_extended(mode=4)
            return
        elif p0_choice == "6" and STAGE0_AVAILABLE:
            self.stage_0_extended(mode=5)
            return
        elif p0_choice == "7" and STAGE0_AVAILABLE:
            self.stage_0_extended(mode=6)
            return

        # 기존 방식 계속...
        bible_file = app._ui_select_bible()
        treatment_file = app._ui_select_treatment()

        if not bible_file or not treatment_file:
            app.ui.log("❌ 파일 선택이 취소되어 중단합니다.")
            return

        # [V60.10] Treatment Block 농축 옵션
        try:
            enrich_choice = (
                self._prompt_with_ui(
                    app,
                    "   🔧 [V60.10] Treatment Block 자동 농축을 수행하시겠습니까? (y/N): ",
                    prompt_id="stage0_enrich_treatment_confirm",
                ).strip().lower()
            )
        except (EOFError, KeyboardInterrupt, ValueError):
            enrich_choice = "n"
        if enrich_choice == "y":
            treatment_file = app._enrich_treatment_blocks(treatment_file)

        # [V60.87] 주인공 유형 설정
        app.ui.log("\n📌 [V60.87] 주인공 기본 설정")

        app.ui.log("   🌍 주인공의 세계관 출신을 선택하세요:")
        app.ui.log("      [1] 현대인 - 제약 없음 (권장: 회귀/빙의물)")
        app.ui.log("      [2] 원시인 - 현대 지식/용어 사용 제한 (권장: 무협/판타지)")
        try:
            world_choice = self._prompt_with_ui(app, "   선택 (기본: 1): ", prompt_id="stage0_world_origin_choice").strip()
        except (EOFError, KeyboardInterrupt, ValueError):
            world_choice = ""
        world_origin = resolve_indexed_menu_choice(
            WORLD_ORIGIN_OPTIONS,
            world_choice,
            default="현대인",
        )

        app.ui.log("   🎭 주인공의 유형을 선택하세요:")
        app.ui.log("      [1] 회귀자 - 먼 미래에서 과거로 회귀 (기억 보존)")
        app.ui.log("      [2] 빙의자 - 다른 사람의 몸에 빙의")
        app.ui.log("      [3] 환생자 - 아기로 다시 태어남")
        app.ui.log("      [4] 기타 - 특별한 유형 없음")
        try:
            type_choice = self._prompt_with_ui(app, "   선택 (기본: 1): ", prompt_id="stage0_incarnation_choice").strip()
        except (EOFError, KeyboardInterrupt, ValueError):
            type_choice = ""
        incarnation_type = resolve_indexed_menu_choice(
            INCARNATION_TYPE_OPTIONS,
            type_choice,
            default="일반",
        )

        app.ui.log("   📖 서술 시점을 선택하세요:")
        app.ui.log("      [1] 1인칭 - 주인공 '나'의 시점 (몰입감↑, 정보 제한)")
        app.ui.log("      [2] 3인칭 - 주인공을 '그/그녀'로 지칭 (자유도↑)")
        app.ui.log("      [3] 전지적 - 모든 캐릭터 내면 접근 가능")
        app.ui.log("      [4] 혼합 - 씬 전환마다 시점을 바꿔 사용할 수 있음")
        try:
            pov_choice = self._prompt_with_ui(app, "   선택 (기본: 2): ", prompt_id="stage0_pov_choice").strip()
        except (EOFError, KeyboardInterrupt, ValueError):
            pov_choice = ""
        selected_pov = resolve_indexed_menu_choice(
            POV_OPTIONS,
            pov_choice,
            default="3인칭",
        )

        genre_type = ""
        if app.selected_genre:
            genre_type = str(app.selected_genre.get("type", "") or "").strip().lower()
        default_policy = default_external_pov_insert_policy(selected_pov, genre=genre_type)
        default_index = EXTERNAL_POV_INSERT_POLICY_OPTIONS.index(default_policy) + 1
        app.ui.log("   📝 외부 시점 삽입 정책을 선택하세요:")
        for i, option in enumerate(EXTERNAL_POV_INSERT_POLICY_OPTIONS, 1):
            app.ui.log(f"      [{i}] {option}")
        try:
            policy_choice = self._prompt_with_ui(
                app,
                f"   선택 (기본: {default_index}): ",
                prompt_id="stage0_external_pov_choice",
            ).strip()
        except (EOFError, KeyboardInterrupt, ValueError):
            policy_choice = ""
        selected_external_policy = resolve_external_pov_insert_policy_choice(
            policy_choice,
            primary_pov=selected_pov,
            genre=genre_type,
        )

        protagonist_config = {
            "world_origin": world_origin,
            "incarnation_type": incarnation_type,
            "pov": selected_pov,
            "external_pov_insert_policy": selected_external_policy,
        }
        app.ui.log(f"   ✅ 설정 완료: {world_origin} / {incarnation_type} / {selected_pov}")

        # 2. [필수] 50개 설계도 DNA 강제 이식
        dna_success = app.current_project.force_sync_v25_dna(bible_file, treatment_file)

        if dna_success:
            try:
                master_bible = app.current_project.master_bible or {}
                bible_root = master_bible.get("MasterBible", master_bible)
                bible_root["protagonist_config"] = protagonist_config
                app.current_project.master_bible = {"MasterBible": bible_root}
                app.current_project.save_v20_anchor("bible", app.current_project.master_bible)
                app.ui.log(f"   💾 [V60.87] 주인공 설정이 Bible에 저장됨: {protagonist_config}")
            except Exception as pc_err:
                logging.warning(f" [V60.87] 주인공 설정 저장 실패 (비차단): {pc_err}")

            draft_path = app.current_project.paths.drafts
            existing_drafts = list(draft_path.glob("*.txt"))

            if existing_drafts:
                app.ui.log(f"📂 [Detect] 기존 원고 {len(existing_drafts)}건 발견. 역사 이식을 시작합니다...")
                try:
                    sync_result = app.current_project.sync_existing_manuscripts(app.memory)
                    if sync_result:
                        app.ui.log("✅ [History] 기존 원고의 역사가 모두 시스템에 안착되었습니다.")
                    else:
                        app.ui.log("⚠️ [Warning] 일부 원고 동기화 실패. 로그를 확인하세요.")
                except Exception as sync_err:
                    logging.warning(f" [Error] 원고 동기화 중 오류 발생: {sync_err}")
                    app._audit_event(
                        "sync_error",
                        "sync_existing_manuscripts failed",
                        {"error": str(sync_err), "draft_count": len(existing_drafts)},
                    )
                    app.ui.log("⚠️ [Fallback] 원고 동기화를 건너뛰고 계속 진행합니다.")
            else:
                app.ui.log("🆕 [New Project] 기존 원고가 없습니다. 신규 프로젝트로 기동합니다.")

            app.current_project._load_from_db()
            app.ui.log("✨ [Success] 설계도(50개)와 원고 역사가 무결하게 통합되었습니다.")

        Stage01Helpers._pause_with_ui(app)

    # ─────────────────────────────────────────────────────────────
    # [4C-1b-a] _extend_blocks
    # ─────────────────────────────────────────────────────────────
    def extend_blocks(self, stage0_manager) -> list[dict]:
        """[V61] Block 확장 기능 — 기존 Treatment에 블록 추가 (원본 main_a.py L2347)"""
        app = self.app

        app.ui.log("\n" + "=" * 50)
        app.ui.log("  📈 Block 확장 - 기존 Treatment에 블록 추가")
        app.ui.log("=" * 50)

        # 1. 기존 Treatment 로드
        existing_treatment = []
        treatment_files = [
            app.current_project.paths.root / "treatment_extended.json",
            app.current_project.paths.root / "treatment_generated.json",
            app.current_project.paths.root / "treatment.json",
        ]

        for tf in treatment_files:
            if tf.exists():
                try:
                    with open(tf, encoding="utf-8") as f:
                        data = json.load(f)
                        existing_treatment = data.get("treatments", [])
                        if existing_treatment:
                            app.ui.log(f"   📂 기존 Treatment 로드: {tf.name} ({len(existing_treatment)} 블록)")
                            break
                except Exception as e:
                    logging.warning(f" 파일 로드 실패: {tf.name} - {e}")

        if not existing_treatment:
            app.ui.log("   ❌ 기존 Treatment를 찾을 수 없습니다.")
            app.ui.log("   먼저 [2] 컨셉 → Bible 생성 또는 [3] 역설계를 실행하세요.")
            return []

        # 2. 확장 설정
        app.ui.log(f"\n   현재 블록 수: {len(existing_treatment)}")
        app.ui.log(
            f"   마지막 블록: {existing_treatment[-1].get('block_id', 'N/A')} - {existing_treatment[-1].get('title', 'N/A')}"
        )

        try:
            extend_count = int(
                self._prompt_with_ui(app, "\n   추가할 블록 수 (기본: 10): ", prompt_id="stage0_extend_count").strip()
                or "10"
            )
        except (ValueError, EOFError, KeyboardInterrupt):
            extend_count = 10

        try:
            direction_hint = self._prompt_with_ui(
                app,
                "   방향 힌트 (예: '클라이맥스로', '새 빌런 등장', 생략 가능): ",
                prompt_id="stage0_extend_direction_hint",
            ).strip()
        except (EOFError, KeyboardInterrupt, ValueError):
            direction_hint = ""

        # 3. 배치별 확인 콜백
        def confirm_batch(batch):
            app.ui.log(f"\n   --- 생성된 블록 ({len(batch)}개) ---")
            for b in batch[:3]:
                app.ui.log(f"   • {b.get('block_id', 'N/A')}: {b.get('title', 'N/A')}")
            if len(batch) > 3:
                app.ui.log(f"   ... 외 {len(batch) - 3}개")

            try:
                confirm = self._prompt_with_ui(
                    app,
                    "   계속 진행하시겠습니까? (Y/n): ",
                    prompt_id="stage0_extend_confirm_batch",
                ).strip().lower()
            except (EOFError, KeyboardInterrupt, ValueError):
                confirm = "y"
            return confirm != "n"

        # 4. StoryExpander 사용하여 확장
        try:
            from modules.core.stage0.story_expander import StoryExpander

            expander = StoryExpander(genre=stage0_manager.genre, llm_client=stage0_manager.client)

            app.ui.log(f"\n   🔄 Block {len(existing_treatment) + 1}부터 {extend_count}개 생성 시작...")

            extended_treatment = expander.extend_treatment(
                existing_treatment=existing_treatment,
                extend_count=extend_count,
                direction_hint=direction_hint,
                batch_size=10,
                confirm_callback=confirm_batch,
            )

            app.ui.log(f"\n   ✅ 확장 완료: {len(existing_treatment)} → {len(extended_treatment)} 블록")
            return extended_treatment

        except Exception as e:
            logging.warning(f"❌ Block 확장 중 오류: {e}")
            import traceback

            traceback.print_exc()
            return existing_treatment

    # ─────────────────────────────────────────────────────────────
    # [4C-1b-b] _stage_0_extended
    # ─────────────────────────────────────────────────────────────
    def stage_0_extended(self, mode: int = 0):
        """[V60.95] Stage 0 확장 기능 — dispatcher + 6 핸들러."""
        app = self.app

        from modules.core.spinners import STAGE0_AVAILABLE

        if not STAGE0_AVAILABLE:
            app.ui.log("❌ Stage 0 모듈이 로드되지 않았습니다.")
            return

        from modules.core.stage0 import PresetRegistry, StageZeroManager

        project_path = str(app.current_project.paths.root) if app.current_project else None
        llm_client = getattr(app.sys, "api_client", None) if hasattr(app, "sys") else None
        stage0_manager = StageZeroManager(project_path=project_path, llm_client=llm_client, ui=app.ui)

        if app.selected_genre:
            genre_type = app.selected_genre.get("type", "")
            if genre_type:
                stage0_manager.genre = genre_type.lower()
                stage0_manager.preset_registry = PresetRegistry(base_genre=genre_type.lower())
        try:
            master_bible = getattr(app.current_project, "master_bible", None) or {}
            bible_root = master_bible.get("MasterBible", master_bible) if isinstance(master_bible, dict) else {}
            protagonist_config = bible_root.get("protagonist_config", {}) if isinstance(bible_root, dict) else {}
            if isinstance(protagonist_config, dict) and protagonist_config:
                stage0_manager.protagonist_config = dict(protagonist_config)
        except Exception as _pov_contract_err:
            logging.debug("[Stage0Helpers] protagonist_config preload failed: %s", _pov_contract_err)

        if mode == 0:
            choice = stage0_manager.show_menu(is_new_project=True)
            if choice == 4:
                choice = 5
            elif choice == 5:
                choice = 6
        else:
            choice = mode

        handlers = {
            1: self._s0_handle_concept,
            2: self._s0_handle_reverse_engineering,
            3: self._s0_handle_bible_import,
            4: self._s0_handle_block_extension,
            5: self._s0_handle_style_analysis,
            6: self._s0_handle_work_guard,
        }
        handler = handlers.get(choice)
        if handler is None:
            app.ui.log("❌ Stage 0 확장이 취소되었습니다.")
            return

        bible, treatment = handler(app, stage0_manager)
        self._s0_save_results(app, stage0_manager, bible, treatment)

    # ── Stage 0 핸들러 ────────────────────────────────────────────

    @staticmethod
    def _s0_handle_concept(app, stage0_manager):
        """choice=1: 컨셉 → Bible/Treatment 생성."""
        bible, treatment, _ = stage0_manager.run_new_project_flow()
        return bible, treatment

    @staticmethod
    def _s0_handle_reverse_engineering(app, stage0_manager):
        """choice=2: 역설계."""
        bible, _episode_bibles, style_guide = stage0_manager.run_reverse_engineering_flow()
        if style_guide:
            app.ui.log("\n📝 스타일 가이드 추출 완료:")
            app.ui.log(f"   - 톤: {style_guide.tone}")
            app.ui.log(f"   - 시점: {style_guide.pov}")
            app.ui.log(f"   - 대화 비율: {style_guide.dialogue_ratio:.0%}")
            try:
                if app.current_project:
                    sg_data = json.loads(style_guide.to_json()) if hasattr(style_guide, "to_json") else {}
                    app.current_project.save_v20_anchor("style_guide", sg_data)
                    app.ui.log("   ✅ StyleGuide DB 저장 완료")
            except Exception as _sg_err:
                logging.warning(f" StyleGuide DB 저장 실패: {_sg_err}")

        # 원고 벡터화
        try:
            if hasattr(stage0_manager, "_reverse_expander") and stage0_manager._reverse_expander:
                _mem = getattr(app, "memory", None)
                vectorize_result = stage0_manager._reverse_expander.persist_to_vectordb(
                    app.current_project, memory=_mem
                )
                if vectorize_result > 0:
                    app.ui.log(f"✅ [Phase 4D] 벡터화 완료: {vectorize_result}개 에피소드")
        except Exception as ve:
            logging.warning(f" [Phase 4D] 벡터화 스킵: {str(ve)[:50]}")

        # SQLite DB 저장
        try:
            if hasattr(stage0_manager, "_reverse_expander") and stage0_manager._reverse_expander:
                db_result = stage0_manager._reverse_expander.persist_to_db(app.current_project)
                if db_result:
                    app.ui.log("✅ [V61] DB 저장 완료:")
                    app.ui.log(f"   - Manuscripts: {db_result.get('manuscripts', 0)}개")
                    app.ui.log(f"   - State Logs (HUD): {db_result.get('state_logs', 0)}개")
                    app.ui.log(f"   - Episode Bibles: {db_result.get('episode_bibles', 0)}개")
                    app.ui.log(f"   - Blueprint stubs: {db_result.get('blueprints', 0)}개")
                    app.ui.log(f"   - Arc stubs: {db_result.get('arcs', 0)}개")

                summary = stage0_manager._reverse_expander.get_stub_summary()
                if summary:
                    app.ui.log("\n📊 역설계 요약:")
                    app.ui.log(
                        f"   - 처리된 에피소드: {summary.get('ep_range', 'N/A')} ({summary.get('episodes', 0)}개)"
                    )
                    app.ui.log(f"   - Arc stubs: {summary.get('arc_stub_range', 'N/A')}")
                    app.ui.log("\n🎯 다음 생성 시작점:")
                    app.ui.log(f"   - Stage 2 (Arc): Arc {summary.get('next_arc', 'N/A')}부터")
                    app.ui.log(f"   - Stage 3 (Blueprint): ep {summary.get('next_blueprint', 'N/A')}부터")
                    app.ui.log(f"   - Stage 4 (Manuscript): ep {summary.get('next_episode', 'N/A')}부터")
        except Exception as db_err:
            logging.warning(f" [V61] DB 저장 스킵: {str(db_err)[:50]}")

        return bible, None

    @staticmethod
    def _s0_handle_bible_import(_app, stage0_manager):
        """choice=3: Bible 임포트."""
        bible = stage0_manager.import_bible()
        return bible, None

    def _s0_handle_block_extension(self, app, stage0_manager):
        """choice=4: Block 확장."""
        treatment = self.extend_blocks(stage0_manager)
        if treatment:
            try:
                treatment_path = app.current_project.paths.root / "treatment_extended.json"
                with open(treatment_path, "w", encoding="utf-8") as f:
                    json.dump({"treatments": treatment}, f, ensure_ascii=False, indent=2)
                app.ui.log(f"✅ 확장된 Treatment 저장: {treatment_path}")
                app.ui.log(f"   총 {len(treatment)} 블록")
            except Exception as e:
                logging.warning(f"❌ Treatment 저장 실패: {e}")

            try:
                refined_roadmap = []
                for i, block in enumerate(treatment):
                    entry = {"block_no": i + 1}
                    entry.update(block)
                    refined_roadmap.append(entry)

                master_bible = app.current_project.master_bible or {}
                bible_root = master_bible.get("MasterBible", master_bible)
                bible_root["plot_roadmap"] = refined_roadmap
                app.current_project.master_bible = {"MasterBible": bible_root}
                app.current_project.save_v20_anchor("bible", app.current_project.master_bible)
                app.current_project._load_from_db()

                app.ui.log(f"✅ [V61] plot_roadmap 주입 완료: {len(refined_roadmap)} 블록 → Master Bible")
                app.ui.log("   이제 Stage 2 (Arc 생성)를 진행할 수 있습니다.")
            except Exception as pr_err:
                logging.warning(f"❌ plot_roadmap 주입 실패: {pr_err}")
                import traceback

                traceback.print_exc()

        Stage01Helpers._pause_with_ui(app)
        return None, None  # 자체 저장 완료, 공통 후처리 불필요

    @staticmethod
    def _s0_handle_style_analysis(app, stage0_manager):
        """choice=5: 스타일 레퍼런스 분석."""
        style_guide = stage0_manager.run_reference_analysis()
        if style_guide and app.current_project:
            try:
                sg_data = json.loads(style_guide.to_json()) if hasattr(style_guide, "to_json") else {}
                app.current_project.save_v20_anchor("style_guide", sg_data)
                app.ui.log("✅ [V70] StyleGuide DB 저장 완료 (anchor: style_guide)")
            except Exception as sg_err:
                logging.warning(f" StyleGuide DB 저장 실패: {sg_err}")
        Stage01Helpers._pause_with_ui(app)
        return None, None

    @staticmethod
    def _s0_handle_work_guard(app, stage0_manager):
        """choice=6: 작품가드 설정."""
        stage0_manager.manage_work_guard()
        Stage01Helpers._pause_with_ui(app)
        return None, None

    @staticmethod
    def _build_plot_roadmap_from_treatment(treatment) -> list[dict]:
        """Stage 2가 기대하는 flat plot_roadmap 형태로 treatment를 정규화한다."""
        if isinstance(treatment, dict):
            treatment = treatment.get("treatments", [])
        if not isinstance(treatment, list):
            return []

        refined_roadmap = []
        for i, block in enumerate(treatment):
            if not isinstance(block, dict):
                continue
            entry = {"block_no": i + 1}
            entry.update(block)
            refined_roadmap.append(entry)
        return refined_roadmap

    @staticmethod
    def _build_plot_roadmap_from_saved_arcs(app) -> list[dict]:
        """역설계 경로에서는 저장된 arc stub을 roadmap placeholder로 승격한다."""
        project = getattr(app, "current_project", None)
        db = getattr(project, "db", None)
        if db is None or not hasattr(db, "load_anchor"):
            return []

        try:
            arcs = db.load_anchor("arcs") or []
        except Exception as exc:
            logging.warning(f"[Stage0] arcs anchor 로드 실패: {exc}")
            return []

        if isinstance(arcs, dict):
            arcs = list(arcs.values())
        if not isinstance(arcs, list):
            return []

        refined_roadmap = []
        for i, arc in enumerate(arcs):
            if not isinstance(arc, dict):
                continue
            entry = {"block_no": i + 1}
            for key in (
                "arc_no",
                "volume_no",
                "ep_start",
                "ep_end",
                "ep_count",
                "tactical_doc",
                "key_events",
                "joint_docs",
                "state_changes",
                "_stub",
                "_source",
            ):
                if key in arc:
                    entry[key] = arc[key]
            if (
                "ep_count" not in entry
                and isinstance(entry.get("ep_start"), int)
                and isinstance(entry.get("ep_end"), int)
            ):
                entry["ep_count"] = max(0, entry["ep_end"] - entry["ep_start"] + 1)
            refined_roadmap.append(entry)
        return refined_roadmap

    @classmethod
    def _ensure_plot_roadmap(cls, app, bible, treatment) -> int:
        """Stage 0 결과 저장 전에 plot_roadmap 누락을 보정한다."""
        if not isinstance(bible, dict):
            return 0

        master = bible.get("MasterBible")
        bible_root = master if isinstance(master, dict) else bible
        existing = bible_root.get("plot_roadmap", [])
        if isinstance(existing, list) and existing:
            return len(existing)

        refined_roadmap = cls._build_plot_roadmap_from_treatment(treatment)
        if not refined_roadmap:
            refined_roadmap = cls._build_plot_roadmap_from_saved_arcs(app)
        if not refined_roadmap:
            return 0

        bible_root["plot_roadmap"] = refined_roadmap
        return len(refined_roadmap)

    @staticmethod
    def _s0_save_results(app, stage0_manager, bible, treatment):
        """공통 후처리: Bible/Treatment DB 저장 + 리로드."""
        bible_saved = False
        if bible:
            try:
                injected_blocks = Stage01Helpers._ensure_plot_roadmap(app, bible, treatment)
                app.current_project.master_bible = bible
                app.current_project.save_v20_anchor("bible", bible)
                bible_saved = True
                app.ui.log("✅ Bible이 DB에 저장되었습니다.")
                if injected_blocks:
                    app.ui.log(f"   ✅ plot_roadmap 준비 완료: {injected_blocks} 블록")

                master = bible.get("MasterBible", bible)
                protagonist_config = master.get("protagonist_config", {})
                if protagonist_config:
                    app.ui.log(f"   💾 주인공 설정: {protagonist_config}")

                if stage0_manager.preset_registry:
                    app.preset_registry = stage0_manager.preset_registry
                    preset_state = stage0_manager.preset_registry.to_json()
                    app.current_project.save_v20_anchor("preset_state", json.loads(preset_state))
                    app.ui.log(f"   📦 프리셋 상태 저장: {list(stage0_manager.preset_registry.active_presets)}")

                if stage0_manager.style_guide:
                    app.current_project.save_v20_anchor("style_guide", stage0_manager.style_guide.to_dict())
                    app.ui.log("   🎨 스타일 가이드 저장 완료")

            except Exception as e:
                logging.warning(f"❌ 저장 중 오류: {e}")

        if treatment:
            if bible and not bible_saved:
                logging.warning("⚠️ Bible 저장 실패로 Treatment 저장을 건너뜁니다.")
                app.ui.log("⚠️ Bible 저장 실패로 Treatment 저장을 건너뜁니다.")
            else:
                try:
                    treatment_path = app.current_project.paths.root / "treatment_generated.json"
                    with open(treatment_path, "w", encoding="utf-8") as f:
                        json.dump({"treatments": treatment}, f, ensure_ascii=False, indent=2)
                    app.ui.log(f"✅ Treatment 저장: {treatment_path}")
                except Exception as e:
                    logging.warning(f"❌ Treatment 저장 실패: {e}")

        if bible_saved:
            try:
                app.current_project._load_from_db()
                app.ui.log("✨ [Stage 0 Complete] 프로젝트 설정이 완료되었습니다.")
            except Exception as e:
                logging.warning(f"❌ Stage 0 결과 리로드 실패: {e}")

        Stage01Helpers._pause_with_ui(app)

    # ─────────────────────────────────────────────────────────────
    # [4C-1b-b] _stage_1_volumes
    # ─────────────────────────────────────────────────────────────
    def stage_1_volumes(self):
        """[Stage 1] 아크 기반 권별 고해상도 전략 설계 (원본 main_a.py L2210)"""
        app = self.app

        app.ui.log("📜 [Stage 1] 권별 고해상도 순차 설계 (V41 유동 아크)")

        # [V41 Patch] 스킵 옵션 제공
        app.ui.log("💡 Stage 1은 선택 사항입니다. 스킵해도 Stage 2 진행이 가능합니다.")
        try:
            skip_choice = self._prompt_with_ui(app, "   [1] 진행  [2] 스킵 (기본: 1): ", prompt_id="stage1_skip_choice").strip()
        except (EOFError, KeyboardInterrupt, ValueError):
            skip_choice = "1"
        if skip_choice == "2":
            app.ui.log("⏭️ Stage 1을 건너뜁니다. Stage 2에서 기본값으로 진행됩니다.")
            self._pause_with_ui(app)
            return

        # [V38 패치] 안전한 커밋으로 변경
        app._safe_commit()

        # [V38 패치] 안전한 데이터 추출 [V44 강화: None 체크]
        if not app.current_project or not hasattr(app.current_project, "master_bible"):
            app.ui.log("❌ 프로젝트가 로드되지 않았습니다.")
            self._pause_with_ui(app)
            return
        master_bible = app.current_project.master_bible or {}
        bible_root = master_bible.get("MasterBible", master_bible) if isinstance(master_bible, dict) else {}
        arcs_source = bible_root.get("plot_roadmap", []) if isinstance(bible_root, dict) else []

        # [V43 패치] plot_roadmap 복구 메커니즘
        if not arcs_source:
            app.ui.log("⚠️ [Recovery] 메모리 내 로드맵이 없습니다. DB에서 재로드를 시도합니다...")
            try:
                app.current_project._load_from_db()
                master_bible = app.current_project.master_bible or {}
                bible_root = master_bible.get("MasterBible", master_bible) if isinstance(master_bible, dict) else {}
                arcs_source = bible_root.get("plot_roadmap", []) if isinstance(bible_root, dict) else []

                if arcs_source:
                    app.ui.log(f"✅ [Recovery] DB에서 {len(arcs_source)}개 아크 복구 성공!")
            except Exception as reload_err:
                app.ui.log(f"🚨 [Recovery Failed] DB 재로드 실패: {reload_err}")
                app._audit_event("recovery_failed", "plot_roadmap reload failed", {"error": str(reload_err)})

        if not arcs_source:
            app.ui.log("❌ 에러: 성경 내 로드맵 데이터가 없습니다. Phase 0을 다시 실행하세요.")
            self._pause_with_ui(app)
            return

        from modules.core.constants import Emojis, RetryLimits, VolumeSettings
        from modules.core.spinners import StageSpinner

        # [V41 Patch] 아크 총량 유동화
        total_arcs = len(arcs_source)
        total_volumes = (total_arcs + VolumeSettings.ARCS_PER_VOLUME - 1) // VolumeSettings.ARCS_PER_VOLUME
        app.ui.log(f"📊 총 {total_arcs}개 아크 발견 → {total_volumes}권 분권 설계를 시작합니다.")

        final_volumes = []
        context_accumulator = ""
        # [V44] 안전한 중첩 dict 접근
        project_data = bible_root.get("ProjectData", {}) if isinstance(bible_root, dict) else {}
        project_data = project_data if isinstance(project_data, dict) else {}
        meta_info = json.dumps(project_data.get("MetaInfo", {}), ensure_ascii=False)

        # [V41 Patch] 유동적 권 수 순차 설계 루프
        arcs_per_vol = VolumeSettings.ARCS_PER_VOLUME
        for vol_idx in range(1, total_volumes + 1):
            start_idx = (vol_idx - 1) * arcs_per_vol
            end_idx = vol_idx * arcs_per_vol
            vol_arcs_chunk = arcs_source[start_idx:end_idx]

            if not vol_arcs_chunk:
                app.ui.log(f"⚠️ [Warning] {vol_idx}권에 해당하는 데이터가 부족합니다. 스킵합니다.")
                continue

            treatment_slice = json.dumps(vol_arcs_chunk, ensure_ascii=False, indent=2)

            # [V65] retry_with_feedback 래퍼로 밀도 확보 재시도 루프 표준화
            from modules.core.adaptive_retry import retry_with_feedback

            def _vol_attempt_func(attempt, _feedback, _vi=vol_idx, _ts=treatment_slice):
                """[V65] 단일 권 설계 시도 로직"""
                app.ui.log(
                    f"   {Emojis.BRAIN} 제 {_vi}권 전략 설계 중... (시도 {attempt + 1}/{RetryLimits.DIRECTOR_MAX_ATTEMPTS})"
                )
                stage1_protagonist_name = app._get_protagonist_name()
                with StageSpinner(1, f"제{_vi}권 설계"):
                    vol_data = app.agents["analyst"].plan_single_volume_v20(
                        _vi,
                        app.current_project.master_bible,
                        _ts,
                        context_accumulator,
                        meta_info,
                        protagonist_name=stage1_protagonist_name,
                    )
                return vol_data

            def _vol_on_success(vol_data, _vi=vol_idx):
                """[V65] 볼륨 설계 성공 판정"""
                if not vol_data or not isinstance(vol_data, dict):
                    app.ui.log(f"🚨 [Analyst Error] 제 {_vi}권 설계 결과가 유효하지 않음: {type(vol_data)}")
                    app._audit_event(
                        "analyst_error", "invalid volume data", {"vol_no": _vi, "type": str(type(vol_data))}
                    )
                    return False

                raw_doc = vol_data.get("strategy_doc", "")
                if isinstance(raw_doc, dict):
                    raw_doc = json.dumps(raw_doc, ensure_ascii=False)
                doc_len = len(raw_doc)
                if doc_len < 2000:
                    app.ui.log(f"   ⚠️ [Low Density] 분량 부족({doc_len}/2000). 다시 설계합니다.")
                    return False

                boundary_check = self.validate_volume_boundaries(vol_data, _vi)
                if boundary_check.get("status") == "REJECT":
                    app.ui.log(f"   🚨 [Boundary Violation] {boundary_check.get('reason')}")
                    app.ui.log(f"   📝 수정 요청: {boundary_check.get('feedback')}")
                    app._audit_event(
                        "volume_boundary_violation",
                        boundary_check.get("reason"),
                        {"vol_no": _vi, "feedback": boundary_check.get("feedback")},
                    )
                    return False

                return True

            def _vol_on_failure(vol_data, attempt):
                """[V65] 실패 시 피드백"""
                return ""

            vol_result, _vol_attempts, vol_passed = retry_with_feedback(
                func=_vol_attempt_func,
                max_attempts=RetryLimits.DIRECTOR_MAX_ATTEMPTS,
                on_success=_vol_on_success,
                on_failure=_vol_on_failure,
                logger=lambda msg: app.ui.log(msg),
                task_name=f"Stage1_Volume_{vol_idx}",
            )

            if not vol_passed:
                app.ui.log(f"❌ [Critical] 제 {vol_idx}권 품질 미달로 공정 중단.")
                return

            # 성공 후처리
            vol_data = vol_result
            raw_doc = vol_data.get("strategy_doc", "")
            if isinstance(raw_doc, dict):
                raw_doc = json.dumps(raw_doc, ensure_ascii=False)
            doc_len = len(raw_doc)
            app.ui.log(f"   ✅ [Pass] {vol_idx}권 검수 완료 (분량: {doc_len}자)")
            final_volumes.append(vol_data)

            # [중요] 다음 권 설계를 위해 현재 권의 요약을 누적
            summary = raw_doc[:500]
            context_accumulator += f"\n[제 {vol_idx}권 요약]: {summary}..."
            MAX_CONTEXT_VOLUMES = 3
            if vol_idx > MAX_CONTEXT_VOLUMES:
                acc_lines = context_accumulator.split("\n")
                compressed_lines = []
                kept_recent = 0
                for line in reversed(acc_lines):
                    if line.startswith("[제 ") and "권 요약]" in line:
                        if kept_recent < MAX_CONTEXT_VOLUMES:
                            compressed_lines.insert(0, line)
                            kept_recent += 1
                        else:
                            vol_label = line.split("]:")[0] + "]: (요약 생략)"
                            compressed_lines.insert(0, vol_label)
                    elif line.strip():
                        compressed_lines.insert(0, line)
                context_accumulator = "\n".join(compressed_lines)

        # 3. 전체 데이터 DB 박제 및 메모리 동기화
        app.current_project.save_v20_anchor("volumes", final_volumes)
        app.current_project.volumes = final_volumes
        if hasattr(app, "_show_volume_table"):
            app._show_volume_table(final_volumes)
        app.ui.log(f"✨ [Complete] {len(final_volumes)}권 대서사시 로드맵이 DB에 최종 안착되었습니다.")

        self._pause_with_ui(app, "\n[Enter] 메뉴로 이동", prompt_id="stage1_return_to_menu")
