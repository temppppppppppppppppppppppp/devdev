# 프론트엔드 전역 전량 전수조사 3PASS 재감리

> 작성일: 2026-03-13
> 상태: `closed`
> 대상 문서: [frontend-global-full-survey-3pass-final-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/frontend-global-full-survey-3pass-final-audit.md)
> 조사 모드: `static / read-only / source-report cross-check / targeted code-and-test verification / UTF-8 only`
> 추가 검증:
> - `cd geuldobi-desktop && npm test` -> `137 passed in 1.52s`
> - `pytest -q tests/test_main_a_boot_binding.py` -> `5 passed in 1.88s`
> - inline `TestClient(app).post('/run', json={'key':'0','sub_key':'0'})` -> `202 / OK / runner_calls=1`
> - packaged resources 확인 -> `engine_exe=False`, `main_a_py=True`, `python_embed=True`

## Executive Summary

최종 감사 문서는 retained finding `7건`과 rejected finding 집합을 현재 코드, 표적 테스트, packaged resource inventory로 다시 재구성했다. 상위 위험군도 모두 현재 worktree에서 직접 재확인된다.

이번 재감리의 핵심은 두 가지였다.

1. `90%`에 머물렀던 확신도를 `문서 정확성 기준 95%`까지 끌어올릴 수 있는지
2. remediation 실행문서의 입력으로 써도 될 만큼 retained set이 안정적인지

결론은 `예`다.

- retained finding `7건`은 모두 현재 코드/테스트/파일시스템으로 다시 입증된다.
- rejected finding 집합도 reopened 필요 없이 유지 가능하다.
- 별도 normalization blocker는 없다.
- 따라서 본 frontend survey는 remediation execution SSOT의 기준 문서로 승격 가능하다.

최종 확신도는 `95%`다.

## Pass 1. Source Coverage

### P1-1. T1~T6 terminal 문서와 최종 감사 문서는 모두 존재한다

직접 근거:

- [FGS-T1-renderer-action-surface-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T1-renderer-action-surface-findings.md)
- [FGS-T2-project-settings-material-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T2-project-settings-material-findings.md)
- [FGS-T3-shell-ipc-splash-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T3-shell-ipc-splash-findings.md)
- [FGS-T4-bridge-runner-contract-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T4-bridge-runner-contract-findings.md)
- [FGS-T5-packaging-bundle-asset-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T5-packaging-bundle-asset-findings.md)
- [FGS-T6-regression-trust-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/FGS-T6-regression-trust-findings.md)
- [frontend-global-full-survey-3pass-final-audit.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/frontend-global-full-survey-3pass-final-audit.md)

판정:

- `confirmed`

### P1-2. retained total `7건`은 source ledger에서 정확히 재구성된다

직접 근거:

- `T1 0`
- `T2 0`
- `T3 1`
- `T4 1`
- `T5 2`
- `T6 3`

재구성 결과:

- `P1 1`
- `P2 4`
- `P3 2`
- `total 7`

판정:

- `confirmed`

### P1-3. rejected set도 source 문서에서 추적 가능하다

직접 근거:

- Stage 0 `1..7` parity broken -> rejected
- Frontier Lag not wired -> rejected
- work_guard template bridge missing -> rejected
- project root split still open -> rejected
- `UI/` archive live runtime dependency -> rejected
- dynamic HTML sanitization absent -> rejected

판정:

- `confirmed`

해석:

- source 문서 누락이나 total mismatch 때문에 통합 판단이 흔들리는 구간은 없다.

## Pass 2. Retained Findings Re-Verification

### P2-1. `FGS-T3-001` shadow main drift는 현재 코드와 shipping pattern에서 직접 재확인된다

직접 근거:

- `geuldobi-desktop/package.json:5` -> main은 `src/main.js`
- `geuldobi-desktop/src/main.js`에는 `project:list-work-guard-templates` IPC가 존재
- `geuldobi-desktop/main.js`에는 동일 IPC가 없다
- direct check:
  - `root_main_has_template_ipc=False`
  - `src_main_has_template_ipc=True`
- `builder-debug.yml` shipping pattern은 `src/**/*`만 포함

판정:

- `confirmed`

해석:

- 즉시 shipping bug는 아니지만, shadow surface drift는 명확히 살아 있다.

### P2-2. `FGS-T4-001` hidden `sub_key 0` contract는 real app 기준으로도 실제 허용된다

직접 근거:

