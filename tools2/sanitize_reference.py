"""
참조 원고 고유명사 제거 스크립트
- 인물명, 기업명, 제품명 등을 태그로 치환
- 문체 분석용 (StyleExtractor)
"""
import re
import sys
from pathlib import Path
from collections import OrderedDict

# ============================================================
# 치환 맵 (긴 문자열 우선 정렬됨)
# ============================================================

# --- 기업/그룹 (태우 계열은 접두어 치환) ---
COMPANY_MAP = OrderedDict([
    # 태우 계열 - 구체적인 것부터
    ("태우장학재단", "[그룹]장학재단"),
    ("태우중공업", "[그룹]중공업"),
    ("태우반도체", "[그룹]반도체"),
    ("태우자동차", "[그룹]자동차"),
    ("태우정밀부품", "[그룹]정밀부품"),
    ("태우정밀", "[그룹]정밀"),
    ("태우조선", "[그룹]조선"),
    ("태우건설", "[그룹]건설"),
    ("태우전자", "[그룹]전자"),
    ("태우증권", "[그룹]증권"),
    ("태우통신", "[그룹]통신"),
    ("태우화학", "[그룹]화학"),
    ("태우 관광", "[그룹] 관광"),
    ("태우 실업", "[그룹] 실업"),
    ("태우그룹", "[그룹]"),
    # 단독 "태우"는 문맥상 그룹을 의미할 때가 많음
    # → 아래에서 별도 처리

    # 경쟁/외부 기업
    ("SAVE 투자회사", "[투자회사]"),
    ("SAVE 투자 회사", "[투자회사]"),
    ("SAVE 펀드", "[투자펀드]"),
    ("SAVE", "[투자회사명]"),
    ("대흥그룹", "[경쟁그룹A]"),
    ("현재반도체", "[경쟁그룹B]반도체"),
    ("현재건설", "[경쟁그룹B]건설"),
    ("현재그룹", "[경쟁그룹B]"),
    ("현진그룹", "[경쟁그룹C]"),
    ("삼진전자", "[경쟁사A]"),
    ("삼진", "[경쟁사A]"),
    ("CL전자", "[경쟁사B]"),
    ("CL그룹", "[경쟁사B그룹]"),
    ("LC전자", "[경쟁사C]"),
    ("삼풍그룹", "[경쟁그룹D]"),
    ("카이자동차", "[인수기업A]"),
    ("신화은행", "[은행A]"),
    ("외환은행", "[은행B]"),
    ("CT은행", "[은행C]"),
    ("한일은행", "[은행D]"),
    ("CT그룹", "[은행C그룹]"),
    ("CITI그룹", "[은행C그룹]"),
    ("CITI", "[은행C그룹명]"),
    ("트래블러스", "[금융사A]"),
    ("화이텐 전자", "[중국기업]"),
    ("화이텐전자", "[중국기업]"),
    ("한보그룹", "[부도기업A]"),
    ("롱스타", "[외국펀드A]"),
    ("아크만 펀드", "[외국펀드B]"),
    ("톰슨 멀티미디어", "[외국기업A]"),
    ("D.E", "[외국금융사]"),
])

# --- 제품/서비스 ---
PRODUCT_MAP = OrderedDict([
    ("이노폰", "[신제품]"),
    ("코코아톡", "[메신저앱]"),
    ("스타박스", "[커피브랜드]"),
    ("KIKO", "[파생상품]"),
])

# --- 인물 (긴 이름부터) ---
CHARACTER_MAP = OrderedDict([
    # 주인공 & 가족
    ("김민재", "[주인공]"),
    ("김태중", "[회장]"),

    # 태우 핵심 인물
    ("김택훈", "[비서실장]"),
    ("한정훈", "[팀장]"),
    ("김덕환", "[직원A]"),
    ("이동훈", "[직원B]"),
    ("배성균", "[부회장]"),
    ("박진훈", "[전임사장]"),
    ("우성일", "[부사장]"),
    ("장수영", "[건설사장]"),
    ("이준수", "[상무A]"),
    ("서우태", "[공장장]"),
    ("정수철", "[감사부장]"),
    ("이석준", "[개발자A]"),
    ("한지혜", "[경리]"),
    ("이감덕", "[노조간부]"),

    # 외부 한국인
    ("김강준", "[인물A]"),
    ("김강민", "[인물B]"),
    ("정태섭", "[은행임원A]"),
    ("양성수", "[은행직원A]"),
    ("박대훈", "[은행직원B]"),
    ("장영주", "[경쟁회장]"),
    ("강준기", "[정치인A]"),
    ("이영한", "[사채업자]"),
    ("이수현", "[은행장]"),
    ("한동구", "[외국은행장]"),
    ("천민정", "[개발자B]"),
    ("차봉훈", "[조합장]"),
    ("고영준", "[인물C]"),
    ("한영준", "[연예인A]"),
    ("이동민", "[연예인B]"),
    ("단청수", "[사채꾼A]"),

    # 외국인
    ("제프리", "[외국인A]"),
    ("데이비드", "[외국인B]"),
    ("다이먼", "[외국인C]"),
    ("샌디 웨일", "[외국인D]"),
    ("샌드 웨일", "[외국인D]"),
    ("제니카 웨일", "[외국인E]"),
    ("리처드", "[외국인F]"),
    ("다니엘", "[외국인G]"),
    ("메기", "[외국인H]"),
    ("카를로스 곤", "[외국인I]"),
    ("무함마드 빈 살만", "[외국왕족]"),

    # 별명/칭호
    ("광화문 곰", "[별명A]"),
    ("현금왕", "[별명B]"),
    ("백 할매", "[별명C]"),
])

