# [S-T5] 보안 · 성능 · 규모 심층 감사 보고서

> 작성일: 2026-03-13
> 터미널: Terminal 5
> 범위: production 보조 인프라의 보안/성능/격리 경계, `BaseAgent` 글로벌 캐시 계층, 기존 고위험 T5 ledger 재점검
> 방법: static / read-only / scale-path inspection / prior-ledger cross-check

---

## 요약

이번 심층 감사에서는 이미 1차·2차에서 잡힌 Desktop 보안 이슈와 도메인 보조 모듈 이슈를 다시 중복 보고하지 않는 대신, **현재 트리에서 새로 확인되는 scale/격리 문제만 남기는 것**을 목표로 삼았다.

결론은 보수적으로 정리했다.

- 신규 P0는 없다.
- 신규 P1도 없다.
- 새로 확정할 만한 생산계 이슈는 `BaseAgent` 글로벌 컨텍스트 캐시의 namespace/eviction 구조 1건이다.

즉, T5 심층 감사의 산출물은 "새로운 치명 취약점 대거 발견"이 아니라, **기존 상위위험을 제외하고도 남는 장기 scale debt 1건을 분리해낸 것**이다.

---

## 확정 발견사항

### [S-T5-001] P2 | `BaseAgent` 컨텍스트 캐시는 프로세스 전역 50-entry LRU인데, 호출부 namespace 규칙이 프로젝트 단위로 일관되지 않다

- 파일:
  - `modules/domain/agents/base_agent.py:1744-1748`
  - `modules/domain/agents/base_agent.py:1814-1826`
  - `modules/domain/agents/chief_writer.py:414-419`
  - `modules/domain/agents/blueprint_ensemble.py:288-293`
  - `modules/domain/agents/arc_ensemble.py:394-399`
  - `modules/domain/agents/director_ensemble.py:1017-1022`
  - `modules/domain/agents/analyst.py:138-147`
  - `modules/domain/agents/analyst.py:185-190`
- 현상:
  - `BaseAgent._context_caches`는 클래스 변수이며, 프로세스 전체가 공유하는 50-entry LRU다.
  - 그런데 호출부 namespace는 일관되지 않다.
  - `ChiefWriter`, `BlueprintEnsemble`, `ArcEnsemble`, `DirectorEnsemble`는 `project_name=f"ep{ep_num}"`, `f"arc{arc_no}"`처럼 회차/아크 번호만 넣는다.
  - 반면 `Analyst`는 `_cache_project_name()`로 실제 프로젝트명 기반 namespace를 만든다.
- 영향:
  - 프로젝트 간 동일 회차/아크 번호가 흔한 환경에서는 cache key namespace discipline이 약해진다.
  - 정확한 내용 hash가 다르면 오답 재사용까지는 덜 가더라도, 글로벌 50-entry LRU가 여러 프로젝트·에이전트 사이에서 서로를 밀어내며 **성능/비용 cross-talk**를 만든다.
  - 즉각적인 정합성 버그보다 **장기 운영 시 token cache 효율 저하와 프로젝트 격리 약화**가 핵심이다.
- 기존 보고서와의 관계:
  - 기존 T5에서 `SemanticItemRegistry` 싱글톤 오염은 다뤘지만, `BaseAgent` 글로벌 context cache namespace drift는 정식 ledger로 올라오지 않았다.

---

## 재점검 메모

다음 항목들은 이번 심층 감사에서 다시 봤지만, 신규 ledger로 재삽입하지 않았다.

- renderer 직접 Gemini fetch / CSP `unsafe-inline`
  - 이미 `D-T5-002`, `D-T5-003` 계열에서 다뤄진 위험
- FactLedger deceased NPC guard
  - 현재 트리에서는 guard가 추가돼 이전 P1이 해소된 상태
- `get_dashboard()` / `SemanticItemRegistry` 싱글톤
  - 기존 T4/T5 ledger에 이미 존재하는 항목

---

## 보안 / 성능 / 규모 요약표

| 축 | 이번 심층 감사 결론 |
|----|-------------------|
| 보안 | 신규 P1 없음. 실질 상위위험은 여전히 Desktop renderer/approval 경계 쪽에 집중 |
| 성능 | 글로벌 50-entry cache가 프로젝트/에이전트 간 상호 축출을 일으킬 수 있음 |
| 규모 | 멀티프로젝트/장시간 배치에서 cache namespace discipline 부족이 점점 불리해짐 |

---

## 3PASS 감리 로그

### PASS 1 — 후보 3건

- global context cache namespace drift
- shared router/provider 글로벌 상태
- 기존 singleton 재보고 여부

### PASS 2 — 제거 2건

- shared router/provider 글로벌 상태: 현재 증거만으로 실질 결함까지는 약함
- 기존 singleton 재보고: T4/T5 기존 ledger와 중복

### PASS 3 — 최종 1건 확정

- `PASS1 3건 → PASS2 2건 제거 → 최종 1건 확정`

---

## 결론

T5 심층 감사는 기존 Desktop 보안 이슈를 다시 적는 문서가 아니다. 현재 코드에서 새로 남는 production-scale 문제는 **전역 컨텍스트 캐시의 namespace discipline과 eviction 경계가 프로젝트 단위로 정리돼 있지 않다**는 1건으로 수렴했다.

후속 조치 우선순위는 다음과 같다.

1. cache key namespace를 실제 프로젝트명 기반으로 통일
2. 글로벌 50-entry LRU가 stage/agent/project별로 어떻게 경쟁하는지 관측 로그 추가
3. 멀티프로젝트 batch 환경이 전제되면 per-project cache partition 또는 별도 캐시 버킷 검토
