# 글도비 파이프라인 데이터 플로우 (전체 시각화)

> 2026-02-17 기준. Stage 0 → 2 → 3 → 4 전체 데이터 흐름.

---

## 1. 마스터 파이프라인 개요

```mermaid
flowchart TB
    subgraph STAGE0["Stage 0: 초기 설정"]
        S0_Input["사용자 입력<br/>(컨셉 OR 기존 원고)"]
        S0_Manager["StageZeroManager"]
        S0_Output["📦 Output:<br/>bible, treatment,<br/>style_guide, preset_registry"]
        S0_Input --> S0_Manager --> S0_Output
    end

    subgraph STAGE2["Stage 2: Arc 설계"]
        S2_Orch["Stage2Orchestrator<br/>(794줄)"]
        S2_Pre["PreflightAnalysis<br/>(682줄)"]
        S2_Val["ValidationPipeline<br/>(685줄)"]
        S2_Fin["Finalizer<br/>(543줄)"]
        S2_FP["FourPhaseArcGenerator"]
        S2_Dir["Director.audit_strategic_plan()"]
        S2_Output["📦 Output:<br/>all_refined_arcs (DB)<br/>+ StateTracker 갱신"]

        S2_Orch --> S2_Pre --> S2_FP
        S2_FP --> S2_Val --> S2_Fin --> S2_Dir
        S2_Dir --> S2_Output
    end

    subgraph STAGE3["Stage 3: Blueprint 설계"]
        S3_Orch["Stage3Orchestrator"]
        S3_3P["ThreePhaseBlueprintGenerator"]
        S3_Dir["Director (judgment)"]
        S3_Output["📦 Output:<br/>에피소드별 blueprint (DB)"]

        S3_Orch --> S3_3P --> S3_Dir --> S3_Output
    end

    subgraph STAGE4["Stage 4: 원고 생성"]
        S4_Orch["Stage4Orchestrator<br/>(803줄)"]
        S4_Ctx["ContextBuilder<br/>(570줄)"]
        S4_Int["InterviewRound<br/>(550줄)"]
        S4_Post["PostProcessor"]
        S4_CW["ChiefWriter"]
        S4_Dir["Director.select_and_judge_ensemble()"]
        S4_Output["📦 Output:<br/>원고 파일 + DB<br/>+ 벡터 메모리"]

        S4_Orch --> S4_Ctx --> S4_Int
        S4_Int --> S4_CW --> S4_Dir
        S4_Dir --> S4_Post --> S4_Output
    end

    subgraph CROSS["횡단 컴포넌트"]
        StateTracker["StateTracker<br/>(NPC, 스킬, 플롯, 아이템)"]
        ContInsp["ContinuityInspector"]
        PromptBuilder["PromptBuilder"]
        WorldState["WorldStateManager"]
        FactLedger["FactLedger"]
        GenreGuard["GenreGuard→WorkGuard→StyleGuard"]
        DBManager["DBManager (SQLite)"]
    end

    S0_Output -->|"bible, treatment,<br/>style_guide, preset"| STAGE2
    STAGE2 -->|"refined_arcs[]<br/>+ arc_summary DB"| STAGE3
    STAGE3 -->|"blueprints DB<br/>(에피소드별 씬 계획)"| STAGE4

    StateTracker -.->|"NPC·플롯·스킬 상태"| STAGE2
    StateTracker -.-> STAGE3
    StateTracker -.-> STAGE4
    ContInsp -.->|"연속성 검증"| STAGE2
    ContInsp -.-> STAGE4
    WorldState -.->|"세계 상태 문서"| STAGE2
    WorldState -.-> STAGE4
    FactLedger -.->|"누적 팩트"| STAGE2
    FactLedger -.-> STAGE4
    GenreGuard -.->|"장르 검증"| STAGE2
    GenreGuard -.-> STAGE4
    DBManager -.->|"read/write"| STAGE2
    DBManager -.-> STAGE3
    DBManager -.-> STAGE4
```

---

## 2. Stage 0: 초기 설정 상세

