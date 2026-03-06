"""
스파이크 2: subprocess stdin/stdout 제어 검증

목적:
  main_a.py를 PIPE 기반으로 숨김 기동하고,
  stdin으로 대화형 흐름을 제어해 종료 메시지를 수신할 수 있는지 확인.

판정 기준:
  main_a.py 기동 → 장르/프로젝트 선택 → stdin "5\\n" → 종료 메시지 수신
  → "SPIKE-2 PASS" 출력

실행:
  cd 글도비루트
  python spikes/subprocess/spike_subprocess.py

참조:
  docs/2026-03-06/P0_스파이크_실행오더.md §스파이크 2
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from queue import Empty, Queue

# Windows: 터미널 CP949 → UTF-8 재설정 (이모지 출력 보장)
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf8"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── 경로 ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent   # 글도비 루트
MAIN_A = ROOT / "main_a.py"

# ── 타임아웃 설정 ────────────────────────────────────────────────────────────
TIMEOUT_TOTAL    = 200   # 전체 최대 실행 시간 (초) — MagicMock 에이전트 초기화 포함
STEP_COOLDOWN    = 1.5   # 입력 전송 후 재감지 방지 쿨다운 (초)

# ── 입력 시퀀스 ─────────────────────────────────────────────────────────────
# 각 항목: (감지 패턴 list, 전송 문자열, 설명, 단계별_max_wait초)
# 패턴이 stdout 라인에 포함되면 해당 입력을 전송.
# max_wait 내 미감지 시 강제 전송.
STEPS: list[tuple[list[str], str, str, float]] = [
    # 1. 장르 선택: "✏️ Choice ..." 프롬프트 감지 (buffering으로 늦게 나타남 → force-send)
    (["Choice (1.무협", "✏️ Choice"],        "\n",   "장르 선택 — Enter = 기본(무협)",        30.0),
    # 2. 장르 선택 완료 후 [Enter] 로 프로젝트 목록 진입
    (["프로젝트 선택으로 이동", "[Enter]"],   "\n",   "프로젝트 목록 진입 — Enter",            15.0),
    # 3. 프로젝트 목록 "👉 Choice:" → 1번 선택
    (["👉 Choice"],                           "1\n",  "프로젝트 1번 선택",                     20.0),
    # 4. 부팅 후 메인 메뉴 — "Exit" 또는 "Stage 4" 또는 메뉴 입력 프롬프트
    (["5. Exit", "Stage 4", "👇 Select", "👉 Choice"],  "5\n",  "메인 메뉴 → 5(Exit)",   120.0),
]

# ── 판정 패턴 ────────────────────────────────────────────────────────────────
PASS_SIGNALS = [
    "종료 완료",         # _shutdown_app() 마지막 메시지
    "종료 시퀀스",       # "🛑 [System] 시스템 종료 시퀀스 가동..."
]

TERMINAL_FAIL_SIGNALS = [
    "프로젝트가 없습니다",  # project 폴더 비어 있음
]

# ── stdout 리더 스레드 ───────────────────────────────────────────────────────

def _reader(proc: subprocess.Popen, q: Queue[str | None]) -> None:
    """proc.stdout을 라인 단위로 읽어 큐에 넣는다."""
    try:
        assert proc.stdout is not None
        for line in iter(proc.stdout.readline, ""):
            q.put(line)
    except Exception:
        pass
    finally:
        q.put(None)  # EOF sentinel


# ── 메인 스파이크 로직 ───────────────────────────────────────────────────────

def _match(line: str, patterns: list[str]) -> bool:
    return any(p in line for p in patterns)


def run_spike() -> str:
    """
    Returns:
        "PASS"       — 종료 메시지 확인
        "TIMEOUT"    — 전체 타임아웃
        "FAIL:<msg>" — 치명 오류 감지
        "ERROR:<msg>"— 스파이크 자체 오류
    """
    if not MAIN_A.exists():
        return f"ERROR:main_a.py not found at {MAIN_A}"

    env = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1",
        # Rich 강제 비-TTY 모드 (markup 제거, 화면 지우기 억제)
        "TERM": "dumb",
        "NO_COLOR": "1",
    }

    print(f"[SPIKE-2] Popen: {sys.executable} {MAIN_A}", flush=True)

    try:
        proc = subprocess.Popen(
            [sys.executable, str(MAIN_A)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
            errors="replace",
            env=env,
            cwd=str(ROOT),
        )
    except Exception as e:
        return f"ERROR:Popen failed: {e}"

    q: Queue[str | None] = Queue()
    reader = threading.Thread(target=_reader, args=(proc, q), daemon=True)
    reader.start()

    step_idx   = 0
    all_lines: list[str] = []
    deadline   = time.monotonic() + TIMEOUT_TOTAL
    last_send  = time.monotonic() - STEP_COOLDOWN   # 즉시 전송 허용
    # 첫 단계의 step_deadline
    step_deadline = time.monotonic() + STEPS[0][3]

    try:
        while time.monotonic() < deadline:

            # 프로세스 먼저 종료 시 남은 큐 소진
            if proc.poll() is not None:
                while True:
                    try:
                        line = q.get_nowait()
                    except Empty:
                        break
                    if line is None:
                        break
                    all_lines.append(line)
                    sys.stdout.write(f"  {line}")
                sys.stdout.flush()
                break

            try:
                line = q.get(timeout=0.3)
            except Empty:
                # 단계별 타임아웃: 패턴 없이 max_wait 초과 → 강제 전송
                if (step_idx < len(STEPS)
                        and time.monotonic() > step_deadline
                        and time.monotonic() - last_send >= STEP_COOLDOWN):
                    _, send, desc, _ = STEPS[step_idx]
                    print(f"[SPIKE-2] ⚠ step[{step_idx}] 강제 전송 (패턴 미감지): {desc} → {send!r}",
                          flush=True)
                    assert proc.stdin is not None
                    proc.stdin.write(send)
                    proc.stdin.flush()
                    last_send = time.monotonic()
                    step_idx += 1
                    if step_idx < len(STEPS):
                        step_deadline = time.monotonic() + STEPS[step_idx][3]
                continue

            if line is None:
                break   # EOF

            all_lines.append(line)
            sys.stdout.write(f"  {line}")
            sys.stdout.flush()

            recent = "".join(all_lines[-50:])

            # ── 1. PASS 감지 ────────────────────────────────────────────
            for sig in PASS_SIGNALS:
                if sig in recent:
                    return "PASS"

            # ── 2. 치명 실패 감지 ───────────────────────────────────────
            for sig in TERMINAL_FAIL_SIGNALS:
                if sig in line:
                    return f"FAIL:{sig}"

            # ── 3. 입력 시퀀스 처리 ────────────────────────────────────
            if step_idx < len(STEPS):
                patterns, send, desc, max_wait = STEPS[step_idx]
                now = time.monotonic()
                if _match(line, patterns) and (now - last_send) >= STEP_COOLDOWN:
                    print(f"[SPIKE-2] ✓ step[{step_idx}] {desc} → {send!r}", flush=True)
                    assert proc.stdin is not None
                    proc.stdin.write(send)
                    proc.stdin.flush()
                    last_send = now
                    step_idx += 1
                    if step_idx < len(STEPS):
                        step_deadline = time.monotonic() + STEPS[step_idx][3]

    finally:
        try:
            proc.kill()
            proc.wait(timeout=5)
        except Exception:
            pass

    return "TIMEOUT"


# ── 엔트리포인트 ─────────────────────────────────────────────────────────────

def main() -> None:
    banner = "=" * 60
    print(banner)
    print("SPIKE-2: subprocess stdin/stdout 제어 검증")
    print(f"대상: {MAIN_A}")
    print(f"Python: {sys.version.split()[0]}")
    print(banner)
    print()

    t0 = time.monotonic()
    verdict = run_spike()
    elapsed = time.monotonic() - t0

    print()
    print(banner)
    print(f"경과: {elapsed:.1f}초")

    if verdict == "PASS":
        print("SPIKE-2 PASS")
        sys.exit(0)
    elif verdict == "TIMEOUT":
        print("SPIKE-2 TIMEOUT")
        print("→ 패턴 미감지 또는 프로세스 초기화 지연")
        print("→ 대안: INTER_STEP_MAX 증가 또는 mock_main.py 사용")
        sys.exit(1)
    elif verdict.startswith("FAIL:"):
        print(f"SPIKE-2 FAIL — {verdict[5:]}")
        sys.exit(1)
    else:
        print(f"SPIKE-2 ERROR — {verdict}")
        sys.exit(1)

    print(banner)


if __name__ == "__main__":
    main()
