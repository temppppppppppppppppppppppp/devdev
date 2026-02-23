# TF-6-H: 데드코드 / 위생 정리 (Dead Code & Hygiene)

## 감사 범위
- 파일/디렉토리: `_ag_deep.py`, `_ag_scan.py`, `_scan_modules.py`, `_tmp_r1f.py`~`_tmp_r3e.py`, `check_blocks.py`, `tools2/`, `test_mode/`, `new_blocks_*.json`, `recent_diff*.txt`, `temp_inspect.txt`
- 코드 줄 수: 약 1,200줄 수동 확인 + 추적 상태 점검

## 발견 사항

### [TF-H-1] 루트 임시 스크립트가 절대 경로 + 파일 생성 부작용을 포함 (MEDIUM)
- **파일**: `_ag_deep.py:5`, `_ag_deep.py:96`, `_ag_scan.py:5`, `_scan_modules.py:6`
- **현재 코드**:
```python
modules = Path(r"C:\Users\wjjo\Desktop\글도비\modules")
...
Path(r"C:\Users\wjjo\Desktop\글도비\_ag_deep_result.txt").write_text(...)
```
- **문제**: 특정 로컬 환경 절대 경로에 강결합된 임시 분석 스크립트가 루트에 잔존.
- **영향**: 다른 개발자/CI에서 실행 시 실패 또는 예기치 않은 파일 생성.
- **수정안**: `tools/scratch/`로 격리하거나 제거, 필요 시 상대 경로+CLI 인자 방식으로 전환.
- **테스트**: 저장소 루트 clean checkout에서 스크립트 실행/미실행 시 산출물 생성 여부 검증.

### [TF-H-2] `check_blocks.py`가 하드코딩된 로컬 데이터에 직접 의존 (MEDIUM)
- **파일**: `check_blocks.py:3`, `check_blocks.py:5`
- **현재 코드**:
```python
with open("treatments/골든루트_tr_block_ALL.json", ...)
for b in d[37:]:
```
- **문제**: 프로젝트 전역 유틸리티가 아닌 1회성 수동 점검 코드가 루트에 노출되어 있다.
- **영향**: 운영 스크립트로 오인될 수 있고, 데이터 포맷 변경 시 즉시 깨진다.
- **수정안**: `tools2/` 또는 `scripts/manual/`로 이동 후 README에 용도 명시.
- **테스트**: 스크립트 인자화(`--start-index`) 후 샘플 파일 대상으로 동작 검증.

### [TF-H-3] `tools2` 스크립트가 절대경로/원본 직접 덮어쓰기를 수행 (MEDIUM)
- **파일**: `tools2/apply_v3.py:3`, `tools2/automate_snack.py:73`
- **현재 코드**:
```python
with open('c:/Users/PC/Desktop/글도비/treatments/...json', ...)
...
automate_snack_culture('...v2_snack.json', '...v2_snack.json')
```
- **문제**: 입력과 출력이 동일 파일인 직접 덮어쓰기 패턴 + 절대경로 고정.
- **영향**: 실수 실행 시 치료 데이터 원본 손실 가능.
- **수정안**: 기본 출력 파일을 별도 경로로 강제하고 `--in-place` 명시 옵션으로만 허용.
- **테스트**: dry-run 모드에서 변경 diff만 출력, 원본 무변경 검증.

## 요약
| 심각도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 3 |
