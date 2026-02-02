"""
[V51.6] Foreshadow Payoff Tracker (복선 회수 추적기)
복선 심기/회수 추적 및 타이밍 관리

핵심: LLM 비용 0원으로 복선 관리 자동화

원리:
1. 복선 심기 등록 (수동/자동)
2. 회수 기한 모니터링
3. 과기한 복선 경고
4. 회수 완료 추적

사용:
    tracker = ForeshadowTracker()
    tracker.plant(ep_num=5, hook="비밀 편지", category="mystery", deadline=15)
    tracker.payoff(ep_num=12, hook="비밀 편지")
    warnings = tracker.get_overdue_hooks(current_ep=20)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from datetime import datetime
import json
import re


class ForeshadowCategory(Enum):
    """복선 카테고리"""
    MYSTERY = "mystery"           # 비밀/미스터리 (인물 정체, 숨겨진 과거)
    CHEKHOV = "chekhov"           # 체호프의 총 (아이템, 기술)
    RELATIONSHIP = "relationship" # 관계 복선 (재회, 배신)
    POWER = "power"               # 힘/성장 복선 (잠재력, 봉인)
    WORLDBUILDING = "worldbuilding"  # 세계관 복선 (역사, 세력)
    FORESIGHT = "foresight"       # 예언/암시
    OTHER = "other"


class ForeshadowStatus(Enum):
    """복선 상태"""
    PLANTED = "planted"           # 심어짐
    HINTED = "hinted"             # 재암시됨 (중간 리마인더)
    PAYOFF = "payoff"             # 회수됨
    OVERDUE = "overdue"           # 기한 초과
    ABANDONED = "abandoned"       # 포기됨 (의도적 미회수)


@dataclass
class Foreshadow:
    """복선 데이터"""
    hook: str                      # 복선 내용
    category: ForeshadowCategory
    planted_ep: int                # 심은 화
    deadline_ep: int               # 회수 기한 (권장)
    status: ForeshadowStatus = ForeshadowStatus.PLANTED

    # 추적
    hint_episodes: List[int] = field(default_factory=list)  # 재암시 화
    payoff_ep: Optional[int] = None    # 회수 화
    importance: int = 5                 # 중요도 (1-10)
    description: str = ""               # 설명

    # 메타
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = ""

    def is_overdue(self, current_ep: int) -> bool:
        """기한 초과 여부"""
        return (
            self.status == ForeshadowStatus.PLANTED and
            current_ep > self.deadline_ep
        )


class ForeshadowTracker:
    """복선 회수 추적기"""

    # 자동 감지 패턴 (무협 기준)
    AUTO_DETECT_PATTERNS = {
        ForeshadowCategory.MYSTERY: [
            r"(비밀|숨겨진|정체|과거|진실).*(?:밝혀|드러나|알려)",
            r"(?:누군가|어떤 자|그림자).*(?:지켜|관찰|감시)",
            r"(의문|수수께끼|이상한|석연치).*(?:느끼|들|보)",
        ],
        ForeshadowCategory.CHEKHOV: [
            r"(?:주머니|품|허리).*(?:넣|챙기|간직)",
            r"(?:비급|초식|무공).*(?:전수|습득|얻)",
            r"(?:보물|보검|신기).*(?:발견|획득|찾)",
        ],
        ForeshadowCategory.RELATIONSHIP: [
            r"(?:언젠가|반드시|꼭).*(?:만나|보|찾)",
            r"(?:원수|복수|원한).*(?:갚|잊지|기억)",
            r"(?:약속|맹세|다짐).*(?:하|지키|어기)",
        ],
        ForeshadowCategory.POWER: [
            r"(?:잠재|숨겨진|봉인).*(?:힘|능력|재능)",
            r"(?:한계|경지|벽).*(?:넘|돌파|깨)",
            r"(?:기혈|단전|내공).*(?:막|트이|열)",
        ],
        ForeshadowCategory.WORLDBUILDING: [
            r"(?:전설|신화|역사).*(?:전해|내려|들)",
            r"(?:비밀|금단|금지).*(?:구역|장소|땅)",
            r"(?:세력|문파|가문).*(?:사라|망|몰락)",
        ],
    }

    # 카테고리별 권장 회수 기한 (화 단위)
    DEFAULT_DEADLINES = {
        ForeshadowCategory.MYSTERY: 20,
        ForeshadowCategory.CHEKHOV: 15,
        ForeshadowCategory.RELATIONSHIP: 30,
        ForeshadowCategory.POWER: 25,
        ForeshadowCategory.WORLDBUILDING: 40,
        ForeshadowCategory.FORESIGHT: 50,
        ForeshadowCategory.OTHER: 20,
    }

    def __init__(self, max_hooks: int = 100):
        self.max_hooks = max_hooks
        self.hooks: Dict[str, Foreshadow] = {}
        self.episode_plants: Dict[int, List[str]] = {}  # 화별 심은 복선
        self.episode_payoffs: Dict[int, List[str]] = {}  # 화별 회수한 복선

    def _normalize_hook(self, hook: str) -> str:
        """복선 키 정규화"""
        return re.sub(r'\s+', ' ', hook.strip().lower())

    def plant(
        self,
        ep_num: int,
        hook: str,
        category: ForeshadowCategory = ForeshadowCategory.OTHER,
        deadline_ep: Optional[int] = None,
        importance: int = 5,
        description: str = ""
    ) -> Foreshadow:
        """복선 심기"""
        key = self._normalize_hook(hook)

        # 이미 존재하면 힌트로 처리
        if key in self.hooks:
            return self.hint(ep_num, hook)

        # 기한 설정
        if deadline_ep is None:
            deadline_ep = ep_num + self.DEFAULT_DEADLINES.get(category, 20)

        foreshadow = Foreshadow(
            hook=hook,
            category=category,
            planted_ep=ep_num,
            deadline_ep=deadline_ep,
            importance=importance,
            description=description
        )

        self.hooks[key] = foreshadow

        # 화별 인덱스 업데이트
        if ep_num not in self.episode_plants:
            self.episode_plants[ep_num] = []
        self.episode_plants[ep_num].append(key)

        # 최대 개수 관리
        if len(self.hooks) > self.max_hooks:
            # 가장 오래된 회수된 복선 제거
            payoff_hooks = [
                k for k, v in self.hooks.items()
                if v.status == ForeshadowStatus.PAYOFF
            ]
            if payoff_hooks:
                oldest = min(payoff_hooks, key=lambda k: self.hooks[k].payoff_ep or 0)
                del self.hooks[oldest]

        return foreshadow

    def hint(self, ep_num: int, hook: str) -> Optional[Foreshadow]:
        """복선 재암시 (리마인더)"""
        key = self._normalize_hook(hook)

        if key not in self.hooks:
            return None

        foreshadow = self.hooks[key]

        if foreshadow.status == ForeshadowStatus.PAYOFF:
            return foreshadow  # 이미 회수됨

        if ep_num not in foreshadow.hint_episodes:
            foreshadow.hint_episodes.append(ep_num)
            foreshadow.status = ForeshadowStatus.HINTED
            foreshadow.updated_at = datetime.now().isoformat()

        return foreshadow

    def payoff(self, ep_num: int, hook: str) -> Optional[Foreshadow]:
        """복선 회수"""
        key = self._normalize_hook(hook)

        if key not in self.hooks:
            return None

        foreshadow = self.hooks[key]

        if foreshadow.status == ForeshadowStatus.PAYOFF:
            return foreshadow  # 이미 회수됨

        foreshadow.status = ForeshadowStatus.PAYOFF
        foreshadow.payoff_ep = ep_num
        foreshadow.updated_at = datetime.now().isoformat()

        # 화별 인덱스 업데이트
        if ep_num not in self.episode_payoffs:
            self.episode_payoffs[ep_num] = []
        self.episode_payoffs[ep_num].append(key)

        return foreshadow

    def abandon(self, hook: str, reason: str = "") -> Optional[Foreshadow]:
        """복선 포기 (의도적 미회수)"""
        key = self._normalize_hook(hook)

        if key not in self.hooks:
            return None

        foreshadow = self.hooks[key]
        foreshadow.status = ForeshadowStatus.ABANDONED
        foreshadow.description = f"[포기] {reason}" if reason else foreshadow.description
        foreshadow.updated_at = datetime.now().isoformat()

        return foreshadow

    def get_overdue_hooks(self, current_ep: int) -> List[Foreshadow]:
        """기한 초과 복선 목록"""
        overdue = []

        for foreshadow in self.hooks.values():
            if foreshadow.is_overdue(current_ep):
                # 상태 업데이트
                foreshadow.status = ForeshadowStatus.OVERDUE
                overdue.append(foreshadow)

        # 중요도 순 정렬
        overdue.sort(key=lambda f: f.importance, reverse=True)
        return overdue

    def get_active_hooks(self) -> List[Foreshadow]:
        """활성 복선 (미회수) 목록"""
        return [
            f for f in self.hooks.values()
            if f.status in [
                ForeshadowStatus.PLANTED,
                ForeshadowStatus.HINTED,
                ForeshadowStatus.OVERDUE
            ]
        ]

    def get_hooks_near_deadline(
        self,
        current_ep: int,
        within_eps: int = 5
    ) -> List[Foreshadow]:
        """기한 임박 복선 목록"""
        near = []

        for foreshadow in self.hooks.values():
            if foreshadow.status not in [ForeshadowStatus.PLANTED, ForeshadowStatus.HINTED]:
                continue

            remaining = foreshadow.deadline_ep - current_ep
            if 0 < remaining <= within_eps:
                near.append(foreshadow)

        # 기한 순 정렬
        near.sort(key=lambda f: f.deadline_ep)
        return near

    def auto_detect_from_manuscript(
        self,
        ep_num: int,
        manuscript: str
    ) -> List[Foreshadow]:
        """원고에서 복선 자동 감지"""
        detected = []

        for category, patterns in self.AUTO_DETECT_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, manuscript, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        match = " ".join(match)

                    # 이미 등록된 복선과 유사한지 확인
                    match_key = self._normalize_hook(match)
                    is_similar = any(
                        match_key in key or key in match_key
                        for key in self.hooks.keys()
                    )

                    if not is_similar and len(match) > 3:
                        foreshadow = self.plant(
                            ep_num=ep_num,
                            hook=match,
                            category=category,
                            importance=3  # 자동 감지는 낮은 중요도
                        )
                        detected.append(foreshadow)

        return detected

    def generate_writer_prompt(self, current_ep: int) -> str:
        """Writer용 복선 관리 프롬프트"""
        lines = []

        # 기한 초과 복선 (반드시 회수 필요)
        overdue = self.get_overdue_hooks(current_ep)
        if overdue:
            lines.append("[🚨 복선 회수 필수]")
            lines.append("다음 복선은 기한이 지났습니다. 이번 화에서 회수하세요:")
            for f in overdue[:3]:
                lines.append(f"- {f.hook} (심은 화: {f.planted_ep}, 기한: {f.deadline_ep})")
            lines.append("")

        # 기한 임박 복선 (곧 회수 필요)
        near = self.get_hooks_near_deadline(current_ep, within_eps=5)
        if near:
            lines.append("[⚠️ 복선 회수 권장]")
            lines.append("다음 복선은 곧 기한이 됩니다:")
            for f in near[:3]:
                remaining = f.deadline_ep - current_ep
                lines.append(f"- {f.hook} (남은 화: {remaining}화)")
            lines.append("")

        # 활성 복선 리마인더
        active = self.get_active_hooks()
        if active and not overdue and not near:
            lines.append("[📌 활성 복선]")
            lines.append("현재 진행 중인 복선입니다 (필요시 암시):")
            for f in sorted(active, key=lambda x: x.importance, reverse=True)[:5]:
                lines.append(f"- {f.hook}")

        if not lines:
            return ""

        return "\n".join(["[V51.6 복선 관리]"] + lines)

    def generate_architect_prompt(self, current_ep: int) -> str:
        """Architect용 복선 체크 프롬프트"""
        overdue = self.get_overdue_hooks(current_ep)
        near = self.get_hooks_near_deadline(current_ep, within_eps=3)

        if not overdue and not near:
            return ""

        lines = ["[V51.6 복선 회수 체크]"]

        if overdue:
            lines.append("다음 복선 회수 씬을 Blueprint에 반드시 포함:")
            for f in overdue[:2]:
                lines.append(f"- {f.hook}")

        if near:
            lines.append("다음 복선은 곧 기한 (암시 씬 권장):")
            for f in near[:2]:
                lines.append(f"- {f.hook} ({f.deadline_ep - current_ep}화 남음)")

        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        """복선 통계"""
        by_status = {}
        by_category = {}

        for f in self.hooks.values():
            status = f.status.value
            by_status[status] = by_status.get(status, 0) + 1

            category = f.category.value
            by_category[category] = by_category.get(category, 0) + 1

        active = self.get_active_hooks()
        payoff_rate = 0
        if self.hooks:
            payoff_count = sum(1 for f in self.hooks.values() if f.status == ForeshadowStatus.PAYOFF)
            payoff_rate = payoff_count / len(self.hooks) * 100

        return {
            "total": len(self.hooks),
            "active": len(active),
            "payoff_rate": round(payoff_rate, 1),
            "by_status": by_status,
            "by_category": by_category
        }

    def save_to_json(self, filepath: str):
        """저장"""
        data = {
            "hooks": {},
            "episode_plants": {str(k): v for k, v in self.episode_plants.items()},
            "episode_payoffs": {str(k): v for k, v in self.episode_payoffs.items()}
        }

        for key, f in self.hooks.items():
            data["hooks"][key] = {
                "hook": f.hook,
                "category": f.category.value,
                "planted_ep": f.planted_ep,
                "deadline_ep": f.deadline_ep,
                "status": f.status.value,
                "hint_episodes": f.hint_episodes,
                "payoff_ep": f.payoff_ep,
                "importance": f.importance,
                "description": f.description,
                "created_at": f.created_at,
                "updated_at": f.updated_at
            }

        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def load_from_json(self, filepath: str):
        """로드"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                data = json.load(file)

            self.hooks = {}
            for key, f_data in data.get("hooks", {}).items():
                try:
                    category = ForeshadowCategory(f_data.get("category", "other"))
                except ValueError:
                    category = ForeshadowCategory.OTHER

                try:
                    status = ForeshadowStatus(f_data.get("status", "planted"))
                except ValueError:
                    status = ForeshadowStatus.PLANTED

                self.hooks[key] = Foreshadow(
                    hook=f_data["hook"],
                    category=category,
                    planted_ep=f_data["planted_ep"],
                    deadline_ep=f_data["deadline_ep"],
                    status=status,
                    hint_episodes=f_data.get("hint_episodes", []),
                    payoff_ep=f_data.get("payoff_ep"),
                    importance=f_data.get("importance", 5),
                    description=f_data.get("description", ""),
                    created_at=f_data.get("created_at", ""),
                    updated_at=f_data.get("updated_at", "")
                )

            self.episode_plants = {
                int(k): v for k, v in data.get("episode_plants", {}).items()
            }
            self.episode_payoffs = {
                int(k): v for k, v in data.get("episode_payoffs", {}).items()
            }

        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"[ForeshadowTracker] Load error: {e}")

    def clear(self):
        """초기화"""
        self.hooks = {}
        self.episode_plants = {}
        self.episode_payoffs = {}
