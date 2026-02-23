# Opus TF-5: ?꾩껜 ?쒖뒪???⑥튂 ?ㅻ뜑 (32嫄?

> **[Codex ?묒뾽 吏????諛섎뱶??以??**
>
> ## ?꾧뎄 ?쒗븳
> - `rg`, `grep`, `fgrep`, `ag`, `ack` ??**?먮룞 寃???꾧뎄 ?ъ슜 湲덉?**.
> - 諛섎뱶???대떦 ?뚯씪??**吏곸젒 ?댁뼱(Read/cat)** ?쇱씤 ?⑥쐞濡??섎룞 ?뺤씤 ???섏젙??寃?
> - ?섏젙 ??諛섎뱶??**?꾩옱 肄붾뱶瑜?吏곸젒 ?쎄퀬** 蹂닿퀬???쇱씤 踰덊샇? ?議고븷 寃?(肄붾뱶媛 ?대룞?덉쓣 ???덉쓬).
>
> ## ?⑥튂 ?먯튃
> - **??踰덉뿉 1嫄댁뵫** ?⑥튂?쒕떎. ?⑥튂 ??利됱떆 `pytest tests/ -q` ?뚭? ?뺤씤.
> - ?뚯뒪???ㅽ뙣 ??**?대떦 ?⑥튂瑜?利됱떆 濡ㅻ갚**?섍퀬 吏꾪뻾?쒖뿉 "BLOCKED" 湲곕줉 ???ㅼ쓬 嫄댁쑝濡??대룞.
> - 湲곗〈 ?뚯뒪?멸? ?녿뒗 ?섏젙? **理쒖냼 1媛??뚯뒪?몃? 異붽?**?쒕떎.
> - ?섏젙 踰붿쐞瑜?**理쒖냼??*?쒕떎. 由ы뙥?좊쭅/?ㅽ???蹂寃?湲덉?. 踰꾧렇 ?섏젙留?
> - `ruff check` + `ruff format --check` ?듦낵 ?뺤씤.
>
> ## 吏꾪뻾???낅뜲?댄듃 洹쒖튃 (而⑦뀓?ㅽ듃 而댄뙥???鍮?
> - **媛??⑥튂 ?꾨즺 ??* ?꾨옒 吏꾪뻾?쒖쓽 ?대떦 ???곹깭瑜?利됱떆 ?낅뜲?댄듃?쒕떎.
> - **5嫄대쭏??* 以묎컙 ?붿빟??吏꾪뻾???섎떒 "泥댄겕?ъ씤?? ?뱀뀡??湲곕줉?쒕떎.
> - 而⑦뀓?ㅽ듃媛 ?뺤텞/由ъ뀑?섏뼱??**??臾몄꽌瑜??ㅼ떆 ?쎌쑝硫?* ?꾩옱 ?꾩튂瑜??????덈떎.
> - ?곹깭媛? `?湲? ??`吏꾪뻾以? ??`?꾨즺` / `BLOCKED` / `SKIP`

---

> ?⑥튂?? 2026-02-23
> ??? 湲?꾨퉬 HEAD (TF-5 媛먯궗 ?꾨즺, 媛먮━ 32/32 CONFIRMED)
> ?뚯뒪??湲곗??? **2,324 passed**, ruff 0 violations
> 媛먯궗 蹂닿퀬?? `docs/2026-02-22/opus_tf5_consolidated_debug_report.md`

---

## 吏꾪뻾??

| # | ID | ?꾪뿕??| ?뚯씪 | ?붿빟 | ?곹깭 | ?뚯뒪??|
|---|-----|--------|------|------|------|--------|
| 1 | B-1 | HIGH | stage4_post_processor.py | Manager ??꾩븘?????뺤궛 ?좎떎 | ?꾨즺 | `pytest tests/ -q` (2340 passed) |
| 2 | F-1 | HIGH | project_service.py | Stage2 reset _safe_commit 臾댁떆 | ?꾨즺 | `pytest tests/ -q` (2341 passed) |
| 3 | F-2 | HIGH | project_service.py | rollback 而ㅻ컠 ?ㅽ뙣 ???뚯씪/踰≫꽣 ??젣 | ?꾨즺 | `pytest tests/ -q` (2342 passed) |
| 4 | K-2 | HIGH | stage4_interview_round.py | _cv_context??blueprint ?꾨씫 | ?꾨즺 | `pytest tests/ -q` (2343 passed) |
| 5 | K-1 | HIGH | blocking_validator_scene_checks.py | min_required=4 ?섎뱶肄붾뵫 | ?꾨즺 | `pytest tests/ -q` (2344 passed) |
| 6 | C-1 | HIGH | project_service.py | rollback??npc_history ??젣 ?꾨씫 | ?꾨즺 | `pytest tests/ -q` (2345 passed) |
| 7 | J-1 | HIGH | four_phase_arc_generator.py | pre_collected_items str(dict) 吏곷젹??| ?꾨즺 | `pytest tests/ -q` (2346 passed) |
| 8 | J-2 | HIGH | four_phase_arc_generator.py | pre_collected_grants str(dict) 吏곷젹??| ?꾨즺 | `pytest tests/ -q` (2347 passed) |
| 9 | L-1 | HIGH | stage4_post_processor.py | record_validation(stage=4) 誘명샇異?| ?꾨즺 | `pytest tests/ -q` (2348 passed) |
| 10 | L-2 | HIGH | stage2_optimizer.py | dict ?꾩씠??name/item ?뺢퇋??鍮꾨?移?| ?꾨즺 | `pytest tests/ -q` (2349 passed) |
| 11 | D-1 | HIGH | arc_ensemble.py | 罹먯떆+?꾨＼?꾪듃 ?댁쨷 ?꾩넚 | ?꾨즺 | `pytest tests/ -q` (2350 passed) |
| 12 | D-2 | HIGH | blueprint_ensemble.py | 罹먯떆+?꾨＼?꾪듃 ?댁쨷 ?꾩넚 | ?꾨즺 | `pytest tests/ -q` (2351 passed) |
| 13 | G-1 | HIGH | stage3_orchestrator.py | DI 肄쒕갚 None ?몄텧 TypeError | ?꾨즺 | `pytest tests/ -q` (2352 passed) |
| 14 | G-2 | HIGH | reverse_expander.py | 諛곗튂 蹂묐젹 prev_state 怨듭쑀 | ?꾨즺 | `pytest tests/ -q` (2354 passed) |
| 15 | H-1 | HIGH | base_guard.py | ?뺣떦???꾩뿭 留ㅼ묶 | ?꾨즺 | `pytest tests/ -q` (2356 passed) |
| 16 | I-1 | HIGH | continuity_arc.py | current_inventory ?좏븘??以묐났 ?고쉶 | ?꾨즺 | `pytest tests/ -q` (2357 passed) |
| 17 | E-1 | HIGH | director_continuity.py | ?⑥씪 MAJOR媛 PASS 泥섎━ | ?꾨즺 | `pytest tests/ -q` (2358 passed) |
| 18 | A-1 | HIGH | stage2_preflight.py | ThreadPool timeout ?湲?釉붾줉 | ?꾨즺 | `pytest tests/ -q` (2359 passed) |
| 19 | B-2 | MEDIUM | stage4_context_builder.py / stage4_interview_round.py | Tier2 ?뚯꽌 ?щ㎎ 遺덉씪移?| ?꾨즺 | `pytest tests/ -q` (2360 passed) |
| 20 | B-3 | MEDIUM | context_advisor.py / stage4_context_builder.py | scene_breakdown dict/list 遺덉씪移?| ?꾨즺 | `pytest tests/ -q` (2362 passed) |
| 21 | F-3 | MEDIUM | main_a.py | rollback 痍⑥냼 ??state_tracker=None | ?꾨즺 | `pytest tests/ -q` (2364 passed) |
| 22 | K-3 | MEDIUM | consistency_validator.py | 3?λⅤ留?Guard 濡쒕뱶 | ?꾨즺 | `pytest tests/ -q` (2365 passed) |
| 23 | C-2 | MEDIUM | db_manager.py / continuity_validator.py | npc_history ?뺣젹 vs ?몃뜳??遺덉씪移?| ?꾨즺 | `pytest tests/ -q` (2366 passed) |
| 24 | L-3 | MEDIUM | stage4_orchestrator.py | director_max_attempts ?섎뱶肄붾뵫 | ?꾨즺 | `pytest tests/ -q` (2367 passed) |
| 25 | G-3 | MEDIUM | stage0/__init__.py | _genre ?꾨씫 ???ъ옄臾?媛뺤젣 | ?꾨즺 | `pytest tests/ -q` (2368 passed) |
| 26 | A-2 | MEDIUM | stage2_validation_pipeline.py | structured feedback merged into retry feedback | 완료 | `pytest tests/ -q` (2369 passed) |
| 27 | D-3 | MEDIUM | context_advisor.py | stage flag default switched to fail-close | 완료 | `pytest tests/ -q` (2370 passed) |
| 28 | E-2 | MEDIUM | director_ensemble.py | keep selected blueprint even on REJECT | 완료 | `pytest tests/ -q` (2370 passed) |
| 29 | H-2 | MEDIUM | base_guard.py | NPC resolution matching limited to local window | 완료 | `pytest tests/ -q` (2374 passed) |
| 30 | H-3 | MEDIUM | base_guard.py | villain generic response requires villain-local proximity | 완료 | `pytest tests/ -q` (2374 passed) |
| 31 | I-2 | MEDIUM | continuity_blueprint.py | grant/possession check now uses _is_same_item matching | 완료 | `pytest tests/ -q` (2375 passed) |
| 32 | I-3 | MEDIUM | continuity_manuscript.py | tighten partial substring item matching by ratio/length | 완료 | `pytest tests/ -q` (2377 passed) |

---

## 泥댄겕?ъ씤??(5嫄??⑥쐞濡?湲곕줉)

### CP-1 (1~5踰??꾨즺 ??
- ?꾨즺: #1 B-1, #2 F-1, #3 F-2, #4 K-2, #5 K-1
- BLOCKED: ?놁쓬
- ?뚯뒪?? passed=2344, failed=0
- ?쒓컖: 2026-02-23 02:34:59

### CP-2 (6~10踰??꾨즺 ??
- ?꾨즺: #6 C-1, #7 J-1, #8 J-2, #9 L-1, #10 L-2
- BLOCKED: ?놁쓬
- ?뚯뒪?? passed=2349, failed=0
- ?쒓컖: 2026-02-23 02:49:11

### CP-3 (11~15踰??꾨즺 ??
- ?꾨즺: #11 D-1, #12 D-2, #13 G-1, #14 G-2, #15 H-1
- BLOCKED: ?놁쓬
- ?뚯뒪?? passed=2356, failed=0
- ?쒓컖: 2026-02-23 03:05:19

### CP-4 (16~20踰??꾨즺 ??
- ?꾨즺: #16 I-1, #17 E-1, #18 A-1, #19 B-2, #20 B-3
- BLOCKED: ?놁쓬
- ?뚯뒪?? passed=2362, failed=0
- ?쒓컖: 2026-02-23 03:22:26

### CP-5 (21~25踰??꾨즺 ??
- ?꾨즺: #21 F-3, #22 K-3, #23 C-2, #24 L-3, #25 G-3
- BLOCKED: ?놁쓬
- ?뚯뒪?? passed=2368, failed=0
- ?쒓컖: 2026-02-23 03:42:00

### CP-6 (26~30踰??꾨즺 ??
- 완료: #26 A-2, #27 D-3, #28 E-2, #29 H-2, #30 H-3
- BLOCKED: 없음
- 테스트: passed=2374, failed=0
- 시각: 2026-02-23 03:58:00

### CP-7 (31~32踰??꾨즺 ????理쒖쥌)
- 완료: #31 I-2, #32 I-3
- BLOCKED: 없음
- 최종 테스트: passed=2377, failed=0
- ruff: violations=0
- 시각: 2026-02-23 04:09:30

---

## 而⑦뀓?ㅽ듃 而댄뙥??蹂듦뎄 ?덉감

> **而⑦뀓?ㅽ듃媛 ?뺤텞/由ъ뀑??寃쎌슦**:
> 1. ??臾몄꽌(`docs/2026-02-23/opus_tf5_patch_order.md`)瑜??쎈뒗??
> 2. 吏꾪뻾?쒖뿉??`?湲? ?곹깭??泥?踰덉㎏ ??ぉ??李얜뒗??
> 3. ?대떦 ??ぉ???곸꽭 ?⑥튂 吏???꾨옒)瑜??쎄퀬 ?ㅽ뻾?쒕떎.
> 4. ?꾨즺 ??吏꾪뻾?쒖? 泥댄겕?ъ씤?몃? ?낅뜲?댄듃?쒕떎.
> 5. ?ㅼ쓬 `?湲? ??ぉ?쇰줈 ?대룞?쒕떎.

---

## ?곸꽭 ?⑥튂 吏??

---

### #1 ??B-1: Manager ??꾩븘?????뺤궛 ?좎떎 (HIGH)

**?뚯씪**: `modules/core/stage4_post_processor.py`
**李몄“ ?쇱씤**: L165, L299, L316

**?꾩옱 肄붾뱶** (L316 遺洹?:
```python
except Exception as mgr_err:
    self.ctx.ui.log(f"      ?좑툘 Manager ?몄텧 ?ㅽ뙣: {str(mgr_err)[:50]}")
```

**?섏젙**:
```python
except Exception as mgr_err:
    self.ctx.ui.log(f"      ?좑툘 Manager ?몄텧 ?ㅽ뙣: {str(mgr_err)[:50]}")
    logging.warning("[B-1] Manager ?뺤궛 ?ㅽ뙣 ???숆린 ?ъ떆?? %s", mgr_err)
    try:
        raw_audit = self.ctx.agents["manager"].update_state_and_lore_v20(
            manuscript=manuscript,
            bible=bible,
            previous_hud=previous_hud,
        )
        if raw_audit and not raw_audit.get("parsing_error"):
            audit = raw_audit
            self.ctx.ui.log("      ??Manager ?숆린 ?ъ떆???깃났")
    except Exception as retry_err:
        logging.error("[B-1] Manager ?숆린 ?ъ떆?꾨룄 ?ㅽ뙣: %s", retry_err)
```

**寃利?*: `pytest tests/ -q` + L319 ?댄븯 `audit` ?ъ슜 寃쎈줈?먯꽌 鍮?dict 諛⑹? ?뺤씤.

**?뚯뒪??異붽?**: `test_stage4_post_processor.py` ??Manager timeout ???숆린 ?ъ떆???몄텧 ?뺤씤.

---

### #2 ??F-1: Stage2 reset _safe_commit 臾댁떆 (HIGH)

**?뚯씪**: `modules/core/services/project_service.py`
**李몄“ ?쇱씤**: L48-51

**?꾩옱 肄붾뱶**:
```python
project.db.cursor.execute("DELETE FROM anchors WHERE key = 'arcs'")
self._safe_commit()
project.arcs = []
self._ui.log("??Stage 2 ?곗씠?곌? ??젣?섏뿀?듬땲??..")
```

**?섏젙**:
```python
project.db.cursor.execute("DELETE FROM anchors WHERE key = 'arcs'")
if not self._safe_commit():
    self._ui.log("??DB 而ㅻ컠 ?ㅽ뙣 ??Stage 2 由ъ뀑 以묐떒")
    return
project.arcs = []
self._ui.log("??Stage 2 ?곗씠?곌? ??젣?섏뿀?듬땲??..")
```

**?뚯뒪??異붽?**: `test_project_service.py` ??`_safe_commit` False ??arcs ?좎? ?뺤씤.

---

### #3 ??F-2: rollback 而ㅻ컠 ?ㅽ뙣 ???뚯씪/踰≫꽣 ??젣 (HIGH)

**?뚯씪**: `modules/core/services/project_service.py`
**李몄“ ?쇱씤**: L185

**?꾩옱 肄붾뱶** (L185 遺洹?:
```python
self._safe_commit()

# 5. 臾쇰━ ?뚯씪 ??젣
for f in project.paths.drafts.glob("*.txt"):
```

**?섏젙**:
```python
if not self._safe_commit():
    self._ui.log("??DB 而ㅻ컠 ?ㅽ뙣 ??濡ㅻ갚 以묐떒 (?뚯씪/踰≫꽣 蹂댁〈)")
    return

# 5. 臾쇰━ ?뚯씪 ??젣
for f in project.paths.drafts.glob("*.txt"):
```

**?뚯뒪??異붽?**: `test_project_service.py` ??而ㅻ컠 ?ㅽ뙣 ???뚯씪 ??젣 誘몄떎???뺤씤.

---

### #4 ??K-2: _cv_context??blueprint ?꾨씫 (HIGH)

**?뚯씪**: `modules/core/stage4_interview_round.py`
**李몄“ ?쇱씤**: L261-269

**?꾩옱 肄붾뱶**:
```python
_cv_context = {
    "mode": "MANUSCRIPT",
    "martial_hud": {},
    ...
    "ep_num": next_ep,
}
```

**?섏젙**: `_cv_context` dict??blueprint ??異붽?:
```python
_cv_context = {
    "mode": "MANUSCRIPT",
    "martial_hud": {},
    ...
    "ep_num": next_ep,
    "blueprint": blueprint if isinstance(blueprint, dict) else {},
    "blueprint_text": str(blueprint or "")[:3000],
}
```

**二쇱쓽**: `blueprint` 蹂?섍? ?ㅼ퐫?꾩뿉 ?덈뒗吏 ?뺤씤. ?놁쑝硫?`self.ctx.blueprint` ?먮뒗 硫붿꽌???뚮씪誘명꽣?먯꽌 媛?몄삱 寃?

**?뚯뒪??異붽?**: `test_stage4_interview_round.py` ??`_cv_context`??blueprint ??議댁옱 ?뺤씤.

---

### #5 ??K-1: min_required=4 ?섎뱶肄붾뵫 (HIGH)

**?뚯씪**: `modules/validation/blocking_validator_scene_checks.py`
**李몄“ ?쇱씤**: L55

**?꾩옱 肄붾뱶**:
```python
scene_count = len(scene_breakdown)
min_required = 4
```

**?섏젙**:
```python
scene_count = len(scene_breakdown)
min_required = min(4, scene_count)
```

**?뚯뒪??異붽?**: `test_blocking_validator.py` ??scene_breakdown 2媛쒖씪 ??2媛?諛섏쁺?쇰줈 PASS ?뺤씤.

---

### #6 ??C-1: rollback??npc_history ??젣 ?꾨씫 (HIGH)

**?뚯씪**: `modules/core/services/project_service.py`
**李몄“ ?쇱씤**: L153-158 (DELETE 臾??섏뿴 ?곸뿭)

**?섏젙**: 湲곗〈 DELETE 臾?釉붾줉??異붽?:
```python
project.db.cursor.execute("DELETE FROM npc_history WHERE episode_no >= ?", (target_ep,))
```

**?뚯뒪??異붽?**: `test_project_service.py` ??rollback ??npc_history??target_ep ?댁긽 ?덉퐫???놁쓬 ?뺤씤.

---

### #7 ??J-1: pre_collected_items str(dict) 吏곷젹??(HIGH)

**?뚯씪**: `modules/domain/agents/four_phase_arc_generator.py`
**李몄“ ?쇱씤**: L205

**?꾩옱 肄붾뱶**:
```python
_pre_items.update((str(i) if isinstance(i, dict) else i).strip() for i in _acq if i)
```

**?섏젙**:
```python
_pre_items.update(
    (i.get("name", i.get("item", "")) if isinstance(i, dict) else str(i)).strip()
    for i in _acq if i
)
```

**?뚯뒪??異붽?**: `test_four_phase_arc_generator.py` ??dict ?꾩씠??`{"name":"泥좉?"}` ?뺢퇋???뺤씤.

---

### #8 ??J-2: pre_collected_grants str(dict) 吏곷젹??(HIGH)

**?뚯씪**: `modules/domain/agents/four_phase_arc_generator.py`
**李몄“ ?쇱씤**: L208

**?꾩옱 肄붾뱶**:
```python
_pre_grants.update((str(g) if isinstance(g, dict) else g).strip() for g in _grt if g)
```

**?섏젙**:
```python
_pre_grants.update(
    (g.get("name", g.get("item", "")) if isinstance(g, dict) else str(g)).strip()
    for g in _grt if g
)
```

**?뚯뒪??異붽?**: `test_four_phase_arc_generator.py` ??dict ?섏뿬臾??뺢퇋???뺤씤.

---

### #9 ??L-1: record_validation(stage=4) 誘명샇異?(HIGH)

**?뚯씪**: `modules/core/stage4_post_processor.py`
**李몄“ ?쇱씤**: L558 洹쇱쿂 (detect_score_regression ?몄텧 ?꾩튂)

**?섏젙**: PASS/REJECT ?뺤젙 吏?먯뿉??`record_validation` ?몄텧 異붽?. ?뚯씪??吏곸젒 ?쎌뼱 PASS 泥섎━ 釉붾줉怨?REJECT 泥섎━ 釉붾줉??李얘퀬 媛곴컖??異붽?:
```python
# PASS ?뺤젙 吏??
self.ctx.quality_dashboard.record_validation(
    ep_num=next_ep,
    result={"verdict": "PASS", "score": final_score},
    stage=4,
)
```
```python
# REJECT ?뺤젙 吏??
self.ctx.quality_dashboard.record_validation(
    ep_num=next_ep,
    result={"verdict": "REJECT", "score": final_score},
    stage=4,
)
```

**?뚯뒪??異붽?**: `test_stage4_post_processor.py` ??PASS ??quality_dashboard??stage=4 湲곕줉 ?뺤씤.

---

### #10 ??L-2: dict ?꾩씠??name/item ?뺢퇋??鍮꾨?移?(HIGH)

**?뚯씪**: `modules/core/stage2_optimizer.py`
**李몄“ ?쇱씤**: L233

**?꾩옱 肄붾뱶**:
```python
current_items = [x.get("name", str(x)) if isinstance(x, dict) else str(x) for x in current_items]
```

**?섏젙**:
```python
current_items = [
    x.get("name", x.get("item", str(x))) if isinstance(x, dict) else str(x)
    for x in current_items
]
```

**?뚯뒪??異붽?**: `test_stage2_optimizer.py` ??`{"item":"泥좉?"}` ?뺢퇋???뺤씤.

---

### #11 ??D-1: ArcEnsemble 罹먯떆+?꾨＼?꾪듃 ?댁쨷 ?꾩넚 (HIGH)

**?뚯씪**: `modules/domain/agents/arc_ensemble.py`
**李몄“ ?쇱씤**: L128, L373, L382, L401

**?섏젙 諛⑺뼢**: 罹먯떆 寃쎈줈?먯꽌 `shared_context`瑜?strategy prompt?먯꽌 ?쒖쇅?섍굅?? 罹먯떆 誘몄궗???쒖뿉留??ы븿. ?뚯씪??吏곸젒 ?쎌뼱 罹먯떆 遺꾧린瑜??뺤씤?섍퀬 ?댁쨷 ?꾩넚 寃쎈줈瑜??쒓굅.

**二쇱쓽**: `base_agent.py`??`_ask_with_cached_context` ?몄텧 援ъ“瑜?癒쇱? ?뺤씤??寃?

---

### #12 ??D-2: BlueprintEnsemble 罹먯떆+?꾨＼?꾪듃 ?댁쨷 ?꾩넚 (HIGH)

**?뚯씪**: `modules/domain/agents/blueprint_ensemble.py`
**李몄“ ?쇱씤**: L171, L361, L367, L381

**?섏젙 諛⑺뼢**: D-1怨??숈씪 ?⑦꽩. 罹먯떆 寃쎈줈?먯꽌 以묐났 ?쒓굅.

---

### #13 ??G-1: Stage3 DI 肄쒕갚 None ?몄텧 TypeError (HIGH)

**?뚯씪**: `modules/core/stage3_orchestrator.py`
**李몄“ ?쇱씤**: L102, L120, L157, L281, L359

**?섏젙**: 媛?肄쒕갚 ?몄텧遺??callable() 媛??異붽?:
```python
# L102
existing_ms_max_ep = ctx.get_max_episode_from_manuscripts() if callable(ctx.get_max_episode_from_manuscripts) else 0

# L120
target_ep = ctx.get_int_input(...) if callable(ctx.get_int_input) else total_planned_ep

# L157
if callable(ctx.write_audit_summary):
    ctx.write_audit_summary("stage3_complete")

# L281
if callable(ctx.get_arc_context_for_episode):
    arc_idx, arc_data = ctx.get_arc_context_for_episode(working_ep)
else:
    arc_idx, arc_data = 0, {}

# L359
stage3_protag = ctx.get_protagonist_name() if callable(ctx.get_protagonist_name) else ""
```

**?뚯뒪??異붽?**: `test_stage3_orchestrator.py` ??None 肄쒕갚?쇰줈 珥덇린????TypeError 誘몃컻???뺤씤.

---

### #14 ??G-2: ReverseExpander 諛곗튂 蹂묐젹 prev_state 怨듭쑀 (HIGH)

**?뚯씪**: `modules/core/stage0/reverse_expander.py`
**李몄“ ?쇱씤**: L402, L410, L655, L660

**?섏젙 諛⑺뼢**: 諛곗튂 ???쒖감 泥섎━濡??꾪솚?섍굅?? 蹂묐젹 異붿텧 ??ep ???뺣젹 + prev_state ?щ컲???④퀎 異붽?.

媛꾨떒???섏젙:
```python
# 諛곗튂 ???쒖감 泥섎━ (prev_state ?섏〈???좎?)
for draft in batch:
    prev_state = self.episode_bibles[-1] if self.episode_bibles else {}
    result = self._extract_single_episode_bible(draft, prev_state, schema)
    if result:
        self.episode_bibles.append(result)
```

**二쇱쓽**: ??怨?L402, L655) 紐⑤몢 ?섏젙. 蹂묐젹?믪닚李??꾪솚?대?濡??띾룄 ?몃젅?대뱶?ㅽ봽 ?덉쓬.

---

### #15 ??H-1: ?뺣떦???꾩뿭 留ㅼ묶 (HIGH)

**?뚯씪**: `modules/core/genre_guards/base_guard.py`
**李몄“ ?쇱씤**: L348-353

**?꾩옱 肄붾뱶**:
```python
has_justification = any(re.search(jp, manuscript) for jp in justifications)
```

**?섏젙**: 留ㅼ묶 ?꾩튂 湲곗? 짹120???덈룄?곕줈 ?쒗븳:
```python
_match_pos = matches[0].start() if hasattr(matches[0], 'start') else manuscript.find(matches[0])
_window = manuscript[max(0, _match_pos - 120):_match_pos + 120]
has_justification = any(re.search(jp, _window) for jp in justifications)
```

**二쇱쓽**: `matches`媛 `re.findall` 寃곌낵(臾몄옄??由ъ뒪???몄? `re.finditer` 寃곌낵?몄? ?뺤씤?섍퀬 ?곸젅??議곗젙. `re.findall`?대㈃ `manuscript.find(match_str)` ?ъ슜.

---

### #16 ??I-1: current_inventory ?좏븘??以묐났 ?고쉶 (HIGH)

**?뚯씪**: `modules/domain/agents/continuity_arc.py`
**李몄“ ?쇱씤**: L712

**?꾩옱 肄붾뱶**:
```python
all_existing_items = prev_inventory_items + current_inventory_items + list(usage_items)
```

**?섏젙**: `current_inventory_items` ?쒖쇅:
```python
all_existing_items = prev_inventory_items + list(usage_items)
```

**?뚯뒪??異붽?**: `test_continuity_arc.py` ??current_inventory???덈뒗 ?꾩씠?쒖씠 以묐났 寃?щ? ?듦낵?섎뒗吏 ?뺤씤.

---

### #17 ??E-1: ?⑥씪 MAJOR媛 PASS 泥섎━ (HIGH)

**?뚯씪**: `modules/domain/agents/director_continuity.py`
**李몄“ ?쇱씤**: L629, L643

**?꾩옱 肄붾뱶**:
```python
if major_count >= 2:
```

**?섏젙**:
```python
if major_count >= 1:
```

**?뚯뒪??異붽?**: `test_director_continuity.py` ???⑥씪 MAJOR issue ??WARNING 諛섑솚 ?뺤씤.

---

### #18 ??A-1: ThreadPool timeout ?湲?釉붾줉 (HIGH)

**?뚯씪**: `modules/core/stage2_preflight.py`
**李몄“ ?쇱씤**: L273

**?섏젙 諛⑺뼢**: `with ThreadPoolExecutor(...)` ???紐낆떆???앹꽦/醫낅즺:
```python
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
try:
    future = executor.submit(...)
    result = future.result(timeout=timeout_sec)
except (TimeoutError, concurrent.futures.TimeoutError):
    executor.shutdown(wait=False, cancel_futures=True)
    raise
finally:
    executor.shutdown(wait=False)
```

---

### #19 ??B-2: Tier2 ?뚯꽌 ?щ㎎ 遺덉씪移?(MEDIUM)

**?뚯씪**: `modules/core/stage4_interview_round.py`
**李몄“ ?쇱씤**: L908

**?꾩옱 肄붾뱶**:
```python
_m = _re_hist.match(r"^\[[^\d]*(\d+)[^\]]*\]\n", _block)
```

**?섏젙**: `\n` ??`\s*` (怨듬갚/以꾨컮轅?紐⑤몢 ?덉슜):
```python
_m = re.match(r"^\[[^\d]*(\d+)[^\]]*\]\s*", _block)
```

---

### #20 ??B-3: scene_breakdown dict/list 遺덉씪移?(MEDIUM)

**?뚯씪 2怨?*:

**context_advisor.py** L586-587:
```python
# ?꾩옱
if not isinstance(scene_breakdown, list) or not scene_breakdown:
    return ""

# ?섏젙
if isinstance(scene_breakdown, dict):
    scene_breakdown = list(scene_breakdown.values())
if not isinstance(scene_breakdown, list) or not scene_breakdown:
    return ""
```

**stage4_context_builder.py** L91-92:
```python
# ?꾩옱
if isinstance(scene_blocks, list):

# ?섏젙
if isinstance(scene_blocks, dict):
    scene_blocks = list(scene_blocks.values())
if isinstance(scene_blocks, list):
```

---

### #21 ??F-3: rollback 痍⑥냼 ??state_tracker=None (MEDIUM)

**?뚯씪**: `modules/core/services/project_service.py` + `main_a.py`

**?섏젙 1** ??project_service.py??`rollback_episode()`媛 bool 諛섑솚:
```python
def rollback_episode(self) -> bool:
    ...
    if confirm != "y":
        self._ui.log("??痍⑥냼?섏뿀?듬땲??")
        return False
    ...
    return True  # ?깃났 ??
```

**?섏젙 2** ??main_a.py L2781:
```python
def _rollback_episode(self):
    success = self._project_service.rollback_episode()
    if success:
        self.state_tracker = None
        self._prompt_builder.invalidate_timeline_cache()
        ...
```

---

### #22 ??K-3: ConsistencyValidator 3?λⅤ留?Guard 濡쒕뱶 (MEDIUM)

**?뚯씪**: `modules/validation/consistency_validator.py`
**李몄“ ?쇱씤**: L51-68

**?섏젙**: if/elif 泥댁씤 ??`create_genre_guard()` ?⑺넗由??ъ슜:
```python
from modules.core.genre_guards import create_genre_guard

def _load_guard_for_genre(self, genre: str):
    try:
        guard = create_genre_guard(genre)
        if guard is None:
            logging.warning(f"[WARNING] 誘몄????λⅤ '{genre}' - 湲곕낯 寃利앸쭔 ?섑뻾")
        return guard
    except Exception as e:
        logging.warning(f"[WARNING] Guard 濡쒕뱶 ?ㅽ뙣 '{genre}': {e}")
        return None
```

---

### #23 ??C-2: npc_history ?뺣젹 vs ?몃뜳??遺덉씪移?(MEDIUM)

**?뚯씪**: `modules/core/db_manager.py` ?먮뒗 `modules/validation/continuity_validator.py`

**?섏젙 諛⑺뼢**: DB 荑쇰━ ORDER BY瑜?ASC濡??듭씪?섍굅?? validator?먯꽌 ?뺣젹 ???몃뜳???묎렐.
```python
personality_changes = sorted(personality_changes, key=lambda h: h.get("id", 0))
prev_p = personality_changes[-2]
curr_p = personality_changes[-1]
```

---

### #24 ??L-3: director_max_attempts ?섎뱶肄붾뵫 (MEDIUM)

**?뚯씪**: `modules/core/stage4_orchestrator.py`
**李몄“ ?쇱씤**: L539

**?꾩옱 肄붾뱶**:
```python
for interview_round in range(5):
```

**?섏젙**:
```python
_max_rounds = int(self._threshold("retry.director_max_attempts", 5))
for interview_round in range(_max_rounds):
```

**二쇱쓽**: `self._threshold` 硫붿꽌??議댁옱 ?щ? ?뺤씤. ?놁쑝硫?`threshold_helper` import.

---

### #25 ??G-3: _genre ?꾨씫 ???ъ옄臾?媛뺤젣 (MEDIUM)

**?뚯씪**: `modules/core/stage0/__init__.py`
**李몄“ ?쇱씤**: L323

**?꾩옱 肄붾뱶**:
```python
self.genre = master.get("_genre", GenreTypes.INVESTMENT)
```

**?섏젙**:
```python
self.genre = master.get("_genre", "")
if not self.genre:
    self.genre = self._select_genre() if hasattr(self, '_select_genre') else ""
```

---

### #26 ??A-2: structured feedback 誘몃퀝??(MEDIUM)

**?뚯씪**: `modules/core/stage2_validation_pipeline.py`
**李몄“ ?쇱씤**: L505, L523

**?섏젙**: `generate_structured_arc_feedback()` 諛섑솚媛믪쓣 retry ?쇰뱶諛깆뿉 蹂묓빀. ?뚯씪???쎌뼱 ?뺥솗??蹂묓빀 吏???뺤씤 ???섏젙.

---

### #27 ??D-3: stage flag fail-open (MEDIUM)

**?뚯씪**: `modules/core/context_advisor.py`
**李몄“ ?쇱씤**: L277

**?꾩옱 肄붾뱶**:
```python
return bool(_threshold(key, True))
```

**?섏젙**:
```python
return bool(_threshold(key, False))
```

---

### #28 ??E-2: REJECT ???좏깮 ?꾨왂 ?좎떎 (MEDIUM)

**?뚯씪**: `modules/domain/agents/director_ensemble.py`
**李몄“ ?쇱씤**: L172

**?섏젙 諛⑺뼢**: REJECT ?쒖뿉??`selected_blueprint` 諛섑솚. ?뚯씪???쎌뼱 諛섑솚 援ъ“ ?뺤씤 ???섏젙.

---

### #29 ??H-2: NPC蹂??댁냼 ?꾩뿭 留ㅼ묶 (MEDIUM)

**?뚯씪**: `modules/core/genre_guards/base_guard.py`
**李몄“ ?쇱씤**: L646

**?꾩옱 肄붾뱶**:
```python
has_resolution_in_manuscript = any(re.search(rp, manuscript) for rp in resolution_patterns)
```

**?섏젙**: NPC紐??곌퀎 ?⑦꽩?쇰줈 ?쒗븳:
```python
_npc_esc = re.escape(npc_name)
has_resolution_in_manuscript = any(
    re.search(f"(?:{_npc_esc}.{{0,60}}{rp}|{rp}.{{0,60}}{_npc_esc})", manuscript)
    for rp in resolution_patterns
)
```

---

### #30 ??H-3: 鍮뚮윴 諛섏쓳 ?쇰컲 ?ㅼ썙???대갚 (MEDIUM)

**?뚯씪**: `modules/core/genre_guards/base_guard.py`
**李몄“ ?쇱씤**: L809

**?꾩옱 肄붾뱶**:
```python
if not has_response:
    has_response = any(re.search(rp, manuscript) for rp in response_patterns)
```

**?섏젙**: 鍮뚮윴紐?洹쇱젒 議곌굔 媛뺤젣:
```python
if not has_response:
    _v_esc = re.escape(villain_name)
    has_response = any(
        re.search(f"(?:{_v_esc}.{{0,80}}{rp}|{rp}.{{0,80}}{_v_esc})", manuscript)
        for rp in response_patterns
    )
```

---

### #31 ??I-2: ?섏뿬臾??ㅼ썙???ㅼ씤 (MEDIUM)

**?뚯씪**: `modules/domain/agents/continuity_blueprint.py`
**李몄“ ?쇱씤**: L341, L344

**?섏젙**: ?ㅼ썙???ы븿 寃????`_is_same_item()` 湲곕컲 鍮꾧탳:
```python
# ?ㅼ썙??留ㅼ묶 ???
for granted_item, g_ep in granted_items.items():
    if self._ci._is_same_item(possession, granted_item):
        was_granted = True
        break
```

**二쇱쓽**: `self._ci` ?묎렐 媛???щ? ?뺤씤. ?놁쑝硫??뺢퇋???⑥닔 吏곸젒 援ы쁽.

---

### #32 ??I-3: 遺遺?臾몄옄???꾩씠??留ㅼ묶 (MEDIUM)

**?뚯씪**: `modules/domain/agents/continuity_manuscript.py`
**李몄“ ?쇱씤**: L500-501

**?꾩옱 肄붾뱶**:
```python
if item in acquired or acquired in item:
    return True
```

**?섏젙**: 湲몄씠 鍮꾩쑉 ?쒗븳 + ?묐갑??遺遺?留ㅼ묶 異뺤냼:
```python
if item == acquired:
    return True
if len(item) >= 2 and len(acquired) >= 2:
    shorter, longer = (item, acquired) if len(item) <= len(acquired) else (acquired, item)
    if shorter in longer and len(shorter) / len(longer) >= 0.5:
        return True
```

---

## 理쒖쥌 寃利?

```bash
# ?꾩껜 ?뚭?
pytest tests/ -q

# Ruff
python -m ruff check modules/ tests/ main_a.py
python -m ruff format --check modules/ tests/ main_a.py

# SC 愿???뚯뒪??
pytest tests/test_context_advisor.py tests/test_npc_aware_retrieval.py tests/test_stage2_preflight.py tests/test_stage4_interview_round.py -q
```

---

## 而ㅻ컠 ?꾨왂

- **5嫄??⑥쐞濡?而ㅻ컠** (泥댄겕?ъ씤?몄? ?숆린??
- 而ㅻ컠 硫붿떆吏: `fix(tf5): patch #{?쒖옉}~#{?? ??{?붿빟}`
- 理쒖쥌 而ㅻ컠: `fix(tf5): 32嫄??꾨웾 ?⑥튂 ?꾨즺 + ?뚭? ?뚯뒪???듦낵`

---

*Generated by Claude Opus 4.6 ??TF-5 媛먮━ ?꾨즺 ???⑥튂 ?ㅻ뜑*
*32嫄??꾨웾 CONFIRMED (FALSE POSITIVE 0嫄?*
