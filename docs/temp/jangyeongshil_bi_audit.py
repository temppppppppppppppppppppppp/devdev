"""
Independent 7-pass audit for jangyeongshil_industrial_revolution
BI refresh correctness verification (read-only).
Runs at cwd = repo root.
"""
import json, os, re, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

TR_PATH = r'treatments/jangyeongshil_industrial_revolution_tr_block_025_draft.json'
BI_PATH = r'bible/jangyeongshil_industrial_revolution_bi.json'
LS_PATH = r'docs/2026-04-08/jangyeongshil_industrial_revolution_live_status.md'

def header(t):
    print('=' * 72)
    print(t)
    print('=' * 72)

# ---- PASS 1: file integrity ----
header('PASS 1 - File integrity')
verdict_1 = True
for p in [TR_PATH, BI_PATH]:
    size = os.path.getsize(p)
    with open(p, 'rb') as f:
        raw = f.read()
    try:
        s = raw.decode('utf-8')
        utf8_ok = True
    except UnicodeDecodeError:
        utf8_ok = False
        verdict_1 = False
        s = raw.decode('utf-8', errors='replace')
    repl = s.count('\ufffd')
    if repl > 0:
        verdict_1 = False
    try:
        json.loads(s)
        json_ok = True
    except Exception:
        json_ok = False
        verdict_1 = False
    print(f'  {os.path.basename(p):60s} size={size:>9}  utf8={utf8_ok}  json={json_ok}  repl_char={repl}')
print(f'  PASS 1 verdict: {"OK" if verdict_1 else "FAIL"}')
print()

with open(TR_PATH, encoding='utf-8') as f:
    TR = json.load(f)
with open(BI_PATH, encoding='utf-8') as f:
    BI = json.load(f)

# ---- PASS 2: plot_roadmap verbatim alignment ----
header('PASS 2 - plot_roadmap 70 verbatim vs TR 70')
tr_blocks = TR['blocks']
bi_pr = BI['MasterBible']['plot_roadmap']
print(f'  TR len={len(tr_blocks)}  BI plot_roadmap len={len(bi_pr)}')

tr_by_id = {}
for b in tr_blocks:
    bid = b.get('block_id') or b.get('id')
    tr_by_id[bid] = b

check_fields = ['title', 'content', 'stakes', 'power_shift', 'relationship_delta',
                'foreshadow', 'callback', 'emotional_beat', 'tension_level',
                'pov_character', 'location', 'time_span', 'genre_ext']

mismatches = []
missing_in_tr = []
for bi_blk in bi_pr:
    bid = bi_blk.get('block_id')
    if bid not in tr_by_id:
        missing_in_tr.append(bid)
        continue
    trb = tr_by_id[bid]
    for fld in check_fields:
        if fld in bi_blk or fld in trb:
            if bi_blk.get(fld) != trb.get(fld):
                mismatches.append((bid, fld))

print(f'  missing BI blocks in TR: {len(missing_in_tr)} {missing_in_tr[:5]}')
print(f'  verbatim mismatches: {len(mismatches)}')
if mismatches:
    fld_counts = Counter(f for _, f in mismatches)
    print(f'  mismatch by field: {dict(fld_counts.most_common())}')
    print(f'  first 15 mismatches: {mismatches[:15]}')
verdict_2 = (not mismatches) and (not missing_in_tr) and len(bi_pr) == 70
print(f'  PASS 2 verdict: {"OK" if verdict_2 else "FAIL"}')
print()

# ---- PASS 3: finance sync ----
header('PASS 3 - Protagonist finance sync (BI vs TR Block 69 capital_after)')
blk69 = tr_by_id.get('Block 69', {})
# canonical location: genre_ext.capital_after
cap_after = (blk69.get('genre_ext') or {}).get('capital_after')
print(f'  TR Block 69 capital_after type: {type(cap_after).__name__}')

