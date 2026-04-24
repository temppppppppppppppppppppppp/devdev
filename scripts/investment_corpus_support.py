from __future__ import annotations

# utf8-hygiene: allow-file -- legacy corpus extraction regex patterns use Hangul-adjacent optional tokens.

import hashlib
import json
import posixpath
import re
import shutil
import unicodedata
import zipfile
from bisect import bisect_right
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

UTC = timezone.utc
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

DEFAULT_TITLE_MANIFEST_PATH = Path(__file__).with_name("investment_epub_title_manifest.json")
TEXT_SUFFIXES = {".xhtml", ".html", ".htm"}
SKIP_NAME_MARKERS = ("cover", "copyright", "toc", "nav", "titlepage", "contents")
COLOPHON_MARKERS = ("전자책 출간일", "펴낸이", "펴낸곳", "이메일", "팩스", "isbn")
MIN_BODY_CHARS = 500
MIN_SAMPLE_TOKENS = 40
DEFAULT_SYSTEM_INSTRUCTION = "앞 문체와 호흡을 유지해 자연스럽게 이어 쓴다."
STYLE_CONTROL_SYSTEM_INSTRUCTION = "주어진 제어 조건과 도입 앵커를 유지해 한국형 웹소설 회차 초안을 작성한다."
DEFAULT_STYLE_CONTROL_GENRE = "현대판타지 / 재벌 / 기업 / 회귀"
GEMINI_SUPERVISED_TUNING_USD_PER_MILLION_TOKENS = 25.0
DEFAULT_USD_KRW_RATE = 1470.0
SCENE_BREAK_RE = re.compile(
    r"^(?:[*#=\-~_]{3,}|(?:\*\s*){3,}|\[(?:장면|시점|전환|컷)[^\]]{0,20}\])$",
    re.IGNORECASE,
)
HEADING_RE = re.compile(r"^\d+\s*화[.\s].*$")
TRANSITION_PREFIXES = (
    "한편",
    "그 시각",
    "잠시 후",
    "다음 날",
    "며칠 뒤",
    "그날 밤",
    "이후",
    "그러는 사이",
)
TONE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "상승": ("성공", "승리", "상승", "확대", "수익", "돌파", "기회", "축하", "미소", "행복"),
    "압박": ("위기", "불안", "긴장", "추락", "도망", "감옥", "각혈", "피", "절망", "흔들"),
    "복수": ("복수", "원망", "살생부", "되갚", "응징", "원수", "증오"),
    "협상": ("협상", "계약", "제안", "조건", "합의", "설득", "지분", "투자", "인수"),
    "가문": ("후계", "손자", "아이", "며느리", "증조", "가문", "혼인"),
}
GOAL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "복수 동기 각인": ("복수", "원망", "살생부", "되갚", "응징", "회귀", "두 번째 기회"),
    "기업 우위 확보": ("지분", "인수", "계약", "투자", "최대주주", "실소유주"),
    "위기 돌파": ("위기", "부도", "압박", "추락", "감옥", "도망", "각혈", "피", "추징금", "징역"),
    "관계/가문 진전": ("결혼", "아이", "며느리", "손자", "증조", "혼인"),
    "정체/비밀 공개": ("정체", "비밀", "실소유주", "드러", "밝혀", "회귀"),
    "판 확대": ("확장", "글로벌", "시장", "방어벽", "동맹", "타워"),
}
TONE_LABEL_WEIGHTS = {"상승": 1.0, "압박": 1.4, "복수": 1.8, "협상": 1.2, "가문": 0.8}
GOAL_LABEL_WEIGHTS = {
    "복수 동기 각인": 1.8,
    "기업 우위 확보": 1.2,
    "위기 돌파": 1.4,
    "관계/가문 진전": 1.0,
    "정체/비밀 공개": 1.4,
    "판 확대": 1.1,
}
CONFLICT_KEYWORDS = (
    "위기",
    "압박",
    "복수",
    "배신",
    "전쟁",
    "함정",
    "추락",
    "부도",
    "조사",
    "갈등",
    "원망",
    "긴장",
    "피",
    "각혈",
)
COMMON_SURNAMES = (
    "김",
    "이",
    "박",
    "최",
    "정",
    "강",
    "조",
    "윤",
    "장",
    "임",
    "한",
    "오",
    "서",
    "신",
    "권",
    "황",
    "안",
    "송",
    "전",
    "홍",
    "유",
    "고",
    "문",
    "양",
    "손",
    "배",
    "허",
    "남",
    "심",
    "노",
    "하",
    "곽",
    "성",
    "차",
    "주",
    "우",
    "구",
    "나",
    "민",
    "진",
    "지",
    "엄",
    "채",
    "원",
)
PERSON_STOPWORDS = {
    "주인공",
    "아버지",
    "어머니",
    "할아버지",
    "할머니",
    "형님",
    "누나",
    "오빠",
    "언니",
    "동생",
    "회장님",
    "부회장",
    "사장님",
    "대표님",
    "팀장님",
    "실장님",
    "부장님",
    "차장님",
    "과장님",
    "대리님",
    "상무님",
    "전무님",
    "이사님",
    "상무",
    "전무",
    "이사",
    "대표",
    "회장",
    "사장",
    "부장",
    "차장",
    "과장",
    "대리",
    "실장",
    "팀장",
    "비서실",
    "재벌가",
    "재벌집",
    "투자자",
    "주주들",
    "이사회",
    "대한민",
    "대한국",
}
ORG_SUFFIXES = (
    "그룹",
    "홀딩스",
    "전자",
    "물산",
    "건설",
    "증권",
    "캐피탈",
    "미디어",
    "상사",
    "제약",
    "바이오",
    "인터내셔널",
    "모터스",
    "조선",
    "통신",
    "화학",
    "식품",
    "벤처스",
    "게임즈",
    "엔터",
    "엔터테인먼트",
    "스튜디오",
    "호텔",
    "백화점",
)
ORG_STOPWORDS = set(ORG_SUFFIXES) | {
    "대기업",
    "중견기업",
    "중소기업",
    "재벌그룹",
    "금융그룹",
    "증권사",
    "은행권",
}
PERSON_ALIAS_FAMILIES = (
    "강",
    "고",
    "권",
    "김",
    "나",
    "남",
    "문",
    "민",
    "박",
    "배",
    "백",
    "서",
    "성",
    "손",
    "송",
    "신",
    "안",
    "양",
    "오",
    "우",
    "유",
    "윤",
    "이",
    "임",
    "장",
    "전",
    "정",
    "조",
    "진",
    "차",
    "채",
    "최",
    "한",
    "허",
    "홍",
    "황",
)
PERSON_ALIAS_GIVEN = (
    "도윤",
    "서진",
    "하준",
    "민성",
    "태윤",
    "지호",
    "준혁",
    "시우",
    "선우",
    "도현",
    "유진",
    "소윤",
    "서윤",
    "하린",
    "유나",
    "지안",
    "채원",
    "예린",
    "현서",
    "민지",
    "다온",
    "은호",
    "재현",
    "수빈",
    "지민",
    "현우",
    "예준",
    "서우",
    "가은",
    "연서",
)
COMMON_GIVEN_NAMES = {
    "가은",
    "강민",
    "건우",
    "경민",
    "규리",
    "다온",
    "도윤",
    "도현",
    "동현",
    "동훈",
    "민규",
    "민성",
    "민서",
    "민석",
    "민재",
    "민정",
    "민지",
    "서연",
    "서우",
    "서윤",
    "서준",
    "서진",
    "석원",
    "선우",
    "성민",
    "성훈",
    "소윤",
    "수빈",
    "수아",
    "수연",
    "수현",
    "승민",
    "승우",
    "승한",
    "시우",
    "아린",
    "연서",
    "연우",
    "예린",
    "예성",
    "예은",
    "예준",
    "유나",
    "유리",
    "유민",
    "유석",
    "유정",
    "유진",
    "윤아",
    "윤원",
    "윤재",
    "은지",
    "은호",
    "이다",
    "재현",
    "재희",
    "정민",
    "정우",
    "정원",
    "정훈",
    "지민",
    "지성",
    "지안",
    "지우",
    "지윤",
    "지은",
    "지호",
    "지훈",
    "진우",
    "진희",
    "채린",
    "채원",
    "태성",
    "태윤",
    "태준",
    "태호",
    "하린",
    "하준",
    "현서",
    "현석",
    "현수",
    "현우",
    "현정",
    "현주",
    "혜린",
    "혜진",
    "호준",
    "효진",
    "희원",
}
ORG_ALIAS_PREFIXES = (
    "한백",
    "동림",
    "세원",
    "서광",
    "유선",
    "해원",
    "태림",
    "성한",
    "재민",
    "정한",
    "다온",
    "율성",
    "현우",
    "은성",
    "서현",
    "민하",
    "청우",
    "한결",
    "선재",
    "도원",
    "신우",
    "가온",
    "로한",
    "이안",
    "예성",
    "남해",
    "청림",
    "세강",
    "우성",
    "한울",
)
_SURNAME_PATTERN = "|".join(re.escape(name) for name in COMMON_SURNAMES)
_ORG_SUFFIX_PATTERN = "|".join(sorted((re.escape(name) for name in ORG_SUFFIXES), key=len, reverse=True))
PERSON_CANDIDATE_RE = re.compile(
    rf"(?<![가-힣A-Za-z])(?P<name>(?:{_SURNAME_PATTERN})[가-힣]{{2}})"
    rf"(?=(?:[은는이가을를와과도만의에로께서한테에게보다부터까지랑씨님]|[\s.,!?\"'“”‘’…:;\)\]])|$)"
)
ORG_CANDIDATE_RE = re.compile(
    rf"(?<![가-힣A-Za-z0-9])(?P<name>[A-Za-z0-9가-힣]{{2,20}}(?:{_ORG_SUFFIX_PATTERN}))"
    rf"(?=(?:[은는이가을를와과도만의에로께서한테에게보다부터까지랑]|[\s.,!?\"'“”‘’…:;\)\]])|$)"
)

