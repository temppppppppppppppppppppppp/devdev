<!-- [참고자료] -->
# Post-Remediation Cross-Cut Integrity Matrix

| Field | Value |
|-------|-------|
| **Baseline** | `bbb00a77` |
| **Date** | 2026-03-15 |

---

## 1. DI Context → Orchestrator Wiring

| Context | Orchestrator | Injection Point | Wiring |
|---------|-------------|-----------------|--------|
| Stage2Context (47 slots) | Stage2Orchestrator | `from_app(app)` in main_a.py | ✅ self.app=0, self.ctx=350 |
| Stage3Context (19 slots) | Stage3Orchestrator | `from_app(app)` in main_a.py | ✅ self.app=lazy-init-only, self.ctx=full |
| Stage4Context (26 slots) | Stage4Orchestrator | `from_app(app)` in main_a.py | ✅ self.app=0, self.ctx=325 |

### Slot Integrity

| Context | Required | Extended | Callbacks | Other | Total |
|---------|----------|----------|-----------|-------|-------|
| Stage2 | 5 (ui, current_project, agents, sys, state_tracker) | 18+1 | 21+1 | 1 session_logger | 47 |
| Stage3 | 2 (ui, current_project) | 11 props | 10 | 1 session_logger | 19 |
| Stage4 | 5 (ui, current_project, agents, sys, state_tracker) | 14 | 7+5 prop | 2 (logger + meta) | 26 |

---

## 2. Callback Chain Integrity

### Stage2Context Callback Matrix

| Callback | Source (main_a.py) | Target (orchestrator) | Verified |
|----------|-------------------|----------------------|----------|
| audit_event | self._audit_event | ctx.audit_event | ✅ |
| write_audit_summary | self._write_audit_summary | ctx.write_audit_summary | ✅ |
| validate_arc_data_fields | StateService.validate_arc_data_fields | ctx.validate_arc_data_fields | ✅ |
| validate_arc_mapping | StateService.validate_arc_mapping | ctx.validate_arc_mapping | ✅ |
| validate_arc_integrity | StateService.validate_arc_integrity | ctx.validate_arc_integrity | ✅ |
| sync_cache_key_to_app | weakref callback | ctx.sync_cache_key_to_app | ✅ |
| safe_commit_async | self._safe_commit_async | ctx.safe_commit_async | ✅ |
| session_logger | self._session_logger | ctx.session_logger | ✅ |
| (+ 13 more) | main_a.py methods | ctx.callback_name | ✅ |

### Stage3Context Callback Matrix

| Callback | Source | Target | Verified |
|----------|--------|--------|----------|
| audit_event | self._audit_event | ctx.audit_event | ✅ |
| write_audit_summary | self._write_audit_summary | ctx.write_audit_summary | ✅ |
| get_protagonist_name | self._get_protagonist_name | ctx.get_protagonist_name | ✅ |
| session_logger | self._session_logger | ctx.session_logger | ✅ |
| (+ 6 more) | main_a.py methods | ctx.callback_name | ✅ |

### Stage4Context Callback Matrix

| Callback | Source | Target | Verified |
|----------|--------|--------|----------|
| audit_event | property-backed via _stage4_context_budget_meta | ctx.audit_event | ✅ |
| write_audit_summary | property-backed | ctx.write_audit_summary | ✅ |
| flush_audit_buffer | self._flush_audit_buffer | ctx.flush_audit_buffer | ✅ |
| session_logger | self._session_logger | ctx.session_logger | ✅ |
| conditional_modules | dict(8 keys) | ctx.conditional_modules | ✅ |
| (+ 8 more) | main_a.py methods / properties | ctx.callback_name | ✅ |

---

## 3. Guard Chain Integrity

```
Input: manuscript text
    │
    ▼
GenreGuard.validate() ──── config/genres/{genre}.yaml
    │                       ├── forbidden_terms
    │                       ├── mandatory_concepts
    │                       └── genre-specific rules
    ▼
WorkGuard.validate() ───── work_guard.yaml (per-project)
    │                       ├── extra_forbidden_terms
    │                       ├── extra_allowed_terms
    │                       ├── extra_forbidden_patterns
    │                       ├── custom_rules
    │                       └── character_constraints
    ▼
StyleGuard.validate() ──── style references
    │                       ├── tone validation
    │                       └── style consistency
    ▼
Output: validation result
```

