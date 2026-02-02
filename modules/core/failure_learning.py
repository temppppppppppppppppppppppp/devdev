"""
[V51.4] Failure Learning System (실패 학습 시스템)
REJECT 사유 자동 수집 → 패턴 분석 → 동적 제약 생성

핵심: LLM 비용 0원으로 재생성 성공률 향상

원리:
1. Director REJECT 사유 수집 (자동)
2. 패턴 분류 및 빈도 분석
3. 고빈도 실패 패턴에 대한 제약 자동 생성
4. 다음 생성 시 해당 제약 주입

사용:
    learner = FailureLearner()
    learner.record_failure(stage, episode, reason, details)
    constraints = learner.get_learned_constraints(stage)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum
from collections import defaultdict
from datetime import datetime
import json
import re


class FailureCategory(Enum):
    """실패 분류"""
    # 연속성 관련
    ITEM_DUPLICATE = "item_duplicate"           # 아이템 중복 획득
    ITEM_MISSING = "item_missing"               # 획득 안 한 아이템 사용
    STATE_DISCONTINUITY = "state_discontinuity" # 상태 불연속 (부상, 경지)
    TIMELINE_ERROR = "timeline_error"           # 시간선 오류

    # 구조 관련
    SCOPE_OVERFLOW = "scope_overflow"           # 범위 초과
    BLUEPRINT_MISMATCH = "blueprint_mismatch"   # 블루프린트 미반영
    MISSING_SCENE = "missing_scene"             # 필수 씬 누락

    # 캐릭터 관련
    RELATIONSHIP_JUMP = "relationship_jump"     # 관계 급변
    CHARACTER_OOC = "character_ooc"             # 캐릭터 일탈 (Out of Character)
    VILLAIN_STUPIDITY = "villain_stupidity"     # 악역 지능 저하

    # 서사 관련
    FREE_POWERUP = "free_powerup"               # 대가 없는 파워업
    DEUS_EX_MACHINA = "deus_ex_machina"         # 기계신 등장
    PACING_ISSUE = "pacing_issue"               # 호흡 문제

    # 기타
    JSON_ERROR = "json_error"                   # JSON 파싱 오류
    LENGTH_ERROR = "length_error"               # 길이 초과/미달
    UNKNOWN = "unknown"                         # 분류 불가


@dataclass
class FailureRecord:
    """실패 기록"""
    category: FailureCategory
    stage: int  # 2, 3, or 4
    episode: int
    arc: int
    reason: str  # Director의 REJECT 사유
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class LearnedConstraint:
    """학습된 제약"""
    rule: str
    category: FailureCategory
    frequency: int  # 발생 빈도
    examples: List[str] = field(default_factory=list)  # 실패 예시
    priority: int = 5  # 1-10


class FailureLearner:
    """실패 학습 시스템"""

    # REJECT 사유 → 카테고리 매핑 패턴
    CATEGORY_PATTERNS = {
        FailureCategory.ITEM_DUPLICATE: [
            r"중복\s*획득", r"이미\s*획득", r"재획득", r"duplicate.*item",
            r"already.*acquired", r"다시.*얻"
        ],
        FailureCategory.ITEM_MISSING: [
            r"미획득.*사용", r"획득.*안.*사용", r"소지하지.*않",
            r"item.*not.*acquired", r"없는.*아이템"
        ],
        FailureCategory.STATE_DISCONTINUITY: [
            r"부상.*연속", r"상태.*불연속", r"갑자기.*완치",
            r"경지.*급변", r"state.*discontin"
        ],
        FailureCategory.TIMELINE_ERROR: [
            r"타임라인", r"시간.*순서", r"시간선", r"timeline",
            r"수여.*전.*소지"
        ],
        FailureCategory.SCOPE_OVERFLOW: [
            r"범위.*초과", r"scope.*overflow", r"분량.*초과",
            r"blueprint.*범위"
        ],
        FailureCategory.BLUEPRINT_MISMATCH: [
            r"blueprint.*미반영", r"설계.*불일치", r"씬.*누락",
            r"핵심.*씬.*없"
        ],
        FailureCategory.MISSING_SCENE: [
            r"필수.*씬", r"장면.*누락", r"missing.*scene",
            r"cliffhanger.*없"
        ],
        FailureCategory.RELATIONSHIP_JUMP: [
            r"관계.*급변", r"relationship.*jump", r"무시.*충성",
            r"적대.*우호.*급변"
        ],
        FailureCategory.CHARACTER_OOC: [
            r"캐릭터.*일탈", r"out.*character", r"성격.*불일치",
            r"OOC"
        ],
        FailureCategory.VILLAIN_STUPIDITY: [
            r"악역.*지능", r"villain.*stupid", r"과소평가",
            r"악당.*멍청"
        ],
        FailureCategory.FREE_POWERUP: [
            r"공짜.*파워", r"대가.*없", r"free.*power",
            r"성장.*정당화"
        ],
        FailureCategory.DEUS_EX_MACHINA: [
            r"기계신", r"deus.*ex", r"뜬금없", r"복선.*없.*등장"
        ],
        FailureCategory.PACING_ISSUE: [
            r"호흡", r"pacing", r"템포", r"전개.*속도"
        ],
        FailureCategory.JSON_ERROR: [
            r"json", r"파싱", r"parsing", r"구조.*오류"
        ],
        FailureCategory.LENGTH_ERROR: [
            r"길이", r"분량", r"length", r"자수"
        ],
    }

    # 카테고리별 기본 제약 규칙 템플릿
    CONSTRAINT_TEMPLATES = {
        FailureCategory.ITEM_DUPLICATE: (
            "이미 획득한 아이템({items})을 다시 획득하는 장면 금지. "
            "'사용' 또는 '소지 확인'으로 대체하세요."
        ),
        FailureCategory.ITEM_MISSING: (
            "획득하지 않은 아이템은 사용 불가. "
            "사용 전 반드시 '획득' 장면이 선행되어야 합니다."
        ),
        FailureCategory.STATE_DISCONTINUITY: (
            "상태(부상/경지)는 연속적으로 변화해야 함. "
            "직전 화 상태: {prev_state}"
        ),
        FailureCategory.TIMELINE_ERROR: (
            "수여물/직위는 수여 시점 이후에만 효력 발생. "
            "타임라인을 재확인하세요."
        ),
        FailureCategory.SCOPE_OVERFLOW: (
            "이번 화 분량은 Blueprint 범위 내로 제한. "
            "씬 개수: {scene_count}개, 예상 분량: {expected_length}자"
        ),
        FailureCategory.BLUEPRINT_MISMATCH: (
            "Blueprint의 모든 핵심 씬을 반영해야 함. "
            "누락된 씬: {missing_scenes}"
        ),
        FailureCategory.RELATIONSHIP_JUMP: (
            "관계 변화는 단계적으로. 한 화에 2단계 이상 변화 금지. "
            "예: 무시→경계→중립 (O), 무시→충성 (X)"
        ),
        FailureCategory.CHARACTER_OOC: (
            "캐릭터 성격 일관성 유지. "
            "{character}의 특성: {traits}"
        ),
        FailureCategory.VILLAIN_STUPIDITY: (
            "악역의 지능 보호. 연속 3회 이상 과소평가 금지. "
            "경계/의심 묘사를 포함하세요."
        ),
        FailureCategory.FREE_POWERUP: (
            "성장에는 반드시 대가 필요. "
            "예: 고통스러운 수련, 귀인의 도움(빚), 기회비용"
        ),
        FailureCategory.DEUS_EX_MACHINA: (
            "갑작스러운 해결책 금지. "
            "최소 2화 전에 복선이 있어야 합니다."
        ),
        FailureCategory.PACING_ISSUE: (
            "호흡 조절 필요. 대화:서술 비율 {ratio} 권장. "
            "긴장/이완 교차를 유지하세요."
        ),
    }

    def __init__(self, max_records: int = 500):
        self.max_records = max_records
        self.records: List[FailureRecord] = []
        self.category_counts: Dict[FailureCategory, int] = defaultdict(int)
        self.stage_counts: Dict[int, Dict[FailureCategory, int]] = {
            2: defaultdict(int),
            3: defaultdict(int),
            4: defaultdict(int)
        }
        self.recent_failures: Dict[int, List[FailureRecord]] = {
            2: [], 3: [], 4: []
        }  # 스테이지별 최근 실패 (최대 10개)

    def classify_failure(self, reason: str) -> FailureCategory:
        """REJECT 사유를 카테고리로 분류"""
        reason_lower = reason.lower()

        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, reason_lower, re.IGNORECASE):
                    return category

        return FailureCategory.UNKNOWN

    def record_failure(
        self,
        stage: int,
        episode: int,
        reason: str,
        arc: int = 0,
        details: Dict[str, Any] = None
    ) -> FailureRecord:
        """실패 기록 추가"""
        category = self.classify_failure(reason)

        record = FailureRecord(
            category=category,
            stage=stage,
            episode=episode,
            arc=arc,
            reason=reason,
            details=details or {}
        )

        # 기록 추가
        self.records.append(record)
        self.category_counts[category] += 1
        self.stage_counts[stage][category] += 1

        # 최근 실패 목록 업데이트
        self.recent_failures[stage].append(record)
        if len(self.recent_failures[stage]) > 10:
            self.recent_failures[stage].pop(0)

        # 최대 기록 수 관리
        if len(self.records) > self.max_records:
            oldest = self.records.pop(0)
            self.category_counts[oldest.category] -= 1
            self.stage_counts[oldest.stage][oldest.category] -= 1

        return record

    def get_top_failures(
        self,
        stage: int = None,
        n: int = 5
    ) -> List[Tuple[FailureCategory, int]]:
        """가장 빈번한 실패 카테고리 반환"""
        if stage:
            counts = self.stage_counts[stage]
        else:
            counts = self.category_counts

        sorted_counts = sorted(
            counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_counts[:n]

    def get_learned_constraints(
        self,
        stage: int,
        threshold: int = 2
    ) -> List[LearnedConstraint]:
        """
        학습된 제약 조건 생성
        threshold 이상 발생한 실패 패턴에 대해 제약 생성
        """
        constraints = []

        for category, count in self.stage_counts[stage].items():
            if count >= threshold and category != FailureCategory.UNKNOWN:
                # 해당 카테고리의 최근 예시 수집
                examples = [
                    r.reason[:100]
                    for r in self.recent_failures[stage]
                    if r.category == category
                ][:3]

                # 템플릿에서 규칙 생성
                template = self.CONSTRAINT_TEMPLATES.get(category, "")
                if template:
                    rule = template.format(
                        items="(최근 획득 아이템)",
                        prev_state="(직전 상태 참조)",
                        scene_count="4-6",
                        expected_length="4000-6000",
                        missing_scenes="(Blueprint 참조)",
                        character="(캐릭터명)",
                        traits="(특성 참조)",
                        ratio="40:60"
                    )
                else:
                    rule = f"{category.value} 관련 오류 방지"

                priority = min(10, 5 + count)  # 빈도에 따라 우선순위 상승

                constraints.append(LearnedConstraint(
                    rule=rule,
                    category=category,
                    frequency=count,
                    examples=examples,
                    priority=priority
                ))

        # 우선순위 순 정렬
        constraints.sort(key=lambda x: x.priority, reverse=True)
        return constraints

    def generate_constraint_prompt(
        self,
        stage: int,
        threshold: int = 2
    ) -> str:
        """학습된 제약을 프롬프트 형식으로 변환"""
        constraints = self.get_learned_constraints(stage, threshold)

        if not constraints:
            return ""

        lines = [f"[V51.4 Failure Learning - Stage {stage} 학습된 제약]"]
        lines.append("과거 REJECT 패턴 분석 결과, 다음 사항에 주의하세요:\n")

        for i, c in enumerate(constraints[:5], 1):
            lines.append(f"{i}. [{c.category.value}] {c.rule}")
            lines.append(f"   (빈도: {c.frequency}회)")
            if c.examples:
                lines.append(f"   예시: {c.examples[0][:80]}...")
            lines.append("")

        return "\n".join(lines)

    def get_failure_stats(self) -> Dict[str, Any]:
        """실패 통계 반환"""
        return {
            "total_failures": len(self.records),
            "by_category": {
                cat.value: count
                for cat, count in self.category_counts.items()
                if count > 0
            },
            "by_stage": {
                stage: {
                    cat.value: count
                    for cat, count in counts.items()
                    if count > 0
                }
                for stage, counts in self.stage_counts.items()
            },
            "top_5": [
                {"category": cat.value, "count": count}
                for cat, count in self.get_top_failures(n=5)
            ]
        }

    def save_to_json(self, filepath: str):
        """기록을 JSON 파일로 저장"""
        data = {
            "records": [
                {
                    "category": r.category.value,
                    "stage": r.stage,
                    "episode": r.episode,
                    "arc": r.arc,
                    "reason": r.reason,
                    "details": r.details,
                    "timestamp": r.timestamp
                }
                for r in self.records
            ],
            "stats": self.get_failure_stats()
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_from_json(self, filepath: str):
        """JSON 파일에서 기록 로드"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.records = []
            self.category_counts = defaultdict(int)
            self.stage_counts = {2: defaultdict(int), 3: defaultdict(int), 4: defaultdict(int)}

            for r in data.get("records", []):
                category = FailureCategory(r.get("category", "unknown"))
                record = FailureRecord(
                    category=category,
                    stage=r["stage"],
                    episode=r["episode"],
                    arc=r.get("arc", 0),
                    reason=r["reason"],
                    details=r.get("details", {}),
                    timestamp=r.get("timestamp", "")
                )
                self.records.append(record)
                self.category_counts[category] += 1
                self.stage_counts[record.stage][category] += 1

        except FileNotFoundError:
            pass  # 파일 없으면 빈 상태 유지
        except Exception as e:
            print(f"[FailureLearner] Load error: {e}")

    def clear(self):
        """모든 기록 초기화"""
        self.records = []
        self.category_counts = defaultdict(int)
        self.stage_counts = {2: defaultdict(int), 3: defaultdict(int), 4: defaultdict(int)}
        self.recent_failures = {2: [], 3: [], 4: []}
