import os

# 경로 설정 (사용자 환경에 맞게 설정됨)
src_dir = r"C:\Users\wjjo\Desktop\글도비\projects\팽가 망나니 가문 재건\drafts"
output_file = r"C:\Users\wjjo\Desktop\글도비\projects\팽가 망나니 가문 재건\0_합본.txt"

def merge_txt_files_with_header():
    # 1. 파일 목록 가져오기 및 정렬
    files = [f for f in os.listdir(src_dir) if f.endswith('.txt')]
    files.sort()

    if not files:
        print("해당 폴더에 txt 파일이 없습니다.")
        return

    print(f"총 {len(files)}개의 파일을 합치는 중입니다...")

    # 2. 합본 파일 쓰기
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for filename in files:
            file_path = os.path.join(src_dir, filename)
            
            # --- 수정된 부분: 파일 시작 지점에 ####과 파일명 삽입 ---
            outfile.write(f"#### {filename}\n")
            
            with open(file_path, 'r', encoding='utf-8') as infile:
                outfile.write(infile.read())
            
            # 각 파일 끝에 구분용 줄바꿈 추가
            outfile.write("\n\n") 
            
            print(f"결합 완료: {filename}")

    print("-" * 30)
    print(f"성공! 합본 파일이 생성되었습니다: {output_file}")

if __name__ == "__main__":
    merge_txt_files_with_header()