```mermaid
flowchart TB
    subgraph NEW["신규 프로젝트"]
        Concept["사용자 컨셉 (텍스트)"] --> GenreSelect["장르 선택<br/>(11종: 무협/헌터/투자/판타지/...)"]
        GenreSelect --> ProtagConfig["주인공 설정<br/>world_origin, incarnation_type,<br/>pov (1인칭/3인칭제한/전지)"]

        ProtagConfig --> Analyze["StoryExpander.analyze_concept()<br/>→ title, protagonist, timeline,<br/>genre, themes"]
        Analyze --> GenBible["StoryExpander.generate_bible()<br/>→ MasterBible dict"]
        GenBible --> GenTreatment["StoryExpander.generate_treatment(60블록)<br/>→ skeleton → 상세 블록"]
        GenreSelect --> PresetBuild["PresetRegistry.build_initial_hud()<br/>→ 장르별 HUD 스키마"]
    end

    subgraph REVERSE["역공학 (기존 원고)"]
        Manuscripts["기존 원고 파일"] --> LoadMS["ReverseExpander.load_manuscripts()"]
        LoadMS --> DetectGenre["장르 감지"]
        DetectGenre --> ExtractBible["bible 추출"]
        ExtractBible --> ExtractEpBibles["에피소드별 bible 추출"]
        Manuscripts --> StyleExtract["StyleExtractor.extract_from_drafts()<br/>5단계: 통계 → 샘플 → 리듬<br/>→ LLM 심층분석 → 반AI 패턴"]
        ExtractEpBibles --> PersistDB["DB 저장:<br/>manuscripts, state_logs,<br/>episode_bibles, stub arcs/blueprints"]
    end

    subgraph OUTPUT["Stage 0 출력 번들"]
        Bible["📄 bible: dict<br/>MasterBible, ProjectData,<br/>AssetLibrary (NPCs), InitialHUD"]
        Treatment["📄 treatment: list[dict]<br/>block_id, title, content,<br/>context, event_villain,<br/>solution, reward"]
        StyleGuide["📄 StyleGuide: dataclass<br/>tone, pov, sentence_length,<br/>dialogue_ratio, description_style,<br/>vocabulary_level, sentence_rhythm,<br/>emotion_rendering, anti_ai_patterns,<br/>exemplary_passages"]
        Preset["📄 PresetRegistry<br/>COMMON_PRESET + GENRE_PRESETS<br/>NPC_COMMON + NPC_GENRE"]
    end

    GenBible --> Bible
    GenTreatment --> Treatment
    StyleExtract --> StyleGuide
    PresetBuild --> Preset
    PersistDB --> Bible
```

---

## 3. Stage 2: Arc 설계 전체 흐름

```mermaid
flowchart TB
    subgraph INIT["초기화"]
        LoadBible["DB에서 bible 로드"]
        LoadArcs["DB에서 기존 arcs 로드"]
        InitST["StateTracker.full_extract_from_arcs()<br/>17개 카테고리 일괄 추출"]
        InitWS["WorldStateManager 초기화"]
        InitFL["FactLedger 초기화"]
        CreateCtx["Stage2Context 생성<br/>(44 __slots__)"]

        LoadBible --> CreateCtx
        LoadArcs --> InitST --> CreateCtx
        InitWS --> CreateCtx
        InitFL --> CreateCtx
    end

    subgraph BATCH["배치 농축 (5 arcs/batch)"]
        RawBlocks["원시 treatment 블록<br/>(Stage 0에서)"]
        EnrichParallel["Analyst.enrich_raw_block_async()<br/>× 5 병렬 (Semaphore=5)<br/>→ 컨텍스트 확장된 블록"]
        StitchJoints["Analyst.stitch_joints()<br/>→ 인접 아크 간 전환 봉합<br/>(joint_docs 생성)"]

        RawBlocks --> EnrichParallel --> StitchJoints
    end

    subgraph LOOP["아크별 시도 루프 (max 5회)"]
        direction TB
        SETUP["_preflight_state_setup()"]
        ANALYSIS["_preflight_arc_analysis()"]
        ENRICHMENT["_preflight_enrichment()"]
        VALIDATION["ValidationPipeline.run_validation()"]
        FINALIZE["Finalizer.run_finalize()"]

        SETUP --> ANALYSIS --> ENRICHMENT --> VALIDATION --> FINALIZE

        FINALIZE -->|"action='break' (PASS)"| PASS_OUT["✅ Arc 저장 → 다음 Arc"]
        FINALIZE -->|"action='retry/next' (REJECT)"| RETRY["🔄 피드백 반영 → 재시도"]
        RETRY --> SETUP
    end

    INIT --> BATCH --> LOOP
```

---

## 4. Stage 2: Preflight 3단계 상세