fin = BI['MasterBible']['FinanceHUD']['Protagonist']['actual_truth'].get('financial_status', {})
total = fin.get('total_assets')
mob = fin.get('mobilizable_capital')
maxa = fin.get('max_assets')

def prev(x):
    s = str(x)
    return s[:100] + ('...' if len(s) > 100 else '')

print(f'  BI total_assets:           {prev(total)}')
print(f'  BI mobilizable_capital:    {prev(mob)}')
print(f'  BI max_assets:             {prev(maxa)}')
print(f'  TR Block 69 capital_after: {prev(cap_after)}')
eq_total = total == cap_after
eq_mob = mob == cap_after
eq_max = maxa == cap_after
print(f'  total==B69: {eq_total}   mob==B69: {eq_mob}   max==B69: {eq_max}')
verdict_3 = (cap_after is not None) and eq_total and eq_mob and eq_max
print(f'  PASS 3 verdict: {"OK" if verdict_3 else "CHECK"}')
print()

# ---- PASS 4: Sejong deceased consistency ----
header('PASS 4 - Sejong deceased consistency (narrative body only)')
he = BI['MasterBible']['HistoricalEvents']
sejong_death_events = [e for e in he
                       if '세종' in str(e)
                       and ('붕어' in str(e) or 'death' in str(e).lower() or 'Block 65' in str(e))]
print(f'  HistoricalEvents with Sejong-death keywords: {len(sejong_death_events)}')
for e in sejong_death_events[:3]:
    print(f'   - block_range={e.get("block_range")} title={str(e.get("title",""))[:60]}')

# Only check NARRATIVE fields (content/stakes), not meta guard fields
# (meta fields like craft_notes/opponent/genre_ext contain rule-declarations
#  of the form "세종 이름 0회" which are the rule itself, not a violation)
narrative_fields = ['content', 'stakes']
post_death_subjects = 0
results = []
for blk_id in ['Block 66', 'Block 67', 'Block 68', 'Block 69', 'Block 70']:
    b = tr_by_id.get(blk_id, {})
    narrative_text = ''
    for fld in narrative_fields:
        v = b.get(fld)
        if v is not None:
            narrative_text += ' ' + json.dumps(v, ensure_ascii=False)
    h1 = len(re.findall(r'세종이(?!라)', narrative_text))
    h2 = len(re.findall(r'세종은', narrative_text))
    h3 = len(re.findall(r'세종께서', narrative_text))
    hits = h1 + h2 + h3
    narrative_sejong = narrative_text.count('세종')
    post_death_subjects += hits
    results.append((blk_id, hits, narrative_sejong))
print(f'  post-death active-subject (narrative content/stakes only): {post_death_subjects}')
for bid, act, allm in results:
    print(f'   - {bid}: active-subject={act}  narrative-sejong-any={allm}')
verdict_4 = post_death_subjects == 0
print(f'  PASS 4 verdict: {"OK" if verdict_4 else "CHECK"}')
print()

# ---- PASS 5: Option C repair persistence ----
header('PASS 5 - Option C repair persistence')

def get_eb_type(b):
    eb = b.get('emotional_beat')
    if isinstance(eb, dict):
        return eb.get('type')
    if isinstance(eb, list) and eb:
        first = eb[0]
        if isinstance(first, dict):
            return first.get('type')
        return first
    return eb

b62 = tr_by_id.get('Block 62', {})
b62_type = get_eb_type(b62)
print(f'  TR Block 62 emotional_beat.type = {b62_type}   (expected: defeat)')

b69 = tr_by_id.get('Block 69', {})
cbs = b69.get('callback') or []
if isinstance(cbs, str):
    cbs = [cbs]
print(f'  TR Block 69 callback count = {len(cbs)}')
for c in cbs[:5]:
    print(f'    - {str(c)[:100]}')

b70 = tr_by_id.get('Block 70', {})
fs = b70.get('foreshadow') or []
if isinstance(fs, str):
    fs = [fs]
print(f'  TR Block 70 foreshadow count = {len(fs)}   (Option C removed 2)')
for c in fs[:5]:
    print(f'    - {str(c)[:100]}')

