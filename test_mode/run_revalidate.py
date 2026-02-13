"""
비대화형 Director 재검증 스크립트
=================================
Stage 2 (분배표 50개) + Stage 3 (Blueprint 78개) 전량 재검증.
Pro 모델 강제 — Pro 제한 시 자동 중단.

사전 조건:
  1. Chrome 디버깅 모드 실행:
     chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\\chrome_debug"
  2. Gemini (gemini.google.com) 로그인 + Pro 사용 가능 상태

사용법:
  python run_revalidate.py
"""

import os
import sys

# Windows UTF-8 강제
if sys.platform == "win32":
    try:
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except (AttributeError, OSError):
        pass

# ANSI 활성화
os.system("")

import json
import re
import time
from datetime import datetime
from pathlib import Path

# ── 경로 설정 ──────────────────────────────────────────────
PROJECT_DIR = Path(__file__).parent / "projects" / "test"
STAGE2_DIR = PROJECT_DIR / "stage2"
STAGE3_DIR = PROJECT_DIR / "stage3"


# ── 컬러 ────────────────────────────────────────────────────
class C:
    ORANGE = "\033[38;5;208m"
    GREEN = "\033[38;5;114m"
    RED = "\033[38;5;203m"
    CYAN = "\033[38;5;117m"
    GRAY = "\033[38;5;243m"
    DIM = "\033[38;5;240m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  {C.DIM}{ts}{C.RESET}  {msg}")


# ── Director 프롬프트 ─────────────────────────────────────
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

