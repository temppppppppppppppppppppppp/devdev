# CX modules audit report

## Summary
- Files scanned: 116
- High risk: 3
- Medium risk: 11
- Low risk: 102
- Key findings:
  - 100+ line try block: modules/core/world_state.py (max 133)
  - 200+ line function: modules/domain/agents/continuity_arc.py (max 224)
  - 200+ line function: modules/domain/agents/four_phase_arc_generator.py (max 215)
  - 200+ line function: modules/domain/agents/three_phase_blueprint_generator.py (max 216)
  - 200+ line function: modules/domain/agents/unified_blueprint_validator.py (max 218)
  - 200+ line function: modules/validation/validation_orchestrator.py (max 338)
  - silent pass found: modules/core/adaptive_retry.py (3)
  - silent pass found: modules/core/genre_guards/investment_guard.py (1)
  - silent pass found: modules/core/hud_utils.py (1)
  - silent pass found: modules/domain/agents/continuity_manuscript.py (1)
  - silent pass found: modules/domain/agents/four_phase_arc_generator.py (1)
  - silent pass found: modules/domain/agents/manuscript_validator.py (1)
  - silent pass found: modules/validation/retrospective_validator.py (3)

## File-by-file Results

### modules/core/adaptive_retry.py (855 lines)
- except Exception: 5 (silent pass 3)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: High
- findings: potential unused imports: L36:Optional | potential dead functions: L776:get_adaptive_manager
- dependencies: import collections, dataclasses, enum, logging, re, time, typing, imported by none

### modules/core/adversarial_self_play.py (399 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `response = self.client.models.generate_content(` (10 files); `self.client = api_client` (5 files); `return json.loads(json_match.group(1))` (4 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L25:Optional
- dependencies: import dataclasses, enum, json, logging, modules.core.constants, re, typing, imported by none

### modules/core/agent_intelligence.py (616 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `avg_len = sum(lengths) / len(lengths)` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L28:Optional, L28:Tuple
- dependencies: import dataclasses, enum, re, typing, imported by none

### modules/core/confidence_calibration.py (461 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `if isinstance(scene_data, dict):` (5 files); `for field in required_fields:` (5 files); `self.client = api_client` (5 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L26:Optional, L26:Tuple, L31:statistics
- dependencies: import dataclasses, enum, json, re, statistics, typing, imported by none

### modules/core/context_compression.py (402 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `if isinstance(scene_data, dict):` (5 files); `blueprint: Dict[str, Any],` (5 files); `if isinstance(items, list):` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L25:Optional, L25:Tuple
- dependencies: import dataclasses, json, re, typing, imported by none

### modules/core/cross_agent_verifier.py (510 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `response = self.client.models.generate_content(` (10 files); `scene_breakdown = blueprint.get('scene_breakdown', {})` (6 files); `if isinstance(scene_data, dict):` (5 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L21:Optional
- dependencies: import dataclasses, enum, json, logging, modules.core.constants, re, typing, imported by none

### modules/core/diversity_sampler.py (518 lines)
- except Exception: 3 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `scene_breakdown = blueprint.get('scene_breakdown', {})` (6 files); `avg_len = sum(lengths) / len(lengths)` (3 files); `lengths = [len(s) for s in sentences]` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L13:json, L14:Counter, L15:Optional, L16:hashlib
- dependencies: import collections, hashlib, json, logging, re, typing, imported by modules/core/narrative_diversity.py

### modules/core/dynamic_prompt_weighting.py (326 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L20:Any, L20:Optional, L20:Tuple, L24:json
- dependencies: import collections, dataclasses, enum, json, typing, imported by none

### modules/core/emotion_tracker.py (325 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L8:json, L9:re
- dependencies: import collections, json, re, imported by none

### modules/core/error_helper.py (360 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L9:Any | potential dead functions: L357:get_solution
- dependencies: import dataclasses, enum, logging, typing, imported by none

### modules/core/escape_utils.py (169 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `if not isinstance(text, str):` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L8:Union, L8:Optional, L9:lru_cache | potential dead functions: L152:escape_json, L167:is_escaped
- dependencies: import functools, json, typing, imported by none

### modules/core/expert_mixture.py (331 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `scene_breakdown = blueprint.get('scene_breakdown', {})` (6 files); `if isinstance(scene_data, dict):` (5 files); `blueprint: Dict[str, Any],` (5 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L27:Optional, L30:re
- dependencies: import dataclasses, enum, re, typing, imported by none

### modules/core/finetuning_automation.py (467 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L9:os, L10:Optional | potential dead functions: L450:quick_finetuning_check
- dependencies: import datetime, json, logging, modules.core.prompt_optimizer, os, pathlib, typing, imported by none

### modules/core/foreshadow_tracker.py (471 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `for pattern in patterns:` (15 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L22:Set
- dependencies: import dataclasses, datetime, enum, json, logging, re, typing, imported by modules/domain/agents/continuity_tracker.py

### modules/core/genre_guard.py (133 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `except (ValueError, TypeError):` (7 files); `parentheses_matches = re.findall(r'\((.*?)\)', content)` (3 files); `if re.search(r'[^\u4e00-\u9fff]', inside):` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import re, imported by none