```mermaid
flowchart TB
    subgraph SETUP["① _preflight_state_setup()"]
        direction TB
        ParallelExec["ThreadPoolExecutor 병렬 실행"]
        ArcDrive["🔀 Weaver LLM<br/>→ arc_drive dict<br/>(서사 방향, 테마)"]
        PreflightLLM["🔀 Preflight LLM<br/>→ preflight_injection<br/>(아이템 타임라인,<br/>금기사항, 관계맵)"]
        CumState["StateExtractor<br/>.extract_cumulative_state()<br/>→ entity_registry"]
        ConstraintCompile["ConstraintCompiler.compile()<br/>→ 제약조건 블록"]

        ParallelExec --> ArcDrive
        ParallelExec --> PreflightLLM
        ParallelExec --> CumState
        ArcDrive --> SetupOut
        PreflightLLM --> SetupOut
        CumState --> SetupOut
        ConstraintCompile --> SetupOut

        SetupOut["📦 Output:<br/>arc_drive, constraint_block,<br/>cached_preflight_injection,<br/>cached_preflight_result,<br/>max_attempts=5, st_snapshot"]
    end

    subgraph ANALYSIS["② _preflight_arc_analysis()"]
        direction TB
        BuildContext["enhanced_context 조립:<br/>+ 제약조건 (ConstraintCompiler)<br/>+ Stage2Optimizer 패턴<br/>+ V51 intelligence 주입<br/>+ 품질추세 (QualityDashboard)<br/>+ focus mode (재시도 시)<br/>+ stage3→2 역방향 피드백"]
        RecentPatterns["recent_patterns 수집:<br/>최근 arcs의 hybrid_composition.primary"]
        EntityRegistry["entity_registry_for_director 준비"]

        BuildContext --> AnalysisOut
        RecentPatterns --> AnalysisOut
        EntityRegistry --> AnalysisOut

        AnalysisOut["📦 Output:<br/>refined_arc (None),<br/>generation_method,<br/>constraint_block,<br/>entity_registry_for_director"]
    end

    subgraph ENRICHMENT["③ _preflight_enrichment()"]
        direction TB
        PatchCheck{"이전 시도<br/>score ≥ 50?"}

        PatchArc["FourPhase.patch_arc_with_feedback()<br/>→ 원본 보존 + 피드백 부분만 수정"]
        GenerateArc["FourPhase.generate()<br/>→ 3후보 앙상블 생성"]

        PatchCheck -->|"Yes (패치 모드)"| PatchArc
        PatchCheck -->|"No (전면 재생성)"| GenerateArc

        STSnapshot["StateTracker 스냅샷 (deep copy)<br/>→ REJECT 시 롤백용"]
        ExtractState["StateTracker 상태 추출:<br/>NPC 사망, 스킬 습득, 관계,<br/>플롯, 아이템, 시간, 부상,<br/>동행자, 약속, 감정"]
        SaveArcSummary["arc_summary DB 저장"]

        PatchArc --> STSnapshot
        GenerateArc --> STSnapshot
        STSnapshot --> ExtractState --> SaveArcSummary

        EnrichOut["📦 Output:<br/>refined_arc (or None),<br/>generation_method,<br/>four_phase_passed,<br/>draft_validator_passed,<br/>consensus_passed,<br/>st_snapshot,<br/>director_feedback_for_fourphase"]
    end

    SETUP --> ANALYSIS --> ENRICHMENT
```

---

## 5. FourPhaseArcGenerator 내부 구조

```mermaid
flowchart TB
    subgraph FP["FourPhaseArcGenerator.generate()"]
        direction TB
        Input["📥 Input:<br/>enriched_block, enhanced_context,<br/>analyst_weapons, constraint_block"]

        EpCount["_determine_ep_count()<br/>Python 휴리스틱: 텍스트 길이 +<br/>문장 수 → 3~7화"]

        subgraph P1["Phase 1: 제약조건 컴파일"]
            CC["ConstraintCompiler.compile()<br/>→ 캐싱된 제약조건"]
            NEI["NegativeExampleInjector<br/>→ 회피할 안티패턴"]
        end

        subgraph P2["Phase 2: Arc 생성"]
            PatchCheck{"_prev_rejected_arc<br/>존재 + retry ≥ 1?"}
            PatchFirst["patch_arc_with_feedback()<br/>→ 이전 거절 Arc 부분 수정"]
            Ensemble["ArcEnsembleGenerator<br/>.generate_ensemble()<br/>→ 3 후보 Arc (병렬 생성)"]

            PatchCheck -->|"Yes"| PatchFirst
            PatchCheck -->|"No"| Ensemble
            PatchFirst -->|"패치 실패"| Ensemble
        end

        subgraph P3["Phase 3: 검증"]
            UAV["UnifiedArcValidator.validate()<br/>→ 최적 Arc + 점수"]
            PC["PreflightChecker<br/>→ 최종 안전성 검사"]
        end

        Input --> EpCount --> P1 --> P2 --> P3

        RetryLoop{"Validator PASS?"}
        P3 --> RetryLoop
        RetryLoop -->|"REJECT"| SavePrev["_prev_rejected_arc 저장<br/>+ feedback 저장"]
        SavePrev --> P2
        RetryLoop -->|"PASS"| Output

        Output["📦 Output:<br/>refined_arc dict + pipeline_result<br/>(tactical_doc, beat_sequence,<br/>ep_start, ep_end, joint_docs,<br/>status_shadow, state_constraints,<br/>hybrid_composition)"]
    end

    subgraph PATCH["patch_arc_with_feedback()"]
        PInput["📥 Input:<br/>이전 Arc + Director 피드백<br/>+ score (≥ 50)"]
        Preserve["좋은 섹션 보존"]
        PartialFix["LLM 부분 수정<br/>(약한 섹션만)"]
        POutput["📦 Output:<br/>패치된 Arc (or None)"]

        PInput --> Preserve --> PartialFix --> POutput
    end
```

