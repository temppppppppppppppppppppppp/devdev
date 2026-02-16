# Codex Order: E-1 Silent Pass 패턴 로깅 보강

> **목표**: YELLOW 등급 Silent Pass 16건에 `logging.warning()` 추가
> **동작 변경**: 없음 — 로깅만 추가, 기존 폴백 동작 100% 유지
> **범위**: 9개 파일, 16건

---

## 원칙

1. **동작 변경 금지** — `except` 블록의 기존 동작(pass, return "", None 등)을 절대 변경하지 않음
2. **1줄 추가** — 각 패턴에 `logging.warning(...)` 1줄만 추가
3. **포맷 통일** — `logging.warning(f"[SilentPass:{모듈명}] {설명}: {str(e)[:100]}")`
4. **Exception as e** — 기존 `except Exception:` → `except Exception as e:` 변경 필요 시 함께

---

## 수정 목록 (16건)

### 1. `main_a.py` L1111 — API 캐시 헬스체크

**현재:**
```python
except Exception:  # API 예외 종류가 다양하므로 Exception 유지
    return False
```

**수정:**
```python
except Exception as e:  # API 예외 종류가 다양하므로 Exception 유지
    logging.debug(f"[SilentPass:CacheCheck] 캐시 헬스체크 실패: {e!s:.100}")
    return False
```

> 이 건은 정상 동작의 일부(캐시 미존재 시 False)이므로 `logging.debug` 사용.

---

### 2. `main_a.py` L1879 — 앱 종료 실패

**현재:**
```python
except Exception:  # 종료 시 모든 예외 무시
    pass
```

**수정:**
```python
except Exception as e:  # 종료 시 모든 예외 무시
    logging.warning(f"[SilentPass:Shutdown] 앱 종료 중 예외: {e!s:.100}")
```

---

### 3. `modules/core/stage4_orchestrator.py` L792 — Bible POV 오버라이드

**현재:**
```python
except Exception:
    pass
```

**수정:**
```python
except Exception as e:
    logging.warning(f"[SilentPass:Stage4] Bible POV 오버라이드 실패: {e!s:.100}")
```

---

### 4. `modules/core/stage4_orchestrator.py` L814 — 최소 스타일 가이드 생성

**현재:**
```python
except Exception:
    pass
```

**수정:**
```python
except Exception as e:
    logging.warning(f"[SilentPass:Stage4] Bible POV 기반 스타일 가이드 생성 실패: {e!s:.100}")
```

---

### 5. `modules/domain/agents/chief_writer.py` L664 — 패치 모드 프롬프트 로드

**현재:**
```python
except Exception:
    _patch_template = None
```

**수정:**
```python
except Exception as e:
    logging.warning(f"[SilentPass:ChiefWriter] PATCH_MODE_PROMPT 로드 실패: {e!s:.100}")
    _patch_template = None
```

---

### 6. `modules/core/stage2_finalizer.py` L124 — 스토리 컨텍스트 생성

**현재:**
```python
except Exception:
    _story_context = ""
```

**수정:**
```python
except Exception as e:
    logging.warning(f"[SilentPass:Stage2Finalizer] 스토리 컨텍스트 생성 실패: {e!s:.100}")
    _story_context = ""
```

---

### 7. `modules/core/stage2_preflight.py` L512 — 장르 레지스트리 갱신

**현재:**
```python
except Exception:
    pass
```

**수정:**
```python
except Exception as e:
    logging.warning(f"[SilentPass:Preflight] 장르 레지스트리 갱신 실패: {e!s:.100}")
```

---

### 8. `modules/core/stage4_post_processor.py` L360 — 주인공 이름 추출

**현재:**
```python
except Exception:
    pass
```

**수정:**
```python
except Exception as e:
    logging.warning(f"[SilentPass:PostProcessor] 주인공 이름 추출 실패: {e!s:.100}")
```

---

### 9. `modules/core/stage4_post_processor.py` L451 — Core NPC 목록 추출

**현재:**
```python
except Exception:
    pass  # Bible 접근 실패 시 빈 set → 전수 검사
```

**수정:**
```python
except Exception as e:
    logging.warning(f"[SilentPass:PostProcessor] Core NPC 목록 추출 실패 (전수 검사 폴백): {e!s:.100}")
```

---

### 10. `modules/core/stage4_context_builder.py` L59 — ChainLink 다이제스트

**현재:**
```python
except Exception:
    return ""
```

**수정:**
```python
except Exception as e:
    logging.warning(f"[SilentPass:ContextBuilder] ChainLink 다이제스트 로드 실패: {e!s:.100}")
    return ""
```

---

### 11. `modules/core/stage4_context_builder.py` L107 — 확장 Lookback 다이제스트

**현재:**
```python
except Exception:
    return ""
```

