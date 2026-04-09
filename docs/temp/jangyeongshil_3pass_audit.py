"""
3-Pass Philosophy Audit — jangyeongshil_industrial_revolution
Framework: docs/blockguide/harness_3pass_audit_and_patch.md
Genre philosophy: canon §4 Post-Patron Independence Lock + §5 Contamination Guard
BI philosophy: bi-production-harness-v1.md §2.2/§11 "BI는 동기화 산출물"
Production philosophy: treatment-production-harness-v2.md §3.1~§3.4 다양성 강제

PASS 1: 구조 정합성 — 파이프라인이 순차적·구조적으로 정합한가?
PASS 2: 근본 원인 / 실패 패턴 — 3대 실패 패턴이 있는가 (장르 스키마 적응)?
PASS 3: 철학 준수도 — canon §4/§5 + 4단 공식 + BI 동기화 원칙 실질 준수?

Read-only. Write scope: none.
"""
import json, os, re, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

TR_PATH = r'treatments/jangyeongshil_industrial_revolution_tr_block_025_draft.json'
BI_PATH = r'bible/jangyeongshil_industrial_revolution_bi.json'
PHASE0_PATH = r'treatments/phase0/jangyeongshil_industrial_revolution_phase0_design.json'
CANON_PATH = r'material_ssot/20_pitch/canon/jangyeongshil_industrial_revolution.md'

with open(TR_PATH, encoding='utf-8') as f: TR = json.load(f)
with open(BI_PATH, encoding='utf-8') as f: BI = json.load(f)
try:
    with open(PHASE0_PATH, encoding='utf-8') as f: PHASE0 = json.load(f)
except Exception:
    PHASE0 = None
with open(CANON_PATH, encoding='utf-8') as f: CANON = f.read()

blocks = TR['blocks']
N = len(blocks)

def hdr(s):
    print()
    print('=' * 76)
    print(s)
    print('=' * 76)

def sec(s):
    print()
    print('--- ' + s + ' ---')

# ===========================================================================
# PASS 1 — 구조 정합성
# ===========================================================================
hdr('PASS 1 — 구조 정합성 (파이프라인 실제 강제 여부)')

sec('1.1 파이프라인 각 단계 존재 여부')
stages = {
    'canon pitch':    os.path.exists(CANON_PATH),
    'phase0 design':  os.path.exists(PHASE0_PATH),
    'live TR (70)':   os.path.exists(TR_PATH) and N == 70,
    'live BI':        os.path.exists(BI_PATH),
    'live_status':    os.path.exists(r'docs/2026-04-08/jangyeongshil_industrial_revolution_live_status.md'),
}
for k, v in stages.items():
    print(f'  {k}: {"OK" if v else "MISSING"}')
pass1_stage_ok = all(stages.values())

sec('1.2 TR 블록 ID 연속성 & _total_blocks 일치')
ids = [b.get('block_id') for b in blocks]
expected = [f'Block {i+1}' for i in range(N)]
ids_ok = ids == expected
total_ok = TR.get('_total_blocks') == N
print(f'  block_id sequential Block 1..Block {N}: {ids_ok}')
print(f'  _total_blocks == len(blocks) == 70: {total_ok}')

sec('1.3 ARC 슬롯 정합성 (Phase0 ARC 설계 vs TR 실제)')
if PHASE0:
    p0_arcs = PHASE0.get('arcs') or PHASE0.get('ArcSheets') or []
    print(f'  phase0 arcs count: {len(p0_arcs)}')
    arc_coverage = {}
    for arc in p0_arcs:
        aid = arc.get('arc_id') or arc.get('id')
        br = arc.get('block_range') or []
        if isinstance(br, list) and len(br) == 2:
            lo, hi = br
        elif isinstance(br, str):
            m = re.match(r'(\d+)[-~](\d+)', br)
            if m: lo, hi = int(m.group(1)), int(m.group(2))
            else: lo, hi = None, None
        else:
            lo, hi = None, None
        arc_coverage[aid] = (lo, hi)
        print(f'    {aid}: block_range = {lo}-{hi}')
    all_covered = sorted(sum([list(range(lo, hi+1)) for (lo,hi) in arc_coverage.values() if lo and hi], []))
    gaps = [i for i in range(1, N+1) if i not in all_covered]
    print(f'  blocks not in any ARC range: {gaps}')
