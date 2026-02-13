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


class Stage01Helpers:
    """
    [Phase 4C-1b] SovereignApp의 Stage 0 / Stage 1 로직 캡슐화

    패턴: self.app = SovereignApp 인스턴스
    """

    def __init__(self, app) -> None:
        self.app = app

    # ─────────────────────────────────────────────────────────────
    # [4C-1b-a] _phase_0_recovery
    # ─────────────────────────────────────────────────────────────
    def phase_0_recovery(self):
        """[V60.95] Phase 0: 프로젝트 설정 서브메뉴 (원본 main_a.py L1994)"""
        app = self.app

        print("\n⚙️ Phase 0: S-Grade 데이터 주권 동기화 가동...")

        # [V40] 장르 정보 표시
        if app.selected_genre:
            print(f"📌 현재 장르: {app.selected_genre['name']} ({app.selected_genre['type']})")

        # [V60.95] Stage 0 서브메뉴
        from main_a import STAGE0_AVAILABLE

        print("\n" + "=" * 50)
        print("  📚 Stage 0 - 프로젝트 설정")
        print("=" * 50)
        print("\n  [1] 기존 방식 - Bible/Treatment 파일 선택")
        if STAGE0_AVAILABLE:
            print("  [2] 🆕 컨셉 → Bible 생성 (AI 확장)")
            print("  [3] 🔄 역설계 - 기존 원고에서 Bible/스타일 추출")
            print("  [4] 📥 Bible JSON 임포트")
            print("  [5] 📈 Block 확장 - 기존 Treatment에 블록 추가")
            print("  [6] 🎨 스타일 레퍼런스 분석 - 참조 원고에서 문체 DNA 추출")
        print("\n  [0] 취소")

        p0_choice = input("\n  선택 (기본: 1): ").strip()

        if p0_choice == "0":
            print("❌ Stage 0이 취소되었습니다.")
            return
        elif p0_choice == "2" and STAGE0_AVAILABLE:
            self.app._stage_0_extended(mode=1)  # 컨셉 → Bible
            return
        elif p0_choice == "3" and STAGE0_AVAILABLE:
            self.app._stage_0_extended(mode=2)  # 역설계
            return
        elif p0_choice == "4" and STAGE0_AVAILABLE:
            self.app._stage_0_extended(mode=3)  # Bible 임포트
            return
        elif p0_choice == "5" and STAGE0_AVAILABLE:
            self.app._stage_0_extended(mode=4)  # Block 확장
            return
        elif p0_choice == "6" and STAGE0_AVAILABLE:
            self.app._stage_0_extended(mode=5)  # 스타일 레퍼런스 분석
            return

        # 기존 방식 계속...
        # 1. 파일 선택 (Bible & Treatment)
        bible_file = app._ui_select_bible()
        treatment_file = app._ui_select_treatment()

        if not bible_file or not treatment_file:
            print("❌ 파일 선택이 취소되어 중단합니다.")
            return

        # 1.5. [V60.10] Treatment Block 농축 옵션
        enrich_choice = input("   🔧 [V60.10] Treatment Block 자동 농축을 수행하시겠습니까? (y/N): ").strip().lower()
        if enrich_choice == "y":
            treatment_file = app._enrich_treatment_blocks(treatment_file)

        # ============================================================
        # [V60.87] 주인공 유형 설정 (Bible에 저장)
        # ============================================================
        print("\n📌 [V60.87] 주인공 기본 설정")

        # 1) 세계관 출신 (현대인/원시인)
        print("   🌍 주인공의 세계관 출신을 선택하세요:")
        print("      [1] 원시인 - 현대 지식/용어 사용 제한 (권장: 무협/판타지)")
        print("      [2] 현대인 - 제약 없음 (권장: 회귀/빙의물)")
        world_choice = input("   선택 (기본: 1): ").strip()
        world_origin = "현대인" if world_choice == "2" else "원시인"

        # 2) 주인공 유형 (빙의자/회귀자/환생자/기타)
        print("   🎭 주인공의 유형을 선택하세요:")
        print("      [1] 회귀자 - 먼 미래에서 과거로 회귀 (기억 보존)")
        print("      [2] 빙의자 - 다른 사람의 몸에 빙의")
        print("      [3] 환생자 - 아기로 다시 태어남")
        print("      [4] 기타 - 특별한 유형 없음")
        type_choice = input("   선택 (기본: 1): ").strip()
        incarnation_types = {"1": "회귀자", "2": "빙의자", "3": "환생자", "4": "기타"}
        incarnation_type = incarnation_types.get(type_choice, "회귀자")

        # 3) [V70] 서술 시점 (1인칭/3인칭/전지적)
        print("   📖 서술 시점을 선택하세요:")
        print("      [1] 1인칭 - 주인공 '나'의 시점 (몰입감↑, 정보 제한)")
        print("      [2] 3인칭 - 주인공을 '그/그녀'로 지칭 (자유도↑)")
        print("      [3] 전지적 - 모든 캐릭터 내면 접근 가능")
        pov_choice = input("   선택 (기본: 2): ").strip()
        pov_types = {"1": "1인칭", "2": "3인칭", "3": "전지적"}
        selected_pov = pov_types.get(pov_choice, "3인칭")

        protagonist_config = {
            "world_origin": world_origin,
            "incarnation_type": incarnation_type,
            "pov": selected_pov,  # [V70] 서술 시점
        }
        print(f"   ✅ 설정 완료: {world_origin} / {incarnation_type} / {selected_pov}")

        # 2. [필수] 50개 설계도 DNA 강제 이식
        dna_success = app.current_project.force_sync_v25_dna(bible_file, treatment_file)

        if dna_success:
            # 2.5 [V60.87] 주인공 설정을 Bible에 주입
            try:
                master_bible = app.current_project.master_bible or {}
                bible_root = master_bible.get("MasterBible", master_bible)
                bible_root["protagonist_config"] = protagonist_config
                app.current_project.master_bible = {"MasterBible": bible_root}
                app.current_project.save_v20_anchor("bible", app.current_project.master_bible)
                print(f"   💾 [V60.87] 주인공 설정이 Bible에 저장됨: {protagonist_config}")
            except Exception as pc_err:
                print(f"   ⚠️ [V60.87] 주인공 설정 저장 실패 (비차단): {pc_err}")

            # 3. [선택] 기존 원고 유무 확인 및 자동 동기화
            draft_path = app.current_project.paths.drafts
            existing_drafts = list(draft_path.glob("*.txt"))

            if existing_drafts:
                print(f"📂 [Detect] 기존 원고 {len(existing_drafts)}건 발견. 역사 이식을 시작합니다...")
                try:
                    sync_result = app.current_project.sync_existing_manuscripts(app.memory)
                    if sync_result:
                        print("✅ [History] 기존 원고의 역사가 모두 시스템에 안착되었습니다.")
                    else:
                        print("⚠️ [Warning] 일부 원고 동기화 실패. 로그를 확인하세요.")
                except Exception as sync_err:
                    print(f"🚨 [Error] 원고 동기화 중 오류 발생: {sync_err}")
                    app._audit_event(
                        "sync_error",
                        "sync_existing_manuscripts failed",
                        {"error": str(sync_err), "draft_count": len(existing_drafts)},
                    )
                    print("⚠️ [Fallback] 원고 동기화를 건너뛰고 계속 진행합니다.")
            else:
                print("🆕 [New Project] 기존 원고가 없습니다. 신규 프로젝트로 기동합니다.")

            # 4. 최종 데이터 리로드
            app.current_project._load_from_db()
            print("✨ [Success] 설계도(50개)와 원고 역사가 무결하게 통합되었습니다.")

        input("\n[Enter] 메뉴로 돌아가기")

    # ─────────────────────────────────────────────────────────────
    # [4C-1b-a] _extend_blocks
    # ─────────────────────────────────────────────────────────────
    def extend_blocks(self, stage0_manager) -> list[dict]:
        """[V61] Block 확장 기능 — 기존 Treatment에 블록 추가 (원본 main_a.py L2347)"""
        app = self.app

        print("\n" + "=" * 50)
        print("  📈 Block 확장 - 기존 Treatment에 블록 추가")
        print("=" * 50)

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
                            print(f"   📂 기존 Treatment 로드: {tf.name} ({len(existing_treatment)} 블록)")
                            break
                except Exception as e:
                    print(f"   ⚠️ 파일 로드 실패: {tf.name} - {e}")

        if not existing_treatment:
            print("   ❌ 기존 Treatment를 찾을 수 없습니다.")
            print("   먼저 [2] 컨셉 → Bible 생성 또는 [3] 역설계를 실행하세요.")
            return []

        # 2. 확장 설정
        print(f"\n   현재 블록 수: {len(existing_treatment)}")
        print(
            f"   마지막 블록: {existing_treatment[-1].get('block_id', 'N/A')} - {existing_treatment[-1].get('title', 'N/A')}"
        )

        try:
            extend_count = int(input("\n   추가할 블록 수 (기본: 10): ").strip() or "10")
        except ValueError:
            extend_count = 10

        direction_hint = input("   방향 힌트 (예: '클라이맥스로', '새 빌런 등장', 생략 가능): ").strip()

        # 3. 배치별 확인 콜백
        def confirm_batch(batch):
            print(f"\n   --- 생성된 블록 ({len(batch)}개) ---")
            for b in batch[:3]:  # 미리보기 3개
                print(f"   • {b.get('block_id', 'N/A')}: {b.get('title', 'N/A')}")
            if len(batch) > 3:
                print(f"   ... 외 {len(batch) - 3}개")

            confirm = input("   계속 진행하시겠습니까? (Y/n): ").strip().lower()
            return confirm != "n"

        # 4. StoryExpander 사용하여 확장
        try:
            from modules.core.stage0.story_expander import StoryExpander

            expander = StoryExpander(genre=stage0_manager.genre)

            print(f"\n   🔄 Block {len(existing_treatment) + 1}부터 {extend_count}개 생성 시작...")

            extended_treatment = expander.extend_treatment(
                existing_treatment=existing_treatment,
                extend_count=extend_count,
                direction_hint=direction_hint,
                batch_size=10,
                confirm_callback=confirm_batch,
            )

            print(f"\n   ✅ 확장 완료: {len(existing_treatment)} → {len(extended_treatment)} 블록")
            return extended_treatment

        except Exception as e:
            print(f"   ❌ Block 확장 중 오류: {e}")
            import traceback

            traceback.print_exc()
            return existing_treatment
