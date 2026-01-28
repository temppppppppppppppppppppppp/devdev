import os
import argparse
from pathlib import Path
from datetime import datetime

# 분석 대상 확장자 및 제외 디렉토리 설정
INCLUDE_EXTS = {'.py', '.yaml', '.yml', '.json'}
EXCLUDE_DIRS = {'.git', '__pycache__', 'venv', 'node_modules', '.idea', '.vscode'}

def export_full_source_markdown(root_path, output_file="project_full_source.md"):
    root = Path(root_path).resolve()
    tree_lines = []
    file_contents = []

    print(f"🔍 Full Source Analysis: {root}...")

    for current_root, dirs, files in os.walk(root):
        # 제외 디렉토리 필터링
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        dirs.sort()
        files.sort()

        rel_path = Path(current_root).relative_to(root)
        depth = len(rel_path.parts)
        spacer = '    ' * depth
        
        if depth > 0:
            tree_lines.append(f"{spacer}📁 {Path(current_root).name}/")
        
        for file in files:
            file_path = Path(current_root) / file
            if file_path.suffix.lower() in INCLUDE_EXTS:
                tree_lines.append(f"{spacer}    📄 {file}")
                
                # 파일 전체 내용 읽기
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read() # 요약 없이 전체 읽기
                    
                    file_contents.append((file_path.relative_to(root), content))
                except Exception as e:
                    file_contents.append((file_path.relative_to(root), f"❌ Error reading file: {e}"))

    # 마크다운 작성
    with open(output_file, 'w', encoding='utf-8') as md:
        md.write(f"# 🤖 Full Source Code Analysis: {root.name}\n")
        md.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # 1. 트리 구조 출력
        md.write("## 1. 🌳 Structure\n```text\n")
        md.write("\n".join(tree_lines) + "\n```\n\n---\n")

        # 2. 전체 소스 코드 출력
        md.write("## 2. 📝 Full Source Codes\n")
        for rel_path, content in file_contents:
            ext = rel_path.suffix.lstrip('.')
            # 마크다운 문법 충돌 방지를 위해 언어 지정
            md.write(f"### 📂 `{rel_path}`\n")
            md.write(f"```{ext}\n{content}\n```\n\n")

    print(f"✅ 전체 소스 코드 분석 파일 생성 완료: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=os.getcwd())
    args = parser.parse_args()
    export_full_source_markdown(args.path)