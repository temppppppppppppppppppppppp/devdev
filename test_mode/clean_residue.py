"""기존 arc/ep 파일에서 Gemini UI 잔재 + 사고과정 헤더 일괄 제거"""

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pathlib import Path

PROJ = Path("projects/test")

UI_RESIDUE = [
    "업로드 용량이 너무 커서 최상의 결과를 얻지 못할 수 있습니다.",
    "자세히 알아보기",
    "새 창에서 열기",
]
HEAD_NOISE = {"생각하는 과정 표시", "단계별 사고", "thinking process", ""}


def clean(text: str) -> str:
    lines = text.split("\n")
    # 머리: 사고과정 + 빈 줄
    while lines and lines[0].strip().lower() in HEAD_NOISE:
        lines.pop(0)
    # 꼬리: UI 잔재 + 빈 줄
    while lines:
        tail = lines[-1].strip()
        if tail == "" or any(r in tail for r in UI_RESIDUE):
            lines.pop()
        else:
            break
    return "\n".join(lines)


def process_dir(stage_dir: Path, pattern: str):
    fixed = 0
    for f in sorted(stage_dir.glob(pattern)):
        original = f.read_text(encoding="utf-8")
        cleaned = clean(original)
        if cleaned != original:
            diff = len(original) - len(cleaned)
            f.write_text(cleaned, encoding="utf-8")
            print(f"  [FIX] {f.name}: -{diff}자 제거")
            fixed += 1
    return fixed


total = 0

# Stage 2: arc 파일 + 히스토리
print("=== Stage 2 ===")
total += process_dir(PROJ / "stage2", "arc_*.txt")
# _history.txt
hist = PROJ / "stage2/_history.txt"
if hist.exists():
    orig = hist.read_text(encoding="utf-8")
    cleaned = orig
    for r in UI_RESIDUE:
        cleaned = cleaned.replace(r, "")
    # 연속 빈 줄 정리 (3줄 이상 → 2줄)
    while "\n\n\n\n" in cleaned:
        cleaned = cleaned.replace("\n\n\n\n", "\n\n\n")
    if cleaned != orig:
        hist.write_text(cleaned, encoding="utf-8")
        print(f"  [FIX] _history.txt: {len(orig) - len(cleaned)}자 제거")
        total += 1

# Stage 3: ep 파일
print("=== Stage 3 ===")
total += process_dir(PROJ / "stage3", "ep_*.txt")
s3_hist = PROJ / "stage3/_history.txt"
if s3_hist.exists():
    orig = s3_hist.read_text(encoding="utf-8")
    cleaned = orig
    for r in UI_RESIDUE:
        cleaned = cleaned.replace(r, "")
    while "\n\n\n\n" in cleaned:
        cleaned = cleaned.replace("\n\n\n\n", "\n\n\n")
    if cleaned != orig:
        s3_hist.write_text(cleaned, encoding="utf-8")
        print(f"  [FIX] _history.txt: {len(orig) - len(cleaned)}자 제거")
        total += 1

print(f"\n=== 완료: {total}개 파일 정리 ===")
