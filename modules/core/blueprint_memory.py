"""
[V54.5] Blueprint Semantic Memory (Enhanced)

Blueprint를 ChromaDB에 임베딩하여 시맨틱 검색 기능 제공.
시간 무관하게 관련 Blueprint를 검색하여 연속성 향상.

V54.5 신규 기능:
- 성공 패턴 저장 및 재사용
- Director PASS 기록 학습
- 유사 상황에 성공 패턴 추천
"""

import os
import logging
import json
from typing import List, Dict, Optional
from pathlib import Path


class BlueprintMemory:
    """
    [V49.3] Blueprint 시맨틱 검색 엔진

    Usage:
        memory = BlueprintMemory(project_context)
        memory.index_blueprint(ep_num, blueprint_data)
        related = memory.search_related(query="주인공이 대도를 획득", n_results=5)
    """

    def __init__(self, project_context) -> None:
        self.context = project_context
        self.collection = None
        self.initialized = False

        try:
            import chromadb
            from modules.core.memory_engine import GoogleEmbeddingFunction

            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                logging.info("⚠️ [BlueprintMemory] API 키 없음, 비활성화")
                return

            # ChromaDB 클라이언트 초기화
            chroma_path = self.context.paths.memory / "blueprint_vectors"
            chroma_path.mkdir(parents=True, exist_ok=True)

            self.client = chromadb.PersistentClient(path=str(chroma_path))
            self.embedding_fn = GoogleEmbeddingFunction(api_key)

            # Blueprint 전용 컬렉션
            project_name = self.context.paths.root.name
            # [V70] ChromaDB는 ASCII 영숫자+_-만 허용, 한글 등은 제거
            import re as _re
            safe_name = _re.sub(r'[^a-zA-Z0-9_-]', '', project_name) or 'project'
            collection_name = f"{safe_name}_blueprints"

            self.collection = self.client.get_or_create_collection(
                name=collection_name[:63],  # ChromaDB 이름 길이 제한
                embedding_function=self.embedding_fn,
                metadata={"description": "Blueprint semantic search"}
            )

            self.initialized = True
            logging.info(f"📚 [BlueprintMemory] 초기화 완료 (컬렉션: {collection_name[:30]}...)")

        except ImportError as e:
            logging.info(f"⚠️ [BlueprintMemory] 의존성 없음: {e}")
        except Exception as e:
            logging.warning(f"⚠️ [BlueprintMemory] 초기화 실패: {e}")

    def index_blueprint(self, ep_num: int, blueprint_data: dict) -> bool:
        """
        Blueprint를 벡터 DB에 인덱싱

        Args:
            ep_num: 에피소드 번호
            blueprint_data: Blueprint 데이터 (dict)

        Returns:
            bool: 성공 여부
        """
        if not self.initialized or not self.collection:
            return False

        try:
            # Blueprint에서 핵심 텍스트 추출
            doc_id = f"bp_{ep_num}"

            # 이미 존재하면 스킵
            existing = self.collection.get(ids=[doc_id])
            if existing and existing['ids']:
                return True

            # 텍스트 구성
            text_parts = []

            # integrated_scenario (핵심 시나리오)
            if 'integrated_scenario' in blueprint_data:
                text_parts.append(f"시나리오: {blueprint_data['integrated_scenario']}")

            # scene_breakdown (씬별 내용)
            if 'scene_breakdown' in blueprint_data:
                scenes = blueprint_data['scene_breakdown']
                if isinstance(scenes, dict):
                    for scene_key, scene_content in scenes.items():
                        if isinstance(scene_content, str):
                            text_parts.append(f"{scene_key}: {scene_content[:200]}")
                        elif isinstance(scene_content, dict):
                            text_parts.append(f"{scene_key}: {scene_content.get('description', '')[:200]}")

            # 메타데이터 추출
            metadata = {
                "ep_num": ep_num,
                "arc_no": blueprint_data.get('arc_no', 0),
                "title": blueprint_data.get('title', f'제{ep_num}화')[:100]
            }

            # 아이템 관련 키워드 추출
            full_text = json.dumps(blueprint_data, ensure_ascii=False)
            item_keywords = self._extract_item_keywords(full_text)
            if item_keywords:
                metadata["items"] = ",".join(item_keywords[:10])

            # 인덱싱
            document = "\n".join(text_parts)[:5000]  # 최대 5000자

            self.collection.add(
                ids=[doc_id],
                documents=[document],
                metadatas=[metadata]
            )

            return True

        except Exception as e:
            logging.warning(f"⚠️ [BlueprintMemory] 인덱싱 실패 (EP{ep_num}): {e}")
            return False

    def search_related(self, query: str, n_results: int = 5,
                       exclude_eps: List[int] = None) -> List[Dict]:
        """
        쿼리와 관련된 Blueprint 검색

        Args:
            query: 검색 쿼리 (예: "주인공이 대도를 획득")
            n_results: 반환할 결과 수
            exclude_eps: 제외할 에피소드 번호 목록

        Returns:
            관련 Blueprint 목록 [{ep_num, title, relevance_score, snippet}, ...]
        """
        if not self.initialized or not self.collection:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results + len(exclude_eps or [])  # 제외 대상 고려
            )

            if not results or not results['ids'] or not results['ids'][0]:
                return []

            related = []
            for i, doc_id in enumerate(results['ids'][0]):
                ep_num = int(doc_id.replace('bp_', ''))

                # 제외 목록 확인
                if exclude_eps and ep_num in exclude_eps:
                    continue

                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                distance = results['distances'][0][i] if results['distances'] else 1.0
                document = results['documents'][0][i] if results['documents'] else ""

                related.append({
                    "ep_num": ep_num,
                    "title": metadata.get('title', f'제{ep_num}화'),
                    "arc_no": metadata.get('arc_no', 0),
                    "items": metadata.get('items', '').split(',') if metadata.get('items') else [],
                    "relevance_score": round(1 - distance, 3),  # 거리 → 유사도 변환
                    "snippet": document[:200] if document else ""
                })

                if len(related) >= n_results:
                    break

            return related

        except Exception as e:
            logging.warning(f"⚠️ [BlueprintMemory] 검색 실패: {e}")
            return []

    def search_by_item(self, item_name: str, n_results: int = 10) -> List[Dict]:
        """
        특정 아이템이 등장하는 Blueprint 검색

        Args:
            item_name: 아이템 이름
            n_results: 반환할 결과 수

        Returns:
            아이템 관련 Blueprint 목록
        """
        return self.search_related(f"아이템 획득: {item_name}", n_results)

    def get_plot_threads(self, current_ep: int, n_results: int = 5) -> List[Dict]:
        """
        현재 에피소드와 연결된 플롯 스레드 검색

        현재 Blueprint의 핵심 키워드로 관련 과거 Blueprint를 찾음

        Args:
            current_ep: 현재 에피소드 번호
            n_results: 반환할 결과 수

        Returns:
            관련 플롯 스레드 목록
        """
        if not self.initialized:
            return []

        try:
            # 현재 Blueprint 가져오기
            current_bp = self.context.db.get_blueprint(current_ep)
            if not current_bp:
                return []

            # 핵심 텍스트 추출
            if isinstance(current_bp, dict):
                query_text = current_bp.get('integrated_scenario', '')[:500]
            else:
                query_text = str(current_bp)[:500]

            if not query_text:
                return []

            # 과거 Blueprint 검색 (현재 에피소드 제외)
            return self.search_related(
                query_text,
                n_results=n_results,
                exclude_eps=[current_ep]
            )

        except Exception as e:
            logging.warning(f"⚠️ [BlueprintMemory] 플롯 스레드 검색 실패: {e}")
            return []

    def generate_context_prompt(self, related_bps: List[Dict]) -> str:
        """
        검색된 관련 Blueprint를 프롬프트로 변환

        Args:
            related_bps: 관련 Blueprint 목록

        Returns:
            프롬프트 문자열
        """
        if not related_bps:
            return ""

        lines = ["📚 [Semantic RAG] 관련 과거 Blueprint (시간 무관 검색):\n"]

        for bp in related_bps:
            lines.append(f"• 제{bp['ep_num']}화 ({bp['title']})")
            lines.append(f"  유사도: {bp['relevance_score']:.1%}")
            if bp.get('items'):
                lines.append(f"  관련 아이템: {', '.join(bp['items'][:3])}")
            if bp.get('snippet'):
                lines.append(f"  내용: {bp['snippet'][:100]}...")
            lines.append("")

        lines.append("⚠️ 위 과거 사건들과의 연속성을 고려하여 설계하라.\n")

        return "\n".join(lines)

    def _extract_item_keywords(self, text: str) -> List[str]:
        """텍스트에서 아이템 관련 키워드 추출"""
        import re

        # 일반적인 아이템 패턴
        patterns = [
            r'획득[한하]?\s+([가-힣]+)',
            r'([가-힣]+)[을를]\s+얻',
            r'([가-힣]{2,}검|도|창|궁|패|서|서책|비급|단약|영약)',
        ]

        keywords = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) >= 2:
                    keywords.add(match)

        return list(keywords)[:10]

    def index_all_blueprints(self) -> int:
        """
        DB의 모든 Blueprint를 인덱싱

        Returns:
            인덱싱된 Blueprint 수
        """
        if not self.initialized:
            return 0

        try:
            # DB에서 모든 Blueprint 가져오기
            cursor = self.context.db.conn.cursor()
            cursor.execute("SELECT ep_num, data FROM blueprints ORDER BY ep_num")
            rows = cursor.fetchall()

            indexed = 0
            for ep_num, data in rows:
                try:
                    bp_data = json.loads(data) if isinstance(data, str) else data
                    if self.index_blueprint(ep_num, bp_data):
                        indexed += 1
                except (json.JSONDecodeError, ValueError, TypeError, KeyError):  # [V64.P4] individual blueprint index failure
                    continue

            logging.info(f"📚 [BlueprintMemory] {indexed}개 Blueprint 인덱싱 완료")
            return indexed

        except Exception as e:
            logging.warning(f"⚠️ [BlueprintMemory] 전체 인덱싱 실패: {e}")
            return 0


