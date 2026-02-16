import json
import logging
import os
from datetime import datetime

import requests


class SlackNotifier:
    """
    [V40] Slack 알림 전송 유틸리티
    - .env파일의 SLACK_WEBHOOK_URL을 사용하여 메시지 전송
    """

    def __init__(self) -> None:
        # [V70] lazy 로딩: send_notification에서 읽음 (import 시점 load_dotenv 미호출 대응)
        self.webhook_url = None

    def send_notification(self, title: str, message: str, color: str = "#36a64f", key_metrics: dict = None) -> None:
        """
        슬랙으로 리치 메시지(Attachment) 전송
        Args:
            title: 알림 제목 (예: "✅ 제 5화 집필 완료")
            message: 본문 메시지
            color: 상태 컬러 (성공: #36a64f, 에러: #ff0000, 경고: #ffcc00)
            key_metrics: 핵심 지표 딕셔너리 (예: {"분량": "5,000자", "소요시간": "3분"})
        """
        if self.webhook_url is None:  # [V70] lazy 로딩
            self.webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
        if not self.webhook_url:
            logging.info("⚠️ [System] 슬랙 웹훅 URL이 설정되지 않아 알림을 건너뜁니다.")
            return

        payload = {
            "text": f"*{title}*",  # 모바일 푸시용 텍스트
            "attachments": [
                {
                    "color": color,
                    "title": title,
                    "text": message,
                    "footer": f"Antigravity Studio • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    "fields": [],
                }
            ],
        }

        # 핵심 지표가 있다면 필드에 추가
        if key_metrics:
            for k, v in key_metrics.items():
                payload["attachments"][0]["fields"].append({"title": k, "value": str(v), "short": True})

        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=10,  # [V70] 무한 대기 방지
            )
            if response.status_code != 200:
                logging.warning(f"⚠️ [Slack Error] 전송 실패 ({response.status_code}): {response.text}")
            else:
                logging.info("📨 [Slack] 알림이 전송되었습니다.")
        except Exception as e:
            logging.warning(f"⚠️ [Slack Error] 연결 실패: {e}")


# 전역 인스턴스 (필요시 사용)
notifier = SlackNotifier()