# 2글자 이름 (문맥 주의 - 단독 사용 시만)
# "민재"는 자주 단독 사용됨
SHORT_NAME_MAP = OrderedDict([
    ("민재", "[주인공]"),
])

# --- "태우" 단독 처리 (그룹 의미일 때만) ---
# "태우그룹", "태우전자" 등은 위에서 이미 처리됨
# 남은 "태우"는 문맥상 그룹명일 가능성 높음
TAEWO_STANDALONE_PATTERN = re.compile(r'태우(?!그룹|전자|증권|자동차|건설|조선|중공업|반도체|통신|화학|정밀|장학| 관광| 실업)')


def sanitize_text(text: str) -> str:
    """고유명사를 태그로 치환"""

    # 1단계: 기업명 (긴 것부터)
    for old, new in COMPANY_MAP.items():
        text = text.replace(old, new)

    # 2단계: 제품명
    for old, new in PRODUCT_MAP.items():
        text = text.replace(old, new)

    # 3단계: 인물명 (긴 것부터)
    for old, new in CHARACTER_MAP.items():
        text = text.replace(old, new)

    # 4단계: 짧은 이름 (2글자)
    for old, new in SHORT_NAME_MAP.items():
        text = text.replace(old, new)

    # 5단계: "태우" 단독 → [그룹]
    text = TAEWO_STANDALONE_PATTERN.sub("[그룹]", text)

    # 6단계: 화 번호 제거 (ⓚ1화. 제목)
    text = re.sub(r'ⓚ\d+화\.\s*[^\n]+', '[화 구분선]', text)

    return text


def count_replacements(original: str, sanitized: str) -> dict:
    """치환 통계"""
    stats = {}
    all_maps = [
        ("기업", COMPANY_MAP),
        ("제품", PRODUCT_MAP),
        ("인물", CHARACTER_MAP),
        ("단축이름", SHORT_NAME_MAP),
    ]
    for category, mapping in all_maps:
        count = 0
        for old_name in mapping:
            c = original.count(old_name)
            if c > 0:
                count += c
        stats[category] = count

    # 태우 단독
    stats["태우단독"] = len(TAEWO_STANDALONE_PATTERN.findall(original))

    # 화 제목
    stats["화제목"] = len(re.findall(r'ⓚ\d+화\.', original))

    return stats


def main():
    if len(sys.argv) < 2:
        print("Usage: python sanitize_reference.py <input_file> [output_file]")
        print("  output_file 미지정 시 _sanitized 접미사로 저장")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"파일 없음: {input_path}")
        sys.exit(1)

    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_path.parent / f"{input_path.stem}_sanitized{input_path.suffix}"

    print(f"입력: {input_path}")
    print(f"출력: {output_path}")
    print(f"크기: {input_path.stat().st_size:,} bytes")
    print()

    # 읽기
    text = input_path.read_text(encoding='utf-8')
    print(f"원본 글자수: {len(text):,}")

    # 치환 통계
    stats = count_replacements(text, "")
    print("\n[치환 대상 통계]")
    total = 0
    for cat, count in stats.items():
        print(f"  {cat}: {count:,}건")
        total += count
    print(f"  합계: {total:,}건")

    # 치환 실행
    sanitized = sanitize_text(text)
    print(f"\n치환 후 글자수: {len(sanitized):,}")

    # 검증: 원본 고유명사가 남아있는지 체크
    remaining = []
    all_names = list(COMPANY_MAP.keys()) + list(PRODUCT_MAP.keys()) + list(CHARACTER_MAP.keys()) + list(SHORT_NAME_MAP.keys())
    for name in all_names:
        if name in sanitized:
            remaining.append((name, sanitized.count(name)))
    if remaining:
        print(f"\n[경고] 치환 안 된 고유명사 {len(remaining)}개:")
        for name, cnt in remaining:
            print(f"  '{name}': {cnt}건")
    else:
        print("\n[OK] 모든 고유명사 치환 완료!")

    # "태우" 잔존 체크
    taewo_remaining = sanitized.count("태우")
    if taewo_remaining > 0:
        print(f"\n[경고] '태우' 잔존: {taewo_remaining}건")
        # 주변 문맥 샘플 출력
        for m in re.finditer(r'.{0,10}태우.{0,10}', sanitized):
            print(f"  ...{m.group()}...")
            if m.start() > 1000:  # 샘플 몇 개만
                break

    # 저장
    output_path.write_text(sanitized, encoding='utf-8')
    print(f"\n저장 완료: {output_path}")
    print(f"크기: {output_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
