"""ProcessRunner — main_a.py subprocess 래퍼 (실체화)

역할:
- main_a.py를 숨김 프로세스로 기동/종료/상태 추적
- stdout 줄 단위 비동기 수집 + ANSI 제거
- 콜백 기반 이벤트 전달 (on_line, on_exit)

기동:
    runner = ProcessRunner()
    await runner.start(key="4", run_id="abc", on_line=..., on_exit=...)
    await runner.stop()

stdin 시퀀스 (Mode A):
    genre_index → [Enter] → project_index → [genre_confirm] → menu_key → [sub_key] → confirmations → exit(5)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sqlite3
import subprocess
import sys
import time
from collections import deque
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path

from modules.api.control_plane_contract import (
    ALLOWED_STAGE0_SUB_KEYS,
    AUTHORITY_ROLE_COMPANION_SNAPSHOT,
    MODE_B_KEYS,
)
from modules.core.runtime_paths import (
    resolve_engine_root,
    resolve_project_dir,
    resolve_projects_root,
    resolve_workspace_root,
)

logger = logging.getLogger(__name__)

# frozen 모드(PyInstaller): GEULDOBI_ENGINE_ROOT 환경 변수 우선
PROJECT_ROOT = resolve_engine_root(Path(__file__).resolve().parent.parent.parent)

# 러너가 취할 수 있는 상태 (StatusEnvelope.data.state enum과 동기화)
VALID_STATES = frozenset({"idle", "starting", "running", "stopping", "error"})

# ─── ANSI escape stripper ────────────────────────────────────────────────────

_ANSI_RE = re.compile(
    r"\x1b\[[0-9;]*[a-zA-Z]"  # CSI (colors, cursor, etc.)
    r"|\x1b\][^\x07]*\x07"  # OSC (title, etc.)
    r"|\x1b[()][A-Z0-9]"  # Character set designation
    r"|\x1b[=>]"  # Keypad mode
    r"|\r"  # Carriage return
)


def _strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences and trailing whitespace."""
    return _ANSI_RE.sub("", text).rstrip()


def _decode_runtime_stream(raw: bytes) -> str:
    """Decode ephemeral runtime stream data without defining durable sink policy."""
    return raw.decode("utf-8", errors="replace")


def _is_benign_stderr_line(text: str) -> bool:
    normalized = str(text or "").strip()
    if not normalized:
        return True
    return normalized.startswith("[V61.3] Faulthandler 활성화 → crash_dump.log")


# ─── Callback 타입 ────────────────────────────────────────────────────────────

OnLineCallback = Callable[[str], Awaitable[None]]
OnExitCallback = Callable[[int], Awaitable[None]]
OnPromptCallback = Callable[[str, list[str]], Awaitable[None]]

# ─── 기본 확인 응답 패딩 수 ──────────────────────────────────────────────────
_DEFAULT_CONFIRM_PADDING = 5
_STAGE0_STYLE_ANALYSIS_SUB_KEY = "6"

# ─── Mode B 프롬프트 감지 타임아웃 (초) ──────────────────────────────────────
_PROMPT_DETECT_TIMEOUT = 0.5
_RUNTIME_TAIL_LINES = 8
_RUNTIME_STDERR_DECODE_POLICY = "utf-8-replace"
_DEFAULT_PROVIDER_MODE = "gemini_direct"
_AMBIENT_PROVIDER_MODE = "ambient"
_NON_GEMINI_PROVIDER_ENV_KEYS = (
    "ANTHROPIC_API_KEY",
    "CLAUDE_API",
    "VERTEX_API_KEY",
    "VERTEX_PROJECT_ID",
    "VERTEX_LOCATION",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_CLOUD_LOCATION",
    "OPENAI_API_KEY",
)

_GENRE_INDEX_TO_TYPE = {
    "1": "wuxia",
    "2": "hunter",
    "3": "investment",
    "4": "fantasy",
    "5": "composer",
    "6": "cooking",
    "7": "alt_history",
    "8": "actor",
    "9": "sports",
    "10": "medical",
}