---

## 6. Stage 2: 검증 파이프라인 10단계

```mermaid
flowchart TB
    subgraph VAL["ValidationPipeline.run_validation()"]
        direction TB
        Input["📥 Input: refined_arc,<br/>four_phase_passed, all_refined_arcs,<br/>entity_registry, global_arc_no"]

        V1["① DraftValidator (1차)<br/>→ 구조·분량·필드 검증"]
        V2["② SelfReflector<br/>→ LLM 자기 검토"]
        V3["③ Consensus (3-LLM 투표)<br/>→ 다수결 합의"]
        V4["④ Data + Mapping 검증<br/>→ 데이터 정합성"]
        V5["⑤ Auto-Corrector<br/>→ 자동 수정 가능한 오류 교정"]
        V6["⑥ Constraint 사전검증<br/>→ 제약조건 위반 체크"]
        V7["⑦ FlowGuard<br/>→ NarrativeStructureAnalyzer:<br/>비트 정체 감지"]
        V8["⑧ DuplicateGuard<br/>→ MD5 해시 + SequenceMatcher<br/>기존 Arc 중복 체크"]
        V9["⑨ DraftValidator (2차)<br/>+ ArcCorrector<br/>→ 최종 구조 검증"]
        V10["⑩ ContinuityInspector<br/>→ Arc 수준 연속성 검증<br/>(NPC·아이템·타임라인)"]

        Input --> V1 --> V2 --> V3 --> V4 --> V5
        V5 --> V6 --> V7 --> V8 --> V9 --> V10

        Result{"검증 결과"}
        V10 --> Result
        Result -->|"action='proceed'"| GoFin["→ Finalizer로"]
        Result -->|"action='retry'"| GoRetry["→ 재생성"]
    end
```

---

## 7. Stage 2: Finalizer + Director 심사

```mermaid
flowchart TB
    subgraph FIN["Finalizer.run_finalize()"]
        direction TB
        Input["📥 Input:<br/>validated refined_arc,<br/>enriched_block, arc_drive,<br/>all_refined_arcs, constraint_db"]

        MissingCheck{"critical data<br/>누락 체크"}
        MissingCheck -->|"누락"| RetryAction["action='retry'<br/>+ 누락 피드백"]

        PreAudit["사전 감사 준비:<br/>① SemanticPlotGuard 중복 체크<br/>② V67 확장 컨텍스트 (30 Arc)<br/>③ story_context 조립<br/>④ 연속성 검사 7항목"]
        MissingCheck -->|"OK"| PreAudit

        DirectorCall["Director.audit_strategic_plan()<br/>📥 arc, story_context,<br/>entity_registry, constraints<br/>📦 score(0-100), decision, reason,<br/>re_slice_instruction"]
        PreAudit --> DirectorCall

        QuotaCheck{"API quota 폴백?<br/>(score=0 + DraftValidator<br/>+ Consensus 모두 PASS)"}
        DirectorCall --> QuotaCheck
        QuotaCheck -->|"Yes"| OverridePASS["강제 PASS<br/>(v60_43_quota_override)"]

        Verdict{"Director 판정"}
        QuotaCheck -->|"No"| Verdict
        OverridePASS --> PassFlow

        subgraph PassFlow["✅ PASS → action='break'"]
            ValidateArc["Pydantic arc 무결성 검증"]
            AtomicCommit["DB 원자적 커밋:<br/>arc + 메타데이터 저장"]
            ConstraintUpdate["ConstraintDB 갱신"]
            GenArcCtx["PromptBuilder<br/>arc_context 생성"]
            VolSummary{"global_arc_no<br/>% 10 == 0?"}
            GenVolSum["Director LLM<br/>→ volume_summary 생성"]
            GenSeriesSum["Director LLM<br/>→ series_summary 갱신"]

            ValidateArc --> AtomicCommit --> ConstraintUpdate
            ConstraintUpdate --> GenArcCtx --> VolSummary
            VolSummary -->|"Yes"| GenVolSum --> GenSeriesSum
        end

        subgraph RejectFlow["❌ REJECT → action='next'"]
            Rollback["StateTracker 롤백<br/>(st_snapshot 복원)"]
            BuildFB["director_feedback_for_fourphase 조립:<br/>reject_reason + base_feedback<br/>+ intensity_guide"]
            RecordMetrics["거절 메트릭 기록:<br/>PassRateMonitor,<br/>QualityDashboard,<br/>stage_rejection_history"]
            SavePrevAttempt["_previous_attempt 갱신<br/>(score ≥ 50이면 패치용 보존)"]

            Rollback --> BuildFB --> RecordMetrics --> SavePrevAttempt
        end

        Verdict -->|"PASS"| PassFlow
        Verdict -->|"REJECT"| RejectFlow
    end
```

---