else:
    print('  phase0 file missing — skip ARC check')
    arc_coverage = {}

sec('1.4 defeat_blocks 정합 (Phase0 설계 vs TR emotional_beat.type=defeat)')
defeat_in_tr = []
for b in blocks:
    eb = b.get('emotional_beat')
    t = None
    if isinstance(eb, dict):
        t = eb.get('type')
    elif isinstance(eb, list) and eb:
        if isinstance(eb[0], dict): t = eb[0].get('type')
    if t == 'defeat':
        defeat_in_tr.append(b.get('block_id'))
print(f'  TR defeat blocks: {defeat_in_tr}')
if PHASE0:
    p0_defeat = PHASE0.get('defeat_blocks') or []
    # may be nested under different key
    if not p0_defeat:
        for k, v in PHASE0.items():
            if isinstance(v, list) and k.lower().endswith('defeat_blocks'):
                p0_defeat = v; break
    print(f'  phase0 defeat_blocks: {p0_defeat}')

sec('1.5 BI "동기화 산출물" 계약 — 직접 생성 금지 영역 검사')
# BI-harness §2.2: plot_roadmap, NPC 대량 본문, 자본 이력, 블록 제목/요약은 직접 작성 금지
# 즉 TR에서 copy만 해야 함. 7-pass PASS 2에서 이미 mismatch=0 확인했으므로 verbatim 준수.
# 여기서는 "BI에만 있고 TR에 없는" 한국어 본문이 있는지 검사
tr_text_signature = set()
for b in blocks:
    for fld in ['content','stakes','power_shift']:
        v = b.get(fld)
        if isinstance(v, str):
            # signature: 30-char chunks
            for i in range(0, len(v)-30, 30):
                tr_text_signature.add(v[i:i+30])
        elif isinstance(v, dict):
            for sv in v.values():
                if isinstance(sv, str):
                    for i in range(0, len(sv)-30, 30):
                        tr_text_signature.add(sv[i:i+30])
# Check BI plot_roadmap: should all be sourced from TR
bi_pr = BI['MasterBible']['plot_roadmap']
bi_orphan_chunks = 0
total_checked = 0
for pb in bi_pr:
    for fld in ['content','stakes','power_shift']:
        v = pb.get(fld)
        if isinstance(v, str) and len(v) >= 60:
            total_checked += 1
            sig = v[:30]
            if sig not in tr_text_signature:
                bi_orphan_chunks += 1
print(f'  BI plot_roadmap text chunks checked: {total_checked}')
print(f'  chunks not sourced from TR (potential direct writing): {bi_orphan_chunks}')

sec('1.6 PASS 1 verdict')
pass1_ok = pass1_stage_ok and ids_ok and total_ok and bi_orphan_chunks == 0
print(f'  파이프라인 stage 존재: {pass1_stage_ok}')
print(f'  TR ID/total 정합:    {ids_ok and total_ok}')
print(f'  BI 동기화 계약 준수: {bi_orphan_chunks == 0}')
print(f'  Overall PASS 1: {"PASS" if pass1_ok else "FAIL"}')


# ===========================================================================
# PASS 2 — 근본 원인 / 실패 패턴 (장르 스키마 적응)
# ===========================================================================
hdr('PASS 2 — 근본 원인 / 실패 패턴 분석')

sec('2.1 opponent 배분 다양성 (althistory 적응: 키워드 기반)')
# Collect opponent.name strings
opp_names = []
for b in blocks:
    opp = (b.get('genre_ext') or {}).get('opponent') or {}
    if isinstance(opp, dict):
        opp_names.append((b.get('block_id'), opp.get('name','')))
# Extract opponent keywords (known adversary actors from canon)
known_adversaries = ['이천','최만리','보수파','명나라','수양대군','문종','호조','병조','예조',
                     '집현전','관상감','유학자','사헌부','사간원','의정부','승정원','자기연민',
                     '위인전','자기과시','감동','회고','유혹','미담','헌정','불안','공포','승리감']
opp_keyword_freq = Counter()
opp_block_to_keywords = {}
for bid, name in opp_names:
    hits = [k for k in known_adversaries if k in name]
    opp_block_to_keywords[bid] = hits
    for k in hits:
        opp_keyword_freq[k] += 1
