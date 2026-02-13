"""
[V63.4] Bridge Runner - 파일 기반 Selenium 자동화
[LITE-V1] StateLedger 통합
==================================================
DB 없음. JSON 없음. 순수 파일 I/O + Selenium.

3단계 파이프라인: 분배표 → Blueprint → 원고
- Stage 2: 블록 → 화별 분배표 (경량)
- Stage 3: 분배표 + 원본 블록 → Blueprint (씬 설계)
- Stage 4: Blueprint → 원고

프로젝트 구조:
  projects/{name}/
    bible.txt           ← 세계관 설정 (선택)
    style_guide.txt     ← 문체 가이드 (선택)
    treatment/          ← 줄거리 블록 (block_001.txt, ...)
    stage2/             ← 화별 분배표 출력
    stage3/             ← 에피소드 Blueprint 출력
    stage4/             ← 원고 출력
    _config.json        ← 설정 (ep_per_arc 등)
"""

import json
import math
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from bridge.gemini_driver import GeminiDriver
from bridge.prompt_builder import GENRE_PRESETS, PromptBuilder
from bridge.state_ledger import StateLedger

# ── Pro 제한 감지 예외 ─────────────────────────────────────


class ProLimitStop(Exception):
    """Pro 모델 제한 감지 시 스테이지 루프를 중단하는 예외"""

    pass


# ── 스피너 (Claude Code 스타일) ────────────────────────────

# Windows ANSI 지원 활성화
import os as _os

_os.system("")

_active_spinner = None  # 현재 활성 스피너 (log()에서 참조)


class Spinner:
    """Claude Code 스타일 braille 스피너 — 항상 맨 아래 줄에만 표시.

    사용법:
        with Spinner("분배표 생성 중", current=3, total=50) as sp:
            sp.update("제5화 Blueprint", current=5)
    """

    _FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    # ANSI 색상 (256-color)
    _ORANGE = "\033[38;5;208m"  # 주황
    _AMBER = "\033[38;5;214m"  # 호박색 (밝은 주황)
    _GOLD = "\033[38;5;220m"  # 골드
    _PEACH = "\033[38;5;216m"  # 피치
    _DIM = "\033[2m"
    _DIM_GRAY = "\033[38;5;240m"  # 어두운 회색
    _BOLD = "\033[1m"
    _RESET = "\033[0m"
    _WHITE = "\033[97m"

    def __init__(self, message: str = "", current: int = 0, total: int = 0):
        self.message = message
        self.current = current
        self.total = total
        self._stop = threading.Event()
        self._thread = None
        self._start_time = 0

    def update(self, message: str = "", current: int = -1):
        """메시지/진행률 실시간 갱신"""
        if message:
            self.message = message
        if current >= 0:
            self.current = current

    def __enter__(self):
        global _active_spinner
        _active_spinner = self
        self._start_time = time.time()
        self._stop.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_):
        global _active_spinner
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)
        _active_spinner = None
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()

    @staticmethod
    def _fmt_time(seconds: int) -> str:
        if seconds < 60:
            return f"{seconds}s"
        m, s = divmod(seconds, 60)
        return f"{m}m {s}s"

    @staticmethod
    def _breath_rgb(t: float) -> str:
        """sin 파형으로 주황 breathing — 어두운 주황 ↔ 밝은 골드 순환.
        t: 0~2π 주기의 시간값
        반환: \\033[38;2;R;G;Bm ANSI RGB 시퀀스
        """
        # sin: -1~1 → 0~1
        s = (math.sin(t) + 1) / 2
        # 어두운 주황(180,100,20) ↔ 밝은 골드(255,200,80)
        r = int(180 + 75 * s)
        g = int(100 + 100 * s)
        b = int(20 + 60 * s)
        return f"\033[38;2;{r};{g};{b}m"

    def _spin(self):
        O = self._ORANGE
        A = self._AMBER
        G = self._GOLD
        DG = self._DIM_GRAY
        B = self._BOLD
        R = self._RESET
        idx = 0

        while not self._stop.is_set():
            elapsed = int(time.time() - self._start_time)
            fi = idx % len(self._FRAMES)
            frame = self._FRAMES[fi]

            # breathing 색상 (스피너 + 메시지 동기화)
            t = idx * 0.25  # 속도 조절 (낮을수록 느리게 숨쉬기)
            bc = self._breath_rgb(t)

            # 진행률 바
            prog = ""
            if self.total > 0:
                pct = self.current / self.total
                pct_i = int(pct * 100)
                bar_len = 24
                filled = int(bar_len * pct)

                # 채워진 부분: 주황 그라데이션
                bar_str = ""
                for bi in range(filled):
                    if bi < filled // 3:
                        bar_str += f"{O}━{R}"
                    elif bi < filled * 2 // 3:
                        bar_str += f"{A}━{R}"
                    else:
                        bar_str += f"{G}━{R}"
                bar_str += f"{DG}{'─' * (bar_len - filled)}{R}"

                prog = f"  {bar_str} {A}{self.current}{DG}/{self.total}{R} {DG}({R}{G}{pct_i}%{R}{DG}){R}"

            time_str = f"{DG}{self._fmt_time(elapsed)}{R}"
            line = f"\r  {bc}{B}{frame} {self.message}{R}{prog}  {time_str}"

            sys.stdout.write(f"{line}\033[K")
            sys.stdout.flush()

            idx += 1
            self._stop.wait(0.12)


# ── 디렉터 프롬프트 ───────────────────────────────────────

DIRECTOR_PROMPT = """★★★ [절대 규칙] ★★★
인사말/사족 없이 아래 형식만 출력.

방금 생성한 결과물을, 첨부된 컨텍스트(세계관/이전 결과물)와 대조하여 평가하라.

[중점 평가 — 모순/일관성 위주]
1. 모순 검사: 이전 결과물/세계관과 캐릭터·사건·설정에 모순이 있는가
2. 이름/고유명사: Bible의 이름·칭호·지명을 정확히 사용했는가
3. 연속성: 직전 결과물의 마지막 상황에서 자연스럽게 이어지는가
4. 누락: 요청된 요소(씬/사건/성장) 중 빠뜨린 것이 있는가
5. 시간선: 사건 순서나 시점에 앞뒤가 맞는가
6. 블록 일치: 첨부된 줄거리 블록/분배표의 내용과 생성 결과가 일치하는가 (전혀 다른 이야기·캐릭터·장르가 생성되었으면 0점 처리)
7. 사망 NPC: 컨텍스트의 [세계 상태]에서 사망으로 표시된 NPC가 등장하면 즉시 0점

[출력 형식 - 반드시 이 형식만]
모순: (발견된 모순 항목. 없으면 "없음")
누락: (빠뜨린 요소. 없으면 "없음")
이름오류: (잘못된 고유명사. 없으면 "없음")
블록불일치: (첨부 블록과 다른 내용이면 구체적으로 기재. 없으면 "없음")
사망NPC위반: (사망 NPC가 등장했으면 이름과 사망화수 기재. 없으면 "없음")
점수: (0~100 정수)
판정: PASS 또는 REVISE"""

REVISION_PROMPT = """★★★ [절대 규칙 - 어기면 응답 무효] ★★★
1. 인사말/사족 없이 수정된 결과물'만' 출력.
2. 절대로 분량을 줄이지 마라. 원본과 동일하거나 더 긴 분량.
3. 생략/요약/축약 절대 금지. "위와 같음", "이하 동일", "..." 등 금지.
4. 처음부터 끝까지 전체를 완전히 다시 작성.

위 평가에서 지적된 모순/누락/이름오류를 수정하여,
결과물을 처음부터 끝까지 전부 다시 작성하라.
출력 형식은 이전과 동일. 분량은 이전과 동일하거나 더 길게."""

CONTRADICTION_CHECK_PROMPT = """★★★ [절대 규칙] ★★★
인사말/사족 없이 아래 형식만 출력.

방금 생성한 결과물을, 컨텍스트에 포함된 '최근 10화 분량'과 대조하여
교차 모순만 집중 검사하라.

[중점 검사]
1. 씬 중복: 이전 화에서 이미 발생한 전투/사건이 반복되지 않았는가
2. 공간 모순: 장소/위치 설정이 이전 화와 충돌하지 않는가
3. 인물 상태: 부상/사망/위치가 이전 화 종료 상태와 일치하는가
4. 아이템 연속성: 소지품/능력치가 이전 화와 맞는가
5. 시간선: 사건의 시간 순서가 논리적인가

[출력 형식]
씬중복: (발견된 중복. 없으면 "없음")
공간모순: (발견된 모순. 없으면 "없음")
인물상태: (불일치 사항. 없으면 "없음")
아이템: (불일치 사항. 없으면 "없음")
시간선: (오류. 없으면 "없음")
점수: (0~100 정수)
판정: PASS 또는 REVISE"""

