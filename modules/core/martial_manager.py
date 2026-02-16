import logging
import math

from .constants import MARTIAL_METRICS  # 👈 상수 임포트


class MartialManager:
    """[V44] DB 스키마와 성경 데이터 간의 1:1 무결성을 보장하는 최종 엔진 (타입 안전성 강화)"""

    def __init__(self, context) -> None:
        self.context = context
        self._initialization_valid = False
        self._validate_initialization()

        # DB(martial_tracker) 컬럼명과 100% 일치하는 15대 표준 캐노니컬 키
        self.canonical_map = {
            "internal_energy": ["energy", "PhysicalStatus", "internal_energy", "내공", "공력", "내공수치"],
            "mental_method": ["current_technique", "MentalMethod", "mental_method", "심법", "수련법"],
            "realm": ["level", "rank", "realm", "경지", "무력단계"],
            "wealth": ["funds", "Wealth", "wealth", "자금", "재산", "은자"],
            "causal_injuries": ["injuries", "physical_status", "Status", "causal_injuries", "상태", "부상", "내상"],
            "current_objective": ["CurrentObjective", "objective", "current_objective", "목표", "현재목표"],
            "reputation": ["reputation", "fame", "명성", "평판"],
            "public_image": ["public_image", "appearance", "이미지", "인상"],
            "equipment": ["equipment", "items", "장비", "착용아이템"],
            "token": ["token", "relic", "신물", "증표"],
            "qi_nature": ["qi_nature", "attribute", "진기성질", "기운"],
            "rank": ["rank", "position", "직위", "신분"],
            "alias": ["alias", "title", "별호", "칭호"],
            "misunderstanding": ["misunderstanding", "착각", "오해지수"],
            "obsession": ["obsession", "집착", "집착지수"],
        }

    def _validate_initialization(self) -> None:
        """[V44] 초기화 시점에 필수 의존성 검증"""
        issues = []

        # context 검증
        if self.context is None:
            issues.append("context가 None입니다")
        else:
            # master_bible 검증
            if not hasattr(self.context, "master_bible"):
                issues.append("context.master_bible 속성 없음")
            elif self.context.master_bible is None:
                issues.append("context.master_bible이 None")

            # guard 검증 (선택적)
            if not hasattr(self.context, "guard"):
                self._log_warning("context.guard 속성 없음 - 직접 변환 사용")
            elif self.context.guard is None:
                self._log_warning("context.guard가 None - 직접 변환 사용")

        if issues:
            for issue in issues:
                self._log_warning(f"초기화 경고: {issue}")
            self._initialization_valid = False
        else:
            self._initialization_valid = True

    def _log_warning(self, msg: str):
        """[V44] 안전한 경고 로깅"""
        if hasattr(self.context, "ui") and self.context.ui:
            self.context.ui.log(f"⚠️ [MartialManager] {msg}")
        else:
            logging.info(f"⚠️ [MartialManager] {msg}")

    def _safe_get_bible(self) -> dict:
        """[V44] 안전한 bible 접근"""
        if self.context is None:
            return {}
        bible = getattr(self.context, "master_bible", None)
        if bible is None:
            return {}
        if not isinstance(bible, dict):
            return {}
        return bible.get("MasterBible", bible)

    def _is_valid_number(self, value) -> bool:
        """[V44] 숫자가 유효한지 검증 (NaN, inf 체크)"""
        if not isinstance(value, int | float):
            return False
        if math.isnan(value) or math.isinf(value):
            return False
        return True

    def _safe_to_float(self, value, default: float = 0.0) -> float:
        """[V44] 안전한 float 변환 (특수값 처리)"""
        if value is None:
            return default

        try:
            # 문자열인 경우
            if isinstance(value, str):
                value = value.strip()
                if not value or value.lower() in ["none", "null", "없음", ""]:
                    return default

                # guard를 통한 변환 시도
                if hasattr(self.context, "guard") and self.context.guard is not None:
                    result = self.context.guard.convert_to_numeric(value)
                else:
                    # 직접 변환
                    result = float(value)
            elif isinstance(value, int | float):
                result = float(value)
            else:
                return default

            # 유효성 검증
            if not self._is_valid_number(result):
                return default

            return result
        except (ValueError, TypeError, AttributeError):
            return default

    def _safe_to_int(self, value, default: int = 0) -> int:
        """[V44] 안전한 int 변환"""
        float_val = self._safe_to_float(value, float(default))
        if not self._is_valid_number(float_val):
            return default
        return int(float_val)

    @property
    def pro_root(self):
        """[V44] Protagonist 데이터의 루트 레이어 확보 (안전 접근)"""
        bible = self._safe_get_bible()

        # [V44] 단계별 안전 접근
        hud_data = None
        if isinstance(bible, dict):
            hud_data = bible.get("MartialHUD")
            if hud_data is None:
                hud_data = bible.get("martial_hud")

        # [V44] HUD 데이터가 없거나 dict가 아니면 기본 구조 생성
        if not isinstance(hud_data, dict):
            hud_data = {
                "Protagonist": {
                    "actual_truth": {
                        "name": "주인공",
                        "realm": "초출",
                        "internal_energy": 0,
                        "mental_method": "기본 심법",
                        "wealth": "은자 100냥",
                        "causal_injuries": "정상",
                        "current_objective": "강해지기",
                        "reputation": "무명",
                    }
                }
            }
            # bible이 유효하면 저장
            if isinstance(bible, dict):
                bible["MartialHUD"] = hud_data

        protagonist = hud_data.get("Protagonist")
        if not isinstance(protagonist, dict):
            return hud_data

        return protagonist

    @property
    def pro_data(self):
        """[Actual Truth] 실제 물리적 수치 주머니 인출"""
        return self.pro_root.get("actual_truth", self.pro_root)

    # --- [데이터 통합 수혈 및 정규화 엔진] ---
    def _get_normalized_val(self, canonical_key, default="기록 없음"):
        """변칙 키들을 뒤져서 표준 키의 값을 찾아 반환함"""
        fallbacks = self.canonical_map.get(canonical_key, [canonical_key])
        for key in fallbacks:
            val = self.pro_data.get(key)
            if val is not None:
                return val
        return default

    # --- [통합 속성 관리] ---
    @property
    def name(self):
        return self.pro_data.get("name", self.pro_data.get("Name", self.pro_data.get("alias", "주인공")))

    @property
    def alias(self):
        return self.pro_data.get("alias", "무명인")

    @property
    def rank(self):
        return self.pro_data.get("rank", "평민")

    @property
    def realm(self):
        return self.pro_data.get("realm", "초출")

    @property
    def internal_energy(self) -> float:
        """[V44] 안전한 내공 수치 접근"""
        val = self.pro_data.get("internal_energy", 0)
        return self._safe_to_float(val, 0.0)

    def get_internal_energy_description(self) -> str:
        """
        [V40.1] 내공 수치를 AI 판단 기반 서술형으로 변환
        서술형 + 정확한 수치를 함께 표시하여 에이전트가 올바른 판단 가능
        """
        try:
            energy = self.internal_energy

            # [V40.1 Safety] 특수값 처리 (음수, inf, nan)
            if energy < 0:
                return "내공 수치 오류 (음수)"
            if not isinstance(energy, int | float) or energy != energy:  # NaN 체크
                return "내공 수치 오류 (비정상)"
            if energy == float("inf"):
                return "내공 수치 오류 (무한대)"

            if energy < 0.1:
                desc = "내공이 거의 없음"
            elif energy < 1:
                desc = "기초 수준의 내공"
            elif energy < 5:
                desc = "내공이 많지 않음"
            elif energy < 10:
                desc = "약간의 내공을 보유"
            elif energy < 30:
                desc = "상당한 내공을 축적"
            elif energy < 50:
                desc = "풍부한 내공을 갖춤"
            elif energy < 100:
                desc = "강력한 내공을 지님"
            elif energy < 200:
                desc = "깊은 내공을 보유"
            else:
                # 200년 이상은 이미 수치 포함
                return f"심오한 경지의 내공 ({int(energy)}년)"

            # 200년 미만은 서술형 + 수치 병기
            # [V40.1 포맷팅] 소수점 처리 (0.0년 같은 경우 깔끔하게)
            if energy == int(energy):
                return f"{desc} ({int(energy)}년)"
            else:
                return f"{desc} ({energy:.1f}년)"
        except Exception as e:
            # 예상치 못한 에러 발생 시 안전한 기본값 반환
            return f"내공 정보 없음 (오류: {str(e)[:20]})"

    @property
    def mental_method(self):
        return self._get_normalized_val("mental_method")

    @property
    def wealth(self):
        return self._get_normalized_val("wealth")

    @property
    def causal_injuries(self):
        return self._get_normalized_val("causal_injuries")

    @property
    def qi_nature(self):
        return self.pro_data.get("qi_nature", "무색무취")

    @property
    def equipment(self):
        return self.pro_data.get("equipment", "평범한 무복")

    @property
    def token(self):
        return self.pro_data.get("token", "없음")

    @property
    def objective(self):
        return self._get_normalized_val("current_objective")

    @property
    def misunderstanding(self) -> int:
        """[V44] 안전한 착각 수치 접근"""
        val = self.pro_data.get("misunderstanding", 0)
        return self._safe_to_int(val, 0)

    @property
    def obsession(self) -> int:
        """[V44] 안전한 집착 수치 접근"""
        val = self.pro_data.get("obsession", 0)
        return self._safe_to_int(val, 0)

    @property
    def inventory(self):
        return self.pro_data.get("inventory", [])

    @property
    def techniques(self) -> list:
        techs = self.pro_data.get("martial_arts", self.pro_data.get("SignatureMove", []))
        if techs is None:
            return []
        return [t.strip() for t in techs.split(",")] if isinstance(techs, str) else techs

    # --- [핵심 업데이트부: 데이터 정규화 가드] ---
    def update_physical_status(self, full_state_data) -> list:
        """[🛡️ Guard Logic] 에이전트의 변칙 키를 표준 키로 강제 치환하여 성경에 박제"""
        if not full_state_data:
            return []  # 변경 사항 리스트 반환으로 변경

        _mb = (
            self.context.master_bible if hasattr(self.context, "master_bible") and self.context.master_bible else {}
        )  # [V70] None 방어
        bible = _mb.get("MasterBible", _mb)
        pro = bible.setdefault("MartialHUD", {}).setdefault("Protagonist", {})
        actual = pro.setdefault("actual_truth", {})
        actual_in = full_state_data.get("actual_truth", full_state_data)

        update_logs = []
        for canonical_key in MARTIAL_METRICS:  # 👈 상수를 직접 순회
            # 1단계: canonical_map에 정의된 변칙 키들을 모두 뒤져서 값 찾기
            val = None
            for alt_key in self.canonical_map.get(canonical_key, [canonical_key]):
                if alt_key in actual_in:
                    val = actual_in[alt_key]
                    break  # 값을 찾았으니 더 이상 검색하지 않음

            # 2단계: 값을 찾았다면 변환 및 업데이트 (for alt_key 루프 밖에서!)
            if val is not None:
                # [V35.6 Fix] 수치형 데이터 변환 시 텍스트 정보 유실 방지 가드 가동
                if canonical_key in ["misunderstanding", "obsession", "internal_energy"]:
                    raw_str_val = str(val).strip()

                    # [V60.22] 현재 값 가져오기 (델타 계산용)
                    current_val = actual.get(canonical_key)
                    if current_val is not None:
                        try:
                            current_val = float(current_val)
                        except (ValueError, TypeError):
                            current_val = None

                    # [V40.1 Critical Fix] guard가 None일 경우 대비
                    if not hasattr(self.context, "guard") or self.context.guard is None:  # [V70] hasattr 가드
                        # guard 없이 직접 변환 시도
                        try:
                            # [V60.22] 델타값 처리
                            if raw_str_val.startswith(("+", "-")) and current_val is not None:
                                delta = float(raw_str_val)
                                numeric_res = max(0, min(100, current_val + delta))
                            elif raw_str_val in ["현상유지", "현상 유지", "유지"]:
                                numeric_res = current_val if current_val is not None else 0
                            else:
                                numeric_res = float(raw_str_val.replace("%", ""))
                        except (ValueError, TypeError):
                            numeric_res = current_val if current_val is not None else 0
                    else:
                        # [V60.22] guard.convert_to_numeric에 현재 값 전달
                        try:
                            numeric_res = self.context.guard.convert_to_numeric(raw_str_val, current_val)
                            if numeric_res is None:
                                numeric_res = current_val if current_val is not None else 0
                        except (ValueError, TypeError, AttributeError):
                            numeric_res = current_val if current_val is not None else 0

                    # 변환 결과가 0이지만, 원본이 실제 숫자 '0' 계열이 아닌 경우 텍스트 보존
                    if numeric_res == 0 and raw_str_val not in ["0", "0.0", "0%", "영", "없음", "고갈", "전무"]:
                        # [V60.22] "현상 유지" 등은 현재 값 유지
                        if raw_str_val in ["현상유지", "현상 유지", "유지", "변화없음"]:
                            val = current_val if current_val is not None else 0
                        # 수치화할 수 없는 고유 묘사(예: "매우 높음")는 문자열 그대로 유지
                        pass
                    else:
                        val = numeric_res

                # [V60.23] 내공 바닥 방지 - 무협 주인공이 0%로 5화 연속은 서사적으로 불가능
                if canonical_key == "internal_energy" and isinstance(val, int | float):
                    # 내공 0% 연속 카운터 체크
                    zero_streak = actual.get("_internal_energy_zero_streak", 0)

                    if val <= 5:  # 5% 이하면 "바닥" 상태
                        zero_streak += 1
                        actual["_internal_energy_zero_streak"] = zero_streak

                        if zero_streak >= 3:
                            # 3화 연속 바닥이면 강제 회복 (휴식/조식 묘사 가정)
                            val = max(val, 20)  # 최소 20%로 강제 회복
                            update_logs.append(f"⚠️ [V60.23] 내공 {zero_streak}화 연속 바닥 → 강제 회복 20%")
                        elif zero_streak >= 2:
                            # 2화 연속이면 경고만
                            update_logs.append("⚠️ [V60.23] 내공 2화 연속 바닥 - 회복 장면 필요")
                    else:
                        # 바닥 아니면 카운터 리셋
                        actual["_internal_energy_zero_streak"] = 0

                    # 절대 하한선: 살아있는 무협 주인공은 최소 5% (폐인 아닌 이상)
                    if val < 5 and actual.get("causal_injuries", "") not in ["폐인", "사망", "식물인간"]:
                        val = 5
                        update_logs.append("⚠️ [V60.23] 내공 하한선 적용 (5%)")

                # 3단계: 실제 업데이트 수행
                old_val = actual.get(canonical_key)
                # 값의 물리적 내용이 변했을 때만 업데이트 수행
                if str(old_val) != str(val):
                    actual[canonical_key] = val
                    update_logs.append(f"{canonical_key}: {old_val} -> {val}")

        # 2. 리스트 데이터 및 상태 맵 유지
        for key in ["inventory", "martial_arts", "public_reputation", "knowledge_map"]:
            if key in full_state_data:
                pro[key] = full_state_data[key]
            elif key in actual_in:
                actual[key] = actual_in[key]

        # [V44 Fix] 들여쓰기 수정 - update_logs가 있을 때만 저장
        if update_logs:
            self.context.save_v20_anchor("bible", self.context.master_bible)

        return update_logs  # 👈 변경된 리스트를 메인으로 던져줌

    def get_critical_keys(self) -> list:
        """[V40] 무협 장르 필수 추적 키"""
        return [
            "realm",
            "internal_energy",
            "mental_method",
            "wealth",
            "current_objective",
            "causal_injuries",
            "reputation",
        ]

    def get_structured_hud(self) -> dict:
        """
        [V45 Fix] 구조화된 HUD 데이터를 딕셔너리로 반환 (Architect/Writer용)

        Returns:
            dict: HUD 데이터 딕셔너리
        """
        rep = self.pro_root.get("public_reputation", {})

        # None 값 방어: 각 속성이 None이면 기본값으로 대체
        def safe_value(value, default):
            return value if value is not None else default

        techniques_list = self.techniques if self.techniques else ["기초 무공"]

        return {
            "actual_truth": {
                "name": safe_value(self.name, "주인공"),
                "alias": safe_value(self.alias, "무명인"),
                "rank": safe_value(self.rank, "평민"),
                "realm": safe_value(self.realm, "초출"),
                "mental_method": safe_value(self.mental_method, "수련 중인 심법 없음"),
                "internal_energy": self.get_internal_energy_description(),
                "causal_injuries": safe_value(self.causal_injuries, "특이사항 없음"),
                "status_tags": [self.causal_injuries] if self.causal_injuries else [],
                "wealth": safe_value(self.wealth, "자금 정보 없음"),
                "objective": safe_value(self.objective, "목표 미설정"),
                "techniques": techniques_list,
                "equipment": safe_value(self.equipment, []),
                "token": safe_value(self.token, []),
            },
            "public_reputation": {
                "identity": rep.get("identity", "기록 없음"),
                "realm": rep.get("realm", "알 수 없음"),
                "perceived_power": rep.get("perceived_power", "평범함"),
            },
            "metrics": {
                "misunderstanding": safe_value(self.misunderstanding, 0),
                "obsession": safe_value(self.obsession, 0),
            },
        }

    def get_v20_hud_report(self) -> str:
        """[V25 High-Res] 정규화된 데이터 기반의 무결성 리포트 출력 (None 값 방어 처리 추가)"""
        rep = self.pro_root.get("public_reputation", {})

        # None 값 방어: 각 속성이 None이면 기본 설명으로 대체
        def safe_str(value, default="기록 없음"):
            return str(value) if value is not None else default

        name = safe_str(self.name, "주인공")
        alias = safe_str(self.alias, "무명인")
        rank = safe_str(self.rank, "평민")
        realm = safe_str(self.realm, "초출")
        mental_method = safe_str(self.mental_method, "수련 중인 심법 없음")
        causal_injuries = safe_str(self.causal_injuries, "특이사항 없음")
        wealth = safe_str(self.wealth, "자금 정보 없음")
        objective = safe_str(self.objective, "목표 미설정")

        techniques_list = self.techniques if self.techniques else ["기초 무공"]
        techniques_str = ", ".join(str(t) for t in techniques_list)

        return f"""
[🛡️ V25 SOVEREIGN HUD - 실시간 다층 통합 상태]
─────────── [실제 진실 (Actual Truth)] ───────────
- 성명: {name} ({alias}) | 직위: {rank}
- 경지: {realm} | 내공: {self.get_internal_energy_description()} | 심법: {mental_method}
- 상태: {causal_injuries} | 자금: {wealth}
- 무공: {techniques_str}

─────────── [세간의 인식 (Reputation)] ───────────
- 대외 호칭: {rep.get("identity", "기록 없음")}
- 인식상 경지: {rep.get("realm", "알 수 없음")}
- 소문난 위력: {rep.get("perceived_power", "평범함")}
- 서사 지표: 착각({self.misunderstanding}) | 집착({self.obsession})
- 목표: {objective}
"""

    def get_hud_trend(self, ep_num: int, window: int = 5) -> str:
        """
        [Lightweight Alternative] 최근 N화의 HUD 변화 추세 반환

        Args:
            ep_num: 현재 화 번호
            window: 추적할 화 수 (기본 5화)

        Returns:
            str: "무력: 50→65 (△15), 내공: 30→28 (▽2)"
        """
        trends = []

        # 주요 메트릭 정의 (숫자로 추적 가능한 것들)
        metrics = ["realm", "internal_energy", "reputation", "wealth"]
        metric_labels = {"realm": "경지", "internal_energy": "내공", "reputation": "명성", "wealth": "자금"}

        for metric in metrics:
            values = []
            valid_eps = []  # 유효한 화 번호 추적

            # 최근 N화 데이터 수집
            for i in range(max(1, ep_num - window), ep_num):
                try:
                    ms_data = self.context.db.get_manuscript(i)
                    if ms_data and isinstance(ms_data, dict):
                        hud_snapshot = ms_data.get("hud_snapshot")
                        if hud_snapshot and isinstance(hud_snapshot, dict):
                            actual_truth = hud_snapshot.get("actual_truth", {})
                            if isinstance(actual_truth, dict) and metric in actual_truth:
                                val = actual_truth[metric]
                                # 숫자로 변환 가능한 경우만 추가
                                try:
                                    if isinstance(val, int | float):
                                        values.append(float(val))
                                        valid_eps.append(i)
                                    elif isinstance(val, str):
                                        # 문자열에서 숫자 추출 시도
                                        import re

                                        nums = re.findall(r"\d+(?:\.\d+)?", val)
                                        if nums:
                                            values.append(float(nums[0]))
                                            valid_eps.append(i)
                                except (ValueError, TypeError, AttributeError):  # [V64.P4] numeric parse failure
                                    pass
                except Exception:
                    continue

            # 추세 계산
            if len(values) >= 2:
                start, end = values[0], values[-1]
                change = end - start

                if abs(change) >= 1:  # 변화가 1 이상일 때만 표시
                    label = metric_labels.get(metric, metric)
                    if change > 0:
                        trends.append(f"{label}: {int(start)}→{int(end)} (△{int(change)})")
                    else:
                        trends.append(f"{label}: {int(start)}→{int(end)} (▽{int(abs(change))})")

        return ", ".join(trends) if trends else "안정적 (변화 없음)"
