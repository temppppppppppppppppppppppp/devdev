# 스파이크 1 결과 — PyInstaller + sqlite-vec 번들

- 실행일: 2026-03-06
- 판정: **PASS**

---

## 실행 출력

```
=== Spike 1: PyInstaller + sqlite-vec ===
sqlite-vec version: v0.1.6
Vector search: rowid=1, distance=0.0
SPIKE-1 PASS
```

---

## 빌드 환경

| 항목 | 값 |
|---|---|
| Python | 3.11.9 |
| PyInstaller | 6.19.0 |
| sqlite-vec | v0.1.6 |
| 플랫폼 | Windows-10-10.0.26200 (64bit) |
| 빌드 모드 | one-file (onefile) |
| UPX | 비활성화 (DLL 손상 방지) |

---

## 번들 크기

| 파일 | 크기 |
|---|---|
| `dist/spike_pyinstaller.exe` | **23.4 MB** |

---

## 핵심 확인 사항

| 항목 | 결과 |
|---|---|
| `sqlite_vec` import 성공 | ✅ |
| `conn.enable_load_extension(True)` | ✅ |
| `sqlite_vec.load(conn)` — vec0.dll 로드 | ✅ |
| `vec_version()` 쿼리 | ✅ v0.1.6 |
| `CREATE VIRTUAL TABLE v USING vec0(...)` | ✅ |
| 벡터 검색 1건 (KNN k=1) | ✅ rowid=1 distance=0.0 |

---

## spec 핵심 설정

```python
# vec0.dll → 번들 내 sqlite_vec/ 디렉토리에 배치
binaries=[(_VEC0_PATH, "sqlite_vec")]
hiddenimports=["sqlite_vec"]
upx=False  # DLL 손상 방지
```

`sqlite_vec.loadable_path()` 는 `os.path.dirname(__file__)` 기준으로 `vec0` 경로를 계산한다.
PyInstaller one-file 모드에서 `__file__` 은 `sys._MEIPASS/sqlite_vec/__init__.py` 가 되어
`sys._MEIPASS/sqlite_vec/vec0.dll` 을 정확히 참조한다.

---

## GO/NO-GO 판정

**GO** — sqlite-vec C 확장이 PyInstaller one-file exe 번들에 정상 포함됨.
exe 배포 아키텍처 블로커 없음. 스파이크 2 결과 확인 후 Phase 2 착수 가능.

---

## 주의사항 (운영 번들 적용 시)

1. **UPX 비활성화 유지** — UPX가 vec0.dll 을 압축하면 로드 실패 가능성 있음
2. **`enable_load_extension(True)` 필요** — 글도비 메인 코드에서 이미 사용 중이므로 추가 설정 불필요
3. **번들 크기 예상** — numpy 포함 시 현재 23.4 MB + numpy.libs (~60 MB) → ~85 MB 예상
   - 전체 글도비 의존성 포함 시 300~500 MB 예상치와 부합
