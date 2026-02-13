"""new_chat 수정 확인 테스트"""

import sys

sys.path.insert(0, ".")

from bridge.gemini_driver import GeminiDriver

print("=== new_chat 테스트 ===\n")

driver = GeminiDriver(debug_port=9222, model="pro", hide=False, log_func=lambda msg: print(f"  {msg}"))

print(f"1. 현재 URL: {driver.driver.current_url}")
current = driver.get_current_model()
print(f"   현재 모델: {current}")

print("\n2. new_chat() 호출...")
driver.new_chat()

print(f"\n3. 새 URL: {driver.driver.current_url}")
current = driver.get_current_model()
print(f"   모델: {current}")

print("\n=== 테스트 완료 ===")
