import os
import requests
import json
from datetime import datetime

class SlackNotifier:
    """
    [V40] Slack 알림 전송 유틸리티
    - .env파일의 SLACK_WEBHOOK_URL을 사용하여 메시지 전송
    """
    def __init__(self):
        # .env 로드는 main_a.py 등 상위에서 이미 되었다고 가정하거나, 여기서 다시 로드
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        
    def send_notification(self, title, message, color="#36a64f", key_metrics=None):
        """
        슬랙으로 리치 메시지(Attachment) 전송
        Args:
            title: 알림 제목 (예: "✅ 제 5화 집필 완료")
            message: 본문 메시지
            color: 상태 컬러 (성공: #36a64f, 에러: #ff0000, 경고: #ffcc00)
            key_metrics: 핵심 지표 딕셔너리 (예: {"분량": "5,000자", "소요시간": "3분"})
        """
        if not self.webhook_url:
            print("⚠️ [System] 슬랙 웹훅 URL이 설정되지 않아 알림을 건너뜁니다.")
            return

        payload = {
            "text": f"*{title}*", # 모바일 푸시용 텍스트
            "attachments": [
                {
                    "color": color,
                    "title": title,
                    "text": message,
                    "footer": f"Antigravity Studio • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    "fields": []
                }
            ]
        }

        # 핵심 지표가 있다면 필드에 추가
        if key_metrics:
            for k, v in key_metrics.items():
                payload["attachments"][0]["fields"].append({
                    "title": k,
                    "value": str(v),
                    "short": True
                })

        try:
            response = requests.post(
                self.webhook_url, 
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )
            if response.status_code != 200:
                print(f"⚠️ [Slack Error] 전송 실패 ({response.status_code}): {response.text}")
            else:
                print("📨 [Slack] 알림이 전송되었습니다.")
        except Exception as e:
            print(f"⚠️ [Slack Error] 연결 실패: {e}")

# 전역 인스턴스 (필요시 사용)
notifier = SlackNotifier()