print(f'  총 opponent.name 서술 수: {len(opp_names)} ({len([n for _,n in opp_names if n])} non-empty)')
print(f'  고유 opponent.name 문자열 수: {len(set(n for _,n in opp_names))}')
print(f'  적대 키워드 빈도 (top 15):')
for k, c in opp_keyword_freq.most_common(15):
    share = c / N * 100
    mark = ' ⚠ >30%' if share > 30 else ''
    print(f'    {k:>10}: {c:>3} blocks ({share:.1f}%){mark}')

# Pattern R check (opponent 독점): dominant keyword >30%
top_kw, top_c = opp_keyword_freq.most_common(1)[0] if opp_keyword_freq else ('',0)
dominance = top_c / N * 100
pattern_R = dominance > 30
print(f'  Pattern R (opponent 독점 >30%): {"FAIL" if pattern_R else "PASS"} (최고 {top_kw}={dominance:.1f}%)')

# Per-ARC opponent variety
if PHASE0 and arc_coverage:
    print(f'  ARC별 고유 적대 키워드 수:')
    for aid, (lo, hi) in arc_coverage.items():
        if not lo or not hi: continue
        arc_kws = set()
        for i in range(lo, hi+1):
            arc_kws.update(opp_block_to_keywords.get(f'Block {i}', []))
        mark = ' ⚠ <2' if len(arc_kws) < 2 else ''
        print(f'    {aid} (Block {lo}-{hi}): {len(arc_kws)}종 {sorted(arc_kws)}{mark}')

sec('2.2 invention / method 다양성 (canon §5.2 문명건설 카탈로그 금지 정량화)')
inventions = []
methods = []
for b in blocks:
    ge = b.get('genre_ext') or {}
    inv = ge.get('invention','')
    mth = ge.get('method','')
    if inv: inventions.append((b.get('block_id'), inv))
    if mth: methods.append((b.get('block_id'), mth))

inv_counter = Counter(i for _,i in inventions)
mth_counter = Counter(m for _,m in methods)
print(f'  invention 필드 채움: {len(inventions)}/{N}')
print(f'  고유 invention 수: {len(inv_counter)}')
print(f'  invention 반복 top 5:')
for inv, c in inv_counter.most_common(5):
    print(f'    × {c}: {str(inv)[:70]}')
print(f'  method 필드 채움: {len(methods)}/{N}')
print(f'  고유 method 수: {len(mth_counter)}')

# Pattern: 같은 invention 3회 이상 반복
inv_repeat_over_3 = [(k,c) for k,c in inv_counter.items() if c >= 3]
print(f'  invention 3회 이상 반복: {len(inv_repeat_over_3)} 건')
for k, c in inv_repeat_over_3[:5]:
    print(f'    × {c}: {str(k)[:60]}')

sec('2.3 solution 말미 20자 반복 (Pattern T 적응)')
sols = []
for b in blocks:
    c = b.get('content')
    if isinstance(c, dict):
        s = c.get('solution','')
    elif isinstance(c, str):
        s = c
    else:
        s = ''
    if isinstance(s, str) and len(s) >= 20:
        sols.append((b.get('block_id'), s))

tails = Counter(s[-20:] for _,s in sols)
repeated_tails = [(t,c) for t,c in tails.items() if c >= 3]
print(f'  solution 필드 있는 블록: {len(sols)}/{N}')
print(f'  solution 말미 20자 반복 (3회 이상): {len(repeated_tails)} 건')
for t, c in repeated_tails[:5]:
    print(f'    × {c}: "...{t}"')
pattern_T = any(c >= 5 for _,c in repeated_tails)
print(f'  Pattern T (solution 말미 5회+ 동일): {"FAIL" if pattern_T else "PASS"}')

