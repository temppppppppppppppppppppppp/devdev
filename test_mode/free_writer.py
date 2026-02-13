"""
자유 형식 Blueprint → 원고 변환기 (Free Writer)
================================================
어떤 형식의 blueprint든 원고로 변환.
기존 글도비라이트 파이프라인과 완전 독립.

사용법:
  python free_writer.py

프로젝트 구조:
  projects/{name}/
    bible.txt         ← 세계관 (선택)
    style_guide.txt   ← 문체 가이드 (선택)
    blueprints/       ← 자유 형식 blueprint (ep_001.txt, ...)
    manuscripts/      ← 원고 출력
    _config.json      ← 설정 (장르, 모델)
"""

import json

# ── Windows ANSI 지원 ──
import os
import re
import sys
import time
from pathlib import Path

# ── 기존 bridge 모듈 재사용 ──
from bridge.gemini_driver import GeminiDriver

os.system("")

# ── 스피너 & 로그 (bridge.runner에서 임포트) ──
from bridge.runner import DIRECTOR_PROMPT, REVISION_PROMPT, Spinner, log

# ── 장르별 문체 팁 ──
GENRE_TIPS = {
    "무협": "전투: 무공 시전(기운 흐름/신체 변화) 구체 묘사. 현대어/외래어 금지.",
    "헌터": "전투: 스킬 발동/마나 소모/던전 환경 구체 묘사. 레벨업/각성 시스템.",
    "현판": "전투: 스킬 발동/마나 소모/던전 환경 구체 묘사. 레벨업/각성 시스템.",
    "투자": "시장: 주가/환율/거래량 등 수치와 시장 분위기 구체 묘사.",
    "대체역사": "정치: 권모술수/파벌 역학/조정 논쟁 구체 묘사. 현대 IT용어 금지.",
    "배우": "연기: 촬영 현장/오디션/감정 이입 구체 묘사.",
    "스포츠": "경기: 기술 시전/신체 역학/경기 흐름 구체 묘사.",
    "의학": "진료: 의학 용어/시술 과정/환자 상태 구체 묘사.",
    "요리": "요리: 식재료/조리 과정/맛과 향의 변화 구체 묘사.",
}