bi_b62 = next((b for b in bi_pr if b.get('block_id') == 'Block 62'), None)
bi_b62_type = get_eb_type(bi_b62 or {})
print(f'  BI Block 62 emotional_beat.type = {bi_b62_type}   (expected: defeat)')

bi_b69 = next((b for b in bi_pr if b.get('block_id') == 'Block 69'), None)
bi_b69_cbs = (bi_b69 or {}).get('callback') or []
if isinstance(bi_b69_cbs, str):
    bi_b69_cbs = [bi_b69_cbs]
print(f'  BI Block 69 callback count = {len(bi_b69_cbs)}   (TR: {len(cbs)})')

bi_b70 = next((b for b in bi_pr if b.get('block_id') == 'Block 70'), None)
bi_b70_fs = (bi_b70 or {}).get('foreshadow') or []
if isinstance(bi_b70_fs, str):
    bi_b70_fs = [bi_b70_fs]
print(f'  BI Block 70 foreshadow count = {len(bi_b70_fs)}   (TR: {len(fs)})')

verdict_5 = (b62_type == 'defeat' and bi_b62_type == 'defeat'
             and len(cbs) == len(bi_b69_cbs) and len(fs) == len(bi_b70_fs))
print(f'  PASS 5 verdict: {"OK" if verdict_5 else "CHECK"}')
print()

# ---- PASS 6: canon §5 Sejong name appearance ----
header('PASS 6 - canon Sec5 Sejong name in narrative body (B65/68/70)')
# Narrative body only — content field alone
verdict_6 = True
for blk_id in ['Block 65', 'Block 68', 'Block 70']:
    b = tr_by_id.get(blk_id, {})
    content_val = b.get('content', '')
    if not isinstance(content_val, str):
        content_val = json.dumps(content_val, ensure_ascii=False)
    n = content_val.count('세종')
    print(f'  {blk_id} content-field 세종 count = {n}')
    if n > 0:
        verdict_6 = False
        for ctx in re.findall(r'.{0,25}세종.{0,25}', content_val)[:3]:
            print(f'    - "{ctx.strip()}"')
print(f'  PASS 6 verdict: {"OK" if verdict_6 else "REVIEW"}')
print()

# ---- PASS 7: live_status drift ----
header('PASS 7 - live_status drift')
with open(LS_PATH, encoding='utf-8') as f:
    ls = f.read()
checks = {
    'Block 1-70 boundary': ('Block 1-70' in ls or 'Block 70' in ls),
    '_total_blocks 70': ('_total_blocks' in ls and '70' in ls),
    'Block 61-70 self-audit': ('Block 61-70' in ls and 'PASS' in ls),
    'Option C / 수리 mention': ('Option C' in ls or '수리' in ls),
    'BI refresh mention': ('BI refresh' in ls or 'bi_refresh' in ls or 'BI 인계' in ls),
    'Block 55 stale marker absent': 'Block 55 기준' not in ls,
}
for k, v in checks.items():
    print(f'  {k}: {v}')
verdict_7 = all(checks.values())
print(f'  PASS 7 verdict: {"OK" if verdict_7 else "DRIFT"}')
print()

# ---- Summary ----
header('SUMMARY')
summary = {
    'PASS 1 file integrity':      verdict_1,
    'PASS 2 BI-TR verbatim':      verdict_2,
    'PASS 3 finance sync':        verdict_3,
    'PASS 4 Sejong deceased':     verdict_4,
    'PASS 5 Option C persist':    verdict_5,
    'PASS 6 canon Sec5 Sejong':   verdict_6,
    'PASS 7 live_status drift':   verdict_7,
}
for k, v in summary.items():
    mark = 'OK' if v is True else ('FAIL' if v is False else str(v))
    print(f'  {k}: {mark}')
all_ok = all(v is True for v in summary.values())
print()
print(f'OVERALL: {"PASS" if all_ok else "REVIEW NEEDED"}')