sec('2.4 10블록 윈도 다양성 (RC-5 아크 내 고정 검사)')
# 블록 1-10, 11-20, ..., 61-70 윈도별 고유 method / opponent 키워드
windows = [(i, i+9) for i in range(1, N+1, 10)]
for lo, hi in windows:
    win_methods = set()
    win_kws = set()
    win_inventions = set()
    for j in range(lo, hi+1):
        b = next((x for x in blocks if x.get('block_id') == f'Block {j}'), None)
        if not b: continue
        ge = b.get('genre_ext') or {}
        if ge.get('method'): win_methods.add(ge['method'])
        if ge.get('invention'): win_inventions.add(ge['invention'])
        win_kws.update(opp_block_to_keywords.get(f'Block {j}', []))
    mark_m = ' ⚠ <3' if len(win_methods) < 3 else ''
    mark_i = ' ⚠ <3' if len(win_inventions) < 3 else ''
    mark_o = ' ⚠ <2' if len(win_kws) < 2 else ''
    print(f'  Block {lo:2}-{hi}: method={len(win_methods)}{mark_m}  invention={len(win_inventions)}{mark_i}  opp_kws={len(win_kws)}{mark_o}')

sec('2.5 PASS 2 verdict')
pass2_ok = not pattern_R and not pattern_T and not inv_repeat_over_3
print(f'  Pattern R (opponent 독점):    {"FAIL" if pattern_R else "PASS"}')
print(f'  invention 3회+ 반복:         {"FAIL" if inv_repeat_over_3 else "PASS"}')
print(f'  Pattern T (solution 템플릿): {"FAIL" if pattern_T else "PASS"}')
print(f'  Overall PASS 2: {"PASS" if pass2_ok else "REVIEW"}')


# ===========================================================================
# PASS 3 — 철학 준수도 (canon §4/§5 + 4단 공식 + BI 동기화)
# ===========================================================================
hdr('PASS 3 — 철학 준수도 (canon §4/§5 + 4단 공식)')

sec('3.1 4단 공식 완결성 (canon §5.2 "발명→태도→자리→다음 문")')
# canon §5.2: 매 발명은 `invention → attitude_change → seat_change → next_door` 4단 공식
four_step = ['invention','attitude_change','seat_change','next_door']
completeness = Counter()
per_block_missing = []
for b in blocks:
    ge = b.get('genre_ext') or {}
    filled = sum(1 for k in four_step if ge.get(k))
    completeness[filled] += 1
    missing = [k for k in four_step if not ge.get(k)]
    if missing:
        per_block_missing.append((b.get('block_id'), missing))
print(f'  4단 완결 분포:')
for n in [0,1,2,3,4]:
    print(f'    {n}/4 채움: {completeness[n]} 블록')
print(f'  4단 결손 블록 수: {len(per_block_missing)}/{N}')
for bid, miss in per_block_missing[:5]:
    print(f'    {bid}: 빠진 필드 = {miss}')
pass3_4step = completeness[4] >= N - 3  # 70 중 67 이상 4단 완결 허용

sec('3.2 canon §5 6원칙 실질 준수 (규칙 선언 + 역침투 탐지)')
# 왕 총애 미담, 문명건설 카탈로그, 감동 위인전, 도덕적 거부, 자기연민, 장광설
principles = {
    '왕 총애 미담 금지': ['은혜','은총','성은','성총','총애'],
    '문명건설 카탈로그 금지': ['또 발명했다','연달아 발명','발명품 목록','다음에 뭘 만들'],
    '감동 위인전 금지': ['위대한','레오나르도','조선의 영웅','위인'],
    '도덕적 거부 금지': ['윤리적으로','도덕적으로 거부','사람을 살리는 기술'],
    '자기연민 금지': ['없으면 난','아무것도 못','혼자서는'],
    '장광설 금지': None,  # 길이 기반 (별도 처리)
}
violations = {}
for pname, keywords in principles.items():
    if keywords is None: continue
    count = 0
    sample = []
    for b in blocks:
        content_val = b.get('content','')
        if isinstance(content_val, dict):
            content_val = json.dumps(content_val, ensure_ascii=False)
        stakes_val = b.get('stakes','') or ''
        if isinstance(stakes_val, dict):
            stakes_val = json.dumps(stakes_val, ensure_ascii=False)
        text = content_val + ' ' + stakes_val
        for kw in keywords:
            if kw in text:
                count += 1
                if len(sample) < 2:
                    sample.append((b.get('block_id'), kw))
                break
    violations[pname] = (count, sample)
    mark = ' ⚠' if count > 0 else ''
    print(f'  {pname}: narrative {count}건 keyword 매칭{mark}')
    for bid, kw in sample:
        print(f'    - {bid}: "{kw}"')