[출력 형식 - 반드시 이 형식만]
모순: (발견된 모순 항목. 없으면 "없음")
누락: (빠뜨린 요소. 없으면 "없음")
이름오류: (잘못된 고유명사. 없으면 "없음")
블록불일치: (첨부 블록과 다른 내용이면 구체적으로 기재. 없으면 "없음")
점수: (0~100 정수)
판정: PASS 또는 REVISE"""


# ── 컨텍스트 경량화 ───────────────────────────────────────
def trim_context(ctx_text: str, max_bytes: int = 80_000) -> str:
    """누적 히스토리 제거 → 경량화"""
    markers = [
        "[이전 분배표 누적",
        "[이전 Blueprint 누적",
        "[이전 원고 누적",
    ]
    for marker in markers:
        idx = ctx_text.find(marker)
        if idx > 0:
            cut = ctx_text.rfind("=" * 50, 0, idx)
            if cut > 0:
                ctx_text = ctx_text[:cut].rstrip()
            else:
                ctx_text = ctx_text[:idx].rstrip()

    if len(ctx_text.encode("utf-8")) > max_bytes:
        while len(ctx_text.encode("utf-8")) > max_bytes:
            ctx_text = ctx_text[: len(ctx_text) - 5000]
        ctx_text = ctx_text.rstrip() + "\n\n[...컨텍스트 일부 생략...]"
    return ctx_text


# ── 단일 파일 재검증 ─────────────────────────────────────
def revalidate_single(driver, ctx_path: Path, output_path: Path, label: str) -> dict:
    """컨텍스트+출력 합본 → Pro Director 평가"""
    ctx_text = ctx_path.read_text(encoding="utf-8") if ctx_path.exists() else ""
    output_text = output_path.read_text(encoding="utf-8") if output_path.exists() else ""

    if not output_text:
        return {"file": output_path.name, "score": 0, "passed": False, "details": "출력 파일 비어있음", "model": "N/A"}

    # 경량화
    ctx_trimmed = trim_context(ctx_text)
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
        resp = driver.send_with_file(str(combined_path), REVALIDATION_DIRECTOR_PROMPT)

        if resp.startswith("[TIMEOUT]") or resp.startswith("[EMPTY]"):
            return {
                "file": output_path.name,
                "score": 0,
                "passed": False,
                "details": resp,
                "model": driver.get_current_model(),
            }

        # 점수 파싱 (최대 3회)
        m = None
        for _try in range(3):
            m = re.search(r"점수\s*[:：]\s*(\d+)", resp)
            if m:
                break
            log(f"[Director] {label}: 점수 파싱 실패 → 재시도")
            resp = driver.send_prompt(REVALIDATION_DIRECTOR_PROMPT)

        if not m:
            return {
                "file": output_path.name,
                "score": 0,
                "passed": False,
                "details": "점수 파싱 실패",
                "model": driver.get_current_model(),
            }

        score = int(m.group(1))
        verdict = "PASS" if score >= 90 else "REVISE"
        vm = re.search(r"판정\s*[:：]\s*(PASS|REVISE)", resp)
        if vm:
            verdict = vm.group(1)

        details_parts = []
        for field in ["모순", "누락", "이름오류", "블록불일치"]:
            fm = re.search(rf"{field}\s*[:：]\s*(.+?)(?:\n|$)", resp)
            if fm and fm.group(1).strip() not in ("없음", "없음."):
                detail = fm.group(1).strip()[:80]
                details_parts.append(f"{field}: {detail}")

        passed = verdict == "PASS"
        model = driver.get_current_model()
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


# ── 스테이지별 재검증 ────────────────────────────────────
def run_stage_revalidation(driver, stage_dir: Path, prefix: str, label_fmt: str) -> dict:
    """한 스테이지의 모든 출력 파일 재검증. Pro 제한 시 중단."""

    # 출력 파일 수집 (_context, _history 제외)
    outputs = sorted(
        [
            f
            for f in stage_dir.glob(f"{prefix}*.txt")
            if "_context" not in f.name
            and "_history" not in f.name
            and "_reval" not in f.name
            and "_metadata" not in f.name
        ]
    )

    if not outputs:
        log(f"[!] {stage_dir.name}/ 에 출력 파일이 없습니다.")
        return {"total": 0, "passed": 0, "failed": 0, "results": [], "stopped": False}

    log(f"\n{'=' * 50}")
    log(f"{stage_dir.name} 재검증 시작: {len(outputs)}개 파일")
    log(f"{'=' * 50}")

    results = []
    pass_count = 0
    fail_count = 0
    stopped = False

    for i, out_path in enumerate(outputs):
        # 빠른 모드(Flash) 감지 → 중단
        actual = driver.get_current_model()
        if actual == "빠른 모드":
            log(f"{C.RED}[STOP] 빠른 모드 감지! 사고/Pro가 아님{C.RESET}")
            log(f"       {i}/{len(outputs)} 완료 시점에서 중단.")
            stopped = True
            break

        stem = out_path.stem
        num_str = stem.split("_", 1)[1]

        ctx_name = f"{prefix}{num_str}_context.txt"
        ctx_path = stage_dir / ctx_name

        if not ctx_path.exists():
            log(f"[!] {ctx_name} 없음 → 스킵")
            results.append(
                {"file": out_path.name, "score": 0, "passed": False, "details": "컨텍스트 파일 없음", "model": "N/A"}
            )
            fail_count += 1
            continue

        try:
            num_int = int(num_str)
        except ValueError:
            num_int = i + 1
        label = label_fmt.format(num_int)

        log(f"[{i + 1}/{len(outputs)}] {label}")

        result = revalidate_single(driver, ctx_path, out_path, label)
        results.append(result)

        if result["passed"]:
            pass_count += 1
        else:
            fail_count += 1

        driver.new_chat()
        time.sleep(2)

    return {
        "total": len(results),
        "passed": pass_count,
        "failed": fail_count,
        "results": results,
        "stopped": stopped,
    }


def print_summary(stage_name: str, report: dict):
    """결과 요약 출력"""
    print(f"\n  {C.BOLD}{'=' * 50}{C.RESET}")
    print(f"  {C.BOLD}{stage_name} 재검증 결과{C.RESET}")
    print(f"  {C.BOLD}{'=' * 50}{C.RESET}")
    print(
        f"  통과: {C.GREEN}{report['passed']}{C.RESET}개  |  "
        f"실패: {C.RED}{report['failed']}{C.RESET}개  |  "
        f"총: {report['total']}개"
    )

    if report.get("stopped"):
        print(f"  {C.RED}(Pro 제한으로 중도 중단됨){C.RESET}")

    if report["failed"] > 0:
        print(f"\n  {C.RED}재생성 필요 파일:{C.RESET}")
        for r in report["results"]:
            if not r["passed"]:
                print(f"    {C.RED}✗{C.RESET} {r['file']} ({r['score']}점) — {r['details']}")

    # PASS 파일도 점수 낮은 순으로 보여주기
    passed = [r for r in report["results"] if r["passed"]]
    if passed:
        passed_sorted = sorted(passed, key=lambda x: x["score"])
        worst_3 = passed_sorted[:3]
        print(f"\n  {C.CYAN}통과 중 최저 점수:{C.RESET}")
        for r in worst_3:
            print(f"    {C.GREEN}✓{C.RESET} {r['file']} ({r['score']}점)")


def main():
    print(f"\n{C.BOLD}{'=' * 55}{C.RESET}")
    print(f"  {C.ORANGE}{C.BOLD}Director 재검증 — 비대화형 전량 검사{C.RESET}")
    print("  Stage 2 (분배표) + Stage 3 (Blueprint)")
    print(f"  모델: {C.CYAN}사고 모드{C.RESET} (빠른 모드 감지 시 자동 중단)")
    print(f"{C.BOLD}{'=' * 55}{C.RESET}")

    # 프로젝트 확인
    if not PROJECT_DIR.exists():
        print(f"\n  [ERROR] 프로젝트 폴더 없음: {PROJECT_DIR}")
        return

    s2_count = len([f for f in STAGE2_DIR.glob("arc_*.txt") if "_context" not in f.name])
    s3_count = len([f for f in STAGE3_DIR.glob("ep_*.txt") if "_context" not in f.name])
    print(f"\n  대상: Stage 2 ({s2_count}개) + Stage 3 ({s3_count}개) = 총 {s2_count + s3_count}개")
    print(f"  예상 소요: ~{(s2_count + s3_count) * 30 // 60}분")

    # 드라이버 연결
    print("\n  Gemini 드라이버 연결 중...")
    sys.path.insert(0, str(Path(__file__).parent))
    from bridge.gemini_driver import GeminiDriver

    driver = GeminiDriver(model="think", hide=False, log_func=log)
    log("연결 성공!")

    # 사고 모드 선택
    driver.select_model("think")
    actual = driver.get_current_model()
    if actual == "빠른 모드":
        print(f"\n  {C.RED}[ERROR] 빠른 모드만 사용 가능 상태!{C.RESET}")
        print("  사고 모드/Pro 사용 가능해진 후 다시 실행하세요.")
        return

    log(f"모델 확인: {C.GREEN}{actual}{C.RESET}")

    all_reports = {}

    # ── Stage 2 재검증 ──
    s2_report = run_stage_revalidation(driver, STAGE2_DIR, "arc_", "분배표 #{}")

    # 중간 저장
    s2_report["timestamp"] = datetime.now().isoformat(timespec="seconds")
    s2_report["model"] = actual
    s2_json = STAGE2_DIR / "_revalidation.json"
    s2_json.write_text(json.dumps(s2_report, ensure_ascii=False, indent=2), encoding="utf-8")
    all_reports["stage2"] = s2_report
    print_summary("Stage 2 (분배표)", s2_report)

    if s2_report.get("stopped"):
        log(f"\n{C.RED}빠른 모드 전환 감지 — Stage 2에서 중단. Stage 3 스킵.{C.RESET}")
        save_final_report(all_reports)
        return

    # ── Stage 3 재검증 ──
    s3_report = run_stage_revalidation(driver, STAGE3_DIR, "ep_", "제{}화 Blueprint")

    s3_report["timestamp"] = datetime.now().isoformat(timespec="seconds")
    s3_report["model"] = actual
    s3_json = STAGE3_DIR / "_revalidation.json"
    s3_json.write_text(json.dumps(s3_report, ensure_ascii=False, indent=2), encoding="utf-8")
    all_reports["stage3"] = s3_report
    print_summary("Stage 3 (Blueprint)", s3_report)

    save_final_report(all_reports)


def save_final_report(reports: dict):
    """최종 종합 리포트 저장"""
    total_pass = sum(r["passed"] for r in reports.values())
    total_fail = sum(r["failed"] for r in reports.values())
    total_all = sum(r["total"] for r in reports.values())

    # 실패 파일 목록 추출
    fail_files = []
    for stage, report in reports.items():
        for r in report["results"]:
            if not r["passed"]:
                fail_files.append(f"{stage}/{r['file']} ({r['score']}점)")

    summary = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "total": total_all,
        "passed": total_pass,
        "failed": total_fail,
        "fail_files": fail_files,
        "stages": {
            k: {"passed": v["passed"], "failed": v["failed"], "total": v["total"], "stopped": v.get("stopped", False)}
            for k, v in reports.items()
        },
    }

    report_path = PROJECT_DIR / "_revalidation_summary.json"
    report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{C.BOLD}{'=' * 55}{C.RESET}")
    print(f"  {C.ORANGE}{C.BOLD}종합 결과{C.RESET}")
    print(f"  통과: {C.GREEN}{total_pass}{C.RESET}  |  실패: {C.RED}{total_fail}{C.RESET}  |  총: {total_all}")

    if fail_files:
        print(f"\n  {C.RED}재생성 필요 ({len(fail_files)}개):{C.RESET}")
        for f in fail_files:
            print(f"    {C.RED}✗{C.RESET} {f}")

    print(f"\n  리포트 저장: {report_path}")
    print(f"{C.BOLD}{'=' * 55}{C.RESET}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {C.ORANGE}Ctrl+C — 중단합니다.{C.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n  {C.RED}[ERROR] {e}{C.RESET}")
        import traceback

        traceback.print_exc()