- `modules/api/run_validator.py:27` -> `"0"` 포함
- `docs/implementation/prompt-map-v1.json:7` -> `"0"` 포함
- `modules/core/stage01_helpers.py:403` -> `mode == 0` interactive branch 유지
- 추가 실검증:
  - inline `TestClient(app).post('/run', json={'key':'0','sub_key':'0'})`
  - 결과 `202 / OK / runner_calls=1`

판정:

- `confirmed`

해석:

- 이건 단순 문서 drift가 아니라 real app이 받아들이는 hidden contract다.
- desktop UI가 노출하지 않아도 external caller 관점에서는 살아 있는 surface다.

### P2-3. `FGS-T5-001`, `FGS-T5-002` packaging drift는 packaged resources inventory로 강화된다

직접 근거:

- `build/build_release.ps1`는 `Sync-EngineBundle`로 `dist/engine/main_a.py`를 만든다
- `build/backend_entry.py`는 `resources/engine` + `resources/python-embed/python.exe`를 주입한다
- `geuldobi-desktop/src/main.js:167`는 `GEULDOBI_ENGINE_EXE=resources/engine/engine.exe`를 주입한다
- direct packaged inventory:
  - `engine_exe=False`
  - `main_a_py=True`
  - `python_embed=True`
- `DESKTOP-GUIDE.md:4`, `:17`, `:24-25`는 `engine.exe`, `소스 코드 비공개`를 설명한다

판정:

- `confirmed`

해석:

- 배포 모델 불일치는 가설이 아니라 실제 artifact inventory와 문서의 정면 충돌이다.

### P2-4. `FGS-T6-001` default gate coverage gap은 `npm test`와 wider pytest의 차이로 재확인된다

직접 근거:

- `npm test`는 8개 suite만 실행하고 `137 passed in 1.52s`
- wider proof set은 `196 passed in 4.52s`
- package script에는 `test_bridge_server_http_contract.py`, `test_bridge_server_desktop_risk_gate.py`, `test_bridge_quality_summary.py`, `test_runtime_paths.py`가 없다

판정:

- `confirmed`

해석:

- coverage gap은 “테스트가 실패한다”가 아니라 “default gate가 좁다”는 뜻이다.

### P2-5. `FGS-T6-002`, `FGS-T6-003` regression trust gap은 현재도 남아 있다

직접 근거:

- `tests/test_frontend_stage0_connectivity.py`, `tests/test_ui_renderer_sanitization.py`, `tests/test_desktop_work_guard_template_contract.py`, `tests/test_desktop_contract_refresh.py`는 source-string assertion 비중이 높다
- `splash`, `getWorkspacePath`, `openWorkspaceFolder`, `listMaterialFiles`, `importMaterialFile`, `deleteMaterialFile` 관련 테스트 검색은 `NONE`

판정:

- `confirmed`

해석:

- 현재 회귀망은 “있다”와 “behavior gap이 남아 있다”가 동시에 참이다.

## Pass 3. False Positive Removal

### P3-1. rejected set은 재오픈 사유가 없다

검토 결과:

- renderer parity/Frontier Lag/work_guard template/sanitization 항목은 현재 코드와 테스트가 직접 반증한다.
- `UI/` archive live dependency도 runtime/shipping 증거가 없다.

판정:

- `confirmed`

### P3-2. 확신도 하락 요인은 live Electron 실행 부재뿐이며, 문서 정확성 기준 blocker는 아니다

검토 결과:

- splash-to-main live handoff
- material file ops actual dialog behavior
- workspace open shell integration
- packaged installer boot UX

위 항목은 여전히 `needs-live-check`다. 그러나 retained/rejected ledger의 정확성을 뒤집을 수준의 blocker는 아니다.

판정:

- `confirmed`

## Confidence Ledger

- 시작점: `70`
- T1~T6 source coverage 재구성: `+10`
- retained set 전량 재입증: `+10`
- 추가 pytest / npm test / inline TestClient / packaged inventory 보강: `+10`
- false-positive 제거 완료: `+5`
- live Electron / installer 미실시: `-10`

최종 확신도: `95%`

## Final Conclusion

- 최종 상태: `closed`
- frontend survey SSOT 승격: `가능`
- remediation execution SSOT 작성: `진행 권장`
- blocker: `없음`

다음 단계는 조사 지속이 아니라 retained `7건`만 흡수하는 remediation execution SSOT 작성이다.
