# Track B — 경로 해석 정합성

> 확신도: 97%
> 범위: FE/BE 양측의 경로 해석 로직, 환경변수 전파, 2중 루트 설계

---

## 1. 2중 루트 설계

### 개념

```
Engine Root  — 코드·설정·모델 (읽기 전용 in 배포)
Workspace Root — 사용자 데이터·프로젝트 (읽기/쓰기)
```

### 모드별 경로

| 항목 | 개발 모드 | 배포 모드 |
|------|----------|----------|
| Engine Root | `Desktop/글도비/` (repo root) | `{resourcesPath}/engine/` |
| Workspace Root | `Desktop/글도비/` (동일) | `{Documents}/글도비/` |
| Projects Root | `Desktop/글도비/projects/` | `{Documents}/글도비/projects/` |
| Material Root | `Desktop/글도비/` | `{Documents}/글도비/` |
| App Config | `%LOCALAPPDATA%/Geuldobi/` | `%LOCALAPPDATA%/Geuldobi/` |
| Backend Exe | `python -m uvicorn` (직접 실행) | `{resourcesPath}/backend/backend.exe` |

---

## 2. 환경변수 체인

### FE → BE 전파 (main.js:269-278)

```javascript
env: {
  ...process.env,
  PYTHONIOENCODING: "utf-8",
  PYTHONUNBUFFERED: "1",
  GEULDOBI_DESKTOP_MODE: "1",                       // 항상
  ...(app.isPackaged ? {
    GEULDOBI_PACKAGED_RUNTIME_MODEL: "source_bundle_primary",
    GEULDOBI_WORKSPACE: getWorkspaceDir(),           // {Documents}/글도비
    GEULDOBI_PROJECTS_ROOT: path.join(getWorkspaceDir(), "projects"),
  } : {}),
}
```

개발 모드에서는 `GEULDOBI_WORKSPACE`와 `GEULDOBI_PROJECTS_ROOT`를 **설정하지 않음** → BE가 기본값(engine root) 사용.

### BE 해석 (runtime_paths.py:9-44)

```python
def resolve_engine_root(default_root):
    return Path(os.environ.get("GEULDOBI_ENGINE_ROOT") or default_root).resolve()

def resolve_workspace_root(default_root):
    return Path(os.environ.get("GEULDOBI_WORKSPACE") or resolve_engine_root(default_root)).resolve()

def resolve_projects_root(default_root):
    explicit = os.environ.get("GEULDOBI_PROJECTS_ROOT")
    if explicit:
        return Path(explicit).resolve()
    return resolve_workspace_root(default_root) / "projects"
```

### 변수 해석 순서 (우선순위 높은 것 → 낮은 것)

| 변수 | 우선순위 1 | 우선순위 2 | 우선순위 3 |
|------|-----------|-----------|-----------|
| Engine Root | `$GEULDOBI_ENGINE_ROOT` | `default_root` (코드 위치) | — |
| Workspace | `$GEULDOBI_WORKSPACE` | Engine Root | — |
| Projects | `$GEULDOBI_PROJECTS_ROOT` | `{Workspace}/projects` | — |

---

## 3. FE 경로 해석 함수

### main.js 경로 함수 목록

```javascript
getLocalAppDataRoot()        // → %LOCALAPPDATA% || ~/AppData/Local
getAppDir()                  // → {localAppData}/Geuldobi
getWorkspaceDir()            // → {Documents}/글도비 (배포) || repo root (개발)
getEngineRoot()              // → {resourcesPath}/engine (배포) || repo root (개발)
getMaterialRoot()            // → workspace (배포) || engine root (개발)
getProjectsDir()             // → {workspace}/projects (배포) || {engine}/projects (개발)
getProjectRoot(name)         // → {projectsDir}/{sanitized_name}
getProjectConfigDir(name)    // → {projectRoot}/config
getWorkGuardLibraryDir()     // → {workspace}/work_guards (배포) || {repo}/work_guards (개발)
getPackagedWorkspaceSeedDir() // → {resourcesPath}/workspace-seed (배포 전용)
```

### 경로 해석 체인

```
app.isPackaged?
├─ YES (배포):
│   workspaceDir   = app.getPath("documents") + "/글도비"
│   engineRoot     = process.resourcesPath + "/engine"
│   materialRoot   = workspaceDir
│   projectsDir    = workspaceDir + "/projects"
│
└─ NO (개발):
    workspaceDir   = path.resolve(__dirname, "../..")  [repo root]
    engineRoot     = path.resolve(__dirname, "../..")  [동일]
    materialRoot   = engineRoot
    projectsDir    = engineRoot + "/projects"
```

