# 글도비 전체 프로젝트 비용 계산 (Stage 0~4)

PRO_INPUT_PER_MTOK = 1.25
PRO_OUTPUT_PER_MTOK = 10.0
FLASH_INPUT_PER_MTOK = 0.30
FLASH_OUTPUT_PER_MTOK = 2.50

print('=' * 70)
print('글도비 250화 프로젝트 전체 비용 분석 (캐시 미사용)')
print('=' * 70)
print()

EXCHANGE_RATE = 1300

# ============================================================
# Stage 0: Bible Recovery (1회)
# ============================================================
print('=== Stage 0: Bible Recovery ===')
analyst_bible_input = 20000  # 기존 원고 + treatment
analyst_bible_output = 8192
bible_cost = (analyst_bible_input / 1_000_000 * PRO_INPUT_PER_MTOK) + (analyst_bible_output / 1_000_000 * PRO_OUTPUT_PER_MTOK)
print(f'Analyst (Bible Recovery) 1회: ${bible_cost:.4f}')
stage0_total = bible_cost
print(f'Stage 0 총 비용: ${stage0_total:.2f} ({int(stage0_total * EXCHANGE_RATE):,}원)')
print()

# ============================================================
# Stage 1: Volume Strategy (10회)
# ============================================================
print('=== Stage 1: Volume Strategy ===')
analyst_volume_input = 8000
analyst_volume_output = 4096
volume_cost = (analyst_volume_input / 1_000_000 * PRO_INPUT_PER_MTOK) + (analyst_volume_output / 1_000_000 * PRO_OUTPUT_PER_MTOK)
print(f'Analyst (Volume) 1회: ${volume_cost:.4f}')
print(f'10개 Volume × 1회: ${volume_cost * 10:.2f}')
stage1_total = volume_cost * 10
print(f'Stage 1 총 비용: ${stage1_total:.2f} ({int(stage1_total * EXCHANGE_RATE):,}원)')
print()

# ============================================================
# Stage 2: Arc Tactical Design (50회)
# ============================================================
print('=== Stage 2: Arc Tactical Design ===')
analyst_arc_input = 10000
analyst_arc_output = 6144
arc_cost = (analyst_arc_input / 1_000_000 * PRO_INPUT_PER_MTOK) + (analyst_arc_output / 1_000_000 * PRO_OUTPUT_PER_MTOK)
print(f'Analyst (Arc) 1회: ${arc_cost:.4f}')

# Director 검수 (재시도 고려: 평균 1.5회)
director_arc_input = 6000
director_arc_output = 1000
director_arc_cost = (director_arc_input / 1_000_000 * FLASH_INPUT_PER_MTOK) + (director_arc_output / 1_000_000 * FLASH_OUTPUT_PER_MTOK)
print(f'Director (Arc Review) 1회: ${director_arc_cost:.4f}')

arc_with_review = (arc_cost + director_arc_cost) * 1.5  # 재시도 고려
print(f'Arc 1개 평균 (재시도 포함): ${arc_with_review:.4f}')
print(f'50개 Arc: ${arc_with_review * 50:.2f}')
stage2_total = arc_with_review * 50
print(f'Stage 2 총 비용: ${stage2_total:.2f} ({int(stage2_total * EXCHANGE_RATE):,}원)')
print()

# ============================================================
# Stage 3: Episode Blueprinting (250회)
# ============================================================
print('=== Stage 3: Episode Blueprinting ===')
weaver_input = 5000
weaver_output = 2048
weaver_cost = (weaver_input / 1_000_000 * PRO_INPUT_PER_MTOK) + (weaver_output / 1_000_000 * PRO_OUTPUT_PER_MTOK)
print(f'Weaver (Arc Drive) 50회: ${weaver_cost * 50:.2f}')

architect_input = 5000
architect_output = 4096
architect_cost = (architect_input / 1_000_000 * FLASH_INPUT_PER_MTOK) + (architect_output / 1_000_000 * FLASH_OUTPUT_PER_MTOK)
print(f'Architect 1회: ${architect_cost:.4f}')

director_bp_input = 4000
director_bp_output = 1000
director_bp_cost = (director_bp_input / 1_000_000 * FLASH_INPUT_PER_MTOK) + (director_bp_output / 1_000_000 * FLASH_OUTPUT_PER_MTOK)
print(f'Director (Blueprint Review) 1회: ${director_bp_cost:.4f}')

# 재시도 고려 (통과율 70%)
bp_with_review = (architect_cost + director_bp_cost) * 1.4
print(f'Blueprint 1개 평균 (재시도 포함): ${bp_with_review:.4f}')
print(f'250개 Blueprint: ${bp_with_review * 250:.2f}')

stage3_total = weaver_cost * 50 + bp_with_review * 250
print(f'Stage 3 총 비용: ${stage3_total:.2f} ({int(stage3_total * EXCHANGE_RATE):,}원)')
print()

# ============================================================
# Stage 4: Manuscript Production (250회)
# ============================================================
print('=== Stage 4: Manuscript Production (V41) ===')
writer_input = 6000
writer_output = 8192
writer_cost = (writer_input / 1_000_000 * PRO_INPUT_PER_MTOK) + (writer_output / 1_000_000 * PRO_OUTPUT_PER_MTOK)
print(f'Writer 1회: ${writer_cost:.4f}')

