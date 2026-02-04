"""
Blueprint NPC 이름 일괄 수정 도구
SQL DB + txt 파일 동시 수정
"""
import sqlite3
import json
import re
import shutil
from pathlib import Path
from datetime import datetime


def get_project_list():
    """프로젝트 목록 조회"""
    root = Path("projects")
    if not root.exists():
        return []
    return sorted([d.name for d in root.iterdir() if d.is_dir()])


def backup_db(db_path: Path) -> Path:
    """DB 백업"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"project_data_backup_{timestamp}.db"
    shutil.copy(db_path, backup_path)
    return backup_path


def safe_replace(text: str, replacements: list) -> str:
    """
    안전한 치환 (팽무진 → 팽팽무진 방지)
    replacements: [(old, new), ...]

    핵심: 모든 소스를 먼저 placeholder로 바꾼 뒤 한 번에 최종 값으로 치환
    """
    result = text

    # 같은 target으로 가는 것들을 그룹핑
    target_groups = {}
    for old, new in replacements:
        if new not in target_groups:
            target_groups[new] = []
        target_groups[new].append(old)

    # 각 target 그룹별로 처리
    for target, sources in target_groups.items():
        placeholder = f"__PLACEHOLDER_{hash(target) % 10000}__"

        # 1. 기존 target을 placeholder로 보호
        result = result.replace(target, placeholder)

        # 2. 모든 source를 placeholder로 (target 제외)
        for src in sources:
            if src != target:
                result = result.replace(src, placeholder)

        # 3. placeholder를 최종 target으로
        result = result.replace(placeholder, target)

    return result


def fix_db_blueprints(db_path: Path, replacements: list, dry_run: bool = True):
    """DB의 blueprints 테이블 수정"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 모든 blueprint 조회
    cur.execute("SELECT ep_num, data FROM blueprints ORDER BY ep_num")
    rows = cur.fetchall()

    changes = []

    for row in rows:
        ep_num = row['ep_num']
        original = row['data']

        if not original:
            continue

        modified = safe_replace(original, replacements)

        if original != modified:
            # 변경된 내용 찾기
            for old, new in replacements:
                if old in original and old != "팽무진":
                    count = original.count(old)
                    changes.append({
                        'ep_num': ep_num,
                        'old': old,
                        'new': new,
                        'count': count
                    })

            if not dry_run:
                cur.execute(
                    "UPDATE blueprints SET data = ? WHERE ep_num = ?",
                    (modified, ep_num)
                )

    if not dry_run:
        conn.commit()

    conn.close()
    return changes