def _resolve_workspace_root() -> Path:
    return resolve_workspace_root(PROJECT_ROOT)


def _resolve_projects_root() -> Path:
    return resolve_projects_root(PROJECT_ROOT)


def _resolve_stage0_style_cache_choice(inputs: dict | None) -> str | None:
    if not inputs:
        return None
    cache_mode = str(inputs.get("stage0_style_cache_mode") or "").strip().lower()
    return {"use": "1", "refresh": "2", "reset": "3"}.get(cache_mode)


def _normalize_public_stage0_sub_key(sub_key: str | None) -> str:
    normalized = str(sub_key or "").strip()
    if not normalized:
        raise ValueError("sub_key is required for public Stage 0 runs")
    if normalized not in ALLOWED_STAGE0_SUB_KEYS:
        raise ValueError(f"sub_key '{normalized}' is not part of the public Stage 0 contract")
    return normalized


def _resolve_requested_genre_type(inputs: dict | None) -> str | None:
    if not inputs:
        return None

    explicit = str(inputs.get("genre_type") or "").strip().lower()
    if explicit:
        return explicit

    genre_index = str(inputs.get("genre_index") or "").strip()
    return _GENRE_INDEX_TO_TYPE.get(genre_index)


def _resolve_requested_project_name(inputs: dict | None) -> str | None:
    if not inputs:
        return None

    explicit = str(inputs.get("project_name") or "").strip()
    if explicit:
        return explicit

    try:
        project_index = int(inputs.get("project_index", 0))
    except (TypeError, ValueError):
        return None

    if project_index < 1:
        return None

    root = _resolve_projects_root()
    try:
        projects = sorted(path.name for path in root.iterdir() if path.is_dir())
    except FileNotFoundError:
        return None

    if project_index > len(projects):
        return None
    return projects[project_index - 1]


def _load_stored_project_genre_type(project_name: str | None) -> str | None:
    normalized_name = str(project_name or "").strip()
    if not normalized_name:
        return None

    db_path = resolve_project_dir(normalized_name, PROJECT_ROOT) / "project_data.db"
    if not db_path.exists():
        return None

    try:
        with sqlite3.connect(db_path) as conn:
            row = conn.execute("SELECT data FROM anchors WHERE key = ?", ("genre_info",)).fetchone()
    except sqlite3.Error as exc:
        logger.warning("failed to inspect stored genre for %s: %s", normalized_name, exc)
        return None

    if not row or not row[0]:
        return None

    try:
        payload = json.loads(row[0])
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("failed to parse stored genre for %s: %s", normalized_name, exc)
        return None

    if not isinstance(payload, dict):
        return None

    stored_type = str(payload.get("type") or "").strip().lower()
    return stored_type or None


def _resolve_provider_mode(inputs: dict | None) -> str:
    requested = str((inputs or {}).get("provider_mode") or _DEFAULT_PROVIDER_MODE).strip().lower()
    return requested if requested == _AMBIENT_PROVIDER_MODE else _DEFAULT_PROVIDER_MODE


def _should_inject_boot_genre_confirm(inputs: dict | None) -> bool:
    selected_genre_type = _resolve_requested_genre_type(inputs)
    if not selected_genre_type:
        return False

    project_name = _resolve_requested_project_name(inputs)
    stored_genre_type = _load_stored_project_genre_type(project_name)
    return bool(stored_genre_type and stored_genre_type != selected_genre_type)


def _resolve_launch_command() -> list[str]:
    engine_exe = os.environ.get("GEULDOBI_ENGINE_EXE")
    if engine_exe:
        engine_path = Path(engine_exe)
        if engine_path.exists():
            return [str(engine_path)]
        logger.warning("engine.exe not found at %s; falling back to python main_a.py", engine_exe)

    main_script = PROJECT_ROOT / "main_a.py"
    if not main_script.exists():
        logger.error("main_a.py not found at %s", main_script)
        raise FileNotFoundError(f"main_a.py not found: {main_script}")

    python_exe = os.environ.get("GEULDOBI_PYTHON_PATH", sys.executable)
    return [python_exe, "-u", str(main_script)]