director_ms_input = 8000
director_ms_output = 1000
director_ms_cost = (director_ms_input / 1_000_000 * FLASH_INPUT_PER_MTOK) + (director_ms_output / 1_000_000 * FLASH_OUTPUT_PER_MTOK)
print(f'Director (Manuscript Review) 1회: ${director_ms_cost:.4f}')

# 재시도 고려 (통과율 55%)
ms_with_review = (writer_cost + director_ms_cost) * 1.8
print(f'Episode 1개 평균 (재시도 포함): ${ms_with_review:.4f}')
print(f'250개 Episode: ${ms_with_review * 250:.2f}')
stage4_v41 = ms_with_review * 250
print(f'Stage 4 총 비용 (V41): ${stage4_v41:.2f} ({int(stage4_v41 * EXCHANGE_RATE):,}원)')
print()

print('=== Stage 4: Manuscript Production (V0128) ===')
# BLOCKING: Python 기반, 비용 0
blocking_cost = 0
print(f'BLOCKING Validator: ${blocking_cost} (Python)')

# SCORING: gemini-2.5-pro
scoring_input = 8000
scoring_output = 2000
scoring_cost = (scoring_input / 1_000_000 * PRO_INPUT_PER_MTOK) + (scoring_output / 1_000_000 * PRO_OUTPUT_PER_MTOK)
print(f'SCORING Evaluator: ${scoring_cost:.4f}')

# ADVISORY: gemini-2.5-flash
advisory_input = 8000
advisory_output = 1000
advisory_cost = (advisory_input / 1_000_000 * FLASH_INPUT_PER_MTOK) + (advisory_output / 1_000_000 * FLASH_OUTPUT_PER_MTOK)
print(f'ADVISORY Evaluator: ${advisory_cost:.4f}')

validation_cost = blocking_cost + scoring_cost + advisory_cost
print(f'ValidationOrchestrator 1회: ${validation_cost:.4f}')

# 재시도 고려 (통과율 80%)
ms_with_validation = (writer_cost + validation_cost) * 1.25
print(f'Episode 1개 평균 (재시도 포함): ${ms_with_validation:.4f}')
print(f'250개 Episode: ${ms_with_validation * 250:.2f}')
stage4_v0128 = ms_with_validation * 250
print(f'Stage 4 총 비용 (V0128): ${stage4_v0128:.2f} ({int(stage4_v0128 * EXCHANGE_RATE):,}원)')
print()

# ============================================================
# 총 비용 비교
# ============================================================
print('=' * 70)
print('전체 프로젝트 비용 비교 (250화)')
print('=' * 70)
print()

total_v41 = stage0_total + stage1_total + stage2_total + stage3_total + stage4_v41
total_v0128 = stage0_total + stage1_total + stage2_total + stage3_total + stage4_v0128

print(f'Stage 0 (Bible): ${stage0_total:.2f} ({int(stage0_total * EXCHANGE_RATE):,}원)')
print(f'Stage 1 (Volumes): ${stage1_total:.2f} ({int(stage1_total * EXCHANGE_RATE):,}원)')
print(f'Stage 2 (Arcs): ${stage2_total:.2f} ({int(stage2_total * EXCHANGE_RATE):,}원)')
print(f'Stage 3 (Blueprints): ${stage3_total:.2f} ({int(stage3_total * EXCHANGE_RATE):,}원)')
print()
print(f'Stage 4 (V41): ${stage4_v41:.2f} ({int(stage4_v41 * EXCHANGE_RATE):,}원)')
print(f'Stage 4 (V0128): ${stage4_v0128:.2f} ({int(stage4_v0128 * EXCHANGE_RATE):,}원)')
print()
print('=' * 70)
print(f'V41 전체: ${total_v41:.2f} = {int(total_v41 * EXCHANGE_RATE):,}원')
print(f'V0128 전체: ${total_v0128:.2f} = {int(total_v0128 * EXCHANGE_RATE):,}원')
print(f'차이: ${total_v41 - total_v0128:.2f} = {int((total_v41 - total_v0128) * EXCHANGE_RATE):,}원')
print('=' * 70)
print()

# ============================================================
# 50만원 예산 대비
# ============================================================
budget = 500_000
print(f'V0128 목표 예산: {budget:,}원')
print(f'V41 예상 비용: {int(total_v41 * EXCHANGE_RATE):,}원 ({int(total_v41 * EXCHANGE_RATE)/budget*100:.1f}%)')
print(f'V0128 예상 비용: {int(total_v0128 * EXCHANGE_RATE):,}원 ({int(total_v0128 * EXCHANGE_RATE)/budget*100:.1f}%)')
print()

if int(total_v0128 * EXCHANGE_RATE) <= budget:
    print(f'OK V0128은 50만원 예산 내 가능 (여유: {budget - int(total_v0128 * EXCHANGE_RATE):,}원)')
else:
    print(f'WARNING 50만원 예산 초과 (초과: {int(total_v0128 * EXCHANGE_RATE) - budget:,}원)')

print()
print('=' * 70)
print('캐시 적용 시 (-90% 절감)')
print('=' * 70)
cached_v41 = int(total_v41 * 0.1 * EXCHANGE_RATE)
cached_v0128 = int(total_v0128 * 0.1 * EXCHANGE_RATE)
print(f'V41 (캐시): {cached_v41:,}원 ({cached_v41/budget*100:.1f}%)')
print(f'V0128 (캐시): {cached_v0128:,}원 ({cached_v0128/budget*100:.1f}%)')
print(f'여유: {budget - cached_v0128:,}원')