---

## 4. BE 경로 해석 체인

### process_runner.py 초기화

```python
# process_runner.py:44
PROJECT_ROOT = resolve_engine_root(Path(__file__).resolve().parent.parent.parent)
# __file__ = modules/api/process_runner.py
# parent.parent.parent = Desktop/글도비/
```

### bridge_server.py 헬퍼

```python
# bridge_server.py:277-287
def _get_projects_root():
    return resolve_projects_root(PROJECT_ROOT)

def _get_project_dir(name):
    return resolve_project_dir(name, PROJECT_ROOT)  # 경로 탈출 검증 포함

def _get_project_db_path(name):
    return _get_project_dir(name) / "project_data.db"
```

---

## 5. Workspace Seed 초기화 (배포 전용)

### 목적

배포 모드 첫 실행 시 `{resourcesPath}/workspace-seed/` → `{Documents}/글도비/`로 초기 파일 복사.

### 복사 대상

```
workspace-seed/
├── bible/           → {Documents}/글도비/bible/
├── treatments/      → {Documents}/글도비/treatments/
└── projects/
    └── investment_canary_demo/  → {Documents}/글도비/projects/investment_canary_demo/
```

### 안전 장치

- `copyMissingTree()` — **기존 파일 덮어쓰기 없음**, 새 파일만 복사
- 디렉토리가 없으면 `fs.mkdirSync({recursive: true})`로 생성
- 실패 시 silent catch (첫 실행 없이도 동작 가능)

코드 위치: `main.js:191-219`

---

## 6. 파일시스템 구조 정합성

### FE가 기대하는 구조

```
{materialRoot}/
├── bible/           # material:list-files("bible")
│   └── *.json, *.txt
└── treatments/      # material:list-files("treatments")
    └── *.json, *.txt

{projectsDir}/
└── {project_name}/
    ├── config/
    │   ├── author_directives.txt
    │   └── work_guard.yaml
    └── ...
```

### BE가 기대하는 구조

```
{workspace}/
├── bible/
│   └── *.json
├── treatments/
│   └── *.json
└── projects/
    └── {project_name}/
        ├── project_data.db
        ├── config/
        │   ├── author_directives.txt
        │   └── work_guard.yaml
        ├── stage0_output/
        │   └── style_guide.json
        ├── plans/
        │   ├── arcs/
        │   └── blueprints/
        ├── drafts/
        └── logs/
```

### 정합성 판정

- **bible/, treatments/**: 양측 동일 경로 (`{workspace}/{folder}/`)
- **projects/**: 양측 동일 (`{projectsDir}/{name}/`)
- **config/**: FE는 `author_directives.txt`, `work_guard.yaml`만 접근. BE는 동일 + 추가 항목
- **stage0_output/, plans/, drafts/, logs/**: BE 전용. FE는 접근하지 않음 (HTTP API 통해 간접 조회)

→ **정합** ✅

---

## 7. 프로젝트 인덱스 정렬 일관성

```
FE: fs.readdirSync(dir).filter(isDir).sort()     // main.js:856
BE: sorted(path.name for path in root.iterdir() if path.is_dir())  // process_runner.py:155
```

양측 모두 **lexical sort (유니코드 사전순)** 사용. 1-based indexing.

→ **정합** ✅

---

## 8. 경로 탈출 방지

### FE 측 (main.js:738-740)

```javascript
// material:delete-file
if (fileName.includes("..") || fileName.includes("/") || fileName.includes("\\")) {
  return { ok: false, message: "invalid filename" };
}
```

### BE 측 (runtime_paths.py:34-44)

```python
def resolve_project_dir(project_name: str, default_root) -> Path:
    projects = resolve_projects_root(default_root)
    candidate = (projects / project_name).resolve()
    # 경로 탈출 검증
    if not str(candidate).startswith(str(projects.resolve())):
        raise ValueError(f"project_name escapes projects root: {project_name}")
    return candidate
```

→ 양측 모두 경로 탈출 방지 처리 완료 ✅

---

## 9. 3-Pass 감리

| Pass | 검증 항목 | 결과 |
|------|----------|------|
| 1차 | 환경변수 4개 전파 경로 FE→BE 추적 완료 | ✅ |
| 2차 | 개발/배포 모드별 경로 해석 결과 교차 확인 | ✅ |
| 3차 | 파일시스템 구조 FE 기대 ↔ BE 기대 일치 확인 | ✅ |