### modules/core/genre_guards/__init__.py (52 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import modules.core.genre_guards.actor_guard, modules.core.genre_guards.alt_history_guard, modules.core.genre_guards.composer_guard, modules.core.genre_guards.cooking_guard, modules.core.genre_guards.fantasy_guard, modules.core.genre_guards.hunter_guard, modules.core.genre_guards.investment_guard, modules.core.genre_guards.medical_guard, imported by none

### modules/core/genre_guards/actor_guard.py (324 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `for pattern in patterns:` (15 files); `result["has_critical"] = any(v.get("severity") == "HIGH" for v in result["violat` (10 files); `result["summary"] = "; ".join(v.get("message", "") for v in result["violations"]` (10 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L7:Tuple
- dependencies: import modules.core.genre_guards.base_guard, typing, imported by modules/core/genre_guards/__init__.py

### modules/core/genre_guards/alt_history_guard.py (354 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `for pattern in patterns:` (15 files); `result["has_critical"] = any(v.get("severity") == "HIGH" for v in result["violat` (10 files); `result["summary"] = "; ".join(v.get("message", "") for v in result["violations"]` (10 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L7:Tuple
- dependencies: import modules.core.genre_guards.base_guard, typing, imported by modules/core/genre_guards/__init__.py

### modules/core/genre_guards/base_guard.py (787 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `self.MANDATORY_CONCEPTS = [` (10 files); `self.FORBIDDEN_TERMS = [` (10 files); `except (ValueError, TypeError):` (7 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import abc, re, typing, imported by modules/core/genre_guards/actor_guard.py, modules/core/genre_guards/alt_history_guard.py, modules/core/genre_guards/composer_guard.py, modules/core/genre_guards/cooking_guard.py, modules/core/genre_guards/fantasy_guard.py, modules/core/genre_guards/hunter_guard.py, modules/core/genre_guards/investment_guard.py, modules/core/genre_guards/medical_guard.py

### modules/core/genre_guards/composer_guard.py (401 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `for pattern in patterns:` (15 files); `result["has_critical"] = any(v.get("severity") == "HIGH" for v in result["violat` (10 files); `result["summary"] = "; ".join(v.get("message", "") for v in result["violations"]` (10 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L7:Tuple
- dependencies: import modules.core.genre_guards.base_guard, typing, imported by modules/core/genre_guards/__init__.py

### modules/core/genre_guards/cooking_guard.py (384 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `for pattern in patterns:` (15 files); `result["has_critical"] = any(v.get("severity") == "HIGH" for v in result["violat` (10 files); `result["summary"] = "; ".join(v.get("message", "") for v in result["violations"]` (10 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L7:Tuple
- dependencies: import modules.core.genre_guards.base_guard, typing, imported by modules/core/genre_guards/__init__.py

### modules/core/genre_guards/fantasy_guard.py (247 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `result["has_critical"] = any(v.get("severity") == "HIGH" for v in result["violat` (10 files); `result["summary"] = "; ".join(v.get("message", "") for v in result["violations"]` (10 files); `result = super().run_deep_validation(manuscript, current_state or {})` (10 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import modules.core.genre_guards.base_guard, re, typing, imported by modules/core/genre_guards/__init__.py

### modules/core/genre_guards/hunter_guard.py (806 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `for pattern in patterns:` (15 files); `result["has_critical"] = any(v.get("severity") == "HIGH" for v in result["violat` (10 files); `result["summary"] = "; ".join(v.get("message", "") for v in result["violations"]` (10 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import modules.core.genre_guards.base_guard, re, typing, imported by modules/core/genre_guards/__init__.py, modules/validation/consistency_validator.py, modules/validation/scoring_validator.py

