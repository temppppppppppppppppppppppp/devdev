"""
[V64.P3] StateTracker Financial Sub-module
투자물 금융 상태 추적: 환율, 자산, 레버리지, 거래 내역.

StateTracker에서 금융 관련 메서드만 분리.
모든 공유 상태는 self.tracker를 통해 접근.
"""


class StateTrackerFinancial:
    """[V64.P3] 금융 상태 추적 서브모듈 (투자물 전용)"""

    def __init__(self, tracker) -> None:
        self.tracker = tracker  # back-reference to main StateTracker

    # ═══════════════════════════════════════════════════════════════
    # [V63.1] 금융 상태 추적
    # ═══════════════════════════════════════════════════════════════

    def extract_financial_events_from_arc(self, arc: dict) -> dict:
        """
        [V63.1] state_changes.financial_events에서 금융 이벤트 추출

        Args:
            arc: Arc 데이터 (state_changes.financial_events 포함)

        Returns:
            추출된 금융 이벤트 dict (빈 dict면 해당 없음)
        """
        arc_no = arc.get("arc_no", 0)
        state_changes = arc.get("state_changes", {})
        if not isinstance(state_changes, dict):
            return {}

        fin_events = state_changes.get("financial_events", {})
        if not fin_events or not isinstance(fin_events, dict):
            return {}

        entry = {
            "exchange_rates": fin_events.get("exchange_rates", []),
            "total_assets": fin_events.get("total_assets", []),
            "leverage": fin_events.get("leverage", []),
            "key_transactions": fin_events.get("key_transactions", []),
        }

        self.tracker.financial_number_registry[arc_no] = entry
        return entry

    def _get_latest_financial_value(self, field_name: str) -> dict | None:
        """
        [V63.1] financial_number_registry에서 특정 필드의 최신 값 반환

        Args:
            field_name: "exchange_rates" | "total_assets" | "leverage"

        Returns:
            최신 엔트리 dict ({"value": ..., "arc_no": ...}) 또는 None
        """
        latest = None

        for arc_no in sorted(self.tracker.financial_number_registry.keys()):
            entries = self.tracker.financial_number_registry[arc_no].get(field_name, [])
            if entries and isinstance(entries, list):
                for entry in entries:
                    if isinstance(entry, dict) and "value" in entry:
                        latest = {**entry, "arc_no": arc_no}

        return latest

    def get_financial_state_summary(self) -> str:
        """
        [V63.1] 금융 상태 요약 -> 프롬프트 주입용

        Returns:
            금융 레지스트리 요약 문자열 (빈 문자열이면 데이터 없음)
        """
        if not self.tracker.financial_number_registry:
            return ""

        lines = ["[V63.1] [금융 상태 레지스트리 - 수치 일관성 유지 필수]"]

        # 최신 환율
        latest_rate = self._get_latest_financial_value("exchange_rates")
        if latest_rate:
            lines.append(f"  환율: {latest_rate['value']}원/달러 (Arc {latest_rate.get('arc_no', '?')})")

        # 최신 자산
        latest_assets = self._get_latest_financial_value("total_assets")
        if latest_assets:
            lines.append(f"  총 자산: {latest_assets['value']} (Arc {latest_assets.get('arc_no', '?')})")

        # 최신 레버리지
        latest_lev = self._get_latest_financial_value("leverage")
        if latest_lev:
            lines.append(f"  레버리지: {latest_lev['value']}배 (Arc {latest_lev.get('arc_no', '?')})")

        # 주요 거래 내역 (최근 5건)
        all_txns = []
        for arc_no, data in sorted(self.tracker.financial_number_registry.items()):
            for txn in data.get("key_transactions", []):
                if isinstance(txn, dict):
                    all_txns.append(
                        f"  - Arc {arc_no}: {txn.get('type', '')} {txn.get('target', '')} {txn.get('amount', '')}"
                    )
        if all_txns:
            lines.append("  거래 내역:")
            lines.extend(all_txns[-5:])

        return "\n".join(lines)

    def export_financial_registry(self) -> dict:
        """[V63.4 P0] 금융 레지스트리를 직렬화 (DB 저장용)"""
        # Dict[int, Dict] → Dict[str, Dict] (JSON 키는 문자열)
        return {str(k): v for k, v in self.tracker.financial_number_registry.items()}

    def import_financial_registry(self, data: dict):
        """[V63.4 P0] DB에서 금융 레지스트리 로드"""
        if not data or not isinstance(data, dict):
            return
        for k, v in data.items():
            try:
                self.tracker.financial_number_registry[int(k)] = v
            except (ValueError, TypeError):
                continue
