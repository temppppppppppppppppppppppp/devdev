# Agent Graph

Purpose:
- Show the live Stage 2/3/4 call graph in text form.
- Give debugging and documentation work a common starting point.

## Stage 2 Call Graph
```text
main_a._stage_2_arcs()
  -> Stage2Context.from_app()
  -> Stage2Orchestrator.stage_2_arcs_async_logic()
     -> Stage2PreflightAnalysis._preflight_state_setup()
        -> agents["weaver"].generate_arc_drive()
        -> agents["preflight"].analyze()
        -> constraint_db.generate_constraint_block()
     -> Stage2PreflightAnalysis._preflight_arc_analysis()
        -> agents["state_extractor"].extract_cumulative_state()
     -> Stage2PreflightAnalysis._preflight_enrichment()
        -> agents["four_phase"].generate() / patch_arc_with_feedback()
     -> Stage2ValidationPipeline.run_validation()
        -> arc_draft_validator.validate()
        -> optional consensus / continuity / duplicate / flow guards
     -> Stage2Finalizer.run_finalize()
        -> ctx.validate_arc_data_fields()            # live repair hook seam
        -> agents["director"].audit_strategic_plan()
        -> save_v20_anchor("arcs", ...)
```

Notes:
- `Stage2Orchestrator` tries `state_tracker.bind_world_state(getattr(ctx, "world_state", None))`, but `Stage2Context` does not currently expose a dedicated `world_state` slot.
- Stage 2 QualityGate uses shared `scoring.quality_gate_score = 90`.

## Stage 3 Call Graph
```text
main_a._stage_3_blueprints()
  -> Stage3Context.from_app()
  -> Stage3Orchestrator.stage_3_batch_blueprinting()
     -> _init_state_tracker_if_needed()
     -> _init_world_state_if_needed()
     -> _init_fact_ledger_if_needed()
     -> loop per episode
        -> _process_single_episode()
           -> ctx.validate_arc_data_fields()         # optional upstream repair seam
           -> _get_entity_registry()
           -> _load_prev_blueprint()
           -> _generate_blueprint()
              -> agents["three_phase_bp"].generate(max_retries=9)
                 -> BlueprintConstraintCompiler.compile()
                 -> BlueprintEnsembleGenerator.generate_ensemble()
                    -> ThreadPoolExecutor(max_workers=3)
                 -> UnifiedBlueprintValidator.validate()
                    -> director.compare_and_select_blueprint() or audit_manuscript()
                 -> QualityGate score=90 on PASS only
                 -> PASS_WITH_FIX patch loop (max 3)
                 -> PASS_WITH_WARNING degraded fallback possible
           -> current_project.save_blueprint()
     -> write_audit_summary("stage3_complete") only when the loop finishes normally
```

Notes:
- Stage 3 injects treatment-block and timeline context before blueprint generation.
- Stage 3 and Stage 4 still extract entity state through different entry shapes, which is why cost / parity discussions recur.

## Stage 4 Call Graph
```text
main_a._stage_4_chief_writer()
  -> Stage4Context.from_app()
  -> Stage4Orchestrator.stage_4_v2_chief_writer()
     -> _prepare_stage4_session()
        -> lazy init context_builder / interview_round / post_processor
     -> per episode:
        -> current_project.get_blueprint(next_ep)    # DB blueprint SSOT
        -> context_builder.prepare_episode_context()
        -> _run_interview_loop()
           -> Stage4InterviewRound.run()
              -> chief_writer.generate_ensemble() / regenerate_with_feedback() / inplace_patch()
              -> _build_cv_context()
                 -> _resolve_npc_profiles()
                    -> ctx.extract_npc_profiles() first
                    -> AssetLibrary fallback if facade fails
              -> manuscript_validator + consistency/blocking/continuity validators
              -> advisory chain (TruthGate, NPC/Numeric/Relationship drift, Flashback, InfoParadox, etc.)
              -> director.select_and_judge_ensemble()
              -> PASS -> QualityGate 90
              -> PASS_WITH_FIX -> patch loop (max 3)
              -> EMPTY -> caller verdict EMPTY, attempt sink verdict ERROR/empty_candidates
           -> optional CoVe quick_verify -> verify
        -> post_processor.process_pass_result()
           -> save_manuscript + episode_bible + state/world/fact + memory updates
```

Notes:
- Stage 4 live round count comes from `retry.director_max_attempts` in YAML; Python fallback defaults may still say `5` if config lookup fails.
- Stage 4 routing is driven by `fix_scope`, `inplace_below`, and `rewrite_below`, not by an older mid-tier patch threshold key.

## Last Verified
- Date: 2026-03-13
- Commit: `e18f9910`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