class ProcessRunner:
    """main_a.py subprocess 래퍼.

    상태머신:
        idle → starting → running → stopping → idle
        any  → error → idle (on unrecoverable failure)
    """

    def __init__(self) -> None:
        self._state: str = "idle"
        self._run_id: str | None = None
        self._pid: int | None = None
        self._process: asyncio.subprocess.Process | None = None
        self._read_task: asyncio.Task | None = None
        self._on_line: OnLineCallback | None = None
        self._on_exit: OnExitCallback | None = None
        self._on_prompt: OnPromptCallback | None = None
        self._mode: str = "A"  # "A" (stdin 사전 주입) | "B" (실시간 대화)
        self._key: str | None = None
        self._sub_key: str | None = None
        self._started_at_iso: str | None = None
        self._started_monotonic: float | None = None
        self._stdout_tail: deque[str] = deque(maxlen=_RUNTIME_TAIL_LINES)
        self._stderr_tail: deque[str] = deque(maxlen=_RUNTIME_TAIL_LINES)
        self._last_prompt_step: str | None = None

    # ──────────────────────────────────────────────────────────────────────────
    # Properties
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def state(self) -> str:
        return self._state

    @property
    def run_id(self) -> str | None:
        return self._run_id

    @property
    def pid(self) -> int | None:
        return self._pid

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    async def start(
        self,
        key: str,
        run_id: str,
        sub_key: str | None = None,
        inputs: dict | None = None,
        *,
        on_line: OnLineCallback | None = None,
        on_exit: OnExitCallback | None = None,
        on_prompt: OnPromptCallback | None = None,
        mode: str | None = None,
    ) -> None:
        """main_a.py subprocess 기동.

        Args:
            key: 메뉴 키 (e.g. "2", "4", "6", "44").
            run_id: 실행 고유 ID.
            sub_key: Stage 0 하위 옵션 키 (e.g. "1" for Bible).
            inputs: 추가 입력 dict (project_index, api_key, etc.).
            on_line: stdout 줄 콜백 (async).
            on_exit: 프로세스 종료 콜백 (async, returncode 전달).
            on_prompt: Mode B 프롬프트 감지 콜백 (async, prompt_text + context_lines).
            mode: "A" (사전 주입) | "B" (실시간). None이면 키 기반 자동 선택.
        """
        if self._state != "idle":
            raise RuntimeError(f"Cannot start: state={self._state}")

        self._state = "starting"
        self._run_id = run_id
        self._on_line = on_line
        self._on_exit = on_exit
        self._on_prompt = on_prompt
        self._mode = mode if mode else ("B" if key in MODE_B_KEYS else "A")
        self._key = key
        self._sub_key = sub_key
        self._started_at_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        self._started_monotonic = time.monotonic()
        self._stdout_tail.clear()
        self._stderr_tail.clear()
        self._last_prompt_step = None

        stdin_data = self._build_stdin_sequence(key, sub_key, inputs)
        env = self._build_env(inputs)

        kwargs: dict = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        try:
            # 배포 모드에서는 workspace를 CWD로 고정하고, engine.exe가 없으면 source-tree 엔진으로 fallback한다.
            work_dir = str(_resolve_workspace_root())
            cmd_args = _resolve_launch_command()

            self._process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir,
                env=env,
                **kwargs,
            )
        except Exception:
            self._state = "idle"
            self._run_id = None
            logger.exception("subprocess 기동 실패")
            raise

        self._pid = self._process.pid
        self._state = "running"

        logger.info(
            "ProcessRunner started pid=%d key=%r sub_key=%r run_id=%r",
            self._pid,
            key,
            sub_key,
            run_id,
        )

        # stdin 시퀀스 전송
        if stdin_data and self._process.stdin:
            try:
                self._process.stdin.write(stdin_data.encode("utf-8"))
                await self._process.stdin.drain()
                if self._mode == "A":
                    self._process.stdin.close()
                # Mode B: stdin을 열어둔 채로 유지 (write_stdin으로 후속 입력)
            except Exception:
                logger.exception("stdin 전송 실패")
                # 실패 시 stdin 정리 — 파이프 열림 방지
                try:
                    if self._process.stdin and not self._process.stdin.is_closing():
                        self._process.stdin.close()
                except Exception:
                    pass

        # stdout/stderr 읽기 루프 (백그라운드 태스크)
        if self._mode == "B":
            self._read_task = asyncio.create_task(self._read_loop_mode_b())
        else:
            self._read_task = asyncio.create_task(self._read_loop())

    async def stop(self) -> None:
        """subprocess 종료 (멱등).

        graceful terminate → 5초 대기 → force kill.
        """
        if self._state in ("idle", "stopping"):
            return

        prev_state = self._state
        self._state = "stopping"
        logger.info(
            "ProcessRunner stopping run_id=%r (was %s)", self._run_id, prev_state
        )

        if self._process and self._process.returncode is None:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except TimeoutError:
                logger.warning("terminate timeout, killing pid=%d", self._pid or -1)
                self._process.kill()
                try:
                    await asyncio.wait_for(self._process.wait(), timeout=3.0)
                except TimeoutError:
                    logger.error("kill timeout pid=%d", self._pid or -1)

        # 읽기 태스크 정리
        if self._read_task and not self._read_task.done():
            self._read_task.cancel()
            try:
                await self._read_task
            except (asyncio.CancelledError, Exception):
                pass

        self._state = "idle"
        self._run_id = None
        self._pid = None
        self._process = None
        self._read_task = None
        self._key = None
        self._sub_key = None
        self._started_at_iso = None
        self._started_monotonic = None
        self._last_prompt_step = None
        self._stdout_tail.clear()
        self._stderr_tail.clear()

    async def write_stdin(self, text: str) -> None:
        """Mode B: 사용자 응답을 subprocess stdin에 쓰기.

        Args:
            text: 입력 텍스트 (개행 없이 전달 — 내부에서 \\n 추가).
        """
        if not self._process or not self._process.stdin:
            logger.warning("write_stdin called but no stdin pipe")
            return
        try:
            data = text if text.endswith("\n") else text + "\n"
            self._process.stdin.write(data.encode("utf-8"))
            await self._process.stdin.drain()
            logger.debug("write_stdin: %r", data.strip())
        except Exception:
            logger.exception("write_stdin 실패")

    def remember_prompt_step(self, step_id: str | None) -> None:
        """Remember the latest interactive prompt step for failure diagnostics."""
        normalized = str(step_id or "").strip()
        if normalized:
            self._last_prompt_step = normalized

    def get_runtime_diagnostics(self) -> dict:
        """Return a compact runtime snapshot for UI/event diagnostics."""
        duration_ms = None
        if self._started_monotonic is not None:
            duration_ms = int(max(0.0, (time.monotonic() - self._started_monotonic) * 1000))

        stdout_tail = list(self._stdout_tail)
        stderr_tail = list(self._stderr_tail)
        return {
            "authority_role": AUTHORITY_ROLE_COMPANION_SNAPSHOT,
            "key": self._key,
            "sub_key": self._sub_key,
            "mode": self._mode,
            "started_at": self._started_at_iso,
            "duration_ms": duration_ms,
            "last_prompt_step": self._last_prompt_step,
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
            "stderr_authoritative": False,
            "stderr_decode_policy": _RUNTIME_STDERR_DECODE_POLICY,
            "failure_phase": self._infer_failure_phase(stdout_tail, stderr_tail),
        }

    def _remember_stdout_line(self, text: str) -> None:
        normalized = str(text or "").strip()
        if normalized:
            self._stdout_tail.append(normalized[:240])

    def _remember_stderr_line(self, text: str) -> None:
        normalized = str(text or "").strip()
        if normalized and not _is_benign_stderr_line(normalized):
            self._stderr_tail.append(normalized[:240])

    def _infer_failure_phase(self, stdout_tail: list[str], stderr_tail: list[str]) -> str:
        if self._last_prompt_step:
            return f"prompt:{self._last_prompt_step}"
        if stderr_tail:
            return "stderr"
        if not stdout_tail:
            return "startup"
        return "runtime"

    # ──────────────────────────────────────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────────────────────────────────────

    async def _read_loop(self) -> None:
        """stdout 줄 단위 수집 + ANSI 제거 + on_line 콜백 호출."""
        proc = self._process
        if not proc or not proc.stdout:
            return

        try:
            while True:
                raw = await proc.stdout.readline()
                if not raw:
                    break  # EOF
                text = _strip_ansi(_decode_runtime_stream(raw))
                if not text:
                    continue
                self._remember_stdout_line(text)
                if self._on_line:
                    try:
                        await self._on_line(text)
                    except Exception:
                        logger.exception("on_line callback error")
        except asyncio.CancelledError:
            return
        except Exception:
            logger.exception("_read_loop error")
        finally:
            # stderr 수집 (나머지 전량, 디버그 로깅)
            if proc.stderr:
                try:
                    stderr_data = await proc.stderr.read()
                    if stderr_data:
                        for line in _decode_runtime_stream(stderr_data).splitlines():
                            stripped = _strip_ansi(line)
                            if stripped:
                                self._remember_stderr_line(stripped)
                                logger.debug("STDERR: %s", stripped[:500])
                except Exception:
                    pass

            # 프로세스 종료 대기 (최대 30초)
            try:
                returncode = await asyncio.wait_for(proc.wait(), timeout=30.0)
            except TimeoutError:
                logger.warning("proc.wait() timeout, killing pid=%d", self._pid or -1)
                try:
                    proc.kill()
                    returncode = await asyncio.wait_for(proc.wait(), timeout=5.0)
                except Exception:
                    returncode = -9
            except Exception:
                returncode = -1

            logger.info(
                "ProcessRunner exited pid=%d returncode=%d run_id=%r",
                self._pid or -1,
                returncode,
                self._run_id,
            )

            # on_exit 콜백
            if self._on_exit:
                try:
                    await self._on_exit(returncode)
                except Exception:
                    logger.exception("on_exit callback error")

            # 상태 초기화 (stop()에서 이미 했을 수도 있음)
            if self._state == "running":
                self._state = "idle"
                self._run_id = None
                self._pid = None

    async def _read_loop_mode_b(self) -> None:
        """Mode B: 청크 기반 읽기 + 프롬프트 감지.

        readline() 대신 read()에 타임아웃을 걸어,
        개행 없이 대기 중인 부분 라인(= input() 프롬프트)을 감지한다.
        """
        from modules.api.prompt_classifier import is_prompt

        proc = self._process
        if not proc or not proc.stdout:
            return

        buffer = ""
        context_lines: list[str] = []  # 최근 N줄 (옵션 추출용)
        max_context = 120

        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(
                        proc.stdout.read(4096),
                        timeout=_PROMPT_DETECT_TIMEOUT,
                    )
                except TimeoutError:
                    # 타임아웃: 버퍼에 남은 텍스트가 프롬프트인지 확인
                    stripped_buf = _strip_ansi(buffer).strip()
                    if stripped_buf and is_prompt(stripped_buf):
                        if self._on_prompt:
                            # 프롬프트 콜백은 사용자 응답까지 대기하므로
                            # await해야 stdin 응답이 완료된 후 다음 읽기로 진행
                            try:
                                await self._on_prompt(stripped_buf, list(context_lines))
                            except Exception:
                                logger.exception("on_prompt callback error")
                        buffer = ""
                        context_lines.clear()  # 이전 메뉴 항목이 다음 프롬프트에 유입되지 않도록 초기화
                    continue

                if not chunk:
                    break  # EOF

                buffer += _decode_runtime_stream(chunk)

                # 완성된 줄 처리
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    text = _strip_ansi(line)
                    if not text:
                        continue
                    self._remember_stdout_line(text)
                    # 컨텍스트 유지
                    context_lines.append(text)
                    if len(context_lines) > max_context:
                        context_lines.pop(0)
                    # on_line 콜백
                    if self._on_line:
                        try:
                            await self._on_line(text)
                        except Exception:
                            logger.exception("on_line callback error")
        except asyncio.CancelledError:
            return
        except Exception:
            logger.exception("_read_loop_mode_b error")
        finally:
            # 잔여 버퍼 처리
            if buffer.strip():
                text = _strip_ansi(buffer)
                if text:
                    self._remember_stdout_line(text)
                if text and self._on_line:
                    try:
                        await self._on_line(text)
                    except Exception:
                        pass

            # stderr 수집
            if proc.stderr:
                try:
                    stderr_data = await proc.stderr.read()
                    if stderr_data:
                        for line in _decode_runtime_stream(stderr_data).splitlines():
                            stripped = _strip_ansi(line)
                            if stripped:
                                self._remember_stderr_line(stripped)
                                logger.debug("STDERR: %s", stripped[:500])
                except Exception:
                    pass

            # 프로세스 종료 대기 (최대 30초)
            try:
                returncode = await asyncio.wait_for(proc.wait(), timeout=30.0)
            except TimeoutError:
                logger.warning("proc.wait(B) timeout, killing pid=%d", self._pid or -1)
                try:
                    proc.kill()
                    returncode = await asyncio.wait_for(proc.wait(), timeout=5.0)
                except Exception:
                    returncode = -9
            except Exception:
                returncode = -1

            logger.info(
                "ProcessRunner(B) exited pid=%d returncode=%d run_id=%r",
                self._pid or -1,
                returncode,
                self._run_id,
            )

            if self._on_exit:
                try:
                    await self._on_exit(returncode)
                except Exception:
                    logger.exception("on_exit callback error")

            if self._state == "running":
                self._state = "idle"
                self._run_id = None
                self._pid = None

    def _build_stdin_sequence(
        self,
        key: str,
        sub_key: str | None,
        inputs: dict | None,
    ) -> str:
        """stdin 시퀀스 빌드 (Mode A: 전량 사전 주입, Mode B: 부트만).

        main_a.py 메뉴 흐름:
            1. 프로젝트 선택 (정수)
            2. 필요 시 장르 불일치 확인 ("y")
            3. 메인 메뉴 키 ("0"~"99")
            4. key="0"일 때 sub_key 선택
            5. 확인 프롬프트 ("y") 패딩  ← Mode A만
            6. 종료 ("5")                ← Mode A만

        inputs dict 키:
            project_index (int): 프로젝트 번호 (기본: 1)
            confirm_count (int): 확인 응답 패딩 수 (기본: 5)
            stdin_lines (list[str]): 완전 오버라이드 (설정 시 나머지 무시)
        """
        inputs = inputs or {}

        # 완전 오버라이드 — 호출측이 stdin 시퀀스를 직접 제어
        if "stdin_lines" in inputs:
            return "\n".join(str(x) for x in inputs["stdin_lines"]) + "\n"

        inject_genre_confirm = _should_inject_boot_genre_confirm(inputs)
        stage0_sub_key = _normalize_public_stage0_sub_key(sub_key) if key == "0" else None

        # Mode B: boot 시퀀스만 사전 주입 (장르→Enter→프로젝트→[필요 시 확인]→메뉴키)
        # stdin은 열어두고, stage-specific 프롬프트만 실시간 감지+UI 처리
        if self._mode == "B":
            lines: list[str] = []
            genre_index = inputs.get("genre_index", 3)
            lines.append(str(genre_index))
            lines.append("")  # [Enter] 프로젝트 선택으로 이동
            project_index = inputs.get("project_index", 1)
            lines.append(str(project_index))
            if inject_genre_confirm:
                lines.append("y")
            if key == "0":
                lines.append("0")
                lines.append(stage0_sub_key)
                if stage0_sub_key == _STAGE0_STYLE_ANALYSIS_SUB_KEY:
                    cache_choice = _resolve_stage0_style_cache_choice(inputs)
                    if cache_choice:
                        lines.append("y")
                        lines.append(cache_choice)
            else:
                lines.append(str(key))
            return "\n".join(lines) + "\n"

        # ── Mode A: 전량 사전 주입 ──
        lines: list[str] = []

        # 1. 장르 선택 (1~10, main_a.py _select_genre)
        genre_index = inputs.get("genre_index", 3)  # 기본: 투자물
        lines.append(str(genre_index))

        # 2. [Enter] 프로젝트 선택으로 이동 (장르 선택 후 확인)
        lines.append("")

        # 3. 프로젝트 선택 (main_a.py _select_project)
        project_index = inputs.get("project_index", 1)
        lines.append(str(project_index))

        # 4. 장르 불일치 확인은 실제 mismatch일 때만 소비
        if inject_genre_confirm:
            lines.append("y")

        # 5. 메인 메뉴 키 + sub_key
        if key == "0":
            lines.append("0")
            lines.append(stage0_sub_key)
            if stage0_sub_key == _STAGE0_STYLE_ANALYSIS_SUB_KEY:
                cache_choice = _resolve_stage0_style_cache_choice(inputs)
                if cache_choice:
                    lines.append("y")
                    lines.append(cache_choice)
        else:
            lines.append(str(key))

        # 6. 확인 응답 패딩 (중간 프롬프트 대응)
        confirm_count = inputs.get("confirm_count", _DEFAULT_CONFIRM_PADDING)
        for _ in range(confirm_count):
            lines.append("y")

        # 7. 종료 (메뉴 복귀 후 깨끗하게 종료)
        lines.append("5")

        return "\n".join(lines) + "\n"

    def _build_env(self, inputs: dict | None) -> dict:
        """subprocess 환경 변수 빌드.

        기본: 현재 환경 + PYTHONIOENCODING=utf-8 + PYTHONUNBUFFERED=1
        inputs에서 API 키, Slack Webhook 등 주입.
        """
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        if isinstance(self._run_id, str) and self._run_id.strip():
            env["GEULDOBI_RUN_ID"] = self._run_id.strip()

        inputs = inputs or {}
        provider_mode = _resolve_provider_mode(inputs)
        env["GEULDOBI_PROVIDER_MODE"] = provider_mode

        if provider_mode != _AMBIENT_PROVIDER_MODE:
            for env_key in _NON_GEMINI_PROVIDER_ENV_KEYS:
                env.pop(env_key, None)

        # Gemini API 키 (기본)
        if inputs.get("api_key"):
            env["GOOGLE_API_KEY"] = inputs["api_key"]

        # 추가 API 키 (쿼터 분산)
        for i in range(2, 10):
            extra = inputs.get(f"api_key_{i}")
            if extra:
                env[f"GOOGLE_API_KEY_{i}"] = extra

        # Slack Webhook
        if inputs.get("slack_webhook"):
            env["SLACK_WEBHOOK_URL"] = inputs["slack_webhook"]

        if provider_mode == _AMBIENT_PROVIDER_MODE:
            # Vertex / Claude / OpenAI passthrough is opt-in only.
            for env_key, input_key in (
                ("VERTEX_API_KEY", "vertex_api_key"),
                ("VERTEX_PROJECT_ID", "vertex_project_id"),
                ("VERTEX_LOCATION", "vertex_location"),
                ("GOOGLE_APPLICATION_CREDENTIALS", "google_credentials_path"),
            ):
                value = inputs.get(input_key)
                if value:
                    env[env_key] = str(value)

            if inputs.get("anthropic_api_key"):
                env["ANTHROPIC_API_KEY"] = inputs["anthropic_api_key"]
                env["CLAUDE_API"] = inputs["anthropic_api_key"]
            if inputs.get("claude_api_key"):
                env["ANTHROPIC_API_KEY"] = inputs["claude_api_key"]
                env["CLAUDE_API"] = inputs["claude_api_key"]

            if inputs.get("openai_api_key"):
                env["OPENAI_API_KEY"] = inputs["openai_api_key"]

        return env