## 8. Stage 3: Blueprint 생성

```mermaid
flowchart TB
    subgraph S3["Stage 3: Blueprint 생성"]
        direction TB

        LazyInit["Lazy init:<br/>StateTracker, WorldState, FactLedger<br/>→ Stage3Context (19 __slots__)"]
        LoadArcs["DB에서 arcs 로드"]

        subgraph EPISODE_LOOP["에피소드별 루프"]
            GetArcCtx["DB에서 arc_context 로드<br/>(Stage 2에서 생성한 캐시)"]
            GetEntityReg["entity_registry 로드<br/>(아크별 캐싱)"]

            subgraph THREE_PHASE["ThreePhaseBlueprintGenerator.generate()"]
                subgraph BP1["Phase 1: 제약조건"]
                    BCC["BlueprintConstraintCompiler.compile()<br/>→ 씬 제약, NPC 제약, 페이싱 요구"]
                end

                subgraph BP2["Phase 2: 앙상블 생성"]
                    BEG["BlueprintEnsembleGenerator<br/>.generate_ensemble()<br/>→ 3전략 × 3재시도 = 최대 9후보"]
                    PrevBest["_previous_best 추적<br/>(패치 모드용)"]
                end

                subgraph BP3["Phase 3: 검증 + Director"]
                    UBV["UnifiedBlueprintValidator.validate()<br/>→ 후보 순위 매기기"]
                    DirJudge["Director 심사<br/>→ PASS/REJECT"]
                end

                BP1 --> BP2 --> BP3

                BPVerdict{"Director 판정"}
                BP3 --> BPVerdict
                BPVerdict -->|"PASS"| BPSave["Blueprint DB 저장<br/>+ prev_blueprints 갱신"]
                BPVerdict -->|"REJECT<br/>score ≥ 50"| BPPatch["패치 모드:<br/>_previous_best 부분 수정"]
                BPVerdict -->|"REJECT<br/>score < 50"| BPRegen["전면 재생성"]
                BPPatch --> BP2
                BPRegen --> BP2
            end

            GetArcCtx --> THREE_PHASE
            GetEntityReg --> THREE_PHASE
        end

        LazyInit --> LoadArcs --> EPISODE_LOOP
    end
```

---

## 9. Stage 4: 원고 생성 전체 흐름

```mermaid
flowchart TB
    subgraph S4_INIT["세션 준비"]
        InitCW["ChiefWriter 초기화"]
        InitValidators["검증기 초기화:<br/>ManuscriptValidator,<br/>ConsistencyValidator,<br/>BlockingValidator,<br/>ContinuityValidator"]
        LoadStyle["StyleGuide 로드"]
        CreateCtx["Stage4Context (24 __slots__)"]

        InitCW --> CreateCtx
        InitValidators --> CreateCtx
        LoadStyle --> CreateCtx
    end

    subgraph S4_EP["에피소드별 루프"]
        LoadBP["DB에서 blueprint 로드"]
        LoadArc["DB에서 arc_data 로드"]

        subgraph CTX["ContextBuilder.prepare_episode_context()"]
            Collect["수집 항목:<br/>arc_pos, tactical_doc,<br/>prev_text (마지막 2000자),<br/>prev_ending (마지막 문단),<br/>prev_manuscripts (30화분),<br/>episode_digest"]
            ChainLink["V68 chain_link 로드:<br/>cliffhanger, pending_actions,<br/>emotional_state, physical_state,<br/>location, time_marker"]
            HUD["HUD report + inventory +<br/>martial_arts + dead_npcs +<br/>item_timeline"]
            WSSummary["WorldState 요약"]

            Collect --> ChainLink --> HUD --> WSSummary
        end

        subgraph MANDATORY["ContextBuilder.build_mandatory_context()"]
            RefAnchor["reference_anchor_prompt<br/>(PromptBuilder)"]
            MandCtx["mandatory_context 조립:<br/>blueprint + arc + state +<br/>chain_link + world_state"]
            AntiTrope["anti_trope_prompt"]
            Justification["justification_prompt"]
            Reflexion["reflexion_prompt"]

            RefAnchor --> MandCtx --> AntiTrope --> Justification --> Reflexion
        end

        LoadBP --> CTX --> MANDATORY

        subgraph INTERVIEW["면담 루프 (max 5라운드)"]
            ROUND["InterviewRound.run()"]
            RoundResult{"Director 판정"}

            ROUND --> RoundResult
            RoundResult -->|"PASS"| GoPost["→ PostProcessor"]
            RoundResult -->|"REJECT<br/>(feedback + score)"| NextRound["다음 라운드"]
            NextRound --> ROUND
        end

        MANDATORY --> INTERVIEW

        subgraph POST["PostProcessor.process_pass_result()"]
            HUDUpdate["Director.on_approve_workflow()<br/>→ HUD 상태 갱신"]
            DBSave["DB 저장:<br/>manuscript + martial_arts"]
            FileSave["파일 저장:<br/>카카오/네이버 포맷"]
            VecMem["VecMemory 저장:<br/>벡터 임베딩"]
            NarrSum["서사 요약<br/>(5화마다)"]
            ExtractChain["chain_link 추출:<br/>Director LLM →<br/>cliffhanger, pending_actions,<br/>emotional/physical_state,<br/>location, time_marker"]
            Advisory["어드바이저리 감지:<br/>NPC 과잉 (3-5C),<br/>반복 감지 (3-B),<br/>품질 회귀 (3-QR)"]

            HUDUpdate --> DBSave --> FileSave --> VecMem
            VecMem --> NarrSum --> ExtractChain --> Advisory
        end

        INTERVIEW --> POST
    end

    S4_INIT --> S4_EP
```