PURE_NUMBER_RE = re.compile(r"^(?P<episode>\d+)\.epub$", re.IGNORECASE)
ID_NUMBER_RE = re.compile(r"^(?P<source_id>\d+)_(?P<episode>\d+)\.epub$", re.IGNORECASE)
TITLE_NUMBER_HWA_RE = re.compile(r".*?(?P<episode>\d+)화\.epub$", re.IGNORECASE)
TITLE_NUMBER_PLAIN_SUFFIX_RE = re.compile(r".*?[_ ](?P<episode>\d+)\.epub$", re.IGNORECASE)
XML_ENCODING_RE = re.compile(rb'encoding=["\'](?P<encoding>[A-Za-z0-9._-]+)["\']')
HANGUL_RE = re.compile(r"[가-힣]")


@dataclass(slots=True)
class SsotSelection:
    title: str
    title_dir: Path
    source_path: Path
    rule: str
    raw_epub_count: int
    ssot_epub_count: int
    root_epub_count: int
    is_root_selection: bool
    subdir_counts: dict[str, int]


@dataclass(slots=True)
class ExtractedEpisode:
    episode: int
    source_epub: str
    content_entries: list[str]
    skipped_entries: list[str]
    text: str
    text_hash: str


class _TextExtractor(HTMLParser):
    BLOCK_TAGS = {
        "article",
        "blockquote",
        "br",
        "dd",
        "div",
        "dt",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "li",
        "ol",
        "p",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }
    SKIP_TAGS = {"head", "link", "meta", "script", "style", "title"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if lowered in self.BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in self.SKIP_TAGS:
            if self._skip_depth:
                self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if lowered in self.BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth or not data:
            return
        self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts)


def now_iso() -> str:
    return datetime.now(UTC).astimezone().isoformat(timespec="seconds")


def load_title_manifest(path: Path | None = None) -> list[str]:
    manifest_path = path or DEFAULT_TITLE_MANIFEST_PATH
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    titles = payload.get("titles")
    if not isinstance(titles, list) or not all(isinstance(title, str) and title for title in titles):
        msg = f"invalid title manifest: {manifest_path}"
        raise ValueError(msg)
    return titles


def slugify_title(title: str) -> str:
    slug = re.sub(r"[^\w]+", "_", title, flags=re.UNICODE)
    slug = slug.strip("_")
    return slug or "untitled"


def classify_filename(filename: str) -> str:
    if PURE_NUMBER_RE.match(filename):
        return "pure_number"
    if ID_NUMBER_RE.match(filename):
        return "id_number"
    if TITLE_NUMBER_HWA_RE.match(filename):
        return "title_number_hwa"
    if TITLE_NUMBER_PLAIN_SUFFIX_RE.match(filename):
        return "title_number_plain_suffix"
    return "unknown"


def parse_episode_number(filename: str) -> int:
    for pattern in (PURE_NUMBER_RE, ID_NUMBER_RE, TITLE_NUMBER_HWA_RE, TITLE_NUMBER_PLAIN_SUFFIX_RE):
        match = pattern.match(filename)
        if match:
            return int(match.group("episode"))
    msg = f"unsupported epub filename pattern: {filename}"
    raise ValueError(msg)


def title_dir_for(source_root: Path, title: str) -> Path:
    return source_root / f"[연재]{title}"


def _count_epubs(path: Path, *, recursive: bool) -> int:
    iterator = path.rglob("*.epub") if recursive else path.glob("*.epub")
    return sum(1 for item in iterator if item.is_file())


def select_ssot_dir(title: str, title_dir: Path) -> SsotSelection:
    root_epub_count = _count_epubs(title_dir, recursive=False)
    subdir_counts: dict[str, int] = {}
    for child in title_dir.iterdir():
        if child.is_dir():
            subdir_counts[child.name] = _count_epubs(child, recursive=True)

    populated_subdirs = {name: count for name, count in subdir_counts.items() if count > 0}
    raw_epub_count = root_epub_count + sum(populated_subdirs.values())

    if populated_subdirs:
        final_candidates = sorted(
            ((name, count) for name, count in populated_subdirs.items() if "최종" in name),
            key=lambda item: (-item[1], item[0]),
        )
        if final_candidates:
            name, count = final_candidates[0]
            return SsotSelection(
                title=title,
                title_dir=title_dir,
                source_path=title_dir / name,
                rule="prefer-final",
                raw_epub_count=raw_epub_count,
                ssot_epub_count=count,
                root_epub_count=root_epub_count,
                is_root_selection=False,
                subdir_counts=populated_subdirs,
            )

        renamed_candidates = sorted(
            (
                (name, count)
                for name, count in populated_subdirs.items()
                if "필명변경후" in name or "필명갈음후" in name
            ),
            key=lambda item: (-item[1], item[0]),
        )
        if renamed_candidates:
            name, count = renamed_candidates[0]
            return SsotSelection(
                title=title,
                title_dir=title_dir,
                source_path=title_dir / name,
                rule="prefer-renamed-after",
                raw_epub_count=raw_epub_count,
                ssot_epub_count=count,
                root_epub_count=root_epub_count,
                is_root_selection=False,
                subdir_counts=populated_subdirs,
            )

    max_subdir_count = max(populated_subdirs.values(), default=0)
    if root_epub_count > 0 and root_epub_count >= max_subdir_count:
        return SsotSelection(
            title=title,
            title_dir=title_dir,
            source_path=title_dir,
            rule="prefer-root-superset-or-equal",
            raw_epub_count=raw_epub_count,
            ssot_epub_count=root_epub_count,
            root_epub_count=root_epub_count,
            is_root_selection=True,
            subdir_counts=populated_subdirs,
        )

    if "연재이펍" in populated_subdirs:
        return SsotSelection(
            title=title,
            title_dir=title_dir,
            source_path=title_dir / "연재이펍",
            rule="prefer-standard-serial-epub",
            raw_epub_count=raw_epub_count,
            ssot_epub_count=populated_subdirs["연재이펍"],
            root_epub_count=root_epub_count,
            is_root_selection=False,
            subdir_counts=populated_subdirs,
        )

    if populated_subdirs:
        name, count = sorted(populated_subdirs.items(), key=lambda item: (-item[1], item[0]))[0]
        return SsotSelection(
            title=title,
            title_dir=title_dir,
            source_path=title_dir / name,
            rule="prefer-largest-epub-subdir",
            raw_epub_count=raw_epub_count,
            ssot_epub_count=count,
            root_epub_count=root_epub_count,
            is_root_selection=False,
            subdir_counts=populated_subdirs,
        )

    return SsotSelection(
        title=title,
        title_dir=title_dir,
        source_path=title_dir,
        rule="root-only",
        raw_epub_count=raw_epub_count,
        ssot_epub_count=root_epub_count,
        root_epub_count=root_epub_count,
        is_root_selection=True,
        subdir_counts=populated_subdirs,
    )


def list_selected_epubs(selection: SsotSelection) -> list[Path]:
    iterator = (
        selection.source_path.glob("*.epub") if selection.is_root_selection else selection.source_path.rglob("*.epub")
    )
    epubs = [path for path in iterator if path.is_file()]
    return sorted(epubs, key=lambda path: (parse_episode_number(path.name), path.name))