# 장광설 금지: content.solution 평균/최대 길이
sol_lens = [len(s) for _,s in sols]
if sol_lens:
    avg_sol = sum(sol_lens)/len(sol_lens)
    max_sol = max(sol_lens)
    print(f'  장광설 금지: solution 평균={avg_sol:.0f}자, 최대={max_sol}자')
else:
    avg_sol = max_sol = 0

sec('3.3 Post-Patron Independence Lock 4축 실증 (canon §4)')
# 4축: 도면 표준 / 검수 결재선 / 제자 라인 / 자재 배분 결재권
axes = {
    '도면 표준': ['도면 표준','표기법','공차'],
    '검수 결재선': ['검수 결재선','검수권','기술소 제조','핵심 부품'],
    '제자 라인': ['제자','김순','판독 훈련','기술 교범','교범'],
    '자재 배분 결재권': ['자재 배분','자재 결재','기술 자재','철'],
}
axis_hits = {}
for aname, kws in axes.items():
    count = 0
    for b in blocks:
        text = json.dumps(b, ensure_ascii=False)
        if any(k in text for k in kws):
            count += 1
    axis_hits[aname] = count
    # 각 축은 canon §4에 따라 ARC 4-7 (Block 31-70)에서 제도화되어야 함
    mark = ' ✅' if count >= 10 else ' ⚠ 부족'
    print(f'  {aname}: {count}/70 블록 등장{mark}')

sec('3.4 Phase0 §4 Post-Patron Independence Lock 8단 누적 검증')
# handoff 문서가 claim한 Phase0 §4 Lock 8단 실제 존재 확인
lock_stages = {
    'Block 40 관청화': '관청화' in json.dumps(blocks[39], ensure_ascii=False),
    'Block 49 검수 축 잠금': '검수' in json.dumps(blocks[48], ensure_ascii=False),
    'Block 59 마지막 보고': '마지막 보고' in json.dumps(blocks[58], ensure_ascii=False) or '그래야 한다' in json.dumps(blocks[58], ensure_ascii=False),
    'Block 60 각성': '각성' in json.dumps(blocks[59], ensure_ascii=False),
    'Block 65 세종 사후': '세종' in json.dumps(blocks[64], ensure_ascii=False) and ('붕어' in json.dumps(blocks[64], ensure_ascii=False) or '사후' in json.dumps(blocks[64], ensure_ascii=False)),
    'Block 67 문종 타협': '문종' in json.dumps(blocks[66], ensure_ascii=False) and '타협' in json.dumps(blocks[66], ensure_ascii=False),
    'Block 69 기술소 조정 필수 관청': '조정의 필수 관청' in json.dumps(blocks[68], ensure_ascii=False),
    'Block 70 자격루 에필로그': '자격루' in json.dumps(blocks[69], ensure_ascii=False),
}
locks_ok = sum(1 for v in lock_stages.values() if v)
for k, v in lock_stages.items():
    print(f'  {k}: {"✅" if v else "❌"}')
print(f'  Lock 8단 누적: {locks_ok}/8')

sec('3.5 PASS 3 verdict')
any_violation = any(c > 0 for c, _ in violations.values())
pass3_ok = pass3_4step and locks_ok >= 7 and all(c >= 10 for c in axis_hits.values())
print(f'  4단 공식 완결 (>=67/70):    {pass3_4step}')
print(f'  canon §5 규칙 선언 탐지:   {"있음 (의미 해석 필요)" if any_violation else "없음"}')
print(f'  Independence Lock 8단:    {locks_ok}/8 {"PASS" if locks_ok >= 7 else "FAIL"}')
print(f'  4축 제도화 keyword:       {"PASS" if all(c >= 10 for c in axis_hits.values()) else "FAIL"}')
print(f'  Overall PASS 3: {"PASS" if pass3_ok else "REVIEW"}')


# ===========================================================================
# SUMMARY
# ===========================================================================
hdr('3-PASS AUDIT SUMMARY')
summary = {
    'PASS 1 구조 정합성':       pass1_ok,
    'PASS 2 실패 패턴':         pass2_ok,
    'PASS 3 철학 준수도':       pass3_ok,
}
for k, v in summary.items():
    print(f'  {k}: {"PASS" if v else "REVIEW"}')
print()
all_ok = all(summary.values())
print(f'OVERALL: {"PASS" if all_ok else "REVIEW NEEDED"}')