---

## 10. Stage 4: 단일 면담 라운드 상세

```mermaid
flowchart TB
    subgraph ROUND["InterviewRound.run()"]
        direction TB
        RoundNum{"라운드 번호"}

        subgraph R0["라운드 0: 초기 생성"]
            CWEnsemble["ChiefWriter.generate_ensemble()<br/>→ 3 후보 원고 (병렬)<br/>+ mandatory_context 전문 주입"]
        end

        subgraph R1PLUS["라운드 1+: 피드백 기반"]
            ScoreCheck{"이전 score<br/>≥ 50?"}
            Patch["ChiefWriter.patch_with_feedback()<br/>→ 좋은 부분 보존<br/>→ 약한 섹션만 수정"]
            Regen["ChiefWriter.regenerate_with_feedback()<br/>→ Director 피드백 반영<br/>→ 전면 재생성"]

            ScoreCheck -->|"Yes + 이전 원고 존재"| Patch
            ScoreCheck -->|"No"| Regen
        end

        RoundNum -->|"0"| R0
        RoundNum -->|"1+"| R1PLUS

        subgraph PYVAL["Python 검증 (advisory)"]
            MVal["ManuscriptValidator<br/>→ 길이·포맷·구조"]
            ConsVal["ConsistencyValidator<br/>→ NPC명·아이템·장소"]
            BlockVal["BlockingValidator<br/>→ 사망 NPC 등장 체크<br/>→ 파괴된 엔티티 체크"]
            ContVal["ContinuityValidator<br/>→ 타임라인·인과관계"]
            FrustCheck["좌절감 연속 체크"]
            V67Hist["V67 원고 이력<br/>모순 체크 (7항목)"]

            MVal --> ConsVal --> BlockVal --> ContVal --> FrustCheck --> V67Hist
        end

        subgraph DIRECTOR["Director.select_and_judge_ensemble()"]
            DirSelect["3후보 중 최적 선택"]
            DirScore["점수: 0-100"]
            SelfCon["Self-Consistency 체크:<br/>점수 40-65 구간 →<br/>3-LLM 투표로 재확인"]
            AdaptThresh["적응형 임계값:<br/>아크 위치 + 재시도 횟수<br/>→ 임계값 동적 조정"]

            DirSelect --> DirScore --> SelfCon --> AdaptThresh
        end

        R0 --> PYVAL
        R1PLUS --> PYVAL
        PYVAL -->|"후보 + 경고 목록"| DIRECTOR

        Verdict{"Director 판정"}
        DIRECTOR --> Verdict

        Verdict -->|"PASS"| PassOut["📦 final_manuscript,<br/>final_title,<br/>final_state_updates"]
        Verdict -->|"REJECT"| RejectOut["📦 previous_attempt:<br/>score, best_manuscript,<br/>rejection_reason,<br/>action_items"]
    end
```

---

## 11. Director 판정 흐름 (전 Stage 통합)

```mermaid
flowchart LR
    subgraph S2_DIR["Stage 2: Arc 심사"]
        S2Call["audit_strategic_plan()<br/>📥 arc, story_context,<br/>확장 이전 (30 arcs)"]
        S2Score["Score 0-100<br/>+ 상세 피드백"]
        S2V{"판정"}
        S2Call --> S2Score --> S2V
        S2V -->|"PASS"| S2P["Arc DB 저장<br/>StateTracker 갱신<br/>요약 생성"]
        S2V -->|"REJECT"| S2R["StateTracker 롤백<br/>피드백 → FourPhase<br/>재시도 (max 5)"]
    end

    subgraph S3_DIR["Stage 3: Blueprint 심사"]
        S3Call["judgment<br/>📥 blueprint, arc_context,<br/>constraints"]
        S3Score3["Score 0-100"]
        S3V3{"판정"}
        S3Call --> S3Score3 --> S3V3
        S3V3 -->|"PASS"| S3P["Blueprint DB 저장"]
        S3V3 -->|"REJECT"| S3R["피드백 →<br/>ThreePhase 재시도"]
    end

    subgraph S4_DIR["Stage 4: 원고 심사"]
        S4Call["select_and_judge_ensemble()<br/>📥 3후보 + mandatory_context<br/>+ Python 경고"]
        S4Select["최적 후보 선택"]
        S4Score4["Score 0-100"]
        S4SC["Self-Consistency<br/>(40-65 → 3투표)"]
        S4AT["적응형 임계값"]
        S4V4{"판정"}

        S4Call --> S4Select --> S4Score4 --> S4SC --> S4AT --> S4V4
        S4V4 -->|"PASS"| S4P["→ PostProcessor"]
        S4V4 -->|"REJECT"| S4R["score ≥ 50: 패치 모드<br/>score < 50: 전면 재생성"]
    end
```