def _decode_zip_text(raw: bytes) -> str:
    candidates: list[str] = []
    match = XML_ENCODING_RE.search(raw[:200])
    if match:
        candidates.append(match.group("encoding").decode("ascii", errors="ignore"))
    candidates.extend(["utf-8-sig", "utf-8", "cp949", "euc-kr"])

    seen: set[str] = set()
    for encoding in candidates:
        normalized = encoding.lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text)
    normalized = normalized.replace("\ufeff", "").replace("\xa0", " ")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in normalized.split("\n")]
    compacted: list[str] = []
    previous_blank = False
    for line in lines:
        if not line:
            if compacted and not previous_blank:
                compacted.append("")
            previous_blank = True
            continue
        compacted.append(line)
        previous_blank = False
    return "\n".join(compacted).strip()


def estimate_token_count(text: str) -> int:
    normalized = _normalize_text(text)
    if not normalized:
        return 0
    korean_chars = sum(1 for char in normalized if "가" <= char <= "힣")
    other_chars = len(normalized) - korean_chars
    estimated = round(korean_chars / 1.5 + other_chars / 4)
    return max(1, estimated)


def _split_paragraphs(text: str) -> list[str]:
    normalized = _normalize_text(text)
    if not normalized:
        return []
    return [paragraph.strip() for paragraph in normalized.split("\n\n") if paragraph.strip()]


def _join_paragraphs(paragraphs: list[str]) -> str:
    return _normalize_text("\n\n".join(paragraphs))


def _is_scene_break(paragraph: str) -> bool:
    stripped = paragraph.strip()
    if not stripped:
        return False
    if SCENE_BREAK_RE.match(stripped):
        return True
    return stripped.startswith("[") and any(token in stripped for token in ("장면", "시점", "전환", "컷"))


def _paragraph_token_lengths(paragraphs: list[str]) -> list[int]:
    return [estimate_token_count(paragraph) for paragraph in paragraphs]


def _choose_split_index(paragraphs: list[str], token_lengths: list[int], target_tokens: int) -> int:
    if len(paragraphs) < 2:
        return 1

    best_index = 1
    best_score: tuple[int, int, int] | None = None
    running_tokens = 0
    for index in range(1, len(paragraphs)):
        running_tokens += token_lengths[index - 1]
        near_scene_break = _is_scene_break(paragraphs[index - 1]) or _is_scene_break(paragraphs[index])
        score = (0 if near_scene_break else 1, abs(running_tokens - target_tokens), index)
        if best_score is None or score < best_score:
            best_score = score
            best_index = index
    return best_index


def _window_end_index(
    paragraphs: list[str],
    token_lengths: list[int],
    *,
    start_index: int,
    target_tokens: int,
) -> int:
    index = start_index
    collected_tokens = 0
    minimum_target = max(1, target_tokens)
    while index < len(paragraphs) and collected_tokens < minimum_target:
        collected_tokens += token_lengths[index]
        index += 1
    if index == start_index and index < len(paragraphs):
        return start_index + 1
    if index < len(paragraphs) and _is_scene_break(paragraphs[index]):
        index += 1
    return index


def _start_indices(token_lengths: list[int], total_needed_tokens: int, stride_tokens: int) -> list[int]:
    if not token_lengths:
        return []

    start_offsets: list[int] = []
    running_tokens = 0
    for length in token_lengths:
        start_offsets.append(running_tokens)
        running_tokens += length

    max_start_tokens = max(0, running_tokens - total_needed_tokens)
    targets = list(range(0, max_start_tokens + 1, max(1, stride_tokens)))
    if not targets or targets[-1] != max_start_tokens:
        targets.append(max_start_tokens)

    indices: list[int] = []
    seen: set[int] = set()
    for target in targets:
        index = max(0, bisect_right(start_offsets, target) - 1)
        if index not in seen:
            seen.add(index)
            indices.append(index)
    return indices


def _take_head_by_tokens(paragraphs: list[str], token_lengths: list[int], target_tokens: int) -> str:
    if not paragraphs:
        return ""
    end_index = _window_end_index(paragraphs, token_lengths, start_index=0, target_tokens=target_tokens)
    return _join_paragraphs(paragraphs[:end_index])


def _take_tail_by_tokens(paragraphs: list[str], token_lengths: list[int], target_tokens: int) -> str:
    if not paragraphs:
        return ""

    minimum_target = max(1, target_tokens)
    collected_tokens = 0
    start_index = len(paragraphs)
    for index in range(len(paragraphs) - 1, -1, -1):
        collected_tokens += token_lengths[index]
        start_index = index
        if collected_tokens >= minimum_target:
            break
    return _join_paragraphs(paragraphs[start_index:])


def _trim_episode_heading(paragraphs: list[str]) -> list[str]:
    if not paragraphs:
        return []
    first = paragraphs[0].strip()
    if HEADING_RE.match(first):
        return paragraphs[1:]
    return paragraphs


def _dialogue_ratio(text: str) -> float:
    normalized = _normalize_text(text)
    if not normalized:
        return 0.0
    quote_spans = re.findall(r"[“\"']([^”\"']+)[”\"']", normalized)
    quoted_length = sum(len(span) for span in quote_spans)
    return max(0.0, min(1.0, quoted_length / max(1, len(normalized))))


def _dialogue_ratio_label(ratio: float) -> str:
    if ratio < 0.12:
        return "낮음"
    if ratio < 0.28:
        return "중간"
    return "높음"


def _narrative_pov(text: str) -> str:
    normalized = _normalize_text(text)
    first_person_hits = sum(normalized.count(token) for token in (" 나는 ", " 내가 ", " 나는", "\n나는 ", "\n내가 "))
    first_person_hits += normalized.count("내가")
    first_person_hits += normalized.count("나는")
    third_person_hits = sum(normalized.count(token) for token in (" 그는 ", " 그녀는 ", " 그가 ", " 그녀가 "))
    if first_person_hits >= max(3, third_person_hits + 1):
        return "1인칭 내면 밀착"
    if third_person_hits >= max(3, first_person_hits + 1):
        return "3인칭 근접"
    return "혼합/불명"


def _score_keyword_buckets(text: str, keyword_map: dict[str, tuple[str, ...]]) -> dict[str, int]:
    normalized = _normalize_text(text)
    scores: dict[str, int] = {}
    for label, keywords in keyword_map.items():
        scores[label] = sum(normalized.count(keyword) for keyword in keywords)
    return scores


def _top_keyword_label(
    text: str,
    keyword_map: dict[str, tuple[str, ...]],
    *,
    default: str,
    label_weights: dict[str, float] | None = None,
) -> str:
    scores = _score_keyword_buckets(text, keyword_map)
    best_label = default
    best_score = -1.0
    for label, score in scores.items():
        weighted_score = score * (label_weights or {}).get(label, 1.0)
        if weighted_score > best_score:
            best_label = label
            best_score = weighted_score
    return best_label if best_score > 0 else default


def _conflict_intensity(text: str) -> int:
    normalized = _normalize_text(text)
    if not normalized:
        return 1
    weighted_hits = 0
    for keyword in CONFLICT_KEYWORDS:
        multiplier = 2 if keyword in {"복수", "배신", "전쟁", "함정", "부도", "추락", "각혈", "피"} else 1
        weighted_hits += normalized.count(keyword) * multiplier
    punctuation_hits = normalized.count("!") + normalized.count("?")
    density = ((weighted_hits * 30) + punctuation_hits * 5) / max(1, estimate_token_count(normalized))
    if density >= 1.00:
        return 5
    if density >= 0.72:
        return 4
    if density >= 0.48:
        return 3
    if density >= 0.24:
        return 2
    return 1


def _opening_mode(paragraphs: list[str]) -> str:
    if not paragraphs:
        return "상황 도입"
    first = paragraphs[0].strip()
    if first.startswith(("“", '"', "'")):
        return "대사 도입"
    if any(token in first for token in ("!", "?", "쿨럭", "피", "충격", "폭락", "추징금")):
        return "충격 도입"
    return "상황 도입"


def _scene_count(paragraphs: list[str], token_lengths: list[int]) -> int:
    if not paragraphs:
        return 0
    explicit_breaks = sum(1 for paragraph in paragraphs if _is_scene_break(paragraph))
    if explicit_breaks:
        return explicit_breaks + 1
    transition_hits = sum(1 for paragraph in paragraphs if paragraph.startswith(TRANSITION_PREFIXES))
    rough_by_tokens = max(1, round(sum(token_lengths) / 320))
    return max(1, min(8, max(rough_by_tokens, 1 + transition_hits)))