**수정:**
```python
except Exception as e:
    logging.warning(f"[SilentPass:ContextBuilder] 확장 lookback 다이제스트 실패: {e!s:.100}")
    return ""
```

---

### 12. `modules/core/stage4_context_builder.py` L135 — 이전 원고 로드 (루프 내)

**현재:**
```python
except Exception:
    pass
```

**수정:**
```python
except Exception as e:
    logging.warning(f"[SilentPass:ContextBuilder] 제{_prev_ep}화 원고 로드 실패: {e!s:.100}")
```

> 루프 내 패턴이므로 `_prev_ep` 변수 참조.

---

### 13. `modules/core/stage4_context_builder.py` L181 — WorldState 요약

**현재:**
```python
except Exception:
    pass
```

**수정:**
```python
except Exception as e:
    logging.warning(f"[SilentPass:ContextBuilder] WorldState 요약 로드 실패: {e!s:.100}")
```

---

### 14. `modules/core/stage4_context_builder.py` L463 — SemanticPlotGuard 경고

**현재:**
```python
except Exception:
    pass
```

**수정:**
```python
except Exception as e:
    logging.warning(f"[SilentPass:ContextBuilder] SemanticPlotGuard 경고 주입 실패: {e!s:.100}")
```

---

### 15. `modules/core/stage4_interview_round.py` L268 — Incarnation type 로드

**현재:**
```python
except Exception:
    pass
```

**수정:**
```python
except Exception as e:
    logging.warning(f"[SilentPass:InterviewRound] incarnation_type 로드 실패: {e!s:.100}")
```

---

### 16. `modules/core/stage4_interview_round.py` L431 — 원고 이력 로드 (루프 내)

**현재:**
```python
except Exception:
    pass
```

**수정:**
```python
except Exception as e:
    logging.warning(f"[SilentPass:InterviewRound] 제{_prev_ep}화 원고 이력 로드 실패: {e!s:.100}")
```

> 루프 내 패턴이므로 `_prev_ep` 변수 참조.

---

## 파일별 요약

| 파일 | 수정 건수 | import 추가 필요 |
|------|----------|----------------|
| `main_a.py` | 2 | 이미 있음 |
| `modules/core/stage4_orchestrator.py` | 2 | 이미 있음 |
| `modules/domain/agents/chief_writer.py` | 1 | 이미 있음 |
| `modules/core/stage2_finalizer.py` | 1 | 이미 있음 |
| `modules/core/stage2_preflight.py` | 1 | 이미 있음 |
| `modules/core/stage4_post_processor.py` | 2 | 이미 있음 |
| `modules/core/stage4_context_builder.py` | 5 | 이미 있음 |
| `modules/core/stage4_interview_round.py` | 2 | 이미 있음 |

> 모든 파일에 `import logging`이 이미 존재함.

---

## 주의사항

1. **라인 번호 확인 필수** — E-2 Ruff 자동 수정으로 라인이 이동했을 수 있음. `except Exception:` 또는 `except Exception as e:` 패턴으로 검색하여 정확한 위치 확인.
2. **`e!s:.100`** — `str(e)[:100]`의 f-string 축약. Ruff 호환됨.
3. **루프 내 패턴 (건 12, 16)** — 반복 로깅 가능성 있으나, 정상 운영 시 발생하지 않으므로 OK.
4. **`logging.debug` 건 (건 1)** — 캐시 헬스체크는 정상 동작의 일부이므로 debug 레벨.

---

## 검증 게이트

```bash
# Gate 1: py_compile (변경 파일 전체)
python -m py_compile main_a.py
python -m py_compile modules/core/stage4_orchestrator.py
python -m py_compile modules/domain/agents/chief_writer.py
python -m py_compile modules/core/stage2_finalizer.py
python -m py_compile modules/core/stage2_preflight.py
python -m py_compile modules/core/stage4_post_processor.py
python -m py_compile modules/core/stage4_context_builder.py
python -m py_compile modules/core/stage4_interview_round.py

# Gate 2: SovereignApp import
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: 전체 테스트
set PYTHONIOENCODING=utf-8
pytest tests/ -q

# Gate 4: pre-commit
pre-commit run --files main_a.py modules/core/stage4_orchestrator.py modules/domain/agents/chief_writer.py modules/core/stage2_finalizer.py modules/core/stage2_preflight.py modules/core/stage4_post_processor.py modules/core/stage4_context_builder.py modules/core/stage4_interview_round.py
```

---

## 체크리스트

- [ ] 16건 전체 수정
- [ ] `except Exception:` → `except Exception as e:` 변경 (기존에 `as e` 없는 건)
- [ ] 기존 동작 (pass, return "", None 등) 100% 유지
- [ ] Gate 1-4 전체 통과
- [ ] 커밋: `fix(logging): add warning logs to 16 silent-pass exception handlers (E-1)`
