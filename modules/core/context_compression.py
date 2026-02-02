"""
[V54.2] Context Compression (컨텍스트 압축)
프롬프트에 전달되는 컨텍스트를 지능적으로 압축

핵심: 중요한 정보는 유지하면서 토큰 사용량 절감

원리:
1. 컨텍스트 중요도 분석
2. 중복/불필요 정보 제거
3. 핵심 정보 요약
4. 압축된 컨텍스트 반환

비용: $0 (Python 휴리스틱)
효과: 토큰 30-40% 절감

사용:
    compressor = ContextCompressor()
    compressed = compressor.compress(
        context=large_context,
        target_type="blueprint",  # or "manuscript"
        max_tokens=4000
    )
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import re
import json


@dataclass
class CompressionResult:
    """압축 결과"""
    compressed: Dict[str, Any]
    original_size: int      # 원본 문자 수
    compressed_size: int    # 압축 후 문자 수
    compression_ratio: float
    removed_fields: List[str]
    summarized_fields: List[str]


class ContextCompressor:
    """컨텍스트 압축 시스템"""

    # 타입별 필수 필드 (절대 제거 안 함)
    ESSENTIAL_FIELDS = {
        "blueprint": [
            "ep_num", "arc_num", "volume_num",
            "scene_breakdown", "integrated_scenario",
            "ending_hook", "prev_cliffhanger"
        ],
        "manuscript": [
            "ep_num", "blueprint", "prev_manuscript_ending",
            "character_states", "current_items"
        ],
        "arc": [
            "arc_num", "volume_num", "tactical_doc",
            "joint_docs", "prev_arc_ending"
        ]
    }

    # 요약 대상 필드 (긴 텍스트 → 핵심만)
    SUMMARIZABLE_FIELDS = [
        "tactical_doc", "prev_manuscript", "prev_blueprints",
        "encyclopedia", "lore", "history"
    ]

    # 제거 가능 필드 (우선순위 낮음)
    REMOVABLE_FIELDS = [
        "debug_info", "metadata", "timestamps", "raw_data",
        "temp_", "_cache", "_internal", "logs"
    ]

    def __init__(
        self,
        target_ratio: float = 0.6,  # 목표 압축률 (60%)
        max_field_length: int = 2000,
        enable_summarization: bool = True
    ):
        """
        Args:
            target_ratio: 목표 압축률 (0-1)
            max_field_length: 필드당 최대 문자 수
            enable_summarization: 요약 활성화 여부
        """
        self.target_ratio = target_ratio
        self.max_field_length = max_field_length
        self.enable_summarization = enable_summarization

    def compress(
        self,
        context: Dict[str, Any],
        target_type: str = "manuscript",
        max_chars: int = None
    ) -> CompressionResult:
        """
        컨텍스트 압축

        Args:
            context: 원본 컨텍스트
            target_type: 대상 타입 ("blueprint", "manuscript", "arc")
            max_chars: 최대 문자 수 (없으면 target_ratio 사용)

        Returns:
            CompressionResult
        """
        # 원본 크기 계산
        original_str = json.dumps(context, ensure_ascii=False, default=str)
        original_size = len(original_str)

        # 목표 크기 계산
        if max_chars:
            target_size = max_chars
        else:
            target_size = int(original_size * self.target_ratio)

        # 필수 필드 목록
        essential = self.ESSENTIAL_FIELDS.get(target_type, [])

        # 압축 수행
        compressed = {}
        removed_fields = []
        summarized_fields = []

        # 1단계: 필수 필드 복사
        for key, value in context.items():
            if key in essential:
                compressed[key] = self._process_field(key, value)
            elif any(rm in key.lower() for rm in self.REMOVABLE_FIELDS):
                removed_fields.append(key)
            else:
                # 임시 저장 (나중에 공간 부족하면 제거)
                compressed[key] = value

        # 2단계: 크기 체크 및 추가 압축
        current_size = len(json.dumps(compressed, ensure_ascii=False, default=str))

        if current_size > target_size:
            # 요약 가능 필드 압축
            for field in self.SUMMARIZABLE_FIELDS:
                if field in compressed and isinstance(compressed[field], str):
                    if len(compressed[field]) > self.max_field_length:
                        compressed[field] = self._summarize_text(
                            compressed[field],
                            self.max_field_length
                        )
                        summarized_fields.append(field)

            # 재계산
            current_size = len(json.dumps(compressed, ensure_ascii=False, default=str))

        if current_size > target_size:
            # 3단계: 비필수 필드 제거 (우선순위 낮은 것부터)
            non_essential = [k for k in compressed.keys() if k not in essential]
            for key in non_essential:
                if current_size <= target_size:
                    break

                value_size = len(json.dumps(compressed[key], ensure_ascii=False, default=str))
                del compressed[key]
                removed_fields.append(key)
                current_size -= value_size

        # 최종 크기
        compressed_str = json.dumps(compressed, ensure_ascii=False, default=str)
        compressed_size = len(compressed_str)

        return CompressionResult(
            compressed=compressed,
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compressed_size / original_size if original_size > 0 else 1.0,
            removed_fields=removed_fields,
            summarized_fields=summarized_fields
        )

    def _process_field(self, key: str, value: Any) -> Any:
        """필드 처리 (타입별 최적화)"""
        if isinstance(value, str):
            # 긴 텍스트 트림
            if len(value) > self.max_field_length:
                return self._smart_trim(value, self.max_field_length)
            return value

        elif isinstance(value, list):
            # 리스트는 최근 N개만
            if len(value) > 10:
                return value[-10:]
            return value

        elif isinstance(value, dict):
            # 딕셔너리 재귀 처리
            return {k: self._process_field(k, v) for k, v in value.items()}

        return value

    def _smart_trim(self, text: str, max_length: int) -> str:
        """스마트 트리밍 (시작 + 끝 보존)"""
        if len(text) <= max_length:
            return text

        # 시작 60%, 끝 40% 비율
        start_len = int(max_length * 0.6)
        end_len = max_length - start_len - 20  # 중간 표시용 20자 확보

        start = text[:start_len]
        end = text[-end_len:] if end_len > 0 else ""

        return f"{start}\n\n[...중략...]\n\n{end}"

    def _summarize_text(self, text: str, max_length: int) -> str:
        """텍스트 요약 (휴리스틱)"""
        if not self.enable_summarization:
            return self._smart_trim(text, max_length)

        # 문장 분리
        sentences = re.split(r'[.!?。]\s*', text)

        if len(sentences) <= 3:
            return self._smart_trim(text, max_length)

        # 중요 문장 추출 (첫 문장 + 마지막 문장 + 키워드 포함 문장)
        important_keywords = [
            "중요", "핵심", "결론", "결과", "반드시", "주의",
            "획득", "상승", "하락", "변화", "전환", "충돌"
        ]

        selected = []
        selected.append(sentences[0])  # 첫 문장

        # 키워드 포함 문장
        for sent in sentences[1:-1]:
            if any(kw in sent for kw in important_keywords):
                selected.append(sent)
                if len(". ".join(selected)) > max_length * 0.7:
                    break

        selected.append(sentences[-1])  # 마지막 문장

        result = ". ".join(selected)

        if len(result) > max_length:
            return self._smart_trim(result, max_length)

        return result

    def compress_for_writer(
        self,
        blueprint: Dict[str, Any],
        prev_manuscripts: List[str],
        encyclopedia: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Writer용 컨텍스트 압축"""
        compressed = {}

        # 블루프린트: 핵심만
        compressed["blueprint"] = {
            "ep_num": blueprint.get("ep_num"),
            "scenes": self._extract_scene_summaries(blueprint),
            "ending_hook": blueprint.get("ending_hook", "")
        }

        # 이전 원고: 마지막 부분만
        if prev_manuscripts:
            last_ms = prev_manuscripts[-1] if prev_manuscripts else ""
            compressed["prev_ending"] = last_ms[-2000:] if len(last_ms) > 2000 else last_ms

        # 백과사전: 등장 캐릭터/아이템만
        if encyclopedia:
            compressed["encyclopedia"] = self._filter_encyclopedia(
                encyclopedia,
                blueprint
            )

        return compressed

    def _extract_scene_summaries(self, blueprint: Dict[str, Any]) -> List[Dict[str, str]]:
        """씬 요약 추출"""
        scenes = blueprint.get("scene_breakdown", {})
        summaries = []

        for scene_id, scene_data in scenes.items():
            if isinstance(scene_data, dict):
                summaries.append({
                    "id": scene_id,
                    "type": scene_data.get("scene_type", ""),
                    "goal": scene_data.get("purpose", scene_data.get("goal", ""))[:100],
                    "chars": scene_data.get("characters", [])[:3]
                })
            elif isinstance(scene_data, str):
                summaries.append({
                    "id": scene_id,
                    "summary": scene_data[:100]
                })

        return summaries

    def _filter_encyclopedia(
        self,
        encyclopedia: Dict[str, Any],
        blueprint: Dict[str, Any]
    ) -> Dict[str, Any]:
        """블루프린트에 등장하는 항목만 필터"""
        blueprint_str = json.dumps(blueprint, ensure_ascii=False, default=str).lower()

        filtered = {}

        for category, items in encyclopedia.items():
            if isinstance(items, dict):
                relevant = {}
                for name, data in items.items():
                    if name.lower() in blueprint_str:
                        relevant[name] = data
                if relevant:
                    filtered[category] = relevant
            elif isinstance(items, list):
                relevant = [item for item in items if str(item).lower() in blueprint_str]
                if relevant:
                    filtered[category] = relevant

        return filtered

    def compress_for_architect(
        self,
        arc_data: Dict[str, Any],
        prev_blueprints: List[Dict[str, Any]],
        episode_bibles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Architect용 컨텍스트 압축"""
        compressed = {}

        # 아크 데이터: tactical_doc 요약
        if arc_data:
            compressed["arc"] = {
                "arc_num": arc_data.get("arc_num"),
                "volume_num": arc_data.get("volume_num"),
                "tactical_summary": self._summarize_text(
                    arc_data.get("tactical_doc", ""),
                    1500
                ),
                "joint_docs": arc_data.get("joint_docs", {})
            }

        # 이전 블루프린트: 마지막 2개만, 엔딩훅 위주
        if prev_blueprints:
            recent = prev_blueprints[-2:]
            compressed["prev_blueprints"] = [
                {
                    "ep_num": bp.get("ep_num"),
                    "ending_hook": bp.get("ending_hook", ""),
                    "scene_count": len(bp.get("scene_breakdown", {}))
                }
                for bp in recent
            ]

        # 에피소드 바이블: 핵심 변화만
        if episode_bibles:
            compressed["recent_changes"] = self._summarize_episode_bibles(
                episode_bibles[-3:]
            )

        return compressed

    def _summarize_episode_bibles(
        self,
        bibles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """에피소드 바이블 요약"""
        summaries = []

        for bible in bibles:
            summary = {
                "ep": bible.get("ep_num"),
            }

            # 주요 변화만
            if bible.get("new_items"):
                summary["new_items"] = bible["new_items"][:3]
            if bible.get("npc_deaths"):
                summary["deaths"] = bible["npc_deaths"]
            if bible.get("relationship_changes"):
                summary["rel_changes"] = bible["relationship_changes"][:2]

            summaries.append(summary)

        return summaries

    def get_stats(self, result: CompressionResult) -> str:
        """압축 통계 문자열"""
        return (
            f"[V54.2 Context Compression]\n"
            f"  원본: {result.original_size:,}자\n"
            f"  압축: {result.compressed_size:,}자\n"
            f"  비율: {result.compression_ratio:.1%}\n"
            f"  절감: {result.original_size - result.compressed_size:,}자 "
            f"({(1 - result.compression_ratio):.1%})\n"
            f"  제거: {len(result.removed_fields)}개 필드\n"
            f"  요약: {len(result.summarized_fields)}개 필드"
        )

