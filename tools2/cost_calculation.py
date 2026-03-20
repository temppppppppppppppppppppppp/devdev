# 현실적인 API 비용 계산 (Gemini API 기준)

PRO_INPUT_PER_MTOK = 1.25
PRO_OUTPUT_PER_MTOK = 10.0
FLASH_INPUT_PER_MTOK = 0.30
FLASH_OUTPUT_PER_MTOK = 2.50

print('=' * 60)
print('글도비 V41 vs V0128 비용 비교 (250화 프로젝트)')
print('=' * 60)
print()

# Gemini API 가격 (2026년 기준)
# gemini-3-pro-preview: Input $1.25/M, Output $10.00/M
# gemini-2.5-pro: Input $1.25/M, Output $10.00/M
# gemini-2.5-flash: Input $0.30/M, Output $2.50/M
# gemini-2.0-flash: Input $0.30/M, Output $2.50/M

EXCHANGE_RATE = 1300  # 1 USD = 1300 KRW

print('=== 현재 시스템 (V41) ===')
print('통과율: 55% → 평균 재시도 1.8회')
print()

# Writer (gemini-3-pro-preview)
writer_input = 6000  # blueprint + context + style seeds
writer_output = 8192  # 원고 (최대 토큰)
writer_cost_per_call = (writer_input / 1_000_000 * PRO_INPUT_PER_MTOK) + (writer_output / 1_000_000 * PRO_OUTPUT_PER_MTOK)
print(f'Writer 1회: ${writer_cost_per_call:.4f}')

# Director (gemini-2.0-flash)
director_input = 8000  # 원고 + arc_doc + history
director_output = 1000  # 피드백 JSON
director_cost_per_call = (director_input / 1_000_000 * FLASH_INPUT_PER_MTOK) + (director_output / 1_000_000 * FLASH_OUTPUT_PER_MTOK)
print(f'Director 1회: ${director_cost_per_call:.4f}')

# Architect (gemini-2.5-flash, Tier 1)
architect_input = 5000
architect_output = 4096
architect_cost_per_call = (architect_input / 1_000_000 * FLASH_INPUT_PER_MTOK) + (architect_output / 1_000_000 * FLASH_OUTPUT_PER_MTOK)
print(f'Architect 1회: ${architect_cost_per_call:.4f}')

# 에피소드당 평균 비용 (재시도 고려)
# Architect는 1회 실행 (이미 PASS된 blueprint 사용)
# Writer + Director는 재시도 1.8회
current_ep_cost = architect_cost_per_call + (writer_cost_per_call + director_cost_per_call) * 1.8
print(f'\n에피소드당 평균: ${current_ep_cost:.4f}')
print(f'250화 프로젝트: ${current_ep_cost * 250:.2f}')
print(f'250화 프로젝트 (원화): {int(current_ep_cost * 250 * EXCHANGE_RATE):,}원')
print()

print('=' * 60)
print()

print('=== V0128 시스템 ===')
print('통과율: 80% → 평균 재시도 1.25회')
print()

# Writer (동일)
print(f'Writer 1회: ${writer_cost_per_call:.4f}')

# BLOCKING Validator (Python 기반, LLM 불필요)
blocking_cost = 0
print(f'BLOCKING Validator: $0 (Python 기반)')

# SCORING Evaluator (gemini-2.5-pro)
scoring_input = 8000  # 원고 + context
scoring_output = 2000  # 점수 + breakdown
scoring_cost = (scoring_input / 1_000_000 * PRO_INPUT_PER_MTOK) + (scoring_output / 1_000_000 * PRO_OUTPUT_PER_MTOK)
print(f'SCORING Evaluator: ${scoring_cost:.4f}')

# ADVISORY Evaluator (gemini-2.5-flash)
advisory_input = 8000
advisory_output = 1000
advisory_cost = (advisory_input / 1_000_000 * FLASH_INPUT_PER_MTOK) + (advisory_output / 1_000_000 * FLASH_OUTPUT_PER_MTOK)
print(f'ADVISORY Evaluator: ${advisory_cost:.4f}')

validation_cost_per_call = blocking_cost + scoring_cost + advisory_cost
print(f'ValidationOrchestrator 1회: ${validation_cost_per_call:.4f}')

# Architect (동일)
print(f'Architect 1회: ${architect_cost_per_call:.4f}')

# 에피소드당 평균 비용
v0128_ep_cost = architect_cost_per_call + (writer_cost_per_call + validation_cost_per_call) * 1.25
print(f'\n에피소드당 평균: ${v0128_ep_cost:.4f}')
print(f'250화 프로젝트: ${v0128_ep_cost * 250:.2f}')
print(f'250화 프로젝트 (원화): {int(v0128_ep_cost * 250 * EXCHANGE_RATE):,}원')
print()

print('=' * 60)
print()

print('=== 비교 결과 ===')
diff = current_ep_cost - v0128_ep_cost
diff_pct = (diff / current_ep_cost) * 100
print(f'에피소드당 절감: ${diff:.4f} ({diff_pct:.1f}%)')
print(f'250화 절감액: ${diff * 250:.2f}')
print(f'250화 절감액 (원화): {int(diff * 250 * EXCHANGE_RATE):,}원')
print()

# 50만원 예산 대비
budget_krw = 500_000
current_krw = int(current_ep_cost * 250 * EXCHANGE_RATE)
v0128_krw = int(v0128_ep_cost * 250 * EXCHANGE_RATE)

print(f'V0128 목표 예산: {budget_krw:,}원')
print(f'현재 V41 예상 비용: {current_krw:,}원 ({(current_krw/budget_krw)*100:.1f}%)')
print(f'V0128 예상 비용: {v0128_krw:,}원 ({(v0128_krw/budget_krw)*100:.1f}%)')
print()

if v0128_krw <= budget_krw:
    print(f'OK V0128은 50만원 예산 내 실현 가능 (여유: {budget_krw - v0128_krw:,}원)')
else:
    print(f'WARNING V0128은 50만원 예산 초과 (초과: {v0128_krw - budget_krw:,}원)')
    print(f'   캐시 적용 시 비용 -90% 가능: {int(v0128_krw * 0.1):,}원')