---

## 12. 패치 모드 분기 (전 Stage 통합)

```mermaid
flowchart TB
    subgraph PATCH_ALL["패치 모드 — 전 Stage 통합"]
        direction TB

        REJECT["Director REJECT"]
        ScoreCheck{"score ≥ 50<br/>(PATCH_REWRITE)?"}
        REJECT --> ScoreCheck

        subgraph S2_PATCH["Stage 2: Arc 패치"]
            S2P_In["이전 rejected_arc 보존"]
            S2P_Call["FourPhase.patch_arc_with_feedback()<br/>→ 원본 Arc의 좋은 부분 유지<br/>→ Director 지적사항만 수정"]
            S2P_Fail["패치 실패 → 전면 재생성"]
            S2P_In --> S2P_Call
            S2P_Call -->|"실패"| S2P_Fail
        end

        subgraph S3_PATCH["Stage 3: Blueprint 패치"]
            S3P_In["이전 _previous_best 보존"]
            S3P_Call["ThreePhase 내부 패치<br/>→ 원본 Blueprint 부분 수정"]
            S3P_Fail["패치 실패 → 9후보 재생성"]
            S3P_In --> S3P_Call
            S3P_Call -->|"실패"| S3P_Fail
        end

        subgraph S4_PATCH["Stage 4: 원고 패치"]
            S4P_In["이전 best_manuscript 보존"]
            S4P_Call["ChiefWriter.patch_with_feedback()<br/>→ 원본 원고 좋은 부분 유지<br/>→ 약한 섹션만 수정"]
            S4P_Fail["패치 실패 → 전면 재생성"]
            S4P_In --> S4P_Call
            S4P_Call -->|"실패"| S4P_Fail
        end

        subgraph FP_PATCH["FourPhase 내부 패치"]
            FP_In["이전 _prev_rejected_arc 보존"]
            FP_Call["patch_arc_with_feedback()<br/>→ Validator 거절 Arc 부분 수정"]
            FP_Fail["패치 실패 → 3후보 앙상블"]
            FP_In --> FP_Call
            FP_Call -->|"실패"| FP_Fail
        end

        subgraph BE_PATCH["Block Enricher 패치"]
            BE_In["이전 enrichment 원본 보존<br/>([:20000] 잘라서)"]
            BE_Call["LLM 재시도 프롬프트:<br/>'이전 결과 원본 보존 +<br/>지적사항만 수정'"]
            BE_In --> BE_Call
        end

        ScoreCheck -->|"Yes"| S2_PATCH
        ScoreCheck -->|"Yes"| S3_PATCH
        ScoreCheck -->|"Yes"| S4_PATCH
        ScoreCheck -->|"No"| FullRegen["전면 재생성"]
    end
```

---

## 13. 횡단 컴포넌트 데이터 흐름