# ── 장르 오염 키워드 ──
GENRE_FINGERPRINTS = {
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

HEADER = """★★★ [절대 규칙 - 이 규칙을 어기면 응답 전체가 무효] ★★★
1. Canvas/문서 편집기 열지 마. 채팅창에 텍스트로 바로 출력.
2. 인사말("물론이죠/네/알겠습니다") 없이 요청한 결과물 첫 줄부터 바로 시작.
3. 마무리 멘트("도움이 되셨나요?/수정 필요하면/Would you like") 금지.
4. 요청한 출력 형식만 출력. 추가 설명/대안/주석/후속 질문 금지.
5. 마크다운 코드블럭(```)으로 감싸지 말 것.
6. 이것은 코딩 작업이 아님. Python/코드를 절대 출력하지 마.
7. 첨부파일을 분석/채점/평가하지 마. 요청한 창작물만 출력.
8. 사고 과정/추론 단계를 표시하지 마. 최종 결과물만 출력.
9. 반드시 한국어로 응답.
★★★ 위 규칙을 모두 지켜서, 결과물만 출력하라. ★★★"""


class FreeWriter:
    """자유 형식 Blueprint → 원고 변환기"""

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.driver = None

        self.bible_path = self.project_dir / "bible.txt"
        self.style_path = self.project_dir / "style_guide.txt"
        self.bp_dir = self.project_dir / "blueprints"
        self.ms_dir = self.project_dir / "manuscripts"
        self.config_path = self.project_dir / "_config.json"

        self.bp_dir.mkdir(exist_ok=True)
        self.ms_dir.mkdir(exist_ok=True)

    # ── 헬퍼 ──────────────────────────────────────────

    def _read(self, p: Path) -> str:
        return p.read_text(encoding="utf-8") if p.exists() else ""

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

    def _init_driver(self):
        if not self.driver:
            cfg = self._load_config()
            model = cfg.get("model", "pro")
            log(f"Gemini 드라이버 연결 중... (모델: {model})")
            self.driver = GeminiDriver(model=model, hide=True, log_func=log)
            log("연결 성공!")

    def _bp_files(self) -> list:
        """blueprint 파일 목록 (정렬)"""
        return sorted([f for f in self.bp_dir.glob("*.txt") if "_context" not in f.name])

    def _ms_files(self) -> list:
        """manuscript 파일 목록"""
        return sorted(self.ms_dir.glob("*.txt"))

    # ── 품질 검증 ─────────────────────────────────────

    _UI_RESIDUE = [
        "업로드 용량이 너무 커서 최상의 결과를 얻지 못할 수 있습니다.",
        "자세히 알아보기",
        "새 창에서 열기",
    ]
    _HEAD_NOISE = {"생각하는 과정 표시", "단계별 사고", "thinking process"}

    _GARBAGE_PATTERNS = [
        "판정: PASS",
        "판정: FAIL",
        "판정: REJECT",
        "점수:",
        "모순:",
        "누락:",
        "이름오류:",
        "```python",
        "import ",
        "def ",
        "print(",
        "코드 표시",
        "코드 출력",
        "I can't",
        "I cannot",
        "I'm not able",
        "도움을 드릴 수 없",
        "생성할 수 없",
    ]

    def _sanitize(self, text: str) -> str:
        lines = text.split("\n")
        while lines and lines[0].strip().lower() in (self._HEAD_NOISE | {""}):
            lines.pop(0)
        while lines:
            tail = lines[-1].strip()
            if tail == "" or any(r in tail for r in self._UI_RESIDUE):
                lines.pop()
            else:
                break
        return "\n".join(lines)

    def _is_garbage(self, text: str) -> str:
        if len(text) < 100:
            return f"극단적 짧음 ({len(text)}자)"
        first_300 = text[:300]
        for pat in self._GARBAGE_PATTERNS:
            if pat in first_300:
                return f"가비지 패턴 '{pat}'"
        korean = sum(1 for c in text if "\uac00" <= c <= "\ud7a3")
        alpha = sum(1 for c in text if c.isalpha())
        if alpha > 0 and korean / alpha < 0.3:
            return f"영어 응답 (한글 {korean * 100 // alpha}%)"
        return ""

    def _check_genre(self, text: str, genre: str) -> str:
        if not genre:
            return ""
        for other, keywords in GENRE_FINGERPRINTS.items():
            if other == genre:
                continue
            hits = [kw for kw in keywords if kw in text]
            if len(hits) >= 3:
                return f"장르 오염: '{other}' 키워드 {len(hits)}개 ({', '.join(hits[:5])})"
        return ""

    def _validate_revision(self, original: str, revised: str) -> bool:
        if len(revised) < len(original) * 0.7:
            log(f"[검증] 수정본 짧음 ({len(revised)}자 < 원본 70%)")
            return False
        skip_pats = [
            r"위와\s*같음",
            r"이하\s*동일",
            r"이하\s*생략",
            r"상동",
            r"\(생략\)",
            r"\.{3,}.*생략",
        ]
        for p in skip_pats:
            if re.search(p, revised):
                log(f"[검증] 생략 패턴: {p}")
                return False
        return True

    # ── 디렉터 ─────────────────────────────────────────

    def _director_check(self, label: str) -> tuple:
        m = None
        resp = ""
        for _try in range(10):
            resp = self.driver.send_prompt(DIRECTOR_PROMPT)
            m = re.search(r"점수\s*[:：]\s*(\d+)", resp)
            if m:
                break
            log(f"[Director] {label}: 점수 파싱 실패 → 재시도 ({_try + 1}/10)")
        if not m:
            log(f"[Director] {label}: 10회 파싱 실패 → 자동 통과")
            return True, resp, 0

        score = int(m.group(1))
        verdict = "PASS" if score >= 90 else "REVISE"
        vm = re.search(r"판정\s*[:：]\s*(PASS|REVISE)", resp)
        if vm:
            verdict = vm.group(1)

        for field in ["모순", "누락", "이름오류"]:
            fm = re.search(rf"{field}\s*[:：]\s*(.+?)(?:\n|$)", resp)
            if fm and fm.group(1).strip() not in ("없음", "없음."):
                log(f"[Director] {field}: {fm.group(1).strip()[:80]}")

        return verdict == "PASS", resp, score

    def _director_revision(self) -> str:
        resp = self.driver.send_prompt(REVISION_PROMPT)
        if resp.startswith("[TIMEOUT]") or resp.startswith("[EMPTY]"):
            return ""
        return resp

    # ── 컨텍스트 & 프롬프트 조립 ──────────────────────

    def _build_context(self, bp_text: str, prev_ms: str = "") -> str:
        bible = self._read(self.bible_path)
        style = self._read(self.style_path)
        sep = "=" * 50
        parts = []
        if bible:
            parts.append(f"{sep}\n[세계관 설정]\n{sep}\n{bible}")
        parts.append(f"{sep}\n[에피소드 Blueprint (자유 형식)]\n{sep}\n{bp_text}")
        if prev_ms:
            parts.append(f"{sep}\n[직전 화 마지막 장면]\n{sep}\n{prev_ms[-2000:]}")
        if style:
            parts.append(f"{sep}\n[문체 가이드]\n{sep}\n{style}")
        return "\n\n".join(parts)

    def _build_instruction(self, ep_num: int, genre: str) -> str:
        tips = GENRE_TIPS.get(genre, "장르 핵심 장면을 구체적이고 감각적으로 묘사.")
        return f"""{HEADER}

첨부 파일에 세계관과 에피소드 Blueprint가 있습니다.
Blueprint 형식은 자유이며, 내용을 해석하여 원고를 작성하세요.

[작업] 제{ep_num}화 웹소설 원고 집필
- 장르: {genre} 웹소설 (문피아 20~30대 독자)
- 분량: 공백 포함 최소 8,000자 이상

[필수 제약]
1. 맨 윗줄에 '제 {ep_num}화' 표기 후 시작
2. 사족 없이 소설 본문만 출력
3. 불필요한 HTML/**굵은글씨** 금지
4. 마지막에 '* * *' 종료 표시
5. 3인칭 시점
6. Blueprint의 모든 내용을 균등 비중으로 전개
7. 후반부 급전개/요약 절대 금지
8. 직전 화 마지막 장면에서 자연스럽게 이어질 것
9. Bible의 캐릭터명/고유명사 정확히 사용
10. 장면 전환은 '%%%%'로만 표시
11. '한글(영어)' 병기 금지, 한자 병기 금지

[문체 원칙]
- 감정어 삭제 → 행동/미세표정으로 감정 유추
- 감각적 묘사 (소리/냄새/질감)
- 날 선 대화가 오가는 실제 장면
- 동사(Action) 위주 짧고 힘 있는 문장
- {tips}"""

    # ── 핵심: 전송 + 검증 + 저장 ────────────────────

    def _generate_one(self, bp_path: Path, ep_num: int, prev_ms: str = "") -> str:
        genre = self._load_config().get("genre", "")
        bp_text = bp_path.read_text(encoding="utf-8")

        # 컨텍스트 파일 생성
        ctx = self._build_context(bp_text, prev_ms)
        ctx_path = self.ms_dir / f"ep_{ep_num:04d}_context.txt"
        ctx_path.write_text(ctx, encoding="utf-8")

        instr = self._build_instruction(ep_num, genre)
        out_path = self.ms_dir / f"ep_{ep_num:04d}.txt"

        ctx_size = ctx_path.stat().st_size
        log(f"[CTX] {ctx_path.name} 첨부 ({ctx_size:,}바이트)")

        max_retry = 5
        for attempt in range(max_retry):
            start_time = time.time()
            resp = self.driver.send_with_file(str(ctx_path), instr)
            elapsed = int(time.time() - start_time)

            # 타임아웃 / 빈 응답
            if resp.startswith("[TIMEOUT]") or resp.startswith("[EMPTY]"):
                tag = "TIMEOUT" if "TIMEOUT" in resp else "EMPTY"
                log(f"[{tag}] 제{ep_num}화 ({elapsed}초) — 재시도 {attempt + 1}/{max_retry}")
                if attempt < max_retry - 1:
                    self.driver.reset_session()
                    time.sleep(5)
                    continue
                log(f"[SKIP] 제{ep_num}화: {max_retry}회 실패")
                return ""

            resp = self._sanitize(resp)

            # 가비지 + 장르 오염
            fail = self._is_garbage(resp)
            if not fail:
                fail = self._check_genre(resp, genre)
            if fail:
                log(f"[FAIL] 제{ep_num}화: {fail} — 재시도 {attempt + 1}/{max_retry}")
                if attempt < max_retry - 1:
                    self.driver.reset_session()
                    time.sleep(5)
                    continue
                log(f"[SKIP] 제{ep_num}화: {max_retry}회 가비지")
                return ""

            if len(resp) < 4000:
                log(f"[!] 제{ep_num}화 응답 짧음 ({len(resp)}자 < 4000)")

            # 디렉터 루프
            best_resp = resp
            best_score = 0

            for d_round in range(10):
                passed, _, score = self._director_check(f"제{ep_num}화 원고")
                log(f"[Director] 제{ep_num}화: {score}점 {'PASS' if passed else 'REVISE'} (round {d_round + 1}/10)")

                if score > best_score:
                    best_score = score
                    best_resp = resp

                if passed:
                    break

                if d_round == 9:
                    log(f"[Director] 10회 실패 → 최고 {best_score}점 채택")
                    resp = best_resp
                    break

                revised = self._director_revision()
                if revised:
                    revised = self._sanitize(revised)
                if revised and self._validate_revision(resp, revised):
                    contam = self._check_genre(revised, genre)
                    if contam:
                        log(f"[Director] 수정본 {contam} → 현재본 유지")
                    else:
                        log(f"[Director] 수정본 채택 ({len(resp)}→{len(revised)}자)")
                        resp = revised
                else:
                    log("[Director] 수정본 부적격 → 현재본 유지")

            # 최소 점수
            if 0 < best_score < 50:
                log(f"[FAIL] 제{ep_num}화: {best_score}점 < 50점 → 재시도 {attempt + 1}/{max_retry}")
                if attempt < max_retry - 1:
                    self.driver.reset_session()
                    time.sleep(5)
                    continue
                log(f"[SKIP] 제{ep_num}화: {max_retry}회 저품질")
                return ""

            out_path.write_text(resp, encoding="utf-8")
            log(f"[OK] {out_path.name} ({len(resp)}자, 최종 {best_score}점, {elapsed}초)")
            time.sleep(5)
            return resp

        return ""

    # ── 메뉴 ──────────────────────────────────────────

    def _ensure_genre(self) -> str:
        cfg = self._load_config()
        genre = cfg.get("genre", "")
        if genre:
            return genre

        genres = list(GENRE_TIPS.keys())
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
        from bridge.runner import _C

        O, B, R = _C.ORANGE, _C.BOLD, _C.RESET
        DM, G = _C.DIM, _C.GOLD

        print(f"\n{'=' * 55}")
        print(f"  Free Writer — {self.project_dir.name}")
        print("  자유 형식 Blueprint → 원고 변환기")
        print(f"{'=' * 55}")

        bps = self._bp_files()
        mss = self._ms_files()
        cfg = self._load_config()
        genre = cfg.get("genre", "(미설정)")

        print(f"  장르: {genre}")
        print(f"  bible.txt: {'있음' if self.bible_path.exists() else '없음'}")
        print(f"  blueprints: {len(bps)}개")
        print(f"  manuscripts: {len(mss)}개")

        while True:
            print("\n  --- 메뉴 ---")
            print(f"  {O}{B}1. 전체 생성 (모든 blueprint → 원고){R}")
            print("  2. 범위 지정 생성")
            print("  g. 장르 변경")
            print("  m. 모델 변경 (fast/think/pro)")
            print("  0. 종료")

            c = input("\n  선택: ").strip()
            if c == "1":
                self._run_all()
            elif c == "2":
                self._run_range()
            elif c == "g":
                self._save_config({"genre": ""})
                self._ensure_genre()
            elif c == "m":
                print("  1. fast  2. think  3. pro")
                mc = input("  선택 (1-3): ").strip()
                model = {"1": "fast", "2": "think", "3": "pro"}.get(mc, "pro")
                self._save_config({"model": model})
                if self.driver:
                    self.driver.select_model(model)
                log(f"모델 변경: {model}")
            elif c == "0":
                break

    def _run_all(self):
        self._ensure_genre()
        self._init_driver()

        bps = self._bp_files()
        if not bps:
            log("[!] blueprints/ 에 txt 파일이 없습니다.")
            return

        mss = self._ms_files()
        start = len(mss)
        if start >= len(bps):
            log(f"모든 blueprint 처리 완료 ({len(bps)}개)")
            return

        total = len(bps)
        log(f"원고 생성: {start + 1}~{total}화 ({total - start}개)")

        if input("  시작? (Y/n): ").strip().lower() == "n":
            return

        self._generate_range(bps, start, total)

    def _run_range(self):
        self._ensure_genre()
        self._init_driver()

        bps = self._bp_files()
        if not bps:
            log("[!] blueprints/ 에 txt 파일이 없습니다.")
            return

        total = len(bps)
        mss = self._ms_files()
        default_start = len(mss) + 1

        while True:
            raw = input(f"  시작 화수 (1~{total}, 기본 {default_start}): ").strip()
            if not raw:
                s = default_start
                break
            try:
                s = int(raw)
                if 1 <= s <= total:
                    break
            except ValueError:
                pass

        while True:
            raw = input(f"  종료 화수 ({s}~{total}, 기본 {total}): ").strip()
            if not raw:
                e = total
                break
            try:
                e = int(raw)
                if s <= e <= total:
                    break
            except ValueError:
                pass

        log(f"원고 생성: {s}~{e}화")
        self._generate_range(bps, s - 1, e)

    def _generate_range(self, bps: list, start_idx: int, end_idx: int):
        count = 0
        start_time = time.time()

        with Spinner("원고 생성 중...", current=start_idx, total=end_idx) as sp:
            for i in range(start_idx, end_idx):
                ep_num = i + 1
                bp_path = bps[i]

                # 직전 원고
                prev_ms = ""
                prev_path = self.ms_dir / f"ep_{ep_num - 1:04d}.txt"
                if prev_path.exists():
                    prev_ms = prev_path.read_text(encoding="utf-8")

                sp.update(f"제{ep_num}화 원고", current=ep_num)
                log(f"제{ep_num}화 원고 ← {bp_path.name}")

                resp = self._generate_one(bp_path, ep_num, prev_ms)
                if not resp:
                    log(f"제{ep_num}화 스킵.")
                    continue

                count += 1
                self.driver.new_chat()
                time.sleep(2)

        elapsed = int(time.time() - start_time)
        h, rem = divmod(elapsed, 3600)
        m, s = divmod(rem, 60)
        t = f"{h}시간 {m}분 {s}초" if h else f"{m}분 {s}초" if m else f"{s}초"
        log(f"완료: {count}개 원고 생성 (소요: {t})")


# ── 메인 ──────────────────────────────────────────────


def main():
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    print(f"\n{'=' * 55}")
    print("  Free Writer — 자유 형식 Blueprint → 원고 ($0)")
    print("  어떤 형식의 blueprint든 원고로 변환")
    print(f"{'=' * 55}")

    proj_root = Path(__file__).parent / "projects_free"
    proj_root.mkdir(exist_ok=True)

    # 프로젝트 목록
    projects = sorted([d for d in proj_root.iterdir() if d.is_dir() and (d / "blueprints").exists()])

    print("\n  프로젝트 선택:")
    for i, p in enumerate(projects, 1):
        bp_count = len(list((p / "blueprints").glob("*.txt")))
        print(f"    {i}. {p.name} (blueprint {bp_count}개)")
    print(f"    {len(projects) + 1}. [새 프로젝트]")

    while True:
        raw = input(f"\n  선택 (1-{len(projects) + 1}): ").strip()
        try:
            idx = int(raw)
            if 1 <= idx <= len(projects):
                proj_dir = projects[idx - 1]
                break
            if idx == len(projects) + 1:
                name = input("  프로젝트명: ").strip()
                if not name:
                    return
                proj_dir = proj_root / name
                proj_dir.mkdir(exist_ok=True)
                (proj_dir / "blueprints").mkdir(exist_ok=True)
                (proj_dir / "manuscripts").mkdir(exist_ok=True)
                print(f"\n  프로젝트 생성: {proj_dir}")
                print("  → blueprints/ 폴더에 txt 파일을 넣으세요.")
                print("  → bible.txt, style_guide.txt는 선택사항입니다.")
                return
        except ValueError:
            pass

    print(f"\n  프로젝트: {proj_dir.name}")
    print(f"  위치: {proj_dir}")

    runner = FreeWriter(proj_dir)
    try:
        runner.run()
    except KeyboardInterrupt:
        print("\n\n  중단됨.")


if __name__ == "__main__":
    main()
