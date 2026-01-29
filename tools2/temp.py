import os

# 설정: 소스 폴더 경로와 저장할 파일 이름
source_dir = r'C:\Users\wjjo\Desktop\글도비'
exclude_folder = '백업'  # 제외할 폴더 이름
output_file = 'scripts_summary.md'

def merge_scripts_to_markdown(target_path, output_name):
    if not os.path.exists(target_path):
        print(f"오류: 경로를 찾을 수 없습니다: {target_path}")
        return

    with open(output_name, 'w', encoding='utf-8') as md_file:
        md_file.write(f"# 글도비 스크립트 목록\n\n")
        md_file.write(f"본 문서는 `{target_path}` 폴더 내의 스크립트를 자동 병합한 결과입니다.\n")
        md_file.write(f"**제외된 폴더:** `{exclude_folder}`\n\n---\n\n")

        # os.walk를 사용하여 하위 폴더까지 탐색
        for root, dirs, files in os.walk(target_path):
            # '백업' 폴더가 경로에 포함되어 있으면 제외
            if exclude_folder in dirs:
                dirs.remove(exclude_folder) # 하위 탐색 목록에서 제거
            
            for filename in files:
                file_path = os.path.join(root, filename)
                
                # 파일 정보 추출
                ext = os.path.splitext(filename)[1].lower()
                lang = ext.replace('.', '') if ext else ''
                
                # 마크다운에 기록
                # 전체 경로에서 소스 디렉토리 이후의 상대 경로만 표시하여 깔끔하게 정리
                relative_path = os.path.relpath(file_path, target_path)
                md_file.write(f"## 파일: {relative_path}\n")
                md_file.write(f"```{lang}\n")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        md_file.write(f.read())
                except (UnicodeDecodeError, Exception):
                    try:
                        # utf-8 실패 시 cp949(윈도우 한글 인코딩) 시도
                        with open(file_path, 'r', encoding='cp949') as f:
                            md_file.write(f.read())
                    except Exception as e:
                        md_file.write(f"파일을 읽는 중 오류 발생: {e}")

                md_file.write(f"\n```\n\n---\n\n")
                print(f"병합 완료: {relative_path}")

    print(f"\n✅ '{exclude_folder}'를 제외한 모든 파일이 '{output_name}'에 저장되었습니다.")

if __name__ == "__main__":
    merge_scripts_to_markdown(source_dir, output_file)