def _cliffhanger_type(text: str) -> str:
    tail = _normalize_text(text)
    if not tail:
        return "다음 국면 예고형"
    if any(token in tail for token in ("비밀", "정체", "실소유주", "드러", "밝혀", "회귀")):
        return "비밀 공개형"
    if any(token in tail for token in ("위기", "함정", "추락", "부도", "체포", "각혈", "피")):
        return "위기 도래형"
    if any(token in tail for token in ("축하", "성공", "미소", "행복", "완.", "完", "수락")):
        return "보상형"
    if any(token in tail for token in ("복수", "전쟁", "시작", "지켜 낼", "돌아오", "간다")):
        return "선언형"
    if "?" in tail and any(token in tail for token in ("누구", "무엇", "어떻게", "왜")):
        return "질문형"
    return "다음 국면 예고형"


def _style_pacing(scene_count: int, dialogue_ratio: float) -> str:
    if scene_count >= 5 or dialogue_ratio >= 0.30:
        return "빠름"
    if scene_count <= 2 and dialogue_ratio < 0.12:
        return "느림"
    return "중간"


def _style_rules(
    *, pov: str, dialogue_ratio_label: str, scene_count: int, tone: str, pacing: str, opening_mode: str
) -> list[str]:
    rules: list[str] = []
    if pov == "1인칭 내면 밀착":
        rules.append("주인공의 계산과 감정을 1인칭으로 즉시 드러낸다.")
    elif pov == "3인칭 근접":
        rules.append("주인공 시점에 바짝 붙은 3인칭 서술을 유지한다.")
    else:
        rules.append("주인공 중심의 밀착 시점을 유지한다.")

    if dialogue_ratio_label == "높음":
        rules.append("대사와 짧은 반응문을 교차해 리듬을 빠르게 유지한다.")
    elif dialogue_ratio_label == "중간":
        rules.append("대사와 설명을 번갈아 배치해 장면을 밀어붙인다.")
    else:
        rules.append("짧은 서술문 위주로 상황을 압축하고 필요한 순간에만 대사를 쓴다.")

    if scene_count >= 4:
        rules.append("장면 전환을 자주 사용해 정보와 긴장을 빠르게 넘긴다.")
    elif scene_count <= 2:
        rules.append("한 국면의 압박을 길게 끌며 감정선과 계산을 눌러 쌓는다.")
    else:
        rules.append("2~4개 장면으로 압박과 보상을 교차한다.")

    if tone == "복수":
        rules.append("원망과 복수 동기를 짧고 강한 문장으로 박아 넣는다.")
    elif tone == "압박":
        rules.append("몸 상태, 표정, 주변 반응을 짧게 끊어 긴장을 올린다.")
    elif tone == "협상":
        rules.append("직함, 조건, 숫자를 박아 넣어 기업물의 힘을 살린다.")
    elif tone == "상승":
        rules.append("성과와 우위를 숫자와 반응으로 선명하게 보여 준다.")
    else:
        rules.append("가문과 관계 변화를 감정 보상과 함께 묶어 준다.")

    if pacing == "빠름":
        rules.append("문단은 짧게 끊고 장면마다 결과를 하나씩 남긴다.")
    elif pacing == "느림":
        rules.append("문장 호흡을 너무 길게 늘리지 말고 압박을 천천히 조여 간다.")

    if opening_mode == "충격 도입":
        rules.append("첫 장면의 충격을 바로 서사의 추진력으로 연결한다.")
    elif opening_mode == "대사 도입":
        rules.append("첫 대사에서 인물 관계와 권력차를 곧바로 드러낸다.")
    else:
        rules.append("도입 장면의 상황 설명은 짧게 끝내고 갈등을 바로 호출한다.")
    return rules


def _find_completion_start_index(
    paragraphs: list[str], token_lengths: list[int], *, target_completion_tokens: int
) -> int:
    if len(paragraphs) < 2:
        return 1
    total_tokens = sum(token_lengths)
    running_tokens = 0
    best_index = 1
    best_score: tuple[int, int, int] | None = None
    for index in range(1, len(paragraphs)):
        running_tokens += token_lengths[index - 1]
        remaining_tokens = total_tokens - running_tokens
        near_scene_break = _is_scene_break(paragraphs[index - 1]) or _is_scene_break(paragraphs[index])
        score = (0 if near_scene_break else 1, abs(remaining_tokens - target_completion_tokens), -index)
        if best_score is None or score < best_score:
            best_score = score
            best_index = index
    return best_index


def _format_style_control_prompt(
    *,
    title: str,
    genre: str,
    task_name: str,
    section_goal: str,
    anchor_text: str,
    pov: str,
    tone: str,
    episode_goal: str,
    conflict_intensity: int,
    scene_count: int,
    dialogue_ratio: float,
    dialogue_ratio_label: str,
    cliffhanger_type: str,
    pacing: str,
    opening_mode: str,
    style_rules: list[str],
) -> str:
    dialogue_percent = round(dialogue_ratio * 100)
    rules_text = "\n".join(f"- {rule}" for rule in style_rules)
    return _normalize_text(
        f"""
작품: {title}
훈련 과제: {task_name}

장르: {genre}
시점: {pov}
톤: {tone}
회차 목표: {episode_goal}
구간 목표: {section_goal}
갈등 강도: {conflict_intensity}/5
장면 수: {scene_count}
대사 비율: {dialogue_ratio_label} ({dialogue_percent}%)
클리프행어 유형: {cliffhanger_type}
전개 속도: {pacing}
도입 방식: {opening_mode}

문체 규칙:
{rules_text}

도입 앵커:
{anchor_text}

요구사항:
- 위 제어값과 문체 규칙을 유지한다.
- 앵커 다음 장면부터 자연스럽게 이어 쓴다.
- {section_goal}
"""
    )


