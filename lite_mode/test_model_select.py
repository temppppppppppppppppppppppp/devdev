"""모델 선택 수정 확인 테스트"""

import sys

sys.path.insert(0, ".")
import time

from bridge.gemini_driver import GeminiDriver

print("=== 모델 선택 테스트 ===\n")

driver = GeminiDriver(debug_port=9222, model="pro", hide=False, log_func=lambda msg: print(f"  {msg}"))

# 1. 현재 모델 확인
current = driver.get_current_model()
print(f"1. 현재 모델: {current}")

# 2. 빠른 모드로 전환
print("\n2. 빠른 모드 선택 시도...")
driver.select_model("fast")
time.sleep(1)
current = driver.get_current_model()
print(f"   결과: {current}")

# 3. Pro로 다시 전환
print("\n3. Pro 선택 시도...")
driver.select_model("pro")
time.sleep(1)
current = driver.get_current_model()
print(f"   결과: {current}")

# 4. 사고 모드 전환
print("\n4. 사고 모드 선택 시도...")
driver.select_model("think")
time.sleep(1)
current = driver.get_current_model()
print(f"   결과: {current}")

# 5. Pro 복원
print("\n5. Pro 복원...")
driver.select_model("pro")
time.sleep(1)
current = driver.get_current_model()
print(f"   결과: {current}")

print("\n=== 테스트 완료 ===")
