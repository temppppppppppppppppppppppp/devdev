"""
Blueprint Editor - 개별 프로젝트 Blueprint 수정 도구
외부 에디터(메모장, VS Code 등)와 연동하여 JSON 편집
"""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


def get_project_list():
    """프로젝트 목록 조회"""
    root = Path("projects")
    if not root.exists():
        return []
    return sorted([d.name for d in root.iterdir() if d.is_dir()])


def get_blueprints(db_path: Path) -> list:
    """Blueprint 목록 조회 (ep_num만)"""
    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT ep_num FROM blueprints ORDER BY ep_num")
    result = [row["ep_num"] for row in cur.fetchall()]
    conn.close()
    return result


def load_blueprint(db_path: Path, ep_num: int) -> dict:
    """특정 Blueprint JSON 로드"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT data FROM blueprints WHERE ep_num = ?", (ep_num,))
    row = cur.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row["data"])
        except json.JSONDecodeError:
            return {}
    return {}


def save_blueprint(db_path: Path, ep_num: int, data: dict) -> bool:
    """Blueprint 저장"""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        cur.execute("INSERT OR REPLACE INTO blueprints (ep_num, data) VALUES (?, ?)", (ep_num, json_data))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"   저장 실패: {e}")
        return False


def delete_blueprint(db_path: Path, ep_num: int) -> bool:
    """Blueprint 삭제"""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("DELETE FROM blueprints WHERE ep_num = ?", (ep_num,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"   삭제 실패: {e}")
        return False


def open_in_editor(file_path: str):
    """외부 에디터로 파일 열기"""
    if sys.platform == "win32":
        # Windows: 기본 연결 프로그램 또는 notepad
        try:
            os.startfile(file_path)
        except OSError:  # [V64.P4] file open failure
            subprocess.run(["notepad", file_path])
    elif sys.platform == "darwin":
        # macOS
        subprocess.run(["open", file_path])
    else:
        # Linux
        editor = os.environ.get("EDITOR", "nano")
        subprocess.run([editor, file_path])


def edit_blueprint_external(db_path: Path, ep_num: int):
    """외부 에디터로 Blueprint 편집"""
    data = load_blueprint(db_path, ep_num)
    if not data:
        print(f"   Blueprint {ep_num}번이 비어있습니다.")
        create = input("   새로 생성하시겠습니까? (y/n): ").strip().lower()
        if create != "y":
            return
        data = {"ep_num": ep_num, "scenes": [], "constraints": []}

    # 임시 파일 생성
    with tempfile.NamedTemporaryFile(mode="w", suffix=f"_blueprint_{ep_num}.json", delete=False, encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        temp_path = f.name

    print(f"\n   외부 에디터로 파일을 엽니다: {temp_path}")
    print("   편집 완료 후 저장하고 에디터를 닫으세요.")

    # 편집 전 수정 시간 기록
    original_mtime = os.path.getmtime(temp_path)

    # 외부 에디터 열기
    open_in_editor(temp_path)

    input("\n   [Enter] 편집 완료 후 이 키를 눌러 저장을 진행하세요...")

    # 파일이 수정되었는지 확인
    current_mtime = os.path.getmtime(temp_path)

    if current_mtime == original_mtime:
        print("   파일이 수정되지 않았습니다. 저장을 건너뜁니다.")
        os.unlink(temp_path)
        return

    # 수정된 JSON 읽기
    try:
        with open(temp_path, encoding="utf-8") as f:
            new_data = json.load(f)

        # 저장 확인
        print("\n   [미리보기] 수정된 데이터의 키:")
        for key in new_data.keys():
            print(f"      - {key}")

        confirm = input("\n   이 내용으로 저장하시겠습니까? (y/n): ").strip().lower()
        if confirm == "y":
            if save_blueprint(db_path, ep_num, new_data):
                print(f"   Blueprint {ep_num}번 저장 완료!")
            else:
                print("   저장 실패.")
        else:
            print("   저장 취소됨.")

    except json.JSONDecodeError as e:
        print(f"   JSON 파싱 오류: {e}")
        print("   저장이 취소되었습니다. 다시 시도해 주세요.")
    finally:
        # 임시 파일 정리
        try:
            os.unlink(temp_path)
        except OSError:  # [V64.P4] temp file cleanup
            pass


def view_blueprint_summary(db_path: Path, ep_num: int):
    """Blueprint 요약 정보 출력"""
    data = load_blueprint(db_path, ep_num)
    if not data:
        print(f"   Blueprint {ep_num}번이 없습니다.")
        return

    print(f"\n   ━━━ Blueprint #{ep_num} 요약 ━━━")

    # 씬 정보
    scenes = data.get("scenes", [])
    print(f"   씬 개수: {len(scenes)}")
    for i, scene in enumerate(scenes[:5], 1):  # 최대 5개만 표시
        title = scene.get("title", scene.get("name", f"Scene {i}"))
        print(f"      {i}. {title[:50]}...")
    if len(scenes) > 5:
        print(f"      ... 외 {len(scenes) - 5}개")

    # 제약사항
    constraints = data.get("constraints", data.get("constraint", []))
    if constraints:
        print(f"   제약 개수: {len(constraints) if isinstance(constraints, list) else 1}")

    # 기타 키 목록
    other_keys = [k for k in data.keys() if k not in ["scenes", "constraints", "constraint", "ep_num"]]
    if other_keys:
        print(f"   기타 필드: {', '.join(other_keys)}")


def main_menu():
    """메인 메뉴"""
    print("\n" + "=" * 50)
    print("     Blueprint Editor v1.0")
    print("     외부 에디터 연동 Blueprint 수정 도구")
    print("=" * 50)

    # 1. 프로젝트 선택
    projects = get_project_list()
    if not projects:
        print("\n   프로젝트가 없습니다. projects/ 폴더를 확인하세요.")
        return

    print("\n   [프로젝트 목록]")
    for i, p in enumerate(projects, 1):
        print(f"   {i}. {p}")

    try:
        p_idx = int(input("\n   프로젝트 번호 선택: ").strip()) - 1
        if p_idx < 0 or p_idx >= len(projects):
            print("   잘못된 선택입니다.")
            return
        project_name = projects[p_idx]
    except ValueError:
        print("   숫자를 입력해 주세요.")
        return

    db_path = Path(f"projects/{project_name}/project_data.db")
    if not db_path.exists():
        print(f"   DB 파일이 없습니다: {db_path}")
        return

    print(f"\n   선택된 프로젝트: {project_name}")

    # 2. Blueprint 작업 루프
    while True:
        blueprints = get_blueprints(db_path)

        print("\n" + "-" * 40)
        print(f"   [{project_name}] Blueprint 목록")
        print("-" * 40)

        if blueprints:
            # 10개씩 그룹으로 표시
            for i in range(0, len(blueprints), 10):
                chunk = blueprints[i : i + 10]
                print(f"   {', '.join(map(str, chunk))}")
        else:
            print("   등록된 Blueprint가 없습니다.")

        print("\n   [메뉴]")
        print("   1. Blueprint 편집 (외부 에디터)")
        print("   2. Blueprint 요약 보기")
        print("   3. Blueprint 삭제")
        print("   4. 새 Blueprint 생성")
        print("   5. 프로젝트 변경")
        print("   0. 종료")

        choice = input("\n   선택: ").strip()

        if choice == "1":
            try:
                ep = int(input("   편집할 Blueprint 번호: ").strip())
                edit_blueprint_external(db_path, ep)
            except ValueError:
                print("   숫자를 입력해 주세요.")

        elif choice == "2":
            try:
                ep = int(input("   조회할 Blueprint 번호: ").strip())
                view_blueprint_summary(db_path, ep)
            except ValueError:
                print("   숫자를 입력해 주세요.")

        elif choice == "3":
            try:
                ep = int(input("   삭제할 Blueprint 번호: ").strip())
                confirm = input(f"   Blueprint {ep}번을 삭제하시겠습니까? (y/n): ").strip().lower()
                if confirm == "y":
                    if delete_blueprint(db_path, ep):
                        print(f"   Blueprint {ep}번 삭제 완료.")
                    else:
                        print("   삭제 실패.")
            except ValueError:
                print("   숫자를 입력해 주세요.")

        elif choice == "4":
            try:
                ep = int(input("   새 Blueprint 번호: ").strip())
                if ep in blueprints:
                    print(f"   {ep}번은 이미 존재합니다. '편집'을 사용하세요.")
                else:
                    edit_blueprint_external(db_path, ep)
            except ValueError:
                print("   숫자를 입력해 주세요.")

        elif choice == "5":
            return main_menu()  # 재귀로 프로젝트 선택

        elif choice == "0":
            print("\n   Blueprint Editor를 종료합니다.")
            break

        else:
            print("   잘못된 선택입니다.")


if __name__ == "__main__":
    main_menu()