### modules/core/genre_guards/investment_guard.py (579 lines)
- except Exception: 1 (silent pass 1)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `for pattern in patterns:` (15 files); `result["has_critical"] = any(v.get("severity") == "HIGH" for v in result["violat` (10 files); `result["summary"] = "; ".join(v.get("message", "") for v in result["violations"]` (10 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import modules.core.genre_guards.base_guard, re, typing, imported by modules/core/genre_guards/__init__.py, modules/validation/consistency_validator.py

### modules/core/genre_guards/medical_guard.py (329 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `for pattern in patterns:` (15 files); `result["has_critical"] = any(v.get("severity") == "HIGH" for v in result["violat` (10 files); `result["summary"] = "; ".join(v.get("message", "") for v in result["violations"]` (10 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L7:Tuple
- dependencies: import modules.core.genre_guards.base_guard, typing, imported by modules/core/genre_guards/__init__.py

### modules/core/genre_guards/sports_guard.py (327 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `for pattern in patterns:` (15 files); `result["has_critical"] = any(v.get("severity") == "HIGH" for v in result["violat` (10 files); `result["summary"] = "; ".join(v.get("message", "") for v in result["violations"]` (10 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L7:Tuple
- dependencies: import modules.core.genre_guards.base_guard, typing, imported by modules/core/genre_guards/__init__.py

### modules/core/genre_guards/wuxia_guard.py (557 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `for pattern in patterns:` (15 files); `result["has_critical"] = any(v.get("severity") == "HIGH" for v in result["violat` (10 files); `result["summary"] = "; ".join(v.get("message", "") for v in result["violations"]` (10 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import modules.core.genre_guards.base_guard, re, typing, imported by modules/core/genre_guards/__init__.py, modules/validation/consistency_validator.py, modules/validation/scoring_validator.py

### modules/core/genre_stage_prompts.py (482 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L14:Any | potential dead functions: L480:get_genre_stage_prompt
- dependencies: import typing, imported by none

### modules/core/graceful_degradation.py (535 lines)
- except Exception: 2 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `response = self.client.models.generate_content(` (10 files); `content_type: str = "manuscript"` (3 files); `context: Dict[str, Any] = None` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L18:json, L21:traceback | potential dead functions: L533:create_graceful_degradation
- dependencies: import dataclasses, datetime, enum, json, logging, re, time, traceback, imported by none

### modules/core/hud_utils.py (259 lines)
- except Exception: 3 (silent pass 1)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Medium
- findings: potential unused imports: L12:Optional | potential dead functions: L237:get_hud_trend_safe
- dependencies: import typing, imported by modules/domain/agents/blueprint_ensemble.py

### modules/core/information_diffusion.py (477 lines)
- except Exception: 2 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `"violations": violations,` (8 files); `"valid": len(violations) == 0,` (3 files); `description=description,` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L8:Set, L8:Optional, L10:field
- dependencies: import dataclasses, logging, re, typing, imported by modules/domain/agents/continuity_tracker.py, modules/validation/blocking_validator.py

### modules/core/jianghu_logic.py (30 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import none, imported by none

### modules/core/justification_patterns.py (319 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential dead functions: L243:get_justification_guide, L294:get_available_patterns, L307:get_pattern_description
- dependencies: import none, imported by modules/validation/blocking_validator.py

### modules/core/karma_service.py (22 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L1:json
- dependencies: import json, imported by none

### modules/core/lore_manager.py (457 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `if isinstance(equipment, list):` (3 files); `if isinstance(equipment, str):` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L1:json, L4:lru_cache
- dependencies: import functools, json, logging, re, time, typing, imported by none

### modules/core/manuscript_enhancer.py (767 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `) -> List[Dict[str, Any]]:` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L26:logging, L27:Optional, L27:Tuple, L29:Enum | potential dead functions: L765:create_enhancer
- dependencies: import dataclasses, enum, logging, re, typing, imported by none

### modules/core/martial_manager.py (528 lines)
- except Exception: 2 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: 1 (L302: current_val=None)
- duplicated patterns (3+ files): `except (ValueError, TypeError):` (7 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import logging, math, modules.core.constants, re, imported by none

### modules/core/material_db.py (122 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import json, logging, pathlib, random, imported by none

### modules/core/model_cascading.py (232 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L7:Dict, L7:Optional | potential dead functions: L210:create_cascade_for_agent
- dependencies: import typing, imported by none

### modules/core/multi_agent_deliberation.py (439 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `response = self.client.models.generate_content(` (10 files); `self.client = api_client` (5 files); `return json.loads(json_match.group(1))` (4 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L25:Optional
- dependencies: import dataclasses, enum, json, logging, re, typing, imported by none

### modules/core/narrative_diversity.py (543 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L23:List, L23:Optional
- dependencies: import modules.core.diversity_sampler, modules.core.pattern_tracker, typing, imported by none

### modules/core/narrative_structure_analyzer.py (314 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: 1 (L166: _text=None)
- duplicated patterns (3+ files): `response = self.client.models.generate_content(` (10 files); `response_mime_type="application/json"` (4 files); `config = types.GenerateContentConfig(` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L17:Tuple, L18:genai | potential dead functions: L312:create_narrative_analyzer
- dependencies: import collections, google, google.genai, json, logging, re, typing, imported by none

### modules/core/pacing_analyzer.py (445 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `avg_len = sum(lengths) / len(lengths)` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L19:Tuple, L22:Counter
- dependencies: import collections, dataclasses, enum, re, typing, imported by none

### modules/core/power_scaling.py (519 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L18:field
- dependencies: import dataclasses, enum, typing, imported by modules/domain/agents/continuity_tracker.py

### modules/core/primitive_guard.py (285 lines)
- except Exception: 2 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `if not protagonist_config:` (3 files); `if severity == "CRITICAL":` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L14:Optional | potential dead functions: L194:get_primitive_constraint_section, L226:validate_primitive_compliance, L272:get_genre_from_context
- dependencies: import json, logging, pathlib, re, typing, imported by modules/domain/agents/arc_ensemble.py, modules/domain/agents/blueprint_ensemble.py

### modules/core/quality_amplifier.py (426 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `for pattern in patterns:` (15 files); `blueprint: Dict[str, Any],` (5 files); `if isinstance(scenes, dict):` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L19:field, L20:Optional, L20:Set, L23:json
- dependencies: import collections, copy, dataclasses, datetime, enum, json, re, typing, imported by none

### modules/core/quality_constitution.py (290 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `elif genre == 'investment':` (4 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential dead functions: L279:get_constitution_for_genre
- dependencies: import none, imported by modules/validation/validation_orchestrator.py

### modules/core/reference_anchor.py (360 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L8:json, L11:List, L11:Dict, L11:Any
- dependencies: import json, logging, modules.domain.agents.base_agent, re, typing, imported by none

### modules/core/reflexion_manager.py (227 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L7:json, L9:Dict, L9:List, L9:Any
- dependencies: import datetime, json, logging, typing, imported by modules/validation/validation_orchestrator.py

### modules/core/response_schemas.py (659 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `response = self.client.models.generate_content(` (10 files); `response_mime_type="application/json"` (4 files); `if isinstance(content, dict):` (4 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential dead functions: L433:validate_response_against_schema, L591:validate_phase0_files
- dependencies: import google.genai, logging, imported by none

### modules/core/seed_tracker.py (559 lines)
- except Exception: 2 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L23:json, L25:time, L27:Optional, L27:Tuple | potential dead functions: L557:create_seed_tracker
- dependencies: import dataclasses, datetime, enum, json, logging, time, typing, imported by none

### modules/core/self_reflection.py (360 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `response = self.client.models.generate_content(` (10 files); `self.client = api_client` (5 files); `return json.loads(json_match.group(1))` (4 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L24:Optional, L24:Callable
- dependencies: import dataclasses, enum, json, logging, re, typing, imported by none

### modules/core/semantic_cache.py (459 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `context: Dict[str, Any],` (3 files); `stats = self.get_stats()` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L29:Tuple, L30:field, L33:json, L35:re
- dependencies: import collections, dataclasses, hashlib, json, re, time, typing, imported by none

### modules/core/semantic_item_registry.py (774 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `"violations": violations,` (8 files); `if isinstance(equipment, list):` (3 files); `"valid": len(violations) == 0,` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L22:Tuple | potential dead functions: L764:get_item_registry, L772:create_item_registry
- dependencies: import dataclasses, re, typing, imported by none

### modules/core/spinners.py (270 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import rich.console, rich.live, rich.text, threading, time, imported by none

### modules/core/state_delta_tracker.py (459 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `"violations": violations,` (8 files); `arc_end = state_constraints.get("arc_end_state", {})` (3 files); `"valid": len(violations) == 0,` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L18:field, L19:Optional
- dependencies: import dataclasses, enum, typing, imported by modules/domain/agents/continuity_tracker.py

### modules/core/studio_visualizer.py (91 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L7:time, L8:Live
- dependencies: import rich, rich.console, rich.layout, rich.live, rich.panel, rich.progress, rich.table, time, imported by none

### modules/core/technique_weaver.py (42 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import none, imported by none

### modules/core/trend_booster.py (40 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import none, imported by none

### modules/core/world_state.py (393 lines)
- except Exception: 5 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: L89-L221 (133 lines); L255-L354 (100 lines)
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: High
- findings: potential unused imports: L13:Dict, L13:List, L13:Optional
- dependencies: import json, logging, typing, imported by none

### modules/core/writer_template.py (433 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `scene_breakdown = blueprint.get('scene_breakdown', {})` (6 files); `genre: ?λⅤ (wuxia, hunter, investment)` (5 files); `if isinstance(scene_data, dict):` (5 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L22:Optional, L25:json | potential dead functions: L431:create_writer_template
- dependencies: import dataclasses, enum, json, re, typing, imported by none

### modules/domain/agents/arc_corrector.py (647 lines)
- except Exception: 4 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `super().__init__(context, client, model_tier)` (14 files); `tactical = arc.get("tactical_doc", "")` (6 files); `if not isinstance(tactical, str):` (5 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L22:Any | potential dead functions: L645:create_arc_corrector
- dependencies: import copy, json, logging, modules.domain.agents.base_agent, re, typing, imported by none

### modules/domain/agents/arc_critic.py (351 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `super().__init__(context, client, model_tier)` (14 files); `tactical = arc.get("tactical_doc", "")` (6 files); `if isinstance(result, str):` (6 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L15:re, L16:Any, L16:Optional | potential dead functions: L349:create_arc_critic
- dependencies: import json, logging, modules.core.arc_summary_utils, modules.domain.agents.base_agent, re, typing, imported by none

### modules/domain/agents/arc_draft_validator.py (793 lines)
- except Exception: 2 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `for pattern in patterns:` (15 files); `tactical = arc.get("tactical_doc", "")` (6 files); `tactical = str(tactical) if tactical else ""` (5 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L23:Tuple, L23:Set | potential dead functions: L791:create_draft_validator
- dependencies: import logging, modules.core.constants, re, typing, imported by none

### modules/domain/agents/arc_ensemble.py (654 lines)
- except Exception: 5 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `super().__init__(context, client, model_tier)` (14 files); `if isinstance(result, str):` (6 files); `tactical = str(tactical) if tactical else ""` (5 files)
- TODO/FIXME/HACK: none
- risk: Medium
- findings: potential unused imports: L17:Any | potential dead functions: L652:create_ensemble_generator
- dependencies: import concurrent.futures, json, logging, modules.core.constants, modules.core.primitive_guard, modules.domain.agents.base_agent, modules.domain.agents.ensemble_prompts, re, imported by modules/domain/agents/four_phase_arc_generator.py

### modules/domain/agents/block_enricher.py (861 lines)
- except Exception: 6 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `super().__init__(context, client, model_tier)` (14 files); `if isinstance(result, str):` (6 files); `"decision": "PASS" ?먮뒗 "REJECT",` (5 files)
- TODO/FIXME/HACK: none
- risk: Medium
- findings: potential unused imports: L590:time
- dependencies: import concurrent.futures, json, modules.domain.agents.base_agent, re, time, typing, imported by none

### modules/domain/agents/blueprint_constraint_compiler.py (468 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `prev_blueprint: Optional[Dict] = None,` (4 files); `if isinstance(inventory, list):` (4 files); `stop_line = constraint_block.get("stop_line", {})` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L20:Any, L20:Tuple | potential dead functions: L466:create_blueprint_constraint_compiler
- dependencies: import json, logging, re, typing, imported by modules/domain/agents/three_phase_blueprint_generator.py

### modules/domain/agents/blueprint_ensemble.py (653 lines)
- except Exception: 5 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `super().__init__(context, client, model_tier)` (14 files); `if not isinstance(result, dict):` (7 files); `prev_blueprint: Optional[Dict] = None,` (4 files)
- TODO/FIXME/HACK: none
- risk: Medium
- findings: potential unused imports: L17:re, L18:Any | potential dead functions: L651:create_blueprint_ensemble
- dependencies: import concurrent.futures, json, logging, modules.core.hud_utils, modules.core.primitive_guard, modules.domain.agents.base_agent, modules.domain.agents.ensemble_prompts, re, imported by modules/domain/agents/three_phase_blueprint_generator.py

### modules/domain/agents/chief_writer_prompts.py (249 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential dead functions: L76:build_chief_writer_main_prompt, L191:get_fix_issues_prompt, L219:get_anti_trope_instructions
- dependencies: import none, imported by none

### modules/domain/agents/consensus_validator.py (432 lines)
- except Exception: 3 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `super().__init__(context, client, model_tier)` (14 files); `if isinstance(result, str):` (6 files); `"""[V64.P4] ?꾩엫 ??modules.core.arc_summary_utils.generate_prev_arc_summary"""` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L15:re, L16:Any | potential dead functions: L430:create_consensus_validator
- dependencies: import concurrent.futures, json, logging, modules.core.arc_summary_utils, modules.domain.agents.base_agent, re, sys, traceback, imported by none

### modules/domain/agents/constraint_compiler.py (379 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `except (ValueError, TypeError):` (7 files); `tactical = arc.get("tactical_doc", "")` (6 files); `tactical = str(tactical) if tactical else ""` (5 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L19:Any, L19:Set | potential dead functions: L377:create_constraint_compiler
- dependencies: import json, re, typing, imported by modules/domain/agents/four_phase_arc_generator.py

### modules/domain/agents/continuity_arc.py (992 lines)
- except Exception: 2 (silent pass 0)
- self.app refs: 0
- large function: inspect_arc L225-L448 (224 lines)
- large function: _arc_python_precheck L574-L775 (202 lines)
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `for pattern in patterns:` (15 files); `if not isinstance(result, dict):` (7 files); `"decision": "PASS" ?먮뒗 "REJECT",` (5 files)
- TODO/FIXME/HACK: none
- risk: Medium
- findings: potential unused imports: L13:Dict, L13:Any
- dependencies: import json, logging, re, typing, imported by modules/domain/agents/continuity_inspector.py

### modules/domain/agents/continuity_blueprint.py (466 lines)
- except Exception: 2 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `if not isinstance(result, dict):` (7 files); `"decision": "PASS" ?먮뒗 "REJECT",` (5 files); `[Output Format] JSON Only` (5 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L12:Dict, L12:Any
- dependencies: import logging, re, typing, imported by modules/domain/agents/continuity_inspector.py

### modules/domain/agents/continuity_inspector.py (521 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `super().__init__(context, client, model_tier)` (14 files); `entity_registry: dict = None) -> dict:` (4 files); `for pattern in self.acquire_patterns:` (4 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L29:Tuple
- dependencies: import logging, modules.domain.agents.base_agent, modules.domain.agents.continuity_arc, modules.domain.agents.continuity_blueprint, modules.domain.agents.continuity_manuscript, modules.domain.agents.continuity_tracker, re, typing, imported by none

### modules/domain/agents/continuity_manuscript.py (1111 lines)
- except Exception: 3 (silent pass 1)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `if not isinstance(result, dict):` (7 files); `scene_breakdown = blueprint.get('scene_breakdown', {})` (6 files); `"decision": "PASS" ?먮뒗 "REJECT",` (5 files)
- TODO/FIXME/HACK: none
- risk: Medium
- findings: potential unused imports: L13:Dict, L13:Any
- dependencies: import logging, re, typing, imported by modules/domain/agents/continuity_inspector.py

### modules/domain/agents/continuity_tracker.py (417 lines)
- except Exception: 3 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: 1 (L64: self._ci.info_diffusion=None)
- duplicated patterns (3+ files): `"violations": violations,` (8 files); `arc_no = arc.get("arc_no", 0)` (5 files); `inspector: ContinuityInspector ?몄뒪?댁뒪 (BaseAgent ?곸냽, 怨듭쑀 ?곹깭 ?묎렐??` (4 files)
- TODO/FIXME/HACK: none
- risk: Medium
- findings: potential unused imports: L10:re
- dependencies: import modules.core.foreshadow_tracker, modules.core.information_diffusion, modules.core.power_scaling, modules.core.relationship_tracker, modules.core.state_delta_tracker, re, typing, imported by modules/domain/agents/continuity_inspector.py

### modules/domain/agents/director_caching.py (181 lines)
- except Exception: 3 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: 1 (L154: self.manuscript_cache_name=None)
- duplicated patterns (3+ files): `bible_root = master_bible.get('MasterBible', master_bible)` (3 files); `master_bible = getattr(self.context, 'master_bible', {})` (3 files)
- TODO/FIXME/HACK: none
- risk: Medium
- findings: no notable extra risk
- dependencies: import google.genai, logging, modules.domain.agents.base_agent, imported by none

### modules/domain/agents/director_ensemble.py (497 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `if not isinstance(result, dict):` (7 files); `[Output Format] JSON Only` (5 files); `integrated = blueprint.get("integrated_scenario", "")` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import json, logging, modules.core.constants, modules.domain.agents.director_prompts, imported by none

### modules/domain/agents/director_grading.py (660 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `elif genre == 'investment':` (4 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import modules.core.constants, re, imported by none

### modules/domain/agents/director_prompts.py (445 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `"decision": "PASS" ?먮뒗 "REJECT",` (5 files); `[Output Format] JSON Only` (5 files); `- ??5?④퀎瑜?醫낇빀?섏뿬 PASS/REJECT 寃곗젙` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import none, imported by modules/domain/agents/director_ensemble.py

### modules/domain/agents/ensemble_prompts.py (347 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `?붴븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븮` (3 files); `?싢븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븧?먥븴` (3 files); `?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺?곣봺` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import none, imported by modules/domain/agents/arc_ensemble.py, modules/domain/agents/blueprint_ensemble.py

### modules/domain/agents/four_phase_arc_generator.py (503 lines)
- except Exception: 2 (silent pass 1)
- self.app refs: 0
- large function: generate L112-L326 (215 lines)
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `super().__init__(context, client, model_tier)` (14 files); `) -> Tuple[Optional[Dict], Dict]:` (4 files); `bible_root = master_bible.get('MasterBible', master_bible)` (3 files)
- TODO/FIXME/HACK: none
- risk: Medium
- findings: potential unused imports: L21:Any | potential dead functions: L501:create_four_phase_generator
- dependencies: import json, logging, modules.core.constants, modules.domain.agents.arc_ensemble, modules.domain.agents.base_agent, modules.domain.agents.constraint_compiler, modules.domain.agents.negative_example_injector, modules.domain.agents.preflight_checker, imported by none

### modules/domain/agents/manager.py (166 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L3:re
- dependencies: import json, logging, modules.domain.agents.base_agent, re, imported by none

### modules/domain/agents/manuscript_validator.py (1067 lines)
- except Exception: 2 (silent pass 1)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `response_mime_type="application/json"` (4 files); `if re.search(pattern, manuscript):` (4 files); `integrated = blueprint.get("integrated_scenario", "")` (3 files)
- TODO/FIXME/HACK: none
- risk: Medium
- findings: potential unused imports: L14:Optional
- dependencies: import google.genai, json, logging, modules.core.constants, re, time, typing, imported by none

### modules/domain/agents/negative_example_injector.py (276 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L13:json, L14:re, L16:Any, L16:Optional | potential dead functions: L274:create_negative_example_injector
- dependencies: import json, re, threading, typing, imported by modules/domain/agents/four_phase_arc_generator.py

### modules/domain/agents/preflight_checker.py (500 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `super().__init__(context, client, model_tier)` (14 files); `tactical = arc.get("tactical_doc", "")` (6 files); `if isinstance(result, str):` (6 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L16:Any, L16:Optional | potential dead functions: L498:create_preflight_checker
- dependencies: import json, logging, modules.domain.agents.base_agent, re, typing, imported by modules/domain/agents/four_phase_arc_generator.py

### modules/domain/agents/state_extractor.py (718 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `for pattern in patterns:` (15 files); `super().__init__(context, client, model_tier)` (14 files); `except (ValueError, TypeError):` (7 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L14:Optional, L14:Any
- dependencies: import json, logging, modules.domain.agents.base_agent, re, typing, imported by none

### modules/domain/agents/state_locked_arc_generator.py (610 lines)
- except Exception: 2 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `super().__init__(context, client, model_tier)` (14 files); `) -> Tuple[Optional[Dict], Dict]:` (4 files); `arc_end = state_constraints.get("arc_end_state", {})` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L13:json, L16:Any | potential dead functions: L608:create_state_locked_generator
- dependencies: import json, logging, modules.domain.agents.base_agent, re, typing, imported by none

### modules/domain/agents/state_tracker_financial.py (129 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `except (ValueError, TypeError):` (7 files); `arc_no = arc.get("arc_no", 0)` (5 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L9:Any
- dependencies: import typing, imported by none

### modules/domain/agents/three_phase_blueprint_generator.py (296 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: generate L54-L269 (216 lines)
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `super().__init__(context, client, model_tier)` (14 files); `prev_blueprint: Optional[Dict] = None,` (4 files); `) -> Tuple[Optional[Dict], Dict]:` (4 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L20:json, L22:Any | potential dead functions: L294:create_three_phase_blueprint_generator
- dependencies: import json, logging, modules.domain.agents.base_agent, modules.domain.agents.blueprint_constraint_compiler, modules.domain.agents.blueprint_ensemble, modules.domain.agents.unified_blueprint_validator, typing, imported by none

### modules/domain/agents/unified_arc_validator.py (542 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `super().__init__(context, client, model_tier)` (14 files); `if not isinstance(result, dict):` (7 files); `tactical = arc.get("tactical_doc", "")` (6 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L27:Any | potential dead functions: L540:create_unified_validator
- dependencies: import json, logging, modules.core.arc_summary_utils, modules.core.constants, modules.domain.agents.base_agent, re, typing, imported by modules/domain/agents/four_phase_arc_generator.py

### modules/domain/agents/unified_blueprint_validator.py (414 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: validate L47-L264 (218 lines)
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `for field in required_fields:` (5 files); `prev_blueprint: Optional[Dict] = None,` (4 files); `constraint_block: ?쒖빟 議곌굔 釉붾줉` (4 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L25:Any | potential dead functions: L412:create_unified_blueprint_validator
- dependencies: import json, logging, re, typing, imported by modules/domain/agents/three_phase_blueprint_generator.py

### modules/domain/agents/weaver.py (144 lines)
- except Exception: 2 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `super().__init__(context, client, model_tier)` (14 files); `response = self.client.models.generate_content(` (10 files); `response_mime_type="application/json"` (4 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import google.genai, json, logging, modules.domain.agents.base_agent, imported by none

### modules/domain/strategies/__init__.py (0 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import none, imported by none

### modules/domain/strategies/base_strategy.py (15 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import abc, imported by modules/domain/strategies/composer_strategy.py, modules/domain/strategies/cooking_strategy.py, modules/domain/strategies/hunter_strategy.py, modules/domain/strategies/investment_strategy.py, modules/domain/strategies/medical_strategy.py, modules/domain/strategies/sports_strategy.py, modules/domain/strategies/wuxia_strategy.py

### modules/domain/strategies/composer_strategy.py (42 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `bible_root = ctx.master_bible.get('MasterBible', ctx.master_bible)` (7 files); `1. ?λⅤ ?꾩닔 ?붿냼: {', '.join(genre_rules.get('mandatory', []))}` (7 files); `protagonist = hud.get('Protagonist', hud.get('main', {}))` (7 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import modules.domain.strategies.base_strategy, imported by none

### modules/domain/strategies/cooking_strategy.py (42 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `bible_root = ctx.master_bible.get('MasterBible', ctx.master_bible)` (7 files); `1. ?λⅤ ?꾩닔 ?붿냼: {', '.join(genre_rules.get('mandatory', []))}` (7 files); `protagonist = hud.get('Protagonist', hud.get('main', {}))` (7 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import modules.domain.strategies.base_strategy, imported by none

### modules/domain/strategies/hunter_strategy.py (39 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `bible_root = ctx.master_bible.get('MasterBible', ctx.master_bible)` (7 files); `1. ?λⅤ ?꾩닔 ?붿냼: {', '.join(genre_rules.get('mandatory', []))}` (7 files); `protagonist = hud.get('Protagonist', hud.get('main', {}))` (7 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import modules.domain.strategies.base_strategy, imported by none

### modules/domain/strategies/investment_strategy.py (40 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `bible_root = ctx.master_bible.get('MasterBible', ctx.master_bible)` (7 files); `1. ?λⅤ ?꾩닔 ?붿냼: {', '.join(genre_rules.get('mandatory', []))}` (7 files); `protagonist = hud.get('Protagonist', hud.get('main', {}))` (7 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import modules.domain.strategies.base_strategy, imported by none

### modules/domain/strategies/medical_strategy.py (42 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `bible_root = ctx.master_bible.get('MasterBible', ctx.master_bible)` (7 files); `1. ?λⅤ ?꾩닔 ?붿냼: {', '.join(genre_rules.get('mandatory', []))}` (7 files); `protagonist = hud.get('Protagonist', hud.get('main', {}))` (7 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import modules.domain.strategies.base_strategy, imported by none

### modules/domain/strategies/sports_strategy.py (42 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `bible_root = ctx.master_bible.get('MasterBible', ctx.master_bible)` (7 files); `1. ?λⅤ ?꾩닔 ?붿냼: {', '.join(genre_rules.get('mandatory', []))}` (7 files); `protagonist = hud.get('Protagonist', hud.get('main', {}))` (7 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import modules.domain.strategies.base_strategy, imported by none

### modules/domain/strategies/wuxia_strategy.py (40 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `bible_root = ctx.master_bible.get('MasterBible', ctx.master_bible)` (7 files); `1. ?λⅤ ?꾩닔 ?붿냼: {', '.join(genre_rules.get('mandatory', []))}` (7 files); `protagonist = hud.get('Protagonist', hud.get('main', {}))` (7 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import modules.domain.strategies.base_strategy, imported by none

### modules/ui/__init__.py (0 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import none, imported by none

### modules/ui/console_interface.py (59 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: no notable extra risk
- dependencies: import os, pathlib, rich, rich.console, rich.panel, rich.prompt, rich.table, imported by none

### modules/validation/__init__.py (42 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): none
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L22:ContinuityValidator, L23:BlockingValidator, L24:ConsistencyValidator, L25:ScoringValidator, L26:AdvisoryValidator
- dependencies: import modules.validation.action_scene_evaluator, modules.validation.advisory_validator, modules.validation.batch_validator, modules.validation.blocking_validator, modules.validation.catharsis_timer, modules.validation.consistency_validator, modules.validation.continuity_validator, modules.validation.scoring_validator, imported by none

### modules/validation/action_scene_evaluator.py (401 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `genre: ?λⅤ (wuxia, hunter, investment)` (5 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L7:Any, L7:Tuple
- dependencies: import re, typing, imported by modules/validation/__init__.py, modules/validation/validation_orchestrator.py

### modules/validation/advisory_validator.py (185 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `for pattern in patterns:` (15 files); `response = self.client.models.generate_content(` (10 files); `response_mime_type="application/json"` (4 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L5:Dict, L5:Any
- dependencies: import google.genai, json, logging, typing, imported by modules/validation/__init__.py, modules/validation/validation_orchestrator.py

### modules/validation/batch_validator.py (309 lines)
- except Exception: 3 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `) -> List[Dict[str, Any]]:` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential dead functions: L247:validate_manuscripts_in_batch
- dependencies: import asyncio, concurrent.futures, logging, sys, time, typing, imported by modules/validation/__init__.py

### modules/validation/blocking_validator.py (1323 lines)
- except Exception: 2 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `except (ValueError, TypeError):` (7 files); `scene_breakdown = blueprint.get('scene_breakdown', {})` (6 files); `if re.search(pattern, manuscript):` (4 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L9:Dict, L9:Any
- dependencies: import logging, modules.core.constants, modules.core.information_diffusion, modules.core.justification_patterns, modules.core.relationship_tracker, re, typing, imported by modules/validation/__init__.py, modules/validation/validation_orchestrator.py

### modules/validation/catharsis_timer.py (257 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `genre: ?λⅤ (wuxia, hunter, investment)` (5 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L7:re, L8:Any
- dependencies: import re, typing, imported by modules/validation/__init__.py, modules/validation/validation_orchestrator.py

### modules/validation/consistency_validator.py (583 lines)
- except Exception: 1 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `"violations": violations,` (8 files); `if re.search(pattern, manuscript):` (4 files); `elif genre == 'investment':` (4 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L14:Any, L14:Optional | potential dead functions: L581:create_consistency_validator
- dependencies: import logging, modules.core.genre_guards.hunter_guard, modules.core.genre_guards.investment_guard, modules.core.genre_guards.wuxia_guard, re, typing, imported by modules/validation/__init__.py, modules/validation/validation_orchestrator.py

### modules/validation/continuity_validator.py (837 lines)
- except Exception: 2 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `"violations": violations,` (8 files); `matches = re.findall(pattern, manuscript)` (4 files); `for pattern in self.acquire_patterns:` (4 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L20:Dict, L20:List, L20:Any
- dependencies: import json, logging, re, typing, imported by modules/validation/__init__.py, modules/validation/validation_orchestrator.py

### modules/validation/pre_llm_validator.py (488 lines)
- except Exception: 0 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `"violations": violations,` (8 files); `genre: ?λⅤ (wuxia, hunter, investment)` (5 files); `encyclopedia = context.get('encyclopedia', {})` (3 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L22:List
- dependencies: import collections, re, statistics, typing, imported by modules/validation/validation_orchestrator.py

### modules/validation/retrospective_validator.py (362 lines)
- except Exception: 7 (silent pass 3)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `"violations": violations,` (8 files); `matches = re.findall(pattern, manuscript)` (4 files); `if not has_justification:` (4 files)
- TODO/FIXME/HACK: none
- risk: High
- findings: potential unused imports: L7:Dict, L7:Any
- dependencies: import logging, modules.core.relationship_tracker, re, typing, imported by modules/validation/validation_orchestrator.py

### modules/validation/scoring_validator.py (988 lines)
- except Exception: 2 (silent pass 0)
- self.app refs: 0
- large function: none
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `response = self.client.models.generate_content(` (10 files); `if not isinstance(result, dict):` (7 files); `except (ValueError, TypeError):` (7 files)
- TODO/FIXME/HACK: none
- risk: Low
- findings: potential unused imports: L10:Dict, L10:Any
- dependencies: import collections, google.genai, json, logging, modules.core.genre_guards.hunter_guard, modules.core.genre_guards.wuxia_guard, re, statistics, imported by modules/validation/__init__.py, modules/validation/validation_orchestrator.py

### modules/validation/validation_orchestrator.py (1427 lines)
- except Exception: 4 (silent pass 0)
- self.app refs: 0
- large function: validate L208-L545 (338 lines)
- large function: validate_parallel_v59 L937-L1137 (201 lines)
- 100+ line try blocks: none
- state->None on error pattern: none
- duplicated patterns (3+ files): `genre: ?λⅤ (wuxia, hunter, investment)` (5 files); `return "\n".join(feedback_parts)` (3 files); `validation_context: 寃利?而⑦뀓?ㅽ듃` (3 files)
- TODO/FIXME/HACK: none
- risk: Medium
- findings: potential unused imports: L19:Any, L19:Optional, L19:Tuple
- dependencies: import asyncio, concurrent.futures, functools, logging, modules.core.quality_constitution, modules.core.reflexion_manager, modules.validation.action_scene_evaluator, modules.validation.advisory_validator, imported by modules/validation/__init__.py
