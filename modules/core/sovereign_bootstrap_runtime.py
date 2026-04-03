"""SovereignApp bootstrap runtime split."""

import json
import logging
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING

from modules.core.constants import AIModels
from modules.core.google_client_factory import resolve_google_provider_mode
from modules.core.llm_generate import generate_content_via_router
from modules.core.provider_mode import VERTEX_AI_MODE

if TYPE_CHECKING:
    from main_a import SovereignApp


_FLASH_ANALYSIS_MODEL = AIModels.FLASH_ANALYSIS_MODEL
_SUMMARY_MODEL = AIModels.SUMMARY_MODEL
_V50_MODULE_MODEL = AIModels.V50_MODULE_MODEL


class SovereignBootstrapRuntime:
    """Owns the bounded bootstrap helper family for SovereignApp."""

    def __init__(self, owner: "SovereignApp") -> None:
        self.owner = owner

    def _build_flash_analysis_callback(self):
        owner = self.owner
        flash_ask_cb = None
        from main_a import _val_threshold

        if bool(_val_threshold("investment_math.flash_enabled", True)):
            try:
                flash_client = owner.sys.api_client

                def flash_ask_cb(prompt: str, _c=flash_client) -> str:
                    resp = generate_content_via_router(
                        client=_c,
                        model=AIModels.FLASH_ANALYSIS_MODEL,
                        contents=prompt,
                    )
                    return resp.text or ""

            except Exception as flash_init_err:
                logging.warning("[Codex F] flash_ask 콜백 준비 실패: %s", str(flash_init_err)[:120])
                flash_ask_cb = None
        return flash_ask_cb

    def _build_core_llm_agents(
        self,
        *,
        _agents: dict,
        models: dict,
        default_model: str,
        flash_ask_cb,
    ) -> dict:
        owner = self.owner
        Analyst = _agents["Analyst"]
        ArcCritic = _agents["ArcCritic"]
        ArcEnsembleGenerator = _agents["ArcEnsembleGenerator"]
        ConsensusValidator = _agents["ConsensusValidator"]
        ContinuityInspector = _agents["ContinuityInspector"]
        Critic = _agents["Critic"]
        Director = _agents["Director"]
        FourPhaseArcGenerator = _agents["FourPhaseArcGenerator"]
        Manager = _agents["Manager"]
        PreflightChecker = _agents["PreflightChecker"]
        StateExtractor = _agents["StateExtractor"]
        StateLockedArcGenerator = _agents["StateLockedArcGenerator"]
        ThreePhaseBlueprintGenerator = _agents["ThreePhaseBlueprintGenerator"]
        Weaver = _agents["Weaver"]
        Writer = _agents["Writer"]
        return {
            "analyst": Analyst(
                owner.current_project, owner.sys.api_client, model_tier=models.get("analyst", default_model)
            ),
            "writer": Writer(
                owner.current_project,
                owner.sys.api_client,
                model_tier=models.get("writer", default_model),
            ),
            "director": Director(
                owner.current_project, owner.sys.api_client, model_tier=models.get("director", default_model)
            ),
            "manager": Manager(
                owner.current_project, owner.sys.api_client, model_tier=models.get("manager", default_model)
            ),
            "weaver": Weaver(
                owner.current_project,
                owner.sys.api_client,
                model_tier=models.get("weaver", models.get("manager", default_model)),
            ),
            "continuity_inspector": ContinuityInspector(
                owner.current_project, owner.sys.api_client, model_tier=AIModels.STAGE2_MAIN_MODEL
            ),
            "critic": Critic(owner.current_project, owner.sys.api_client, model_tier=_SUMMARY_MODEL),
            "state_extractor": StateExtractor(
                owner.current_project,
                owner.sys.api_client,
                model_tier=_FLASH_ANALYSIS_MODEL,
            ),
            "arc_ensemble": ArcEnsembleGenerator(
                owner.current_project,
                owner.sys.api_client,
                model_tier=AIModels.STAGE2_MAIN_MODEL,
            ),
            "four_phase": FourPhaseArcGenerator(
                owner.current_project,
                owner.sys.api_client,
                model_tier=AIModels.STAGE2_MAIN_MODEL,
                flash_ask=flash_ask_cb,
            ),
            "state_locked": StateLockedArcGenerator(
                owner.current_project, owner.sys.api_client, model_tier=AIModels.STAGE2_MAIN_MODEL
            ),
            "preflight": PreflightChecker(
                owner.current_project,
                owner.sys.api_client,
                model_tier=_FLASH_ANALYSIS_MODEL,
            ),
            "arc_critic": ArcCritic(
                owner.current_project, owner.sys.api_client, model_tier=AIModels.STAGE2_MAIN_MODEL
            ),
            "consensus": ConsensusValidator(
                owner.current_project, owner.sys.api_client, model_tier=AIModels.STAGE2_MAIN_MODEL
            ),
            "three_phase_bp": ThreePhaseBlueprintGenerator(
                owner.current_project, owner.sys.api_client, model_tier=AIModels.STAGE2_MAIN_MODEL
            ),
        }

    def _init_stage2_support_agents(self, *, _agents: dict, _v50: dict | None) -> None:
        owner = self.owner
        ArcCorrector = _agents["ArcCorrector"]
        ArcDraftValidator = _agents["ArcDraftValidator"]
        ConstraintCompiler = _agents["ConstraintCompiler"]

        genre_for_stage2 = owner.selected_genre.get("type", "") if isinstance(owner.selected_genre, dict) else ""
        owner.arc_draft_validator = ArcDraftValidator(genre=genre_for_stage2)
        owner.constraint_compiler = ConstraintCompiler(genre=genre_for_stage2)
        owner.arc_corrector = ArcCorrector(
            context=owner.current_project,
            client=owner.sys.api_client,
            model_tier=_FLASH_ANALYSIS_MODEL,
        )
        owner.use_arc_corrector = True
        create_stage2_optimizer = _v50["create_stage2_optimizer"] if _v50 else None
        owner.stage2_optimizer = create_stage2_optimizer() if create_stage2_optimizer else None
        owner.ui.log("   🔧 [V60.11] Stage 2 고도화 모듈 초기화 (Ensemble + DraftValidator + ConstraintCompiler)")
        owner.ui.log("   🚀 [V60.12] Stage 2 초기통과율 극대화 모듈 초기화 (FourPhase + Preflight + Critic + Consensus)")
        owner.ui.log(
            f"   🔧 [V60.42] Arc Corrector 초기화 (MAJOR 이슈 부분 수정: {'활성화' if owner.use_arc_corrector else '비활성화'})"
        )
        if owner.stage2_optimizer:
            owner.ui.log("   ⚡ [V60.25] Stage 2 Optimizer 활성화 (StateSnapshot + AutoCorrector + ConstraintAmplifier)")

    def init_core_agents(self, *, _agents: dict, _v50: dict | None, models: dict, default_model: str) -> None:
        owner = self.owner
        flash_ask_cb = self._build_flash_analysis_callback()
        owner.agents = self._build_core_llm_agents(
            _agents=_agents,
            models=models,
            default_model=default_model,
            flash_ask_cb=flash_ask_cb,
        )
        self._init_stage2_support_agents(_agents=_agents, _v50=_v50)

    def _restore_failure_learner_from_db_snapshot(self) -> bool:
        owner = self.owner
        try:
            failure_row = owner.current_project.db.conn.execute(
                "SELECT description FROM reflexion_memory WHERE pattern_type = ?",
                ("failure_learner_snapshot",),
            ).fetchone()
            if failure_row and failure_row[0]:
                from collections import defaultdict as _defaultdict

                from modules.core.failure_learning import FailureCategory as _FailureCategory
                from modules.core.failure_learning import FailureRecord as _FailureRecord

                failure_snapshot = json.loads(failure_row[0])
                owner.failure_learner.records = []
                owner.failure_learner.category_counts = _defaultdict(int)
                owner.failure_learner.stage_counts = {
                    2: _defaultdict(int),
                    3: _defaultdict(int),
                    4: _defaultdict(int),
                }
                owner.failure_learner.recent_failures = {2: [], 3: [], 4: []}

                for record in failure_snapshot.get("records", []):
                    try:
                        category = _FailureCategory(record.get("category", "unknown"))
                    except ValueError:
                        category = _FailureCategory.UNKNOWN

                    stage = int(record.get("stage", 4))
                    failure_record = _FailureRecord(
                        category=category,
                        stage=stage,
                        episode=int(record.get("episode", 0)),
                        arc=int(record.get("arc", 0)),
                        reason=str(record.get("reason", "")),
                        details=record.get("details", {}),
                        timestamp=str(record.get("timestamp", "")),
                    )
                    owner.failure_learner.records.append(failure_record)
                    owner.failure_learner.category_counts[category] += 1
                    owner.failure_learner.stage_counts.setdefault(stage, _defaultdict(int))[category] += 1
                    owner.failure_learner.recent_failures.setdefault(stage, []).append(failure_record)
                    if len(owner.failure_learner.recent_failures[stage]) > 10:
                        owner.failure_learner.recent_failures[stage].pop(0)
                return bool(owner.failure_learner.records)
        except Exception as failure_db_err:
            logging.debug("[DB-Eff] failure_learner DB load 실패: %s", failure_db_err)
        return False

    def _migrate_failure_learner_snapshot_from_json(self) -> None:
        owner = self.owner
        failure_log_path = owner._get_current_project_log_path("failure_learning.json")
        if not failure_log_path.exists():
            return
        owner.failure_learner.load_from_json(failure_log_path)
        if not owner.failure_learner.records:
            return
        failure_snapshot = {
            "records": [
                {
                    "category": record.category.value,
                    "stage": record.stage,
                    "episode": record.episode,
                    "arc": record.arc,
                    "reason": record.reason,
                    "details": record.details,
                    "timestamp": record.timestamp,
                }
                for record in owner.failure_learner.records
            ],
            "stats": owner.failure_learner.get_failure_stats(),
        }
        snapshot_ts = time.strftime("%Y-%m-%d %H:%M:%S")
        first_ep = min((int(record.episode) for record in owner.failure_learner.records), default=0)
        last_ep = max((int(record.episode) for record in owner.failure_learner.records), default=0)
        owner.current_project.db.conn.execute(
            """INSERT INTO reflexion_memory
               (pattern_type, description, frequency, solution, first_seen, last_seen, first_ep, last_ep)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(pattern_type) DO UPDATE SET
                 description=excluded.description,
                 frequency=excluded.frequency,
                 solution=excluded.solution,
                 last_seen=excluded.last_seen,
                 first_ep=excluded.first_ep,
                 last_ep=excluded.last_ep""",
            (
                "failure_learner_snapshot",
                json.dumps(failure_snapshot, ensure_ascii=False),
                len(owner.failure_learner.records),
                "failure_learner_json_migrated",
                snapshot_ts,
                snapshot_ts,
                first_ep,
                last_ep,
            ),
        )
        owner.current_project.db.conn.commit()
        owner.ui.log("   📚 [DB-Eff] failure_learning JSON→DB 마이그레이션 완료")

    def _restore_character_voice_tracker(self) -> None:
        owner = self.owner
        character_voice_db_count = owner.character_voice.load_from_db(owner.current_project.db)
        if character_voice_db_count == 0:
            voice_log_path = owner._get_current_project_log_path("character_voice.json")
            if voice_log_path.exists():
                owner.character_voice.load_from_json(voice_log_path)
                owner.character_voice.save_to_db(owner.current_project.db)
                owner.ui.log("   🎭 [DB-Eff] character_voice JSON→DB 마이그레이션 완료")
        else:
            owner.ui.log(f"   🎭 [V51.5] 캐릭터 음성 {len(owner.character_voice.profiles)}명 로드(DB)")

    def _restore_foreshadow_tracker(self) -> None:
        owner = self.owner
        foreshadow_db_count = owner.foreshadow_tracker.load_from_db(owner.current_project.db)
        if foreshadow_db_count == 0:
            foreshadow_log_path = owner._get_current_project_log_path("foreshadow.json")
            if foreshadow_log_path.exists():
                owner.foreshadow_tracker.load_from_json(foreshadow_log_path)
                owner.foreshadow_tracker.save_to_db(owner.current_project.db)
                owner.ui.log("   🔮 [DB-Eff] foreshadow JSON→DB 마이그레이션 완료")
        else:
            stats = owner.foreshadow_tracker.get_stats()
            owner.ui.log(
                f"   🔮 [V51.6] 복선 {stats['total']}개 로드(DB) "
                f"(활성: {stats['active']}, 회수율: {stats['payoff_rate']}%)"
            )

    def _init_semantic_plot_guard_module(self) -> None:
        owner = self.owner
        try:
            from modules.core.semantic_plot_guard import SemanticPlotGuard

            api_key = "" if resolve_google_provider_mode() == VERTEX_AI_MODE else os.getenv("GOOGLE_API_KEY", "")
            owner.semantic_plot_guard = SemanticPlotGuard(api_key=api_key)
            if owner.semantic_plot_guard._client:
                owner.ui.log("   📊 [V66] SemanticPlotGuard 초기화 완료 (임베딩 모드)")
            else:
                owner.ui.log("   📊 [V66] SemanticPlotGuard 초기화 완료 (키워드 폴백 모드)")
        except Exception as guard_err:
            owner.ui.log(f"   ⚠️ [V66] SemanticPlotGuard 초기화 실패: {str(guard_err)[:80]}")
            owner.semantic_plot_guard = None

    def init_v51_tracking_modules(self, *, _v50: dict, genre_type: str) -> None:
        owner = self.owner
        owner.pacing_analyzer = _v50["PacingAnalyzer"]()
        owner.quality_amplifier = _v50["QualityAmplifier"]()
        owner.agent_intelligence = _v50["AgentIntelligence"](genre=genre_type)

        owner.failure_learner = _v50["FailureLearner"]()
        if self._restore_failure_learner_from_db_snapshot():
            owner.ui.log(f"   \U0001f4da [V51.4] \uc2e4\ud328 \uae30\ub85d {len(owner.failure_learner.records)}\uac74 \ub85c\ub4dc(DB)")
        else:
            self._migrate_failure_learner_snapshot_from_json()

        owner.character_voice = _v50["CharacterVoiceTracker"]()
        self._restore_character_voice_tracker()

        owner.foreshadow_tracker = _v50["ForeshadowTracker"]()
        self._restore_foreshadow_tracker()

        self._init_semantic_plot_guard_module()

    def init_v6026_reasoning_modules(self, *, _v50: dict, genre_type: str) -> None:
        owner = self.owner
        owner.emotion_tracker = _v50["EmotionArcTracker"](owner.current_project)
        try:
            owner.emotion_tracker.load_from_db(owner.current_project.db)
            if owner.emotion_tracker.history:
                owner.ui.log(
                    f"   \U0001f493 [V60.26] \uac10\uc815\uc120 \ucd94\uc801\uae30 \ub85c\ub4dc ({len(owner.emotion_tracker.history)}\uac1c \uae30\ub85d)"
                )
            else:
                owner.ui.log("   \U0001f493 [V60.26] \uac10\uc815\uc120 \ucd94\uc801\uae30 \ud65c\uc131\ud654")
        except Exception:
            owner.ui.log("   \U0001f493 [V60.26] \uac10\uc815\uc120 \ucd94\uc801\uae30 \ud65c\uc131\ud654")

        owner.power_scaling = _v50["PowerScalingTracker"]()
        owner.ui.log("   \u26a1 [V60.26] \ud30c\uc6cc \uc2a4\ucf00\uc77c\ub9c1 \ucd94\uc801\uae30 \ud65c\uc131\ud654")

        owner.state_delta_tracker = _v50["StateDeltaTracker"]()
        owner.ui.log("   \U0001f4ca [V60.26] \uc0c1\ud0dc \ubcc0\ud654 \ucd94\uc801\uae30 \ud65c\uc131\ud654")

        owner.semantic_item_registry = _v50["SemanticItemRegistry"]()
        owner.ui.log("   \U0001f4e6 [V60.26] \uc758\ubbf8\uc801 \uc544\uc774\ud15c \ub808\uc9c0\uc2a4\ud2b8\ub9ac \ud65c\uc131\ud654")

        owner.voice_profiler = _v50["CharacterVoiceProfiler"]()
        voice_profiler_path = owner._get_current_project_log_path("voice_profiles.json")
        if voice_profiler_path.exists():
            try:
                with open(voice_profiler_path, encoding="utf-8") as voice_file:
                    profiles_data = json.load(voice_file)
                    for name_key, profile_data in profiles_data.items():
                        owner.voice_profiler.add_profile(name_key, profile_data)
                owner.ui.log(
                    f"   \U0001f3ad [V60.26] \uce90\ub9ad\ud130 \uc74c\uc131 \ud504\ub85c\ud30c\uc77c\ub7ec \ub85c\ub4dc ({len(owner.voice_profiler.profiles)}\uba85)"
                )
            except (json.JSONDecodeError, KeyError, TypeError, OSError) as voice_err:
                owner.ui.log(
                    f"   \U0001f3ad [V60.26] \uce90\ub9ad\ud130 \uc74c\uc131 \ud504\ub85c\ud30c\uc77c\ub7ec \ud65c\uc131\ud654 "
                    f"(\ub85c\ub4dc \uc2e4\ud328: {str(voice_err)[:40]})"
                )
        else:
            owner.ui.log("   \U0001f3ad [V60.26] \uce90\ub9ad\ud130 \uc74c\uc131 \ud504\ub85c\ud30c\uc77c\ub7ec \ud65c\uc131\ud654")

        owner.self_reflector = _v50["SelfReflector"](
            api_client=owner.sys.api_client,
            model=_V50_MODULE_MODEL,
        )
        owner.ui.log("   \U0001f504 [V52.1] Self-Reflection Chain \ud65c\uc131\ud654")

        owner.expert_mixture = _v50["ExpertMixture"](genre=genre_type)
        owner.ui.log(f"   \U0001f3af [V52.3] Expert Mixture \ud65c\uc131\ud654 ({genre_type})")

        owner.cross_verifier = _v50["CrossAgentVerifier"](
            api_client=owner.sys.api_client,
            model=_V50_MODULE_MODEL,
        )
        owner.ui.log("   \U0001f517 [V52.4] Cross-Agent Verifier \ud65c\uc131\ud654")

        owner.prompt_weighter = _v50["DynamicPromptWeighter"](failure_learner=owner.failure_learner)
        owner.ui.log("   \u2696\ufe0f [V53.1] Dynamic Prompt Weighter \ud65c\uc131\ud654")

        owner.chain_of_verification = _v50["ChainOfVerification"](
            api_client=owner.sys.api_client,
            model=_V50_MODULE_MODEL,
        )
        owner.ui.log("   \U0001f50d [V53.2] Chain-of-Verification \ud65c\uc131\ud654")

        owner.confidence_calibrator = _v50["ConfidenceCalibrator"](
            api_client=owner.sys.api_client,
            use_llm=False,
        )
        owner.ui.log("   \U0001f4ca [V53.3] Confidence Calibrator \ud65c\uc131\ud654")

        owner.pre_director_checklist = _v50["PreDirectorChecklist"]()
        owner.ui.log("   \u2705 [V53.4] Pre-Director Checklist \ud65c\uc131\ud654")

        owner.tree_of_thoughts = _v50["TreeOfThoughts"](
            api_client=owner.sys.api_client,
            model=AIModels.STAGE2_MAIN_MODEL,
        )
        owner.ui.log("   \U0001f333 [V53.5] Tree of Thoughts \ud65c\uc131\ud654 (Gemini 3)")

        owner.adversarial_self_play = _v50["AdversarialSelfPlay"](
            api_client=owner.sys.api_client,
            model=_V50_MODULE_MODEL,
        )
        owner.ui.log("   \u2694\ufe0f [V53.6] Adversarial Self-Play \ud65c\uc131\ud654")

        owner.multi_agent_deliberation = _v50["MultiAgentDeliberation"](
            api_client=owner.sys.api_client,
            model=_V50_MODULE_MODEL,
        )
        owner.ui.log("   \U0001f5e3\ufe0f [V53.7] Multi-Agent Deliberation \ud65c\uc131\ud654")

        owner.adaptive_manager = _v50["get_adaptive_manager"]()
        if owner.failure_learner:
            owner.adaptive_manager.connect_failure_learner(owner.failure_learner)
            owner.ui.log("   \U0001f504 [V54.3] Adaptive Retry Manager \ud65c\uc131\ud654 (FailureLearner \uc5f0\ub3d9)")
        else:
            owner.ui.log("   \U0001f504 [V54.3] Adaptive Retry Manager \ud65c\uc131\ud654")

        owner.constitutional_checker = _v50["ConstitutionalChecker"](genre=genre_type)
        owner.ui.log("   \U0001f4dc [V55.2] Constitutional Checker \ud65c\uc131\ud654")

        owner.writer_template = _v50["WriterTemplate"](genre=genre_type)
        owner.ui.log("   \U0001f4dd [V55.3] Writer Template \ud65c\uc131\ud654")

        project_path = str(owner.current_project.paths.root) if owner.current_project else "."
        owner.pass_rate_monitor = _v50["PassRateMonitor"](project_path)
        owner.ui.log("   \U0001f4ca [V55.3] Pass Rate Monitor \ud65c\uc131\ud654")

        owner.quality_dashboard = _v50["QualityDashboard"](Path(project_path))
        owner.ui.log("   \U0001f4ca [V60] Quality Dashboard \ud65c\uc131\ud654")

        owner.context_advisor = _v50["ContextAdvisor"]()
        owner.ui.log("   \U0001f9ed [SC] Context Advisor \ud65c\uc131\ud654")