def fix_txt_blueprints(blueprints_dir: Path, replacements: list, dry_run: bool = True):
    """txt 파일들 수정"""
    changes = []

    for txt_file in sorted(blueprints_dir.glob("blueprint_*.txt")):
        original = txt_file.read_text(encoding='utf-8')
        modified = safe_replace(original, replacements)

        if original != modified:
            ep_num = int(txt_file.stem.split('_')[1])
            for old, new in replacements:
                if old in original and old != "팽무진":
                    count = original.count(old)
                    changes.append({
                        'file': txt_file.name,
                        'ep_num': ep_num,
                        'old': old,
                        'new': new,
                        'count': count
                    })

            if not dry_run:
                txt_file.write_text(modified, encoding='utf-8')

    return changes


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Blueprint NPC 이름 일괄 수정')
    parser.add_argument('--project', '-p', type=str, help='프로젝트 이름')
    parser.add_argument('--dry-run', '-d', action='store_true', help='미리보기만 (실제 수정 안 함)')
    parser.add_argument('--yes', '-y', action='store_true', help='확인 없이 바로 실행')
    parser.add_argument('--extra', '-e', type=str, help='추가 치환 규칙 (예: "철산->팽철산,조악->팽조악")')
    args = parser.parse_args()

    print("\n" + "=" * 50)
    print("   Blueprint NPC 이름 일괄 수정 도구")
    print("=" * 50)

    # 프로젝트 선택
    projects = get_project_list()
    if not projects:
        print("\n   프로젝트가 없습니다.")
        return

    if args.project:
        # 인자로 받은 프로젝트
        if args.project in projects:
            project_name = args.project
        else:
            # 부분 매칭 시도
            matches = [p for p in projects if args.project in p]
            if len(matches) == 1:
                project_name = matches[0]
            elif len(matches) > 1:
                print(f"\n   여러 프로젝트 매칭됨: {matches}")
                return
            else:
                print(f"\n   프로젝트 없음: {args.project}")
                return
    else:
        print("\n   [프로젝트 목록]")
        for i, p in enumerate(projects, 1):
            print(f"   {i}. {p}")
        print("\n   사용법: python blueprint_name_fixer.py -p 프로젝트명")
        return

    print(f"\n   선택된 프로젝트: {project_name}")

    project_root = Path(f"projects/{project_name}")
    db_path = project_root / "project_data.db"
    blueprints_dir = project_root / "plans" / "blueprints"

    if not db_path.exists():
        print(f"   DB 없음: {db_path}")
        return

    # 치환 규칙 설정
    replacements = [
        ("주인공", "팽무진"),
        ("무진", "팽무진"),  # safe_replace가 '팽무진' 보호함
    ]

    if args.extra:
        for rule in args.extra.split(','):
            if '->' in rule:
                old, new = rule.split('->')
                replacements.append((old.strip(), new.strip()))

    print(f"\n   [치환 규칙]")
    for old, new in replacements:
        print(f"   '{old}' → '{new}'")

    # DRY RUN (미리보기)
    print("\n" + "-" * 50)
    print("   [DRY RUN] 변경 예정 내역 (아직 적용 안 됨)")
    print("-" * 50)

    db_changes = fix_db_blueprints(db_path, replacements, dry_run=True)
    txt_changes = fix_txt_blueprints(blueprints_dir, replacements, dry_run=True)

    if db_changes:
        print("\n   [DB 변경 예정]")
        # ep_num별로 그룹핑
        by_ep = {}
        for c in db_changes:
            ep = c['ep_num']
            if ep not in by_ep:
                by_ep[ep] = []
            by_ep[ep].append(f"'{c['old']}'x{c['count']}")

        for ep in sorted(by_ep.keys()):
            print(f"   ep_{ep:04d}: {', '.join(by_ep[ep])}")
    else:
        print("\n   [DB] 변경 사항 없음")

    if txt_changes:
        print("\n   [TXT 변경 예정]")
        by_ep = {}
        for c in txt_changes:
            ep = c['ep_num']
            if ep not in by_ep:
                by_ep[ep] = []
            by_ep[ep].append(f"'{c['old']}'x{c['count']}")

        for ep in sorted(by_ep.keys()):
            print(f"   ep_{ep:04d}: {', '.join(by_ep[ep])}")
    else:
        print("\n   [TXT] 변경 사항 없음")

    if not db_changes and not txt_changes:
        print("\n   변경할 내용이 없습니다.")
        return

    # Dry run이면 여기서 종료
    if args.dry_run:
        print("\n   [DRY RUN 완료] 실제 수정하려면 --dry-run 옵션 제거")
        return

    # 실행 확인
    if not args.yes:
        print("\n" + "-" * 50)
        print("   실행하려면: -y 옵션 추가")
        print("   예: python blueprint_name_fixer.py -p 팽가 -y")
        return

    # 백업
    backup_path = backup_db(db_path)
    print(f"\n   DB 백업 완료: {backup_path.name}")

    # 실제 수정
    fix_db_blueprints(db_path, replacements, dry_run=False)
    fix_txt_blueprints(blueprints_dir, replacements, dry_run=False)

    print("\n   수정 완료!")
    print(f"   - DB: {len(set(c['ep_num'] for c in db_changes))}개 에피소드")
    print(f"   - TXT: {len(set(c['ep_num'] for c in txt_changes))}개 파일")


if __name__ == "__main__":
    main()