REVALIDATION_DIRECTOR_PROMPT = """★★★ [절대 규칙] ★★★
인사말/사족 없이 아래 형식만 출력.

첨부 파일의 하단에 있는 [평가 대상 결과물]을, 상단의 컨텍스트(세계관/이전 결과물)와 대조하여 평가하라.

[중점 평가 — 모순/일관성 위주]
1. 모순 검사: 컨텍스트와 캐릭터·사건·설정에 모순이 있는가
2. 이름/고유명사: Bible의 이름·칭호·지명을 정확히 사용했는가
3. 연속성: 직전 결과물의 마지막 상황에서 자연스럽게 이어지는가
4. 누락: 요청된 요소(씬/사건/성장) 중 빠뜨린 것이 있는가
5. 시간선: 사건 순서나 시점에 앞뒤가 맞는가
6. 블록 일치: 첨부된 줄거리 블록/분배표의 내용과 생성 결과가 일치하는가 (전혀 다른 이야기·캐릭터·장르가 생성되었으면 0점 처리)
7. 사망 NPC: 컨텍스트의 [세계 상태]에서 사망으로 표시된 NPC가 등장하면 즉시 0점

[출력 형식 - 반드시 이 형식만]
모순: (발견된 모순 항목. 없으면 "없음")
누락: (빠뜨린 요소. 없으면 "없음")
이름오류: (잘못된 고유명사. 없으면 "없음")
블록불일치: (첨부 블록과 다른 내용이면 구체적으로 기재. 없으면 "없음")
사망NPC위반: (사망 NPC가 등장했으면 이름과 사망화수 기재. 없으면 "없음")
점수: (0~100 정수)
판정: PASS 또는 REVISE"""


# ── 컬러 로그 (Claude Code 스타일) ──────────────────────────


class _C:
    """ANSI 256-color 팔레트"""

    ORANGE = "\033[38;5;208m"
    AMBER = "\033[38;5;214m"
    GOLD = "\033[38;5;220m"
    GREEN = "\033[38;5;114m"
    RED = "\033[38;5;203m"
    YELLOW = "\033[38;5;221m"
    CYAN = "\033[38;5;117m"
    BLUE = "\033[38;5;111m"
    GRAY = "\033[38;5;243m"
    DIM = "\033[38;5;240m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


# 태그별 색상 매핑 (긴 태그 우선 — 순서 중요)
_TAG_COLORS = [
    ("[Director]", _C.AMBER, "⬡"),
    ("[TIMEOUT]", _C.RED, "⏱"),
    ("[EMPTY]", _C.RED, "∅"),
    ("[SKIP]", _C.YELLOW, "⊘"),
    ("[FAIL]", _C.RED, "✗"),
    ("[OK]", _C.GREEN, "✓"),
    ("[CTX]", _C.DIM, "◈"),
    ("[검증]", _C.CYAN, "◇"),
    ("[삭제]", _C.DIM, "✕"),
    ("[리셋]", _C.DIM, "↺"),
    ("[모델]", _C.DIM, "◆"),
    ("[!]", _C.YELLOW, "⚠"),
]


def log(msg):
    R = _C.RESET

    # 스피너가 돌고 있으면 그 줄을 지운 뒤 로그 출력
    if _active_spinner:
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()

    ts = f"{_C.DIM}{datetime.now().strftime('%H:%M:%S')}{R}"

    # 태그 감지 → 아이콘 + 색상 적용
    colored_msg = None
    for tag, color, icon in _TAG_COLORS:
        if tag in msg:
            # 태그 앞뒤 분리
            before, _, after = msg.partition(tag)
            colored_msg = f"{color}{before}{_C.BOLD}{icon}  {tag}{R}{color}{after}{R}"
            break

    if colored_msg is None:
        colored_msg = f"{_C.WHITE}{msg}{R}"

    # 숫자+단위 강조
    colored_msg = re.sub(
        r"(\d[\d,]*)(자|점|초|바이트|화|개|%)",
        lambda m: f"{_C.BOLD}{_C.WHITE}{m.group(1)}{R}{_C.DIM}{m.group(2)}{R}",
        colored_msg,
    )

    print(f"  {ts} {colored_msg}", flush=True)