# ============================================================================
# [V54.5] Success Pattern Memory
# ============================================================================

class SuccessPatternMemory:
    """
    [V54.5] 성공 패턴 저장 및 재사용

    Director PASS를 받은 Blueprint/Manuscript의 패턴을 학습하여
    유사한 상황에서 성공 패턴을 추천합니다.
    """

    def __init__(self, project_context=None, max_patterns: int = 100):
        """
        Args:
            project_context: ProjectContext (없으면 메모리 모드)
            max_patterns: 저장할 최대 패턴 수
        """
        self.context = project_context
        self.max_patterns = max_patterns

        # 성공 패턴 저장소
        self._patterns: Dict[str, List[Dict]] = {
            "blueprint": [],
            "manuscript": [],
            "arc": []
        }

        # 패턴 특성 추출기
        self._feature_extractors = {
            "blueprint": self._extract_blueprint_features,
            "manuscript": self._extract_manuscript_features,
            "arc": self._extract_arc_features
        }

    def record_success(
        self,
        content_type: str,
        content: Dict,
        context: Dict,
        score: int = 0
    ):
        """
        성공 패턴 기록

        Args:
            content_type: "blueprint", "manuscript", "arc"
            content: 성공한 콘텐츠
            context: 생성 컨텍스트 (ep_num, arc_num 등)
            score: Director 점수 (있으면)
        """
        if content_type not in self._patterns:
            return

        # 특성 추출
        extractor = self._feature_extractors.get(content_type)
        if not extractor:
            return

        features = extractor(content)

        pattern = {
            "features": features,
            "context": {
                "ep_num": context.get("ep_num"),
                "arc_num": context.get("arc_num"),
                "scene_type": context.get("scene_type")
            },
            "score": score,
            "sample": self._extract_sample(content, content_type)
        }

        self._patterns[content_type].append(pattern)

        # 용량 제한
        if len(self._patterns[content_type]) > self.max_patterns:
            # 점수 낮은 것부터 제거
            self._patterns[content_type].sort(key=lambda x: x.get("score", 0), reverse=True)
            self._patterns[content_type] = self._patterns[content_type][:self.max_patterns]

    def find_similar_patterns(
        self,
        content_type: str,
        target_context: Dict,
        n_results: int = 3
    ) -> List[Dict]:
        """
        유사한 성공 패턴 검색

        Args:
            content_type: 콘텐츠 타입
            target_context: 현재 상황 컨텍스트
            n_results: 반환할 결과 수

        Returns:
            유사 패턴 목록
        """
        patterns = self._patterns.get(content_type, [])
        if not patterns:
            return []

        # [V60.4] REJECT 이유별 필터링
        rejection_context = target_context.get("rejection_context", "")
        if rejection_context and target_context.get("retry_mode"):
            # REJECT 유형에 맞는 패턴 우선 필터링
            filtered_patterns = self._filter_patterns_by_rejection(
                patterns, rejection_context, content_type
            )
            if filtered_patterns:
                patterns = filtered_patterns

        # 유사도 계산
        scored = []
        for pattern in patterns:
            similarity = self._calculate_similarity(pattern["context"], target_context)

            # [V60.4] rejection_context가 있고 패턴이 해당 문제를 해결한 경우 가중치
            if rejection_context and self._match_rejection_pattern(
                pattern.get("features", {}), rejection_context
            ):
                similarity += 0.2

            scored.append((similarity, pattern))

        # 정렬 및 반환
        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:n_results]]

    def _filter_patterns_by_rejection(
        self,
        patterns: List[Dict],
        rejection_context: str,
        content_type: str
    ) -> List[Dict]:
        """
        [V60.4] REJECT 유형에 맞는 패턴 필터링

        Args:
            patterns: 전체 패턴 목록
            rejection_context: REJECT 사유
            content_type: 콘텐츠 타입

        Returns:
            필터링된 패턴 목록
        """
        # REJECT 키워드별 관련 특성 매핑
        rejection_feature_requirements = {
            "분량": {"manuscript": ["dialogue_ratio", "sensory_descriptions"]},
            "밀도": {"manuscript": ["sensory_descriptions", "action_density"]},
            "폭주": {"blueprint": ["scene_count", "emotional_pattern"]},
            "정체": {"manuscript": ["action_density"], "blueprint": ["scene_count"]},
            "대화": {"manuscript": ["dialogue_ratio"]},
            "묘사": {"manuscript": ["sensory_descriptions"]},
            "씬": {"blueprint": ["scene_count"]},
            "균등": {"manuscript": ["dialogue_ratio", "sensory_descriptions"]},
        }

        # 감지된 REJECT 유형
        detected_types = []
        for kw in rejection_feature_requirements.keys():
            if kw in rejection_context:
                detected_types.append(kw)

        if not detected_types:
            return patterns  # 특별히 필터링할 필요 없음

        # 관련 특성이 있는 패턴 우선
        relevant_patterns = []
        for pattern in patterns:
            features = pattern.get("features", {})
            for reject_type in detected_types:
                requirements = rejection_feature_requirements[reject_type].get(content_type, [])
                for req_feature in requirements:
                    if req_feature in features:
                        relevant_patterns.append(pattern)
                        break
                if pattern in relevant_patterns:
                    break

        return relevant_patterns if relevant_patterns else patterns

    def get_guidance_from_patterns(
        self,
        content_type: str,
        target_context: Dict
    ) -> str:
        """
        유사 패턴에서 가이드라인 생성

        Args:
            content_type: 콘텐츠 타입
            target_context: 현재 상황

        Returns:
            가이드라인 문자열
        """
        # [V60.4] retry_mode일 때 더 많은 패턴 검색
        n_results = 3 if target_context.get("retry_mode") else 2
        similar = self.find_similar_patterns(content_type, target_context, n_results=n_results)

        if not similar:
            return ""

        # [V60.4] retry_mode일 때 다른 헤더 사용
        if target_context.get("retry_mode"):
            lines = ["[V60.4 REJECT 개선을 위한 성공 패턴]"]
            rejection_context = target_context.get("rejection_context", "")
            if rejection_context:
                # REJECT 사유에서 핵심 키워드 추출
                reject_keywords = []
                for kw in ["분량", "밀도", "폭주", "정체", "대화", "묘사", "연결", "모순"]:
                    if kw in rejection_context:
                        reject_keywords.append(kw)
                if reject_keywords:
                    lines.append(f"감지된 문제: {', '.join(reject_keywords)}")
            lines.append("아래 성공 패턴을 참고하여 개선하세요:\n")
        else:
            lines = ["[V54.5 Success Pattern Guide]"]
            lines.append("이전에 성공한 유사 패턴을 참고하세요:\n")

        for i, pattern in enumerate(similar, 1):
            features = pattern.get("features", {})
            sample = pattern.get("sample", "")
            score = pattern.get("score", 0)

            lines.append(f"성공 패턴 #{i}" + (f" (점수: {score})" if score else "") + ":")

            if content_type == "blueprint":
                if scene_count := features.get("scene_count"):
                    lines.append(f"  - 씬 구성: {scene_count}개")
                if emotional := features.get("emotional_pattern"):
                    lines.append(f"  - 감정선: {emotional}")
                if cliffhanger := features.get("cliffhanger_type"):
                    lines.append(f"  - 클리프행어: {cliffhanger}")

            elif content_type == "manuscript":
                if dialogue_ratio := features.get("dialogue_ratio"):
                    lines.append(f"  - 대화 비율: {dialogue_ratio:.1%}")
                if sensory_count := features.get("sensory_descriptions"):
                    lines.append(f"  - 감각 묘사: {sensory_count}개")
                if action_density := features.get("action_density"):
                    lines.append(f"  - 액션 밀도: {action_density}")

            if sample:
                lines.append(f"  - 샘플: {sample[:150]}...")

            lines.append("")

        # [V60.4] retry_mode일 때 추가 조언
        if target_context.get("retry_mode"):
            lines.append("⚠️ 위 성공 패턴들의 구조와 비율을 참고하여 REJECT 사유를 해결하라.")

        return "\n".join(lines)

    def _extract_blueprint_features(self, content: Dict) -> Dict:
        """Blueprint 특성 추출"""
        features = {}

        # 씬 개수
        if scenes := content.get("scene_breakdown"):
            features["scene_count"] = len(scenes) if isinstance(scenes, dict) else 0

        # 감정 패턴
        if scenario := content.get("integrated_scenario", ""):
            if "절정" in scenario or "클라이막스" in scenario:
                features["emotional_pattern"] = "상승"
            elif "이완" in scenario or "휴식" in scenario:
                features["emotional_pattern"] = "이완"
            else:
                features["emotional_pattern"] = "중립"

        # 클리프행어 유형
        if hook := content.get("ending_hook", ""):
            if any(k in hook for k in ["등장", "나타나", "출현"]):
                features["cliffhanger_type"] = "새 캐릭터"
            elif any(k in hook for k in ["위기", "위험", "공격"]):
                features["cliffhanger_type"] = "위기"
            elif any(k in hook for k in ["비밀", "진실", "발견"]):
                features["cliffhanger_type"] = "미스터리"
            else:
                features["cliffhanger_type"] = "일반"

        return features

    def _extract_manuscript_features(self, content: Dict) -> Dict:
        """Manuscript 특성 추출"""
        features = {}

        text = content.get("text", "") if isinstance(content, dict) else str(content)

        # 대화 비율
        import re
        dialogue_count = len(re.findall(r'["\「][^"\」]+["\」]', text))
        total_sentences = len(re.split(r'[.!?。]', text))
        features["dialogue_ratio"] = dialogue_count / max(total_sentences, 1)

        # 감각 묘사 수
        sensory_words = ['보이', '들리', '느껴', '냄새', '맛', '차가', '뜨거', '부드러']
        features["sensory_descriptions"] = sum(1 for w in sensory_words if w in text)

        # 액션 밀도
        action_words = ['달려', '치', '막', '피하', '공격', '방어', '검을', '도를']
        features["action_density"] = sum(1 for w in action_words if w in text)

        return features

    def _extract_arc_features(self, content: Dict) -> Dict:
        """Arc 특성 추출"""
        features = {}

        features["ep_count"] = content.get("ep_count", 0)

        if tactical := content.get("tactical_doc", ""):
            features["tactical_length"] = len(tactical)

        if beat_seq := content.get("beat_sequence", []):
            features["beat_count"] = len(beat_seq)

        return features

    def _extract_sample(self, content: Dict, content_type: str) -> str:
        """콘텐츠에서 샘플 추출"""
        if content_type == "blueprint":
            return content.get("integrated_scenario", "")[:300]
        elif content_type == "manuscript":
            text = content.get("text", "") if isinstance(content, dict) else str(content)
            return text[:300]
        elif content_type == "arc":
            beats = content.get("beat_sequence", [])
            return " | ".join(beats[:3]) if beats else ""
        return ""

    def _calculate_similarity(self, ctx1: Dict, ctx2: Dict) -> float:
        """두 컨텍스트의 유사도 계산"""
        score = 0.0

        # 같은 Arc면 높은 점수
        if ctx1.get("arc_num") == ctx2.get("arc_num"):
            score += 0.5

        # 에피소드 번호 근접도
        ep1 = ctx1.get("ep_num", 0)
        ep2 = ctx2.get("ep_num", 0)
        if ep1 and ep2:
            distance = abs(ep1 - ep2)
            score += max(0, 0.3 - distance * 0.03)

        # 씬 타입 일치
        if ctx1.get("scene_type") == ctx2.get("scene_type"):
            score += 0.2

        # [V60.4] rejection_context가 있으면 REJECT 유형 기반 검색
        rejection_context = ctx2.get("rejection_context", "")
        if rejection_context:
            # 패턴의 score가 높을수록 가중치 부여
            pattern_score = ctx1.get("score", 0)
            if pattern_score and pattern_score >= 80:
                score += 0.3  # 고득점 패턴 우선

        return min(1.0, score)

    def _match_rejection_pattern(self, pattern_features: Dict, rejection_context: str) -> bool:
        """
        [V60.4] REJECT 사유와 패턴의 관련성 확인
        """
        # REJECT 사유별 관련 패턴 특성 매핑
        rejection_feature_map = {
            "분량": ["scene_count", "dialogue_ratio"],
            "밀도": ["sensory_descriptions", "action_density"],
            "폭주": ["emotional_pattern"],
            "정체": ["action_density"],
            "대화": ["dialogue_ratio"],
            "묘사": ["sensory_descriptions"],
        }

        for reject_keyword, relevant_features in rejection_feature_map.items():
            if reject_keyword in rejection_context:
                for feature in relevant_features:
                    if feature in pattern_features:
                        return True
        return False

    def extract_style_characteristics(self, n_samples: int = 5) -> Dict:
        """
        [V60.6] 성공 원고에서 스타일 특징 추출

        최근 PASS된 원고들에서 공통된 스타일 특징을 추출.

        Args:
            n_samples: 분석할 샘플 수

        Returns:
            {
                'avg_sentence_length': float,
                'dialogue_style': str,
                'description_density': str,
                'pacing_pattern': str,
                'common_techniques': list,
                'sample_sentences': list
            }
        """
        import re

        manuscripts = self._patterns.get("manuscript", [])
        if not manuscripts:
            return {}

        # 점수순 정렬 후 상위 N개
        sorted_ms = sorted(manuscripts, key=lambda x: x.get("score", 0), reverse=True)[:n_samples]

        if not sorted_ms:
            return {}

        # 통계 수집
        sentence_lengths = []
        dialogue_ratios = []
        action_densities = []
        sensory_counts = []
        sample_sentences = []

        for pattern in sorted_ms:
            features = pattern.get("features", {})
            sample = pattern.get("sample", "")

            # 특성 수집
            if dr := features.get("dialogue_ratio"):
                dialogue_ratios.append(dr)
            if ad := features.get("action_density"):
                action_densities.append(ad)
            if sc := features.get("sensory_descriptions"):
                sensory_counts.append(sc)

            # 문장 길이 분석
            if sample:
                sentences = re.split(r'[.!?]', sample)
                for s in sentences:
                    s = s.strip()
                    if len(s) > 10:
                        sentence_lengths.append(len(s))
                        if len(sample_sentences) < 5:
                            sample_sentences.append(s[:100])

        # 평균 계산
        result = {}

        if sentence_lengths:
            avg_len = sum(sentence_lengths) / len(sentence_lengths)
            result['avg_sentence_length'] = avg_len
            if avg_len < 30:
                result['sentence_style'] = "짧고 간결"
            elif avg_len < 50:
                result['sentence_style'] = "중간 길이"
            else:
                result['sentence_style'] = "길고 상세"

        if dialogue_ratios:
            avg_dr = sum(dialogue_ratios) / len(dialogue_ratios)
            result['avg_dialogue_ratio'] = avg_dr
            if avg_dr < 0.2:
                result['dialogue_style'] = "서술 중심"
            elif avg_dr < 0.35:
                result['dialogue_style'] = "균형잡힌 대화"
            else:
                result['dialogue_style'] = "대화 중심"

        if action_densities:
            avg_ad = sum(action_densities) / len(action_densities)
            result['avg_action_density'] = avg_ad
            if avg_ad < 3:
                result['pacing'] = "차분한 전개"
            elif avg_ad < 7:
                result['pacing'] = "균형잡힌 페이스"
            else:
                result['pacing'] = "빠른 액션"

        if sensory_counts:
            avg_sc = sum(sensory_counts) / len(sensory_counts)
            result['avg_sensory_count'] = avg_sc
            if avg_sc < 3:
                result['description_style'] = "간결한 묘사"
            elif avg_sc < 6:
                result['description_style'] = "적절한 묘사"
            else:
                result['description_style'] = "풍부한 감각 묘사"

        result['sample_sentences'] = sample_sentences
        result['sample_count'] = len(sorted_ms)

        return result

    def generate_style_injection(self, n_samples: int = 5) -> str:
        """
        [V60.6] Writer 프롬프트에 주입할 스타일 가이드 생성

        성공 원고에서 추출한 스타일 특징을 프롬프트 형태로 변환.

        Args:
            n_samples: 분석할 샘플 수

        Returns:
            스타일 주입 프롬프트 문자열
        """
        characteristics = self.extract_style_characteristics(n_samples)

        if not characteristics or characteristics.get('sample_count', 0) < 2:
            return ""

        lines = [
            "[V60.6 성공 원고 스타일 가이드]",
            f"최근 {characteristics.get('sample_count', 0)}개 PASS 원고 분석 결과:",
            ""
        ]

        # 스타일 특성
        if sentence_style := characteristics.get('sentence_style'):
            lines.append(f"📝 문장 스타일: {sentence_style}")

        if dialogue_style := characteristics.get('dialogue_style'):
            lines.append(f"💬 대화 스타일: {dialogue_style}")
            if avg_dr := characteristics.get('avg_dialogue_ratio'):
                lines.append(f"   → 대화 비율 목표: {avg_dr:.0%}")

        if pacing := characteristics.get('pacing'):
            lines.append(f"⚡ 페이싱: {pacing}")

        if desc_style := characteristics.get('description_style'):
            lines.append(f"🎨 묘사 스타일: {desc_style}")

        # 샘플 문장
        samples = characteristics.get('sample_sentences', [])
        if samples:
            lines.append("")
            lines.append("📖 성공 문장 예시:")
            for i, sample in enumerate(samples[:3], 1):
                lines.append(f"   {i}. \"{sample}...\"")

        lines.append("")
        lines.append("→ 위 스타일 특성을 참고하여 일관된 품질을 유지하라.")

        return "\n".join(lines)

    def get_stats(self) -> Dict[str, int]:
        """통계 반환"""
        return {
            content_type: len(patterns)
            for content_type, patterns in self._patterns.items()
        }

    def get_summary(self) -> str:
        """요약 문자열"""
        stats = self.get_stats()
        return (
            f"[V54.5 Success Pattern Memory]\n"
            f"  Blueprint: {stats.get('blueprint', 0)}개\n"
            f"  Manuscript: {stats.get('manuscript', 0)}개\n"
            f"  Arc: {stats.get('arc', 0)}개"
        )
