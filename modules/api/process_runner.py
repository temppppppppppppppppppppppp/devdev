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
    project_index → menu_key → [sub_key] → confirmations → exit(5)
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import subprocess
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

# frozen 모드(PyInstaller): GEULDOBI_ENGINE_ROOT 환경 변수 우선
_ENGINE_ROOT_ENV = os.environ.get("GEULDOBI_ENGINE_ROOT")
PROJECT_ROOT = Path(_ENGINE_ROOT_ENV) if _ENGINE_ROOT_ENV else Path(__file__).resolve().parent.parent.parent

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


# ─── Callback 타입 ────────────────────────────────────────────────────────────

OnLineCallback = Callable[[str], Awaitable[None]]
OnExitCallback = Callable[[int], Awaitable[None]]
OnPromptCallback = Callable[[str, list[str]], Awaitable[None]]

# ─── 기본 확인 응답 패딩 수 ──────────────────────────────────────────────────
_DEFAULT_CONFIRM_PADDING = 5

# ─── Mode B 프롬프트 감지 타임아웃 (초) ──────────────────────────────────────
_PROMPT_DETECT_TIMEOUT = 0.5

# Mode B 대상 키 — 전체 (main_a.py boot 흐름이 인터랙티브)
MODE_B_KEYS = frozenset({"0", "1", "2", "3", "4", "5", "6", "44", "77", "88", "99"})


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

        # frozen 모드: engine.exe 직접 실행 / 개발 모드: python main_a.py
        engine_exe = os.environ.get("GEULDOBI_ENGINE_EXE")
        if engine_exe:
            if not Path(engine_exe).exists():
                self._state = "error"
                logger.error("engine.exe not found at %s", engine_exe)
                raise FileNotFoundError(f"engine.exe not found: {engine_exe}")
        else:
            main_script = PROJECT_ROOT / "main_a.py"
            if not main_script.exists():
                self._state = "error"
                logger.error("main_a.py not found at %s", main_script)
                raise FileNotFoundError(f"main_a.py not found: {main_script}")

        stdin_data = self._build_stdin_sequence(key, sub_key, inputs)
        env = self._build_env(inputs)

        kwargs: dict = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        try:
            # 작업 디렉토리: GEULDOBI_WORKSPACE (배포) 또는 PROJECT_ROOT (개발)
            work_dir = os.environ.get("GEULDOBI_WORKSPACE", str(PROJECT_ROOT))

            if engine_exe:
                # 배포 모드: engine.exe 직접 실행 (소스 비공개 바이너리)
                cmd_args = [engine_exe]
            else:
                # 개발 모드: python -u main_a.py
                python_exe = os.environ.get("GEULDOBI_PYTHON_PATH", sys.executable)
                cmd_args = [python_exe, "-u", str(main_script)]

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
                text = _strip_ansi(raw.decode("utf-8", errors="replace"))
                if not text:
                    continue
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
                        for line in stderr_data.decode(
                            "utf-8", errors="replace"
                        ).splitlines():
                            stripped = _strip_ansi(line)
                            if stripped:
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
                except asyncio.TimeoutError:
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

                buffer += chunk.decode("utf-8", errors="replace")

                # 완성된 줄 처리
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    text = _strip_ansi(line)
                    if not text:
                        continue
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
                        for line in stderr_data.decode(
                            "utf-8", errors="replace"
                        ).splitlines():
                            stripped = _strip_ansi(line)
                            if stripped:
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
            2. 메인 메뉴 키 ("0"~"99")
            3. key="0"일 때 sub_key 선택
            4. 확인 프롬프트 ("y") 패딩  ← Mode A만
            5. 종료 ("5")                ← Mode A만

        inputs dict 키:
            project_index (int): 프로젝트 번호 (기본: 1)
            confirm_count (int): 확인 응답 패딩 수 (기본: 5)
            stdin_lines (list[str]): 완전 오버라이드 (설정 시 나머지 무시)
        """
        inputs = inputs or {}

        # 완전 오버라이드 — 호출측이 stdin 시퀀스를 직접 제어
        if "stdin_lines" in inputs:
            return "\n".join(str(x) for x in inputs["stdin_lines"]) + "\n"

        # Mode B: boot 시퀀스만 사전 주입 (장르→Enter→프로젝트→확인→메뉴키)
        # stdin은 열어두고, stage-specific 프롬프트만 실시간 감지+UI 처리
        if self._mode == "B":
            lines: list[str] = []
            genre_index = inputs.get("genre_index", 3)
            lines.append(str(genre_index))
            lines.append("")  # [Enter] 프로젝트 선택으로 이동
            project_index = inputs.get("project_index", 1)
            lines.append(str(project_index))
            # 장르 불일치 확인("y")은 조건부 input()이므로 boot에 포함하지 않음.
            # 불일치 발생 시 Mode B 프롬프트 감지가 처리한다.
            if key == "0" and sub_key:
                lines.append("0")
                lines.append(str(sub_key))
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

        # 4. 장르 불일치 확인 (기존 프로젝트와 장르가 다를 때 y/n)
        lines.append("y")

        # 5. 메인 메뉴 키 + sub_key
        if key == "0" and sub_key:
            lines.append("0")
            lines.append(str(sub_key))
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

        inputs = inputs or {}

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

        return env