def _build_style_control_examples(
    title: str,
    text: str,
    *,
    genre: str,
    body_anchor_tokens: int,
    body_completion_tokens: int,
    ending_prompt_tokens: int,
    ending_completion_tokens: int,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    paragraphs = _trim_episode_heading(_split_paragraphs(text))
    if len(paragraphs) < 3:
        return ([], {})

    token_lengths = _paragraph_token_lengths(paragraphs)
    if sum(token_lengths) < max(
        body_anchor_tokens + body_completion_tokens, ending_prompt_tokens + ending_completion_tokens
    ):
        return ([], {})

    full_text = _join_paragraphs(paragraphs)
    tail_window = _take_tail_by_tokens(paragraphs, token_lengths, max(ending_completion_tokens, 220))
    dialogue_ratio = _dialogue_ratio(full_text)
    dialogue_ratio_label = _dialogue_ratio_label(dialogue_ratio)
    pov = _narrative_pov(full_text)
    tone = _top_keyword_label(full_text, TONE_KEYWORDS, default="상승", label_weights=TONE_LABEL_WEIGHTS)
    episode_goal = _top_keyword_label(
        full_text,
        GOAL_KEYWORDS,
        default="기업 우위 확보",
        label_weights=GOAL_LABEL_WEIGHTS,
    )
    conflict_intensity = _conflict_intensity(full_text)
    scene_count = _scene_count(paragraphs, token_lengths)
    cliffhanger_type = _cliffhanger_type(tail_window)
    pacing = _style_pacing(scene_count, dialogue_ratio)
    opening_mode = _opening_mode(paragraphs)
    style_rules = _style_rules(
        pov=pov,
        dialogue_ratio_label=dialogue_ratio_label,
        scene_count=scene_count,
        tone=tone,
        pacing=pacing,
        opening_mode=opening_mode,
    )

    examples: list[dict[str, str]] = []

    body_anchor_end = _window_end_index(paragraphs, token_lengths, start_index=0, target_tokens=body_anchor_tokens)
    body_completion_end = _window_end_index(
        paragraphs,
        token_lengths,
        start_index=body_anchor_end,
        target_tokens=body_completion_tokens,
    )
    body_anchor = _join_paragraphs(paragraphs[:body_anchor_end])
    body_completion = _join_paragraphs(paragraphs[body_anchor_end:body_completion_end])
    if (
        estimate_token_count(body_anchor) >= MIN_SAMPLE_TOKENS
        and estimate_token_count(body_completion) >= MIN_SAMPLE_TOKENS
    ):
        examples.append(
            {
                "section": "middle_continuation",
                "prompt": _format_style_control_prompt(
                    title=title,
                    genre=genre,
                    task_name="중반 전개 이어쓰기",
                    section_goal="주인공의 계산과 우위 확보 과정을 중반부 전개로 밀어붙인다.",
                    anchor_text=body_anchor,
                    pov=pov,
                    tone=tone,
                    episode_goal=episode_goal,
                    conflict_intensity=conflict_intensity,
                    scene_count=scene_count,
                    dialogue_ratio=dialogue_ratio,
                    dialogue_ratio_label=dialogue_ratio_label,
                    cliffhanger_type=cliffhanger_type,
                    pacing=pacing,
                    opening_mode=opening_mode,
                    style_rules=style_rules,
                ),
                "completion": body_completion,
            }
        )

    ending_start = _find_completion_start_index(
        paragraphs,
        token_lengths,
        target_completion_tokens=ending_completion_tokens,
    )
    ending_prompt_source = paragraphs[:ending_start]
    ending_prompt = _take_tail_by_tokens(
        ending_prompt_source,
        _paragraph_token_lengths(ending_prompt_source),
        ending_prompt_tokens,
    )
    ending_completion_end = _window_end_index(
        paragraphs,
        token_lengths,
        start_index=ending_start,
        target_tokens=ending_completion_tokens,
    )
    ending_completion = _join_paragraphs(paragraphs[ending_start:ending_completion_end])
    if (
        estimate_token_count(ending_prompt) >= MIN_SAMPLE_TOKENS
        and estimate_token_count(ending_completion) >= MIN_SAMPLE_TOKENS
    ):
        examples.append(
            {
                "section": "ending_cliffhanger",
                "prompt": _format_style_control_prompt(
                    title=title,
                    genre=genre,
                    task_name="종결 장면 작성",
                    section_goal=f"회차를 {cliffhanger_type}로 닫아 다음 화를 당긴다.",
                    anchor_text=ending_prompt,
                    pov=pov,
                    tone=tone,
                    episode_goal=episode_goal,
                    conflict_intensity=conflict_intensity,
                    scene_count=scene_count,
                    dialogue_ratio=dialogue_ratio,
                    dialogue_ratio_label=dialogue_ratio_label,
                    cliffhanger_type=cliffhanger_type,
                    pacing=pacing,
                    opening_mode=opening_mode,
                    style_rules=style_rules,
                ),
                "completion": ending_completion,
            }
        )

    profile = {
        "pov": pov,
        "tone": tone,
        "episode_goal": episode_goal,
        "conflict_intensity": conflict_intensity,
        "scene_count": scene_count,
        "dialogue_ratio": round(dialogue_ratio, 4),
        "dialogue_ratio_label": dialogue_ratio_label,
        "cliffhanger_type": cliffhanger_type,
        "pacing": pacing,
        "opening_mode": opening_mode,
    }
    return (examples, profile)


def _stable_episode_partition(episode_paths: list[Path], holdout_fraction: float) -> tuple[set[str], set[str]]:
    if len(episode_paths) < 2:
        names = {path.name for path in episode_paths}
        return (names, set())

    ordered = sorted(episode_paths, key=lambda path: hashlib.sha1(path.name.encode("utf-8")).hexdigest())
    holdout_count = max(1, round(len(ordered) * holdout_fraction))
    holdout_count = min(holdout_count, len(ordered) - 1)
    holdout_names = {path.name for path in ordered[:holdout_count]}
    train_names = {path.name for path in ordered if path.name not in holdout_names}
    return (train_names, holdout_names)


def estimate_supervised_tuning_cost(
    train_tokens: int,
    *,
    epochs: int,
    usd_per_million_tokens: float = GEMINI_SUPERVISED_TUNING_USD_PER_MILLION_TOKENS,
    usd_krw_rate: float = DEFAULT_USD_KRW_RATE,
) -> dict[str, float]:
    epoch_tokens = max(0, train_tokens)
    total_tokens = epoch_tokens * max(1, epochs)
    usd_cost = (total_tokens / 1_000_000) * usd_per_million_tokens
    krw_cost = usd_cost * usd_krw_rate
    return {
        "train_tokens": float(train_tokens),
        "epochs": float(epochs),
        "usd_per_million_tokens": usd_per_million_tokens,
        "usd_krw_rate": usd_krw_rate,
        "estimated_cost_usd": round(usd_cost, 2),
        "estimated_cost_krw": round(krw_cost),
    }


def html_to_text(raw_html: str) -> str:
    parser = _TextExtractor()
    parser.feed(raw_html)
    parser.close()
    return _normalize_text(parser.get_text())


def _resolve_opf_path(epub: zipfile.ZipFile) -> str:
    container_xml = _decode_zip_text(epub.read("META-INF/container.xml"))
    container_root = ET.fromstring(container_xml)
    rootfile = container_root.find(".//{*}rootfile")
    if rootfile is None:
        msg = "missing rootfile in META-INF/container.xml"
        raise ValueError(msg)
    opf_path = rootfile.attrib.get("full-path")
    if not opf_path:
        msg = "missing full-path in rootfile"
        raise ValueError(msg)
    return opf_path


def _fallback_text_entries(epub: zipfile.ZipFile) -> list[str]:
    return sorted(entry.filename for entry in epub.infolist() if Path(entry.filename).suffix.lower() in TEXT_SUFFIXES)


def _spine_documents(epub: zipfile.ZipFile, opf_path: str) -> list[str]:
    opf_root = ET.fromstring(_decode_zip_text(epub.read(opf_path)))
    manifest = opf_root.find(".//{*}manifest")
    spine = opf_root.find(".//{*}spine")
    if manifest is None or spine is None:
        return _fallback_text_entries(epub)

    manifest_map: dict[str, str] = {}
    opf_dir = posixpath.dirname(opf_path)
    for item in list(manifest):
        item_id = item.attrib.get("id")
        href = item.attrib.get("href")
        if item_id and href:
            normalized_href = posixpath.normpath(posixpath.join(opf_dir, href.split("#", 1)[0]))
            manifest_map[item_id] = normalized_href

    documents: list[str] = []
    for itemref in list(spine):
        item_id = itemref.attrib.get("idref")
        if not item_id or item_id not in manifest_map:
            continue
        href = manifest_map[item_id]
        if Path(href).suffix.lower() in TEXT_SUFFIXES:
            documents.append(href)

    return documents or _fallback_text_entries(epub)


def _looks_like_body(entry_name: str, text: str) -> bool:
    lowered_name = posixpath.basename(entry_name).lower()
    if any(marker in lowered_name for marker in SKIP_NAME_MARKERS):
        return False
    if len(text) < MIN_BODY_CHARS:
        return False
    lowered_text = text.lower()
    if len(text) < 2000 and any(marker in lowered_text for marker in COLOPHON_MARKERS):
        return False
    return bool(HANGUL_RE.search(text))


def extract_epub_text(epub_path: Path) -> ExtractedEpisode:
    episode = parse_episode_number(epub_path.name)
    with zipfile.ZipFile(epub_path) as epub:
        documents = _spine_documents(epub, _resolve_opf_path(epub))
        kept_entries: list[str] = []
        kept_texts: list[str] = []
        skipped_entries: list[str] = []
        seen_hashes: set[str] = set()
        fallback_candidates: list[tuple[str, str]] = []

        for document in documents:
            raw_html = _decode_zip_text(epub.read(document))
            text = html_to_text(raw_html)
            if not text:
                skipped_entries.append(f"{document}:empty")
                continue

            if not _looks_like_body(document, text):
                fallback_candidates.append((document, text))
                skipped_entries.append(f"{document}:probable-front-matter")
                continue

            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if digest in seen_hashes:
                skipped_entries.append(f"{document}:duplicate-doc")
                continue
            seen_hashes.add(digest)
            kept_entries.append(document)
            kept_texts.append(text)

        if not kept_texts and fallback_candidates:
            document, text = max(fallback_candidates, key=lambda item: len(item[1]))
            kept_entries = [document]
            kept_texts = [text]
            skipped_entries = [entry for entry in skipped_entries if not entry.startswith(f"{document}:")]

        combined_text = _normalize_text("\n\n".join(kept_texts))
        if not combined_text:
            msg = f"no body text extracted from {epub_path}"
            raise ValueError(msg)

        return ExtractedEpisode(
            episode=episode,
            source_epub=epub_path.name,
            content_entries=kept_entries,
            skipped_entries=skipped_entries,
            text=combined_text,
            text_hash=hashlib.sha256(combined_text.encode("utf-8")).hexdigest(),
        )


def _prepare_output_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def build_corpus(
    source_root: Path,
    output_root: Path,
    titles: list[str],
    *,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    titles_root = output_root / "titles"
    output_root.mkdir(parents=True, exist_ok=True)
    titles_root.mkdir(parents=True, exist_ok=True)

    error_lines: list[str] = []
    title_entries: list[dict[str, Any]] = []
    total_written = 0

    for title in titles:
        source_dir = title_dir_for(source_root, title)
        title_manifest: dict[str, Any] = {
            "title": title,
            "slug": slugify_title(title),
            "source_dir": str(source_dir),
            "status": "pending",
        }

        if not source_dir.exists():
            title_manifest["status"] = "missing-source-dir"
            title_manifest["errors"] = ["missing source title directory"]
            error_lines.append(f"ERROR\t{title}\t-\tmissing source title directory")
            title_entries.append(title_manifest)
            continue

        selection = select_ssot_dir(title, source_dir)
        title_manifest.update(
            {
                "status": "selected",
                "ssot_dir": str(selection.source_path),
                "ssot_rule": selection.rule,
                "raw_epub_count": selection.raw_epub_count,
                "ssot_epub_count": selection.ssot_epub_count,
                "root_epub_count": selection.root_epub_count,
                "subdir_counts": selection.subdir_counts,
                "output_dir": str(titles_root / slugify_title(title)),
            }
        )

        epubs = list_selected_epubs(selection)
        if not epubs:
            title_manifest["status"] = "no-epub-in-ssot"
            title_manifest["errors"] = ["no epub files found in selected SSOT path"]
            error_lines.append(f"ERROR\t{title}\t-\tno epub files found in selected SSOT path")
            title_entries.append(title_manifest)
            continue

        title_output_dir = titles_root / slugify_title(title)
        _prepare_output_dir(title_output_dir)

        chosen_by_episode: dict[int, ExtractedEpisode] = {}
        chosen_by_hash: dict[str, int] = {}
        duplicate_events: list[str] = []
        extraction_errors: list[str] = []

        for epub_path in epubs:
            try:
                extracted = extract_epub_text(epub_path)
            except Exception as exc:  # noqa: BLE001
                message = f"extract-failed:{epub_path.name}:{exc}"
                extraction_errors.append(message)
                error_lines.append(f"ERROR\t{title}\t{epub_path.name}\t{exc}")
                continue

            if extracted.text_hash in chosen_by_hash:
                existing_episode = chosen_by_hash[extracted.text_hash]
                message = (
                    f"duplicate-text-hash:{epub_path.name}:episode={extracted.episode}:"
                    f"existing_episode={existing_episode}"
                )
                duplicate_events.append(message)
                error_lines.append(f"WARN\t{title}\t{epub_path.name}\t{message}")
                continue

            existing = chosen_by_episode.get(extracted.episode)
            if existing is None:
                chosen_by_episode[extracted.episode] = extracted
                chosen_by_hash[extracted.text_hash] = extracted.episode
                continue

            if existing.text_hash == extracted.text_hash:
                message = f"duplicate-episode-exact:{epub_path.name}:episode={extracted.episode}"
                duplicate_events.append(message)
                error_lines.append(f"WARN\t{title}\t{epub_path.name}\t{message}")
                continue

            replacement = extracted if len(extracted.text) > len(existing.text) else existing
            chosen_by_episode[extracted.episode] = replacement
            chosen_by_hash.pop(existing.text_hash, None)
            chosen_by_hash[replacement.text_hash] = replacement.episode
            message = f"episode-collision:{epub_path.name}:episode={extracted.episode}:kept={replacement.source_epub}"
            duplicate_events.append(message)
            error_lines.append(f"WARN\t{title}\t{epub_path.name}\t{message}")

        written_episodes: list[dict[str, Any]] = []
        for episode in sorted(chosen_by_episode):
            extracted = chosen_by_episode[episode]
            output_file = title_output_dir / f"{episode:04d}.txt"
            output_file.write_text(f"{extracted.text}\n", encoding="utf-8")
            written_episodes.append(
                {
                    "episode": episode,
                    "source_epub": extracted.source_epub,
                    "output_file": output_file.name,
                    "content_entries": extracted.content_entries,
                    "skipped_entries": extracted.skipped_entries,
                    "text_hash": extracted.text_hash,
                }
            )

        title_manifest.update(
            {
                "status": "ok" if written_episodes else "empty-after-dedupe",
                "written_episode_count": len(written_episodes),
                "duplicate_count": len(duplicate_events),
                "error_count": len(extraction_errors),
                "duplicates": duplicate_events,
                "errors": extraction_errors,
                "episodes": written_episodes,
            }
        )
        total_written += len(written_episodes)
        title_entries.append(title_manifest)

    manifest_payload = {
        "generated_at": now_iso(),
        "source_root": str(source_root),
        "output_root": str(output_root),
        "titles_manifest_path": str(manifest_path or DEFAULT_TITLE_MANIFEST_PATH),
        "trust_policy": "epub_only",
        "titles": title_entries,
        "summary": {
            "title_count": len(titles),
            "written_title_count": sum(1 for entry in title_entries if entry.get("written_episode_count")),
            "written_episode_count": total_written,
            "error_line_count": len(error_lines),
        },
    }

    (output_root / "manifest.json").write_text(
        json.dumps(manifest_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    error_log = "\n".join(error_lines).strip()
    (output_root / "errors.log").write_text(f"{error_log}\n" if error_log else "", encoding="utf-8")
    return manifest_payload


def _collect_person_candidates(texts: list[str], *, min_frequency: int) -> list[str]:
    counts: dict[str, int] = {}
    for text in texts:
        for match in PERSON_CANDIDATE_RE.finditer(text):
            candidate = match.group("name").strip()
            if len(candidate) != 3:
                continue
            if candidate in PERSON_STOPWORDS:
                continue
            if candidate[1:] not in COMMON_GIVEN_NAMES:
                continue
            counts[candidate] = counts.get(candidate, 0) + 1
    ordered = sorted(counts.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))
    return [candidate for candidate, count in ordered if count >= min_frequency]


def _collect_org_candidates(texts: list[str], *, min_frequency: int) -> list[str]:
    counts: dict[str, int] = {}
    for text in texts:
        for match in ORG_CANDIDATE_RE.finditer(text):
            candidate = match.group("name").strip()
            if candidate in ORG_STOPWORDS:
                continue
            counts[candidate] = counts.get(candidate, 0) + 1
    ordered = sorted(counts.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))
    return [candidate for candidate, count in ordered if count >= min_frequency]


def _person_alias_for(candidate: str, *, used_aliases: set[str]) -> str:
    family_index = int(hashlib.sha1(candidate.encode("utf-8")).hexdigest()[:8], 16) % len(PERSON_ALIAS_FAMILIES)
    given_index = int(hashlib.sha1((candidate + "::given").encode("utf-8")).hexdigest()[:8], 16) % len(
        PERSON_ALIAS_GIVEN
    )
    for offset in range(len(PERSON_ALIAS_FAMILIES) * len(PERSON_ALIAS_GIVEN)):
        family = PERSON_ALIAS_FAMILIES[(family_index + offset) % len(PERSON_ALIAS_FAMILIES)]
        given = PERSON_ALIAS_GIVEN[(given_index + offset) % len(PERSON_ALIAS_GIVEN)]
        alias = f"{family}{given}"
        if alias != candidate and alias not in used_aliases:
            used_aliases.add(alias)
            return alias
    msg = f"unable to allocate unique person alias for {candidate}"
    raise ValueError(msg)


def _split_org_suffix(candidate: str) -> tuple[str, str]:
    for suffix in sorted(ORG_SUFFIXES, key=len, reverse=True):
        if candidate.endswith(suffix) and len(candidate) > len(suffix):
            return candidate[: -len(suffix)], suffix
    return candidate, ""


def _org_alias_for(candidate: str, *, used_aliases: set[str]) -> str:
    _, suffix = _split_org_suffix(candidate)
    prefix_index = int(hashlib.sha1(candidate.encode("utf-8")).hexdigest()[:8], 16) % len(ORG_ALIAS_PREFIXES)
    for offset in range(len(ORG_ALIAS_PREFIXES)):
        prefix = ORG_ALIAS_PREFIXES[(prefix_index + offset) % len(ORG_ALIAS_PREFIXES)]
        alias = f"{prefix}{suffix}"
        if alias != candidate and alias not in used_aliases:
            used_aliases.add(alias)
            return alias
    msg = f"unable to allocate unique org alias for {candidate}"
    raise ValueError(msg)


def build_title_pseudonym_map(
    texts: list[str],
    *,
    min_person_frequency: int = 5,
    min_org_frequency: int = 3,
) -> dict[str, dict[str, str]]:
    used_aliases: set[str] = set()
    persons = {
        candidate: _person_alias_for(candidate, used_aliases=used_aliases)
        for candidate in _collect_person_candidates(texts, min_frequency=min_person_frequency)
    }
    organizations = {
        candidate: _org_alias_for(candidate, used_aliases=used_aliases)
        for candidate in _collect_org_candidates(texts, min_frequency=min_org_frequency)
    }
    return {
        "persons": persons,
        "organizations": organizations,
    }


def apply_pseudonym_map(text: str, pseudonym_map: dict[str, dict[str, str]]) -> tuple[str, dict[str, int]]:
    replacements: list[tuple[str, str]] = []
    for category in ("organizations", "persons"):
        category_map = pseudonym_map.get(category, {})
        replacements.extend(category_map.items())

    working = text
    replacement_counts: dict[str, int] = {}
    placeholders: dict[str, str] = {}
    for index, (original, alias) in enumerate(sorted(replacements, key=lambda item: (-len(item[0]), item[0]))):
        placeholder = f"@@PSEUDO_{index:04d}@@"
        working, count = re.subn(re.escape(original), placeholder, working)
        if count:
            placeholders[placeholder] = alias
            replacement_counts[original] = count

    for placeholder, alias in placeholders.items():
        working = working.replace(placeholder, alias)
    return working, replacement_counts


def build_pseudonymized_corpus(
    input_root: Path,
    output_root: Path,
    *,
    min_person_frequency: int = 5,
    min_org_frequency: int = 3,
) -> dict[str, Any]:
    source_manifest = json.loads((input_root / "manifest.json").read_text(encoding="utf-8"))
    title_entries = source_manifest.get("titles", [])
    _prepare_output_dir(output_root)
    titles_root = output_root / "titles"
    titles_root.mkdir(parents=True, exist_ok=True)

    rewritten_titles: list[dict[str, Any]] = []
    entity_map_payload: dict[str, Any] = {
        "generated_at": now_iso(),
        "input_root": str(input_root),
        "output_root": str(output_root),
        "titles": {},
    }

    for entry in title_entries:
        if not isinstance(entry, dict):
            continue
        title = str(entry.get("title", "")).strip()
        output_dir_value = str(entry.get("output_dir", "")).strip()
        slug = str(entry.get("slug") or slugify_title(title))
        if not title or not output_dir_value or not entry.get("written_episode_count"):
            rewritten_titles.append(entry)
            continue

        source_title_dir = Path(output_dir_value)
        episodes = sorted(source_title_dir.glob("*.txt"))
        texts = [episode.read_text(encoding="utf-8").rstrip("\n") for episode in episodes]
        pseudonym_map = build_title_pseudonym_map(
            texts,
            min_person_frequency=min_person_frequency,
            min_org_frequency=min_org_frequency,
        )

        title_output_dir = titles_root / slug
        _prepare_output_dir(title_output_dir)
        total_replacements = 0
        per_episode_replacements: list[dict[str, Any]] = []
        for episode_path, text in zip(episodes, texts, strict=False):
            rewritten_text, replacement_counts = apply_pseudonym_map(text, pseudonym_map)
            (title_output_dir / episode_path.name).write_text(f"{rewritten_text}\n", encoding="utf-8")
            total_replacements += sum(replacement_counts.values())
            per_episode_replacements.append(
                {
                    "episode_file": episode_path.name,
                    "replacement_count": sum(replacement_counts.values()),
                    "replacements": replacement_counts,
                }
            )

        rewritten_entry = dict(entry)
        rewritten_entry["output_dir"] = str(title_output_dir)
        rewritten_entry["pseudonymized"] = True
        rewritten_entry["pseudonymization"] = {
            "person_count": len(pseudonym_map["persons"]),
            "organization_count": len(pseudonym_map["organizations"]),
            "replacement_count": total_replacements,
            "per_episode": per_episode_replacements,
        }
        rewritten_titles.append(rewritten_entry)
        entity_map_payload["titles"][title] = pseudonym_map

    rewritten_manifest = {
        "generated_at": now_iso(),
        "source_manifest_path": str(input_root / "manifest.json"),
        "input_root": str(input_root),
        "output_root": str(output_root),
        "trust_policy": "epub_only_pseudonymized_variant",
        "pseudonymization_profile": {
            "min_person_frequency": min_person_frequency,
            "min_org_frequency": min_org_frequency,
            "strategy": "title_scoped_stable_aliases",
        },
        "titles": rewritten_titles,
        "summary": {
            "title_count": sum(1 for entry in rewritten_titles if isinstance(entry, dict)),
            "written_title_count": sum(
                1 for entry in rewritten_titles if isinstance(entry, dict) and entry.get("written_episode_count")
            ),
            "written_episode_count": sum(
                int(entry.get("written_episode_count", 0) or 0) for entry in rewritten_titles if isinstance(entry, dict)
            ),
            "pseudonymized_title_count": sum(
                1 for entry in rewritten_titles if isinstance(entry, dict) and entry.get("pseudonymized")
            ),
        },
    }

    (output_root / "manifest.json").write_text(
        json.dumps(rewritten_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_root / "entity_map.json").write_text(
        json.dumps(entity_map_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_root / "errors.log").write_text("", encoding="utf-8")
    return rewritten_manifest


def _jsonl_record(system_instruction: str, prompt: str, completion: str) -> dict[str, Any]:
    return {
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]},
            {"role": "model", "parts": [{"text": completion}]},
        ],
    }


def _make_local_examples(
    text: str,
    *,
    prompt_tokens: int,
    completion_tokens: int,
    stride_tokens: int,
) -> list[tuple[str, str]]:
    paragraphs = _split_paragraphs(text)
    if len(paragraphs) < 2:
        return []

    token_lengths = _paragraph_token_lengths(paragraphs)
    total_tokens = sum(token_lengths)
    total_needed_tokens = prompt_tokens + completion_tokens
    examples: list[tuple[str, str]] = []

    if total_tokens <= total_needed_tokens:
        split_index = _choose_split_index(paragraphs, token_lengths, max(1, total_tokens // 2))
        prompt = _join_paragraphs(paragraphs[:split_index])
        completion = _join_paragraphs(paragraphs[split_index:])
        if estimate_token_count(prompt) >= MIN_SAMPLE_TOKENS and estimate_token_count(completion) >= MIN_SAMPLE_TOKENS:
            return [(prompt, completion)]
        return []

    for start_index in _start_indices(token_lengths, total_needed_tokens, stride_tokens):
        prompt_end_index = _window_end_index(
            paragraphs,
            token_lengths,
            start_index=start_index,
            target_tokens=prompt_tokens,
        )
        if prompt_end_index >= len(paragraphs):
            continue
        completion_end_index = _window_end_index(
            paragraphs,
            token_lengths,
            start_index=prompt_end_index,
            target_tokens=completion_tokens,
        )
        prompt = _join_paragraphs(paragraphs[start_index:prompt_end_index])
        completion = _join_paragraphs(paragraphs[prompt_end_index:completion_end_index])
        if estimate_token_count(prompt) >= MIN_SAMPLE_TOKENS and estimate_token_count(completion) >= MIN_SAMPLE_TOKENS:
            examples.append((prompt, completion))
    return examples


def _make_bridge_example(
    previous_text: str, next_text: str, *, prompt_tokens: int, completion_tokens: int
) -> tuple[str, str] | None:
    previous_paragraphs = _split_paragraphs(previous_text)
    next_paragraphs = _split_paragraphs(next_text)
    if not previous_paragraphs or not next_paragraphs:
        return None

    prompt = _take_tail_by_tokens(
        previous_paragraphs,
        _paragraph_token_lengths(previous_paragraphs),
        prompt_tokens,
    )
    completion = _take_head_by_tokens(
        next_paragraphs,
        _paragraph_token_lengths(next_paragraphs),
        completion_tokens,
    )
    if estimate_token_count(prompt) < MIN_SAMPLE_TOKENS or estimate_token_count(completion) < MIN_SAMPLE_TOKENS:
        return None
    return (prompt, completion)


def _stable_title_partition(titles: list[str], holdout_fraction: float) -> tuple[list[str], list[str]]:
    if len(titles) < 2:
        return (titles[:], [])

    ordered = sorted(titles, key=lambda title: hashlib.sha1(title.encode("utf-8")).hexdigest())
    holdout_count = max(1, round(len(ordered) * holdout_fraction))
    holdout_count = min(holdout_count, len(ordered) - 1)
    holdout_titles = ordered[:holdout_count]
    train_titles = [title for title in ordered if title not in holdout_titles]
    return (train_titles, holdout_titles)


def build_gemini_dataset(
    input_root: Path,
    *,
    system_instruction: str = DEFAULT_SYSTEM_INSTRUCTION,
    holdout_fraction: float = 0.15,
    prompt_tokens: int = 1200,
    completion_tokens: int = 1200,
    stride_tokens: int = 600,
    bridge_prompt_tokens: int = 800,
    bridge_completion_tokens: int = 1000,
    include_bridge_examples: bool = True,
) -> dict[str, Any]:
    manifest_path = input_root / "manifest.json"
    corpus_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    title_entries = [
        entry
        for entry in corpus_manifest.get("titles", [])
        if isinstance(entry, dict) and entry.get("written_episode_count")
    ]
    titles = [entry["title"] for entry in title_entries]
    train_titles, holdout_titles = _stable_title_partition(titles, holdout_fraction)
    title_lookup = {entry["title"]: entry for entry in title_entries}

    gemini_root = input_root / "gemini"
    gemini_root.mkdir(parents=True, exist_ok=True)
    train_path = gemini_root / "train.jsonl"
    val_path = gemini_root / "val.jsonl"

    train_lines: list[str] = []
    val_lines: list[str] = []
    example_hashes: set[str] = set()
    per_title_counts: dict[str, dict[str, int]] = {}
    local_example_count = 0
    bridge_example_count = 0

    for title in titles:
        entry = title_lookup[title]
        output_dir = Path(entry["output_dir"])
        episodes = sorted(output_dir.glob("*.txt"))
        texts = [episode.read_text(encoding="utf-8").strip() for episode in episodes]
        examples: list[tuple[str, str]] = []
        for text in texts:
            local_examples = _make_local_examples(
                text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                stride_tokens=stride_tokens,
            )
            local_example_count += len(local_examples)
            examples.extend(local_examples)

        if include_bridge_examples:
            for previous_text, next_text in zip(texts, texts[1:], strict=False):
                bridge_example = _make_bridge_example(
                    previous_text,
                    next_text,
                    prompt_tokens=bridge_prompt_tokens,
                    completion_tokens=bridge_completion_tokens,
                )
                if bridge_example is not None:
                    bridge_example_count += 1
                    examples.append(bridge_example)

        split_name = "train" if title in train_titles else "val"
        per_title_counts[title] = {"train": 0, "val": 0}
        for prompt, completion in examples:
            digest = hashlib.sha256(f"{prompt}\0{completion}".encode()).hexdigest()
            if digest in example_hashes:
                continue
            example_hashes.add(digest)
            record = _jsonl_record(system_instruction, prompt, completion)
            line = json.dumps(record, ensure_ascii=False)
            if split_name == "train":
                train_lines.append(line)
                per_title_counts[title]["train"] += 1
            else:
                val_lines.append(line)
                per_title_counts[title]["val"] += 1

    train_path.write_text(("\n".join(train_lines) + "\n") if train_lines else "", encoding="utf-8")
    val_path.write_text(("\n".join(val_lines) + "\n") if val_lines else "", encoding="utf-8")

    dataset_manifest = {
        "generated_at": now_iso(),
        "input_root": str(input_root),
        "train_path": str(train_path),
        "val_path": str(val_path),
        "system_instruction": system_instruction,
        "train_titles": train_titles,
        "holdout_titles": holdout_titles,
        "train_example_count": len(train_lines),
        "val_example_count": len(val_lines),
        "window_unit": "estimated_tokens",
        "window_strategy": "paragraph_boundary_scene_aware",
        "local_example_count": local_example_count,
        "bridge_example_count": bridge_example_count,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "stride_tokens": stride_tokens,
        "bridge_prompt_tokens": bridge_prompt_tokens,
        "bridge_completion_tokens": bridge_completion_tokens,
        "include_bridge_examples": include_bridge_examples,
        "per_title_counts": per_title_counts,
    }
    (gemini_root / "dataset_manifest.json").write_text(
        json.dumps(dataset_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return dataset_manifest


def build_style_control_dataset(
    input_root: Path,
    *,
    title: str,
    output_root: Path,
    genre: str = DEFAULT_STYLE_CONTROL_GENRE,
    system_instruction: str = STYLE_CONTROL_SYSTEM_INSTRUCTION,
    holdout_fraction: float = 0.15,
    body_anchor_tokens: int = 220,
    body_completion_tokens: int = 900,
    ending_prompt_tokens: int = 220,
    ending_completion_tokens: int = 700,
    usd_per_million_tokens: float = GEMINI_SUPERVISED_TUNING_USD_PER_MILLION_TOKENS,
    usd_krw_rate: float = DEFAULT_USD_KRW_RATE,
) -> dict[str, Any]:
    manifest_path = input_root / "manifest.json"
    corpus_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    title_entries = {
        entry["title"]: entry
        for entry in corpus_manifest.get("titles", [])
        if isinstance(entry, dict) and entry.get("written_episode_count")
    }
    if title not in title_entries:
        msg = f"title not found in corpus manifest: {title}"
        raise ValueError(msg)

    title_entry = title_entries[title]
    title_dir = Path(title_entry["output_dir"])
    episodes = sorted(title_dir.glob("*.txt"))
    if not episodes:
        msg = f"no episode txt files found for title: {title}"
        raise ValueError(msg)

    output_root.mkdir(parents=True, exist_ok=True)
    train_path = output_root / "train.jsonl"
    val_path = output_root / "val.jsonl"
    train_episode_names, holdout_episode_names = _stable_episode_partition(episodes, holdout_fraction)

    train_lines: list[str] = []
    val_lines: list[str] = []
    example_hashes: set[str] = set()
    train_token_total = 0
    val_token_total = 0
    example_type_counts = {"middle_continuation": 0, "ending_cliffhanger": 0}
    per_episode_counts: dict[str, dict[str, Any]] = {}

    for episode_path in episodes:
        text = episode_path.read_text(encoding="utf-8").strip()
        examples, profile = _build_style_control_examples(
            title,
            text,
            genre=genre,
            body_anchor_tokens=body_anchor_tokens,
            body_completion_tokens=body_completion_tokens,
            ending_prompt_tokens=ending_prompt_tokens,
            ending_completion_tokens=ending_completion_tokens,
        )
        split_name = "train" if episode_path.name in train_episode_names else "val"
        per_episode_counts[episode_path.name] = {
            "split": split_name,
            "example_count": 0,
            "profile": profile,
        }
        for example in examples:
            prompt = example["prompt"]
            completion = example["completion"]
            digest = hashlib.sha256(f"{episode_path.name}\0{prompt}\0{completion}".encode()).hexdigest()
            if digest in example_hashes:
                continue
            example_hashes.add(digest)
            record = _jsonl_record(system_instruction, prompt, completion)
            line = json.dumps(record, ensure_ascii=False)
            example_tokens = (
                estimate_token_count(system_instruction)
                + estimate_token_count(prompt)
                + estimate_token_count(completion)
            )
            if split_name == "train":
                train_lines.append(line)
                train_token_total += example_tokens
            else:
                val_lines.append(line)
                val_token_total += example_tokens
            example_type_counts[example["section"]] += 1
            per_episode_counts[episode_path.name]["example_count"] += 1

    train_path.write_text(("\n".join(train_lines) + "\n") if train_lines else "", encoding="utf-8")
    val_path.write_text(("\n".join(val_lines) + "\n") if val_lines else "", encoding="utf-8")

    cost_epoch_1 = estimate_supervised_tuning_cost(
        train_token_total,
        epochs=1,
        usd_per_million_tokens=usd_per_million_tokens,
        usd_krw_rate=usd_krw_rate,
    )
    cost_epoch_3 = estimate_supervised_tuning_cost(
        train_token_total,
        epochs=3,
        usd_per_million_tokens=usd_per_million_tokens,
        usd_krw_rate=usd_krw_rate,
    )
    dataset_manifest = {
        "generated_at": now_iso(),
        "input_root": str(input_root),
        "title": title,
        "title_output_dir": str(title_dir),
        "output_root": str(output_root),
        "train_path": str(train_path),
        "val_path": str(val_path),
        "genre": genre,
        "system_instruction": system_instruction,
        "window_strategy": "control_conditioned_episode_segments",
        "train_episode_count": len(train_episode_names),
        "holdout_episode_count": len(holdout_episode_names),
        "train_example_count": len(train_lines),
        "val_example_count": len(val_lines),
        "train_tokens_estimated": train_token_total,
        "val_tokens_estimated": val_token_total,
        "body_anchor_tokens": body_anchor_tokens,
        "body_completion_tokens": body_completion_tokens,
        "ending_prompt_tokens": ending_prompt_tokens,
        "ending_completion_tokens": ending_completion_tokens,
        "example_type_counts": example_type_counts,
        "train_episode_names": sorted(train_episode_names),
        "holdout_episode_names": sorted(holdout_episode_names),
        "per_episode_counts": per_episode_counts,
        "cost_estimate": {
            "pricing_basis": "usd_per_million_training_tokens",
            "usd_per_million_tokens": usd_per_million_tokens,
            "usd_krw_rate": usd_krw_rate,
            "epoch_1": cost_epoch_1,
            "epoch_3": cost_epoch_3,
        },
    }
    (output_root / "dataset_manifest.json").write_text(
        json.dumps(dataset_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return dataset_manifest


def dump_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def ssot_selection_to_dict(selection: SsotSelection) -> dict[str, Any]:
    return asdict(selection)