class BridgeRunner:
    """파일 기반 Selenium 자동화 Bridge Runner"""

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.driver = None
        self.prompt = PromptBuilder()

        # 경로
        self.bible_path = self.project_dir / "bible.txt"
        self.style_path = self.project_dir / "style_guide.txt"
        self.treatment_dir = self.project_dir / "treatment"
        self.stage2_dir = self.project_dir / "stage2"
        self.stage3_dir = self.project_dir / "stage3"
        self.stage4_dir = self.project_dir / "stage4"
        self.config_path = self.project_dir / "_config.json"

        # [LITE-V1] 세계 상태 추적
        self.ledger = StateLedger(self.project_dir)

    # ── 헬퍼 ─────────────────────────────────────────────

    def _read(self, p: Path) -> str:
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def _output_files(self, directory: Path, prefix: str) -> list:
        """출력 파일만 반환 (_context/_history 파일 제외)"""
        return sorted(
            [f for f in directory.glob(f"{prefix}*.txt") if "_context" not in f.name and "_history" not in f.name]
        )

    def _save_config(self, data: dict):
        existing = {}
        if self.config_path.exists():
            try:
                existing = json.loads(self.config_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        existing.update(data)
        self.config_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_config(self) -> dict:
        if self.config_path.exists():
            try:
                return json.loads(self.config_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _load_metadata(self, stage_dir: Path) -> dict:
        """스테이지 메타데이터 로드"""
        meta_path = stage_dir / "_metadata.json"
        if meta_path.exists():
            try:
                return json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_metadata_entry(self, stage_dir: Path, filename: str, entry: dict):
        """단일 파일의 메타데이터 추가/갱신"""
        meta = self._load_metadata(stage_dir)
        meta[filename] = entry
        meta_path = stage_dir / "_metadata.json"
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    def _init_driver(self, hide: bool = False):
        if not self.driver:
            cfg = self._load_config()
            model = cfg.get("model", "pro")
            log(f"Gemini 드라이버 연결 중... (모델: {model})")
            self.driver = GeminiDriver(model=model, hide=hide, log_func=log, cache_dir=self.project_dir.parent.parent)
            # project_dir = projects/조상님/
            # .parent     = projects/
            # .parent.parent = test_mode/ (.env 위치)
            state = "Chrome 창 숨김" if hide else "Chrome 창 표시"
            log(f"연결 성공! ({state})")

    # ── 누적 히스토리 (스테이지별 참고 컨텍스트) ──────────

    def _append_history(self, stage_dir: Path, label: str, text: str):
        """응답을 누적 히스토리에 추가"""
        hist = stage_dir / "_history.txt"
        with open(hist, "a", encoding="utf-8") as f:
            f.write(f"\n--- {label} ---\n{text}\n")

    def _read_history(self, stage_dir: Path, max_entries: int = 5) -> str:
        """누적 히스토리 읽기 — 최근 N개 항목만 반환.

        전체 히스토리는 _history.txt에 보존되지만,
        컨텍스트에는 최근 5개만 포함하여 크기를 제한한다.
        """
        hist = stage_dir / "_history.txt"
        if not hist.exists():
            return ""
        text = hist.read_text(encoding="utf-8").strip()
        # "--- 제XX화 ... ---" 구분자로 분리, 최근 N개만
        parts = re.split(r"\n(?=--- )", text)
        if len(parts) > max_entries:
            parts = parts[-max_entries:]
        return "\n".join(parts)

    def _collect_prev(
        self,
        directory: Path,
        pattern: str,
        current: int,
        count: int = 10,
        max_chars: int = 1500,
        header_fmt: str = "[#{n}]",
    ) -> str:
        """최근 N개 파일 수집 → 합본 문자열 반환.

        Args:
            directory: 파일이 있는 디렉토리
            pattern: 파일명 패턴 (예: "arc_{n:03d}.txt", "ep_{n:04d}.txt")
            current: 현재 번호 (이 번호 직전까지 수집)
            count: 최대 수집 개수
            max_chars: 각 파일당 최대 글자 수 (뒤에서 잘라냄)
            header_fmt: 각 파일 헤더 포맷 ({n}이 번호로 치환됨)
        Returns:
            합본된 문자열. 파일이 하나도 없으면 빈 문자열.
        """
        parts = []
        start = max(1, current - count)
        for n in range(start, current):
            path = directory / pattern.format(n=n)
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            if len(text) > max_chars:
                text = text[-max_chars:]
            header = header_fmt.format(n=n)
            parts.append(f"{header}\n{text}")
        return "\n\n".join(parts)

    def _get_int(self, prompt_text, default, lo, hi):
        while True:
            raw = input(prompt_text).strip()
            if not raw:
                return default
            try:
                v = int(raw)
                if lo <= v <= hi:
                    return v
            except ValueError:
                pass
            print(f"    {lo}~{hi} 범위 입력")

    # ── 디렉터 (같은 세션에서 텍스트만 전송) ────────────

    def _director_check(self, label: str) -> tuple:
        """디렉터 평가 → (통과여부, 전체응답, 점수)"""
        m = None
        resp = ""
        for _try in range(3):
            resp = self.driver.send_prompt(DIRECTOR_PROMPT)
            if resp.startswith("[TIMEOUT]") or resp.startswith("[EMPTY]"):
                log(f"[Director] {label}: 응답 실패 → 새 세션 ({_try + 1}/3)")
                self.driver.new_chat()
                time.sleep(3)
                continue
            m = re.search(r"점수\s*[:：]\s*(\d+)", resp)
            if m:
                break
            log(f"[Director] {label}: 점수 파싱 실패 → 새 세션 ({_try + 1}/3)")
            self.driver.new_chat()
            time.sleep(3)
        if not m:
            log(f"[Director] {label}: 3회 실패 → 자동 통과 (0점)")
            return True, resp, 0

        score = int(m.group(1))

        # 판정 파싱 (PASS/REVISE)
        verdict = "PASS" if score >= 90 else "REVISE"
        vm = re.search(r"판정\s*[:：]\s*(PASS|REVISE)", resp)
        if vm:
            verdict = vm.group(1)

        # 구조화 로그
        for field in ["모순", "누락", "이름오류", "블록불일치", "사망NPC위반"]:
            fm = re.search(rf"{field}\s*[:：]\s*(.+?)(?:\n|$)", resp)
            if fm and fm.group(1).strip() not in ("없음", "없음."):
                log(f"[Director] {field}: {fm.group(1).strip()[:80]}")

        return verdict == "PASS", resp, score

    def _director_revision(self) -> str:
        """디렉터 피드백 기반 수정 요청 → 수정본 반환"""
        resp = self.driver.send_prompt(REVISION_PROMPT)
        if resp.startswith("[TIMEOUT]") or resp.startswith("[EMPTY]"):
            return ""
        return resp

    def _contradiction_check(self, label: str) -> tuple:
        """교차 모순 검사 → (통과여부, 응답, 점수)"""
        m = None
        resp = ""
        for _try in range(3):
            resp = self.driver.send_prompt(CONTRADICTION_CHECK_PROMPT)
            if resp.startswith("[TIMEOUT]") or resp.startswith("[EMPTY]"):
                log(f"[Director·교차] {label}: 응답 실패 → 재시도 ({_try + 1}/3)")
                self.driver.new_chat()
                time.sleep(3)
                continue
            m = re.search(r"점수\s*[:：]\s*(\d+)", resp)
            if m:
                break
            log(f"[Director·교차] {label}: 점수 파싱 실패 → 재시도 ({_try + 1}/3)")
            self.driver.new_chat()
            time.sleep(3)
        if not m:
            log(f"[Director·교차] {label}: 3회 실패 → 자동 통과 (0점)")
            return True, resp, 0

        score = int(m.group(1))

        verdict = "PASS" if score >= 90 else "REVISE"
        vm = re.search(r"판정\s*[:：]\s*(PASS|REVISE)", resp)
        if vm:
            verdict = vm.group(1)

        # 구조화 로그
        for field in ["씬중복", "공간모순", "인물상태", "아이템", "시간선"]:
            fm = re.search(rf"{field}\s*[:：]\s*(.+?)(?:\n|$)", resp)
            if fm and fm.group(1).strip() not in ("없음", "없음."):
                log(f"[Director·교차] {field}: {fm.group(1).strip()[:80]}")

        return verdict == "PASS", resp, score

    @staticmethod
    def _trim_context(ctx_text: str, max_bytes: int = 80_000) -> str:
        """컨텍스트에서 누적 히스토리 제거 → 경량화.

        구조: Bible + 블록/분배표 + (직전 결과물) + [누적 히스토리]
        누적 히스토리만 잘라내고, 그래도 크면 뒤에서부터 자름.
        """
        # 누적 히스토리 섹션 마커들
        markers = [
            "[이전 분배표 누적",
            "[이전 Blueprint 누적",
            "[이전 원고 누적",
        ]
        for marker in markers:
            idx = ctx_text.find(marker)
            if idx > 0:
                # 마커 앞의 구분선(===)도 제거
                cut = ctx_text.rfind("=" * 50, 0, idx)
                if cut > 0:
                    ctx_text = ctx_text[:cut].rstrip()
                else:
                    ctx_text = ctx_text[:idx].rstrip()

        # 그래도 크면 뒤에서부터 자름 (Bible은 앞에 있으므로 보존)
        if len(ctx_text.encode("utf-8")) > max_bytes:
            while len(ctx_text.encode("utf-8")) > max_bytes:
                ctx_text = ctx_text[: len(ctx_text) - 5000]
            ctx_text = ctx_text.rstrip() + "\n\n[...컨텍스트 일부 생략...]"

        return ctx_text

    def _revalidate_single(self, ctx_path: Path, output_path: Path, label: str) -> dict:
        """단일 파일 재검증: 컨텍스트+출력 합본 → Director 평가"""
        ctx_text = self._read(ctx_path)
        output_text = self._read(output_path)

        if not output_text:
            return {
                "file": output_path.name,
                "score": 0,
                "passed": False,
                "details": "출력 파일 비어있음",
                "model": "N/A",
            }

        # 누적 히스토리 제거하여 경량화
        ctx_trimmed = self._trim_context(ctx_text)
        orig_kb = len(ctx_text.encode("utf-8")) // 1024
        trim_kb = len(ctx_trimmed.encode("utf-8")) // 1024
        if orig_kb != trim_kb:
            log(f"[CTX] 경량화 {orig_kb}KB → {trim_kb}KB")

        combined_text = (
            f"{ctx_trimmed}\n\n"
            f"{'=' * 50}\n"
            f"[평가 대상 결과물 — 아래 내용을 위 컨텍스트와 대조하여 평가하라]\n"
            f"{'=' * 50}\n\n"
            f"{output_text}"
        )
        combined_path = output_path.parent / "_reval_temp.txt"
        combined_path.write_text(combined_text, encoding="utf-8")

        try:
            resp = self.driver.send_with_file(str(combined_path), REVALIDATION_DIRECTOR_PROMPT)

            if resp.startswith("[TIMEOUT]") or resp.startswith("[EMPTY]"):
                return {
                    "file": output_path.name,
                    "score": 0,
                    "passed": False,
                    "details": resp,
                    "model": self.driver.get_current_model(),
                }

            # 점수 파싱 (최대 3회 재시도)
            m = None
            for _try in range(3):
                m = re.search(r"점수\s*[:：]\s*(\d+)", resp)
                if m:
                    break
                log(f"[Director] {label}: 점수 파싱 실패 → 재시도")
                resp = self.driver.send_prompt(REVALIDATION_DIRECTOR_PROMPT)

            if not m:
                return {
                    "file": output_path.name,
                    "score": 0,
                    "passed": False,
                    "details": "점수 파싱 실패",
                    "model": self.driver.get_current_model(),
                }

            score = int(m.group(1))
            verdict = "PASS" if score >= 90 else "REVISE"
            vm = re.search(r"판정\s*[:：]\s*(PASS|REVISE)", resp)
            if vm:
                verdict = vm.group(1)

            details_parts = []
            for field in ["모순", "누락", "이름오류", "블록불일치", "사망NPC위반"]:
                fm = re.search(rf"{field}\s*[:：]\s*(.+?)(?:\n|$)", resp)
                if fm and fm.group(1).strip() not in ("없음", "없음."):
                    detail = fm.group(1).strip()[:80]
                    details_parts.append(f"{field}: {detail}")
                    log(f"[Director] {field}: {detail}")

            passed = verdict == "PASS"
            model = self.driver.get_current_model()
            log(f"[Director] {label}: {score}점 {verdict} ({model})")

            return {
                "file": output_path.name,
                "score": score,
                "passed": passed,
                "details": "; ".join(details_parts) if details_parts else "이상 없음",
                "model": model,
            }
        finally:
            if combined_path.exists():
                combined_path.unlink()

    def _validate_revision(self, original: str, revised: str) -> bool:
        """수정본 유사도 검증 — 생략/개소리 감지"""
        # 1) 길이 체크: 원본의 70% 미만이면 생략
        if len(revised) < len(original) * 0.7:
            log(f"[검증] 수정본 너무 짧음 ({len(revised)}자 < 원본 {len(original)}자의 70%)")
            return False

        # 2) 구조 보존: ## 섹션 헤딩이 있는 경우, 절반 이상 보존되어야
        orig_heads = set(re.findall(r"^##\s+.+", original, re.MULTILINE))
        if orig_heads:
            rev_heads = set(re.findall(r"^##\s+.+", revised, re.MULTILINE))
            overlap = len(orig_heads & rev_heads)
            if overlap < len(orig_heads) * 0.5:
                log(f"[검증] 구조 불일치 (원본 섹션 {len(orig_heads)}개 중 {overlap}개만 보존)")
                return False

        # 3) 생략 패턴 감지
        skip_patterns = [
            r"위와\s*같음",
            r"이하\s*동일",
            r"이하\s*생략",
            r"상동",
            r"\(생략\)",
            r"\.{3,}.*생략",
        ]
        for p in skip_patterns:
            if re.search(p, revised):
                log(f"[검증] 생략 패턴 감지: {p}")
                return False

        return True

    # ── Layer 1: 세정 (저장 전 잡음 제거) ─────────────────

    _UI_RESIDUE = [
        "업로드 용량이 너무 커서 최상의 결과를 얻지 못할 수 있습니다.",
        "자세히 알아보기",
        "새 창에서 열기",
    ]
    _HEAD_NOISE = {"생각하는 과정 표시", "단계별 사고", "thinking process"}

    def _sanitize(self, text: str) -> str:
        """응답에서 Gemini UI 잔재·사고과정 헤더 제거."""
        lines = text.split("\n")
        # 머리: "생각하는 과정 표시" + 빈 줄
        while lines and lines[0].strip().lower() in (self._HEAD_NOISE | {""}):
            lines.pop(0)
        # 꼬리: UI 잔재 + 빈 줄
        while lines:
            tail = lines[-1].strip()
            if tail == "" or any(r in tail for r in self._UI_RESIDUE):
                lines.pop()
            else:
                break
        return "\n".join(lines)

    # ── Layer 2: 가비지 판정 (reject + retry) ─────────

    _GARBAGE_PATTERNS = [
        "판정: PASS",
        "판정: FAIL",
        "판정: REJECT",  # Director 평가문
        "점수:",
        "모순:",
        "누락:",
        "이름오류:",  # Director 평가 필드
        "```python",
        "import ",
        "def ",
        "print(",  # Python 코드
        "코드 표시",
        "코드 출력",  # Gemini 코드 모드
        "I can't",
        "I cannot",
        "I'm not able",  # Gemini 영어 거부
        "도움을 드릴 수 없",
        "생성할 수 없",  # Gemini 한국어 거부
    ]

    def _is_garbage(self, text: str) -> str:
        """가비지 응답이면 사유 반환, 정상이면 빈 문자열."""
        if len(text) < 100:
            return f"극단적 짧음 ({len(text)}자)"
        first_300 = text[:300]
        for pat in self._GARBAGE_PATTERNS:
            if pat in first_300:
                return f"가비지 패턴 '{pat}'"
        # 영어 응답 감지 — 한글 비율 30% 미만이면 거부
        korean = sum(1 for c in text if "\uac00" <= c <= "\ud7a3")
        alpha = sum(1 for c in text if c.isalpha())
        if alpha > 0 and korean / alpha < 0.3:
            return f"영어 응답 (한글 비율 {korean}/{alpha} = {korean * 100 // alpha}%)"
        return ""

    # ── Layer 3: 장르 오염 감지 ─────────────────────────

    # 장르별 고유 키워드 (다른 장르에 절대 나오면 안 되는 것들)
    _GENRE_FINGERPRINTS = {
        "무협": [
            "내공",
            "진기",
            "경맥",
            "단전",
            "무림",
            "강호",
            "무공",
            "검법",
            "권법",
            "장법",
            "비급",
            "문파",
            "방파",
            "기연",
            "경지",
            "화경",
            "현경",
            "절정",
            "초식",
            "초절정",
        ],
        "헌터": [
            "던전",
            "마나",
            "스킬",
            "레벨업",
            "각성",
            "게이트",
            "마석",
            "레이드",
            "시스템 창",
            "파티원",
            "헌터",
            "랭커",
            "보스몹",
            "마력",
            "각성자",
            "드롭",
            "인벤토리",
        ],
        "현판": [
            "던전",
            "마나",
            "스킬",
            "레벨업",
            "각성",
            "게이트",
            "마석",
            "레이드",
            "시스템 창",
            "파티원",
            "마력",
            "각성자",
        ],
        "투자": [
            "주가",
            "환율",
            "매수",
            "매도",
            "펀드",
            "주식",
            "시가총액",
            "종목",
            "배당",
            "증권",
            "코스피",
            "코스닥",
            "선물",
        ],
        "대체역사": [
            "조정",
            "상소",
            "내시",
            "과거급제",
            "어전",
            "궁궐",
            "전하",
            "중전",
            "동궁",
            "사간원",
            "의정부",
            "승정원",
        ],
        "배우": [
            "오디션",
            "촬영장",
            "시청률",
            "캐스팅",
            "대본 리딩",
            "연기력",
            "출연료",
            "에이전시",
            "팬덤",
            "스캔들",
        ],
        "스포츠": [
            "코치",
            "리그",
            "토너먼트",
            "라운드",
            "준결승",
            "결승전",
            "MVP",
            "드래프트",
            "트레이드",
        ],
        "의학": [
            "수술실",
            "레지던트",
            "인턴",
            "처방전",
            "진단서",
            "응급실",
            "회진",
            "차트",
            "집도",
            "오퍼레이션",
        ],
        "요리": [
            "식재료",
            "조리법",
            "레시피",
            "셰프",
            "주방장",
            "미슐랭",
            "플레이팅",
            "디저트",
            "코스요리",
        ],
    }

    def _check_genre_contamination(self, text: str, genre: str) -> str:
        """장르 오염 감지 — 다른 장르 키워드가 3개 이상이면 오염 판정."""
        if not genre:
            return ""

        for other_genre, keywords in self._GENRE_FINGERPRINTS.items():
            if other_genre == genre:
                continue
            hits = [kw for kw in keywords if kw in text]
            if len(hits) >= 3:
                return f"장르 오염: '{genre}' 작품에 '{other_genre}' 키워드 {len(hits)}개 감지 ({', '.join(hits[:5])})"
        return ""

    # ── 전송 + 디렉터 + 저장 ──────────────────────────

    def _send_and_save(self, ctx_path: Path, instr: str, out_path: Path, min_len: int = 200, label: str = "") -> str:
        """전송 → 가비지 검증 → 디렉터 평가 → (필요시 수정+검증) → 저장."""
        # 컨텍스트 파일 크기 로그 + 자동 경량화
        ctx_size = ctx_path.stat().st_size if ctx_path.exists() else 0
        if ctx_size > 150_000:  # 150KB 초과 시 히스토리 제거 + 크기 제한
            ctx_text = ctx_path.read_text(encoding="utf-8")
            trimmed = self._trim_context(ctx_text, max_bytes=150_000)
            ctx_path.write_text(trimmed, encoding="utf-8")
            new_size = ctx_path.stat().st_size
            log(f"[CTX] {ctx_path.name} 경량화 ({ctx_size:,} → {new_size:,}바이트)")
            ctx_size = new_size
        else:
            log(f"[CTX] {ctx_path.name} 첨부 ({ctx_size:,}바이트)")

        # Pro 제한 감지 — 설정이 Pro인데 실제 Flash면 중단
        # 모델 선택 실패 대비: 한 번 더 시도 후 판단
        cfg_model = self._load_config().get("model", "pro")
        if cfg_model == "pro":
            actual = self.driver.get_current_model()
            if actual != "Pro":
                # "알 수 없음"이면 페이지 상태 문제 → 새로고침 후 재확인
                if actual == "알 수 없음":
                    log("[!] 모델 피커 읽기 실패 — 페이지 새로고침 후 재확인")
                    self.driver.driver.refresh()
                    time.sleep(5)
                    self.driver._install_upload_interceptor()
                    actual = self.driver.get_current_model()

                if actual != "Pro":
                    # 재선택 시도 후 재확인
                    log(f"[!] 모델 불일치 (현재: {actual}) — Pro 재선택 시도")
                    self.driver.select_model("pro")
                    time.sleep(1)
                    actual = self.driver.get_current_model()
                    if actual != "Pro" and actual != "알 수 없음":
                        log(f"[STOP] Pro 제한 감지! (현재: {actual}) — 생성을 중단합니다.")
                        log("       Pro 제한 해제 후 다시 실행하세요.")
                        raise ProLimitStop(f"Pro 제한 감지 (현재: {actual})")
                    elif actual == "알 수 없음":
                        log("[STOP] 모델 피커 읽기 불가 — UI 확인 후 재실행하세요.")
                        raise ProLimitStop("모델 피커 읽기 불가 (UI 확인 필요)")

        max_retry = 5
        for attempt in range(max_retry):
            start_time = time.time()
            resp = self.driver.send_with_file(str(ctx_path), instr)
            elapsed = int(time.time() - start_time)

            # 실패 체크 (타임아웃 / 빈 응답)
            if resp.startswith("[TIMEOUT]") or resp.startswith("[EMPTY]"):
                tag = "TIMEOUT" if "TIMEOUT" in resp else "EMPTY"
                log(f"[{tag}] {label} ({elapsed}초) — 재시도 {attempt + 1}/{max_retry}")
                if attempt < max_retry - 1:
                    self.driver.reset_session()
                    time.sleep(5)
                    continue
                log(f"[SKIP] {label}: {max_retry}회 실패 → 자동 스킵")
                return ""

            # Layer 1: 세정 (UI 잔재·사고과정 헤더 제거)
            resp = self._sanitize(resp)

            # Layer 2: 가비지 판정
            garbage_reason = self._is_garbage(resp)
            if not garbage_reason:
                # Layer 3: 장르 오염 감지
                genre = self._load_config().get("genre", "")
                garbage_reason = self._check_genre_contamination(resp, genre)
            if garbage_reason:
                log(
                    f"[FAIL] {label} 가비지 응답: {garbage_reason} "
                    f"({len(resp)}자, {elapsed}초) — "
                    f"재시도 {attempt + 1}/{max_retry}"
                )
                if attempt < max_retry - 1:
                    self.driver.reset_session()
                    time.sleep(5)
                    continue
                log(f"[SKIP] {label}: {max_retry}회 가비지 → 자동 스킵")
                return ""

            # 너무 짧은 응답 → reject + 재시도
            if len(resp) < min_len:
                log(f"[FAIL] {label} 응답 짧음 ({len(resp)}자 < {min_len}) — 재시도 {attempt + 1}/{max_retry}")
                if attempt < max_retry - 1:
                    self.driver.reset_session()
                    time.sleep(5)
                    continue
                log(f"[SKIP] {label}: {max_retry}회 짧은 응답 → 자동 스킵")
                return ""

            # ── 디렉터 루프 (최대 10회, 90점 이상까지) ──
            # 사고 모드로 전환 (Flash Thinking — 분석 특화, Pro 쿼터 절약)
            writer_model = self.driver.get_current_model()
            self.driver.select_model("think")

            best_resp = resp
            best_score = 0
            director_passed = False
            zero_streak = 0  # 연속 0점 카운터

            for d_round in range(10):
                passed, d_resp, score = self._director_check(label)
                log(f"[Director] {label}: {score}점 {'PASS' if passed else 'REVISE'} (round {d_round + 1}/10)")

                # [LITE-V1] Director 모순 기록
                ep_match = re.search(r"제(\d+)화", label)
                if ep_match and d_resp:
                    self.ledger.update_from_director(d_resp, int(ep_match.group(1)))

                if score > best_score:
                    best_score = score
                    best_resp = resp

                if passed:
                    director_passed = True
                    break

                # 연속 0점 조기 중단 (컨텍스트 미인식 등)
                if score == 0:
                    zero_streak += 1
                    if zero_streak >= 3:
                        log(f"[Director] 연속 {zero_streak}회 0점 → 조기 중단 (컨텍스트 미인식 의심)")
                        resp = best_resp
                        break
                else:
                    zero_streak = 0

                if d_round == 9:
                    log(f"[Director] 10회 시도 실패 → 최고 {best_score}점 채택")
                    resp = best_resp
                    break

                # 수정 요청
                revised = self._director_revision()
                if revised:
                    revised = self._sanitize(revised)
                # 수정본 검증: 길이/구조 + 장르 오염
                if revised and self._validate_revision(resp, revised):
                    genre = self._load_config().get("genre", "")
                    contam = self._check_genre_contamination(revised, genre)
                    if contam:
                        log(f"[Director] 수정본 {contam} → 현재본 유지")
                    else:
                        log(f"[Director] 수정본 채택 ({len(resp)}→{len(revised)}자)")
                        resp = revised
                else:
                    log("[Director] 수정본 부적격 → 현재본 유지, 재평가")

            # ── 2차 디렉터: 교차 모순 검사 (최대 2회) ──
            contra_revise_count = 0
            for c_round in range(2):
                c_passed, c_resp, c_score = self._contradiction_check(label)
                log(f"[Director·교차] {label}: {c_score}점 {'PASS' if c_passed else 'REVISE'} (round {c_round + 1}/2)")

                if c_passed:
                    break

                contra_revise_count += 1
                if contra_revise_count >= 2:
                    log("[Director·교차] 2회 연속 REVISE → 현재본 유지")
                    break

                # 수정 요청 → 재검사
                revised = self._director_revision()
                if revised:
                    revised = self._sanitize(revised)
                if revised and self._validate_revision(resp, revised):
                    genre = self._load_config().get("genre", "")
                    contam = self._check_genre_contamination(revised, genre)
                    if contam:
                        log(f"[Director·교차] 수정본 {contam} → 현재본 유지")
                    else:
                        log(f"[Director·교차] 수정본 채택 ({len(resp)}→{len(revised)}자)")
                        resp = revised
                else:
                    log("[Director·교차] 수정본 부적격 → 현재본 유지")

            # 디렉터 루프 후 Writer 모델 복원
            self.driver.select_model(cfg_model)

            # 최소 점수 기준 — Director가 명시적으로 낮은 점수를 준 경우
            # (auto-pass=파싱실패 시 director_passed=True이므로 여기 안 걸림)
            if not director_passed and best_score < 50:
                log(f"[FAIL] {label}: 최종 {best_score}점 < 50점 → 재시도 {attempt + 1}/{max_retry}")
                if attempt < max_retry - 1:
                    self.driver.reset_session()
                    time.sleep(5)
                    continue
                log(f"[SKIP] {label}: {max_retry}회 저품질 → 자동 스킵")
                return ""

            # 저장
            out_path.write_text(resp, encoding="utf-8")

            # 메타데이터 기록 (Writer 모델 사용)
            model_name = writer_model
            self._save_metadata_entry(
                out_path.parent,
                out_path.name,
                {
                    "model": model_name,
                    "score": best_score,
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "length": len(resp),
                },
            )

            log(f"[OK] {out_path.name} ({len(resp)}자, 최종 {best_score}점, {elapsed}초, {model_name})")

            # 쿨다운 — 연속 요청 시 Gemini에 여유 부여
            time.sleep(5)
            return resp

        return ""  # 모든 재시도 실패

    # ── 메인 메뉴 ────────────────────────────────────────

    def _ensure_genre(self) -> str:
        """장르 설정 확인/선택. config에 저장."""
        cfg = self._load_config()
        genre = cfg.get("genre", "")
        if genre:
            return genre

        genres = list(GENRE_PRESETS.keys())
        print("\n  장르 선택:")
        for i, g in enumerate(genres, 1):
            print(f"    {i}. {g}")
        print(f"    {len(genres) + 1}. [직접 입력]")

        while True:
            raw = input(f"\n  선택 (1-{len(genres) + 1}): ").strip()
            try:
                idx = int(raw)
                if 1 <= idx <= len(genres):
                    genre = genres[idx - 1]
                    break
                if idx == len(genres) + 1:
                    genre = input("  장르명: ").strip() or "웹소설"
                    break
            except ValueError:
                pass

        self._save_config({"genre": genre})
        log(f"장르 설정: {genre}")
        return genre

    def run(self):
        print(f"\n{'=' * 55}")
        print(f"  Bridge Runner — {self.project_dir.name}")
        print(f"{'=' * 55}")

        # 현황 표시
        blocks = sorted(self.treatment_dir.glob("*.txt"))
        arcs = self._output_files(self.stage2_dir, "arc_")
        bps = self._output_files(self.stage3_dir, "ep_")
        mss = self._output_files(self.stage4_dir, "ep_")

        cfg = self._load_config()
        genre = cfg.get("genre", "(미설정)")

        print(f"  장르: {genre}")
        print(f"  bible.txt: {'있음' if self.bible_path.exists() else '없음'}")
        print(f"  treatment blocks: {len(blocks)}개")
        print(f"  stage2 분배표: {len(arcs)}개")
        print(f"  stage3 blueprints: {len(bps)}개")
        print(f"  stage4 manuscripts: {len(mss)}개")

        while True:
            print("\n  --- 메뉴 ---")
            print(f"  {_C.ORANGE}{_C.BOLD}1. Easy Mode (2→3→4 원테이크){_C.RESET}")
            print("  2. Stage 2: 분배표 생성 (블록→화별 요약)")
            print("  3. Stage 3: Blueprint (분배표+블록→씬 설계)")
            print("  4. Stage 4: 원고 집필")
            print("  g. 장르 변경")
            print("  m. 모델 변경 (fast/think/pro)")
            print(f"  d. Director 재검증 ({_C.CYAN}Pro{_C.RESET})")
            print(f"  p. 패치 ({_C.RED}0점/누락{_C.RESET} 재생성)")
            print("  0. 종료")

            c = input("\n  선택: ").strip()
            try:
                if c == "1":
                    self.run_easy()
                elif c == "2":
                    self.run_stage_2()
                elif c == "3":
                    self.run_stage_3()
                elif c == "4":
                    self.run_stage_4()
                elif c == "g":
                    self._save_config({"genre": ""})
                    self._ensure_genre()
                elif c == "m":
                    print("  1. fast (빠른 모드)")
                    print("  2. think (사고 모드) [기본]")
                    print("  3. pro (Pro)")
                    mc = input("  선택 (1-3): ").strip()
                    model = {"1": "fast", "2": "think", "3": "pro"}.get(mc, "think")
                    self._save_config({"model": model})
                    if self.driver:
                        self.driver.select_model(model)
                    log(f"모델 변경: {model}")
                elif c == "d":
                    self.run_revalidate()
                elif c == "p":
                    self.run_patch()
                elif c == "0":
                    break
            except ProLimitStop:
                log("[STOP] Pro 제한 감지 — 제한 해제 후 다시 실행하세요.")
                continue

    # ═══════════════════════════════════════════════════════
    # Easy Mode: Stage 2 → 3 → 4 원테이크
    # ═══════════════════════════════════════════════════════

    def run_easy(self):
        O = _C.ORANGE
        B = _C.BOLD
        G = _C.GOLD
        DM = _C.DIM
        R = _C.RESET

        print(f"\n  {O}{B}{'━' * 45}{R}")
        print(f"  {O}{B}  Easy Mode — Stage 2 → 3 → 4 원테이크{R}")
        print(f"  {O}{B}{'━' * 45}{R}")

        # ── 사전 설정 수집 ──
        cfg = self._load_config()

        # 1) 화수/Arc
        if "ep_per_arc" not in cfg:
            ep_per_arc = self._get_int("  화수/Arc (3~7, 기본 5): ", 5, 3, 7)
            self._save_config({"ep_per_arc": ep_per_arc})
        else:
            ep_per_arc = cfg["ep_per_arc"]

        # 2) 장르
        genre = self._ensure_genre()

        # ── 현황 요약 ──
        blocks = sorted(self.treatment_dir.glob("*.txt"))
        s2_done = len(self._output_files(self.stage2_dir, "arc_"))
        s3_done = len(self._output_files(self.stage3_dir, "ep_"))
        s4_done = len(self._output_files(self.stage4_dir, "ep_"))
        total_blocks = len(blocks)
        total_eps = total_blocks * ep_per_arc

        print(f"\n  {B}설정{R}")
        print(
            f"    장르: {O}{genre}{R}  |  "
            f"화수/Arc: {O}{ep_per_arc}{R}  |  "
            f"총 블록: {O}{total_blocks}{R}  →  "
            f"총 에피소드: {O}{total_eps}{R}화"
        )

        print(f"\n  {B}진행 현황{R}")
        for label, done, total in [
            ("Stage 2  분배표  ", s2_done, total_blocks),
            ("Stage 3  Blueprint", s3_done, total_eps),
            ("Stage 4  원고    ", s4_done, total_eps),
        ]:
            if done >= total:
                status = f"{_C.GREEN}✓ 완료{R}"
            else:
                status = f"{G}{done}{DM}/{total}{R}"
            print(f"    {label}  {status}")

        if s4_done >= total_eps:
            log("모든 스테이지 이미 완료!")
            return

        print(f"\n  {DM}시작하면 완료될 때까지 자동 진행됩니다.{R}")
        if input("  시작? (Y/n): ").strip().lower() == "n":
            return

        # ── 순차 실행 ──
        start_time = time.time()

        try:
            log(f"{O}{B}▶ Stage 2 시작{R}")
            self.run_stage_2(auto=True)

            log(f"{O}{B}▶ Stage 3 시작{R}")
            self.run_stage_3(auto=True)

            log(f"{O}{B}▶ Stage 4 시작{R}")
            self.run_stage_4(auto=True)
        except ProLimitStop:
            log(f"\n  {O}{B}[STOP] Pro 제한 감지 — Easy Mode 중단{R}")
            log("  제한 해제 후 다시 실행하면 이어서 진행됩니다.")
            return

        total_sec = int(time.time() - start_time)
        h, rem = divmod(total_sec, 3600)
        m, s = divmod(rem, 60)
        time_str = ""
        if h:
            time_str = f"{h}시간 {m}분 {s}초"
        elif m:
            time_str = f"{m}분 {s}초"
        else:
            time_str = f"{s}초"

        print(f"\n  {O}{B}{'━' * 45}{R}")
        print(f"  {O}{B}  Easy Mode 완료!  총 소요: {time_str}{R}")
        print(f"  {O}{B}{'━' * 45}{R}\n")

    # ═══════════════════════════════════════════════════════
    # Stage 2: 분배표 (블록 → 화별 분배)
    # ═══════════════════════════════════════════════════════

    def run_stage_2(self, auto=False, hide=False):
        self._init_driver(hide=hide)

        bible = self._read(self.bible_path)
        if not bible:
            log("[!] bible.txt 없음. 없이 진행합니다.")

        blocks = sorted(self.treatment_dir.glob("*.txt"))
        if not blocks:
            log("[!] treatment/ 에 txt 파일이 없습니다.")
            return

        done = self._output_files(self.stage2_dir, "arc_")
        done_names = {f.name for f in done}

        # 누락된 블록 번호 수집
        missing = []
        for i in range(len(blocks)):
            arc_no = i + 1
            fname = f"arc_{arc_no:03d}.txt"
            if fname not in done_names:
                missing.append(i)

        if not missing:
            log(f"모든 block 처리 완료 ({len(blocks)}개)")
            return

        if auto:
            cfg = self._load_config()
            ep_per_arc = cfg.get("ep_per_arc", 5)
        else:
            ep_per_arc = self._get_int("  화수/Arc (3~7, 기본 5): ", 5, 3, 7)
            self._save_config({"ep_per_arc": ep_per_arc})

        log(
            f"Stage 2 분배표: 누락 {len(missing)}개 "
            f"(#{', #'.join(str(m + 1) for m in missing[:10])}"
            f"{'...' if len(missing) > 10 else ''})"
        )

        if not auto:
            if input("  시작? (Y/n): ").strip().lower() == "n":
                return

        total = len(blocks)
        count = 0
        try:
            with Spinner("Stage 2 시작...", current=total - len(missing), total=total) as sp:
                for i in missing:
                    arc_no = i + 1
                    ep_start = i * ep_per_arc + 1
                    block_text = blocks[i].read_text(encoding="utf-8")

                    # 이전 Arc (최근 10개 수집)
                    prev_arc = self._collect_prev(
                        self.stage2_dir,
                        "arc_{n:03d}.txt",
                        current=arc_no,
                        count=10,
                        max_chars=2000,
                        header_fmt="[Arc #{n} 분배표]",
                    )

                    ep_end = ep_start + ep_per_arc - 1
                    sp.update(f"Stage 2 — 분배표 #{arc_no}", current=total - len(missing) + count + 1)
                    log(f"분배표 #{arc_no} (제{ep_start}~{ep_end}화) <- {blocks[i].name}")

                    # 컨텍스트 파일 생성 (누적 히스토리 포함)
                    ctx = self.prompt.build_arc_context(
                        bible, block_text, prev_arc, state_summary=self.ledger.get_state_summary()
                    )
                    history = self._read_history(self.stage2_dir)
                    if history:
                        ctx += f"\n\n{'=' * 50}\n[이전 분배표 누적 (참고용 — 일관성 유지)]\n{'=' * 50}\n{history}"
                    ctx_path = self.stage2_dir / f"arc_{arc_no:03d}_context.txt"
                    ctx_path.write_text(ctx, encoding="utf-8")

                    # 인스트럭션
                    instr = self.prompt.build_arc_instruction(
                        arc_no, ep_start, ep_per_arc, dead_npc_warning=self.ledger.get_dead_npc_warning()
                    )

                    # Gemini 전송 + 저장
                    out = self.stage2_dir / f"arc_{arc_no:03d}.txt"
                    resp = self._send_and_save(
                        ctx_path, instr, out, min_len=ep_per_arc * 300, label=f"분배표 #{arc_no}"
                    )
                    if not resp:
                        log(f"분배표 #{arc_no} 스킵.")
                        continue

                    self._append_history(self.stage2_dir, f"Arc #{arc_no} 분배표", resp)

                    # [LITE-V1] 세계 상태 갱신
                    self.ledger.update_from_arc(arc_no, resp)
                    self.ledger.save()
                    count += 1
        except ProLimitStop:
            log("[STOP] Pro 제한으로 Stage 2 중단.")
            raise

        log(f"Stage 2 완료: {count}개 분배표 생성")
        if self.driver:
            self.driver.reset_session()

    # ═══════════════════════════════════════════════════════
    # Stage 3: Blueprint (분배표 + 원본 블록 → 씬 설계)
    # ═══════════════════════════════════════════════════════

    def run_stage_3(self, auto=False, hide=False):
        self._init_driver(hide=hide)

        arcs = self._output_files(self.stage2_dir, "arc_")
        if not arcs:
            log("[!] stage2/ 에 분배표 파일이 없습니다.")
            return

        blocks = sorted(self.treatment_dir.glob("*.txt"))
        if not blocks:
            log("[!] treatment/ 에 블록 파일이 없습니다.")
            return

        bible = self._read(self.bible_path)

        cfg = self._load_config()
        ep_per_arc = cfg.get("ep_per_arc", 5)
        total_eps = len(arcs) * ep_per_arc

        done = self._output_files(self.stage3_dir, "ep_")
        start_ep = len(done) + 1
        if start_ep > total_eps:
            log(f"모든 에피소드 처리 완료 ({total_eps}화)")
            return

        if auto:
            target = total_eps
        else:
            target = self._get_int(
                f"  몇 화까지? ({start_ep}~{total_eps}, 기본 {total_eps}): ", total_eps, start_ep, total_eps
            )

        log(f"Stage 3: 제{start_ep}화 ~ 제{target}화")
        if not auto:
            if input("  시작? (Y/n): ").strip().lower() == "n":
                return

        count = 0
        try:
            with Spinner("Stage 3 시작...", current=start_ep - 1, total=target) as sp:
                for ep in range(start_ep, target + 1):
                    arc_idx = (ep - 1) // ep_per_arc
                    if arc_idx >= len(arcs):
                        log(f"[!] 제{ep}화: 해당 분배표 없음. 중단.")
                        break

                    # 분배표 (stage2 출력)
                    arc_text = arcs[arc_idx].read_text(encoding="utf-8")

                    # 원본 블록 (treatment 원문)
                    block_text = ""
                    if arc_idx < len(blocks):
                        block_text = blocks[arc_idx].read_text(encoding="utf-8")
                    else:
                        log(f"[!] 블록 #{arc_idx + 1} 없음. 분배표만으로 진행.")

                    # 최근 Blueprint (최대 10개 수집)
                    prev_bp = self._collect_prev(
                        self.stage3_dir,
                        "ep_{n:04d}.txt",
                        current=ep,
                        count=10,
                        max_chars=1500,
                        header_fmt="[제{n}화 Blueprint]",
                    )

                    sp.update(f"Stage 3 — 제{ep}화 Blueprint", current=ep)
                    block_name = blocks[arc_idx].name if arc_idx < len(blocks) else "?"
                    log(f"제{ep}화 Blueprint (분배표 #{arc_idx + 1} + {block_name})")

                    # 컨텍스트
                    ctx = self.prompt.build_blueprint_context(
                        bible, arc_text, block_text, prev_bp, state_summary=self.ledger.get_state_summary()
                    )
                    history = self._read_history(self.stage3_dir)
                    if history:
                        ctx += f"\n\n{'=' * 50}\n[이전 Blueprint 누적 (참고용)]\n{'=' * 50}\n{history}"
                    ctx_path = self.stage3_dir / f"ep_{ep:04d}_context.txt"
                    ctx_path.write_text(ctx, encoding="utf-8")

                    instr = self.prompt.build_blueprint_instruction(
                        ep, dead_npc_warning=self.ledger.get_dead_npc_warning()
                    )

                    out = self.stage3_dir / f"ep_{ep:04d}.txt"
                    resp = self._send_and_save(ctx_path, instr, out, min_len=800, label=f"제{ep}화 Blueprint")
                    if not resp:
                        log(f"제{ep}화 스킵.")
                        continue

                    self._append_history(self.stage3_dir, f"제{ep}화 Blueprint", resp)

                    # [LITE-V1] 세계 상태 갱신
                    self.ledger.update_from_blueprint(ep, resp)
                    self.ledger.save()

                    count += 1

                    self.driver.new_chat()
                    time.sleep(2)
        except ProLimitStop:
            log("[STOP] Pro 제한으로 Stage 3 중단.")
            raise

        log(f"Stage 3 완료: {count}개 Blueprint 생성")
        if self.driver:
            self.driver.reset_session()

    # ═══════════════════════════════════════════════════════
    # Stage 4: 원고 집필
    # ═══════════════════════════════════════════════════════

    def run_stage_4(self, auto=False, hide=False):
        self._init_driver(hide=hide)
        genre = self._ensure_genre()

        bps = self._output_files(self.stage3_dir, "ep_")
        if not bps:
            log("[!] stage3/ 에 blueprint 파일이 없습니다.")
            return

        total = len(bps)
        done = self._output_files(self.stage4_dir, "ep_")
        start_ep = len(done) + 1
        if start_ep > total:
            log(f"모든 에피소드 집필 완료 ({total}화)")
            return

        if auto:
            target = total
        else:
            target = self._get_int(f"  몇 화까지? ({start_ep}~{total}, 기본 {total}): ", total, start_ep, total)

        bible = self._read(self.bible_path)
        style = self._read(self.style_path)

        log(f"Stage 4: 제{start_ep}화 ~ 제{target}화")
        if not auto:
            if input("  시작? (Y/n): ").strip().lower() == "n":
                return

        count = 0
        try:
            with Spinner("Stage 4 시작...", current=start_ep - 1, total=target) as sp:
                for ep in range(start_ep, target + 1):
                    bp_path = self.stage3_dir / f"ep_{ep:04d}.txt"
                    if not bp_path.exists():
                        log(f"[!] 제{ep}화 Blueprint 없음. 스킵.")
                        continue

                    bp_text = bp_path.read_text(encoding="utf-8")

                    # 최근 원고 (최대 10개 수집)
                    prev_ms = self._collect_prev(
                        self.stage4_dir,
                        "ep_{n:04d}.txt",
                        current=ep,
                        count=10,
                        max_chars=1500,
                        header_fmt="[제{n}화 원고]",
                    )

                    sp.update(f"Stage 4 — 제{ep}화 원고", current=ep)
                    log(f"제{ep}화 원고")

                    # 컨텍스트 (누적 히스토리 포함)
                    ctx = self.prompt.build_manuscript_context(
                        bible,
                        bp_text,
                        prev_ms,
                        style,
                        state_summary=self.ledger.get_state_summary(),
                        chain_link=self.ledger.get_chain_link(),
                    )
                    history = self._read_history(self.stage4_dir)
                    if history:
                        ctx += f"\n\n{'=' * 50}\n[이전 원고 누적 (참고용 — 문체/톤 일관성 유지)]\n{'=' * 50}\n{history}"
                    ctx_path = self.stage4_dir / f"ep_{ep:04d}_context.txt"
                    ctx_path.write_text(ctx, encoding="utf-8")

                    # 인스트럭션 (장르별)
                    instr = self.prompt.build_manuscript_instruction(
                        ep, genre, dead_npc_warning=self.ledger.get_dead_npc_warning()
                    )

                    # 전송 + 저장
                    out = self.stage4_dir / f"ep_{ep:04d}.txt"
                    resp = self._send_and_save(ctx_path, instr, out, min_len=4000, label=f"제{ep}화 원고")
                    if not resp:
                        log(f"제{ep}화 스킵.")
                        continue

                    self._append_history(self.stage4_dir, f"제{ep}화 원고", resp)

                    # [LITE-V1] 세계 상태 갱신
                    self.ledger.update_from_manuscript(ep, resp)
                    self.ledger.save()

                    count += 1

                    self.driver.new_chat()
                    time.sleep(2)
        except ProLimitStop:
            log("[STOP] Pro 제한으로 Stage 4 중단.")
            raise

        log(f"Stage 4 완료: {count}개 원고 집필")
        if self.driver:
            self.driver.reset_session()

    # ═══════════════════════════════════════════════════════
    # Director 재검증 (Pro)
    # ═══════════════════════════════════════════════════════

    def run_revalidate(self):
        """기존 출력 파일을 Pro/사고 모델로 재검증 (재생성 없음)"""
        print(f"\n  {'=' * 45}")
        print("  Director 재검증 — 기존 출력 평가")
        print("  콘텐츠는 재생성하지 않습니다.")
        print(f"  {'=' * 45}")

        # 스테이지 선택
        print("\n  검증 대상:")
        print("  2. Stage 2 분배표")
        print("  3. Stage 3 Blueprint")
        print("  4. Stage 4 원고")
        sc = input("\n  선택 (2/3/4): ").strip()

        if sc == "2":
            stage_dir = self.stage2_dir
            prefix = "arc_"
            label_fmt = "분배표 #{}"
        elif sc == "3":
            stage_dir = self.stage3_dir
            prefix = "ep_"
            label_fmt = "제{}화 Blueprint"
        elif sc == "4":
            stage_dir = self.stage4_dir
            prefix = "ep_"
            label_fmt = "제{}화 원고"
        else:
            print("  잘못된 선택.")
            return

        # 출력 파일 목록
        outputs = self._output_files(stage_dir, prefix)
        if not outputs:
            log(f"[!] {stage_dir.name}/ 에 출력 파일이 없습니다.")
            return

        print(f"\n  대상 파일: {len(outputs)}개")

        # 범위 선택
        start_idx = self._get_int(f"  시작 번호 (1~{len(outputs)}, 기본 1): ", 1, 1, len(outputs))
        end_idx = self._get_int(
            f"  끝 번호 ({start_idx}~{len(outputs)}, 기본 {len(outputs)}): ", len(outputs), start_idx, len(outputs)
        )

        target_outputs = outputs[start_idx - 1 : end_idx]
        print(f"\n  검증 범위: {len(target_outputs)}개 파일")

        if input("\n  Pro 모델로 시작? (Y/n): ").strip().lower() == "n":
            return

        # 드라이버 초기화 + Pro 강제 선택
        self._init_driver()
        self.driver.select_model("pro")

        actual_model = self.driver.get_current_model()
        if "Pro" not in actual_model:
            log(f"[!] Pro 선택 실패 (현재: {actual_model})")
            if input("  Pro 아닌 상태로 계속? (y/N): ").strip().lower() != "y":
                return

        # 검증 루프
        results = []
        pass_count = 0
        fail_count = 0

        with Spinner("Director 재검증 중...", current=0, total=len(target_outputs)) as sp:
            for i, out_path in enumerate(target_outputs):
                # 번호 추출
                stem = out_path.stem
                num_str = stem.split("_", 1)[1]

                # 컨텍스트 파일 경로
                ctx_name = f"{prefix}{num_str}_context.txt"
                ctx_path = stage_dir / ctx_name

                if not ctx_path.exists():
                    log(f"[!] {ctx_name} 없음 → 스킵")
                    results.append(
                        {
                            "file": out_path.name,
                            "score": 0,
                            "passed": False,
                            "details": "컨텍스트 파일 없음",
                            "model": "N/A",
                        }
                    )
                    fail_count += 1
                    continue

                try:
                    num_int = int(num_str)
                except ValueError:
                    num_int = i + 1
                label = label_fmt.format(num_int)

                sp.update(f"재검증 — {label}", current=i + 1)

                result = self._revalidate_single(ctx_path, out_path, label)
                results.append(result)

                if result["passed"]:
                    pass_count += 1
                else:
                    fail_count += 1

                self.driver.new_chat()
                time.sleep(2)

        # 결과 저장
        report = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "stage": stage_dir.name,
            "model": actual_model,
            "total": len(results),
            "passed": pass_count,
            "failed": fail_count,
            "results": results,
        }
        report_path = stage_dir / "_revalidation.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        # 메타데이터에도 재검증 결과 기록
        for r in results:
            if r["score"] > 0:
                existing = self._load_metadata(stage_dir).get(r["file"], {})
                existing["reval_model"] = r["model"]
                existing["reval_score"] = r["score"]
                existing["reval_passed"] = r["passed"]
                existing["reval_timestamp"] = report["timestamp"]
                self._save_metadata_entry(stage_dir, r["file"], existing)

        # 요약 출력
        print(f"\n  {'=' * 45}")
        print("  Director 재검증 결과")
        print(f"  {'=' * 45}")
        print(f"  모델: {actual_model}")
        print(f"  통과: {_C.GREEN}{pass_count}{_C.RESET}개  |  재생성 필요: {_C.RED}{fail_count}{_C.RESET}개")

        if fail_count > 0:
            print("\n  재생성 필요 파일:")
            for r in results:
                if not r["passed"]:
                    print(f"    {_C.RED}✗{_C.RESET} {r['file']} ({r['score']}점) — {r['details']}")

        print(f"\n  상세 리포트: {report_path}")
        print(f"  {'=' * 45}")

    # ═══════════════════════════════════════════════════════
    # Patch: 0점/누락 파일 재생성
    # ═══════════════════════════════════════════════════════

    def _find_bad_files(self, stage_dir: Path, prefix: str, total: int) -> list:
        """0점 또는 누락된 파일 목록 반환 → [(번호, 사유), ...]"""
        meta = self._load_metadata(stage_dir)
        bad = []
        for i in range(1, total + 1):
            fname = f"{prefix}{i:04d}.txt"
            fpath = stage_dir / fname
            if not fpath.exists():
                bad.append((i, "누락"))
            elif fname in meta and meta[fname].get("score", 100) < 50:
                bad.append((i, f"{meta[fname]['score']}점"))
        return bad

    def run_patch(self):
        """0점/누락 파일만 골라서 재생성"""
        print(f"\n  {'=' * 45}")
        print("  재생성 (Patch) — 0점/누락 파일만 재생성")
        print(f"  {'=' * 45}")

        print("\n  스테이지 선택:")
        print("  3. Stage 3 (Blueprint)")
        print("  4. Stage 4 (원고)")
        sc = input("  선택 (3/4): ").strip()

        if sc == "3":
            self._patch_stage3()
        elif sc == "4":
            self._patch_stage4()
        else:
            log("취소.")

    def _patch_stage3(self):
        """Stage 3: 0점/누락 Blueprint 재생성"""
        self._init_driver()

        arcs = self._output_files(self.stage2_dir, "arc_")
        blocks = sorted(self.treatment_dir.glob("*.txt"))
        bible = self._read(self.bible_path)
        cfg = self._load_config()
        ep_per_arc = cfg.get("ep_per_arc", 5)
        total_eps = len(arcs) * ep_per_arc

        bad = self._find_bad_files(self.stage3_dir, "ep_", total_eps)
        if not bad:
            log("재생성 대상 없음 — 모든 Blueprint 정상")
            return

        print(f"\n  재생성 대상 ({len(bad)}건):")
        for ep, reason in bad:
            print(f"    ep_{ep:04d}.txt — {reason}")

        confirm = input(f"\n  {len(bad)}건 재생성? (Y/n): ").strip().lower()
        if confirm == "n":
            return

        count = 0
        try:
            for ep, reason in bad:
                arc_idx = (ep - 1) // ep_per_arc
                if arc_idx >= len(arcs):
                    log(f"[!] 제{ep}화: 분배표 없음. 스킵.")
                    continue

                arc_text = arcs[arc_idx].read_text(encoding="utf-8")
                block_text = ""
                if arc_idx < len(blocks):
                    block_text = blocks[arc_idx].read_text(encoding="utf-8")

                prev_bp = ""
                prev_path = self.stage3_dir / f"ep_{ep - 1:04d}.txt"
                if prev_path.exists():
                    prev_bp = prev_path.read_text(encoding="utf-8")

                log(f"[REGEN] 제{ep}화 Blueprint ({reason})")

                # 기존 불량 파일 삭제
                out = self.stage3_dir / f"ep_{ep:04d}.txt"
                if out.exists():
                    out.unlink()

                # 컨텍스트 빌드
                ctx = self.prompt.build_blueprint_context(
                    bible, arc_text, block_text, prev_bp, state_summary=self.ledger.get_state_summary()
                )
                history = self._read_history(self.stage3_dir)
                if history:
                    ctx += f"\n\n{'=' * 50}\n[이전 Blueprint 누적 (참고용)]\n{'=' * 50}\n{history}"
                ctx_path = self.stage3_dir / f"ep_{ep:04d}_context.txt"
                ctx_path.write_text(ctx, encoding="utf-8")

                instr = self.prompt.build_blueprint_instruction(ep, dead_npc_warning=self.ledger.get_dead_npc_warning())

                resp = self._send_and_save(ctx_path, instr, out, min_len=800, label=f"제{ep}화 Blueprint")
                if resp:
                    count += 1
                else:
                    log(f"[!] 제{ep}화 재생성 실패")

                self.driver.new_chat()
                time.sleep(2)
        except ProLimitStop:
            log("[STOP] Pro 제한으로 패치 중단.")
            raise

        log(f"패치 완료: {count}/{len(bad)}")
        if self.driver:
            self.driver.reset_session()

    def _patch_stage4(self):
        """Stage 4: 0점/누락 원고 재생성"""
        self._init_driver()
        genre = self._ensure_genre()

        bps = self._output_files(self.stage3_dir, "ep_")
        total = len(bps)
        bible = self._read(self.bible_path)
        style = self._read(self.style_path)

        bad = self._find_bad_files(self.stage4_dir, "ep_", total)
        if not bad:
            log("재생성 대상 없음 — 모든 원고 정상")
            return

        print(f"\n  재생성 대상 ({len(bad)}건):")
        for ep, reason in bad:
            print(f"    ep_{ep:04d}.txt — {reason}")

        confirm = input(f"\n  {len(bad)}건 재생성? (Y/n): ").strip().lower()
        if confirm == "n":
            return

        count = 0
        try:
            for ep, reason in bad:
                bp_path = self.stage3_dir / f"ep_{ep:04d}.txt"
                if not bp_path.exists():
                    log(f"[!] 제{ep}화 Blueprint 없음. 스킵.")
                    continue

                bp_text = bp_path.read_text(encoding="utf-8")
                prev_ms = ""
                prev_path = self.stage4_dir / f"ep_{ep - 1:04d}.txt"
                if prev_path.exists():
                    prev_ms = prev_path.read_text(encoding="utf-8")

                log(f"[REGEN] 제{ep}화 원고 ({reason})")

                out = self.stage4_dir / f"ep_{ep:04d}.txt"
                if out.exists():
                    out.unlink()

                ctx = self.prompt.build_manuscript_context(
                    bible,
                    bp_text,
                    prev_ms,
                    style,
                    state_summary=self.ledger.get_state_summary(),
                    chain_link=self.ledger.get_chain_link(),
                )
                history = self._read_history(self.stage4_dir)
                if history:
                    ctx += f"\n\n{'=' * 50}\n[이전 원고 누적 (참고용 — 문체/톤 일관성 유지)]\n{'=' * 50}\n{history}"
                ctx_path = self.stage4_dir / f"ep_{ep:04d}_context.txt"
                ctx_path.write_text(ctx, encoding="utf-8")

                instr = self.prompt.build_manuscript_instruction(
                    ep, genre, dead_npc_warning=self.ledger.get_dead_npc_warning()
                )

                resp = self._send_and_save(ctx_path, instr, out, min_len=4000, label=f"제{ep}화 원고")
                if resp:
                    count += 1
                else:
                    log(f"[!] 제{ep}화 재생성 실패")

                self.driver.new_chat()
                time.sleep(2)
        except ProLimitStop:
            log("[STOP] Pro 제한으로 패치 중단.")
            raise

        log(f"패치 완료: {count}/{len(bad)}")
        if self.driver:
            self.driver.reset_session()