| Step | Guard | Config Source | Optional | Verified |
|------|-------|-------------|----------|----------|
| 1 | BaseGuard → GenreGuard (10 subclasses) | config/genres/*.yaml | No | ✅ |
| 2 | WorkGuard | work_guard.yaml (per project) | Yes | ✅ |
| 3 | StyleGuard | style references | Yes | ✅ |

---

## 4. Service Boundary Integrity

### Dependency Direction

```
main_a.py (SovereignApp)
    ├── AuditService ← modules/core/services/audit_service.py
    ├── StateService ← modules/core/services/state_service.py
    ├── ProjectService ← modules/core/services/project_service.py
    ├── UIService ← modules/core/services/ui_service.py
    ├── SessionLogger ← modules/core/session_logger.py
    ├── DBManager ← modules/core/db_manager.py
    ├── Stage2Orchestrator ← modules/core/stage2_orchestrator.py
    ├── Stage3Orchestrator ← modules/core/stage3_orchestrator.py
    └── Stage4Orchestrator ← modules/core/stage4_orchestrator.py
```

### Service → Agent/Module Cross-References

| Service | Depends On | Depends On Service? |
|---------|-----------|---------------------|
| AuditService | DBManager (read-only), SessionLogger | No |
| StateService | PromptBuilder, FeedbackSystem | No |
| ProjectService | DBManager, VecMemory, BaseAgent | No |
| UIService | StudioVisualizer (optional) | No |

**No circular service dependencies.** All services are leaf nodes in the dependency graph.

---

## 5. Persistence Sink Integrity

### Write Path Matrix

| Sink | Writer | Lock | Encoding | Append/Overwrite |
|------|--------|------|----------|-----------------|
| project_data.db | DBManager | RLock | WAL mode | Upsert/Update |
| session_*.jsonl | SessionLogger | _write_lock | UTF-8 | Append |
| runtime_audit.jsonl | AuditService | inline | UTF-8 | Append |
| episode_production.jsonl | Stage4 | jsonl_io lock | UTF-8 | Append |
| quality_*.jsonl | DataCollector | jsonl_io lock | UTF-8 | Append |
| failure_*.jsonl | FailureAnalyzer | jsonl_io lock | UTF-8 | Append |
| soft_failures.jsonl | SoftFailure | jsonl_io lock | UTF-8 | Append |
| artifacts/*.json | artifact_logging | None (single-writer) | UTF-8 bytes | Overwrite |
| drafts/ep_*.txt | Orchestrators | None (sequential) | UTF-8 | Overwrite |

### Shutdown Sink Ordering

```
WRITE PHASE (all sinks active)
    │
    ▼
SessionLogger.begin_shutdown() ── JSONL frozen
    │
    ▼
DBManager.begin_shutdown() ──── DB telemetry frozen
    │
    ▼
AuditService.write_audit_summary() ── Proof digest (read-only DB)
    │
    ▼
DBManager.close() ──── Connection closed
```

**Invariant**: No writes occur after begin_shutdown() on the respective sink.

---

## 6. API / Desktop Bridge Integrity

### Communication Paths

| Path | Protocol | Direction | Verified |
|------|----------|-----------|----------|
| /run | HTTP POST | Desktop → Backend | ✅ |
| /stop | HTTP POST | Desktop → Backend | ✅ |
| /run/{id}/input | HTTP POST | Desktop → Backend | ✅ |
| /status | HTTP GET | Splash → Backend | ✅ |
| /events | WebSocket | Backend → Desktop | ✅ |

### Prompt Lifecycle

```
Desktop → POST /run/{id}/input (resolution)
    │
Backend: PromptBroker.resolve(prompt_id, value)
    │
    ├── PromptState.resolved = True
    ├── asyncio.Event.set()
    └── Runner continues
```

**Concurrency model**: Multiple prompt_ids per run, each on its own asyncio.Event. Timeout triggers default value. No silent drops.

---

## 7. Import Graph Integrity

### Circular Dependency Guards (6 files)

| File | Guard Type |
|------|-----------|
| pre_director_manuscript_checker.py | `from __future__ import annotations` + `TYPE_CHECKING` |
| pre_director_narrative_checker.py | `TYPE_CHECKING` |
| pre_director_style_checker.py | `TYPE_CHECKING` |
| relationship_tracker_factions.py | `TYPE_CHECKING` |
| relationship_tracker_npc.py | `TYPE_CHECKING` |
| stage4_context_builder.py | `TYPE_CHECKING` |

**No bare circular imports detected across 244 module files.**