```mermaid
flowchart TB
    subgraph ST["StateTracker (facade + 3 서브모듈)"]
        ST_NPC["StateTrackerNPC:<br/>npc_registry, deaths, skills,<br/>relationships, injuries,<br/>movements, companions,<br/>commitments, emotion"]
        ST_Fin["StateTrackerFinancial:<br/>financial_registry<br/>(투자 장르 전용)"]
        ST_Plot["StateTrackerPlots:<br/>resolved_plots, active_plots,<br/>suspended_plots,<br/>entity_destructions"]
        ST_Main["Main: EpisodeState<br/>(location, weapons, items,<br/>injuries, internal_energy,<br/>relationships, extra_fields)"]
        ST_Extract["full_extract_from_arcs():<br/>17개 카테고리 일괄 추출"]
    end

    subgraph CI["ContinuityInspector (facade + 4 서브모듈)"]
        CI_Arc["ArcValidator:<br/>Arc 수준 연속성"]
        CI_BP["BlueprintValidator:<br/>Blueprint 수준 연속성"]
        CI_MS["ManuscriptValidator:<br/>원고 수준 연속성"]
        CI_Track["TrackerIntegration:<br/>StateTracker 연동"]
    end

    subgraph PB["PromptBuilder (15메서드, 5카테고리)"]
        PB_Writer["Writer guides"]
        PB_Arc["generate_arc_context_v60()"]
        PB_V50["V50 plugins"]
        PB_Val["build_validation_context()"]
        PB_Item["build_item_acquisition_timeline()"]
    end

    subgraph GG["Guard 체인"]
        GG1["GenreGuard<br/>(무협/헌터/투자/판타지 + 6확장)"]
        GG2["WorkGuard<br/>(작품별 YAML:<br/>금기어/허용어/금기패턴/<br/>필수개념/캐릭터제약)"]
        GG3["StyleGuard<br/>(문체 분석 결과 자동 생성)"]
        GG1 -->|"chain"| GG2 -->|"chain"| GG3
    end

    subgraph DB["DBManager (SQLite)"]
        DB_T["테이블:<br/>arcs, blueprints, manuscripts,<br/>episode_bibles, state_logs,<br/>npc_history, director_selections,<br/>anchors (world_state, fact_ledger,<br/>chain_link_N, volume_summary_N,<br/>series_summary, arc_summary_N),<br/>constraint_db, vec_memory"]
    end

    ST -->|"상태 스냅샷"| S2["Stage 2"]
    ST -->|"NPC 데이터"| S3["Stage 3"]
    ST -->|"전체 상태"| S4["Stage 4"]
    CI -->|"Arc 검증"| S2
    CI -->|"Blueprint 검증"| S3
    CI -->|"원고 검증"| S4
    PB -->|"writer guide,<br/>arc context"| S4
    GG -->|"deep_validation"| S2
    GG -->|"deep_validation"| S4
    DB <-->|"read/write"| S2
    DB <-->|"read/write"| S3
    DB <-->|"read/write"| S4
```

---

## 14. 핵심 데이터 구조 사전

| 데이터 구조 | 생성 | 소비 | 주요 필드 |
|---|---|---|---|
| **bible** (dict) | Stage 0 | Stage 2, 3, 4 | MasterBible, ProjectData, AssetLibrary (NPCs), InitialHUD |
| **treatment** (list[dict]) | Stage 0 | Stage 2 | block_id, title, content, context, event_villain, solution, reward |
| **StyleGuide** (dataclass) | Stage 0 | Stage 4 | tone, pov, sentence_length, dialogue_ratio, anti_ai_patterns, exemplary_passages |
| **refined_arc** (dict) | Stage 2 FourPhase | Stage 2→3→4 | tactical_doc, beat_sequence, ep_start, ep_end, joint_docs, status_shadow, state_constraints, hybrid_composition |
| **blueprint** (dict) | Stage 3 ThreePhase | Stage 4 | scene_list, pacing, npc_assignments, emotional_beats |
| **manuscript** (str) | Stage 4 ChiefWriter | 파일 출력 | 전체 에피소드 텍스트 (4,000~15,000자) |
| **arc_drive** (dict) | Weaver LLM | Stage 2 Preflight | desire_vector, themes, narrative_direction |
| **chain_link** (dict) | Stage 4 Post | 다음 에피소드 Stage 4 | cliffhanger, pending_actions, emotional_state, physical_state, location, time_marker |
| **entity_registry** (dict) | StateExtractor | Stage 2 Director | NPC별 역할·상태·관계 |
| **st_snapshot** (dict) | Stage 2 Preflight | REJECT 시 롤백 | StateTracker 전체 딥카피 |
| **director_feedback** (str) | Director | FourPhase/ChiefWriter | score, 상세 비평, 개선 제안 |
| **previous_attempt** (dict) | REJECT 시 | 다음 시도 패치 모드 | score, best_arc/manuscript, rejection_reason |

---

## 15. 핵심 상수

| 상수 | 값 | 위치 | 용도 |
|---|---|---|---|
| PatchModeThresholds.REWRITE | 50 | constants.py | 50 미만: 전면 재생성 |
| PatchModeThresholds.PATCH | 80 | constants.py | 50-80: 패치, 80+: Director PASS |
| ManuscriptLimits.MIN | 4,000 | constants.py | 최소 원고 길이 |
| ManuscriptLimits.TARGET | 5,000 | constants.py | 목표 원고 길이 |
| ManuscriptLimits.MAX | 15,000 | constants.py | 최대 원고 길이 |
| Self-Consistency 구간 | 40-65 | director_ensemble.py | 3-LLM 투표 트리거 |
| 면담 라운드 | 5 | stage4_orchestrator.py | Stage 4 재시도 한도 |
| Arc 시도 횟수 | 5 | stage2_orchestrator.py | Stage 2 재시도 한도 |
| 배치 크기 | 5 | stage2_orchestrator.py | 배치당 Arc 수 |
| 이전 원고 참조 | 30화 | stage4_context_builder.py | V67 확장 컨텍스트 |
| Volume 요약 주기 | 10 Arc | stage2_finalizer.py | 요약 생성 빈도 |
| 서사 요약 주기 | 5화 | stage4_post_processor.py | 요약 생성 빈도 |
