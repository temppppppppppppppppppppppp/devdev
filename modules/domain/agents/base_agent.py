import json
import os
import re
import time
import ast  # 👈 [필수] literal_eval 가동을 위해 반드시 필요
from google import genai
from google.genai import types

# [V44] 에스케이프 유틸리티 임포트
try:
    from modules.core.escape_utils import EscapeUtils, escape_braces as util_escape_braces
except ImportError:
    # 폴백: 유틸리티 없을 시 기본 구현 사용
    util_escape_braces = None


# [V44] 에러 타입 분류
class AgentErrorType:
    TIMEOUT = "timeout"
    QUOTA_EXCEEDED = "quota_exceeded"
    MALFORMED_RESPONSE = "malformed_response"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"


class BaseAgent:
    def __init__(self, context, client, model_tier="gemini-2.0-flash", enable_cascade=False):
        self.context = context
        self.client = client
        self.primary_model = model_tier
        self.backup_model = "gemini-2.0-flash"
        self.cache_name = None
        self.enable_cascade = enable_cascade
        self.cascade = None  # ModelCascade instance (lazy init)
        # [V44] 실패 복구 상태 추적
        self.last_partial_response = ""
        self.requires_human_intervention = False
        self.last_error_type = None

    # 📂 modules/domain/agents/base_agent.py

    def ask(self, prompt, temperature=0.5, response_schema=None):
        directives = self._escape_braces(getattr(self.context, 'author_directives', ""))
        base_prompt = (
            f"### [AUTHOR'S ABSOLUTE DIRECTIVES]\n{directives}\n\n"
            f"### [TASK]\n{prompt}\n\n"
            f"### [FORMAT]\nRespond ONLY in valid JSON format."
        )
        
        full_response = ""
        current_prompt = base_prompt

        config_params = {
            "temperature": temperature,
            "max_output_tokens": 8192,
            "top_p": 0.95,
            "response_mime_type": "application/json"
        }

        # [V0128] JSON Schema enforcement if provided
        if response_schema:
            config_params["response_schema"] = response_schema

        config = types.GenerateContentConfig(**config_params)

        try:
            # 🔒 Circuit Breaker: 최대 5회 시도 (API 비용 폭증 방지)
            MAX_CONTINUATIONS = 5
            WARN_THRESHOLD = 3

            for attempt in range(MAX_CONTINUATIONS):
                response = self.client.models.generate_content(
                    model=self.primary_model,
                    contents=current_prompt,
                    config=config
                )

                chunk = response.text if response.text else ""

                # 💡 [Sovereign Logic] 지능형 중첩 제거 병합 (Overlap-Aware Merge)
                if full_response:
                    # 앞 응답의 끝부분과 뒤 응답의 시작부분이 겹치는지 최대 100자 대조
                    max_overlap = min(len(full_response), len(chunk), 100)
                    overlap_found = 0
                    for i in range(max_overlap, 0, -1):
                        if full_response.endswith(chunk[:i]):
                            overlap_found = i
                            break

                    # 중복된 부분은 제외하고 순수 데이터만 정밀하게 접합
                    full_response += chunk[overlap_found:]
                else:
                    full_response = chunk

                # 이어쓰기 중 이스케이프 단절 방지
                # [V44] 최소 길이 체크 (빈 문자열/단일 백슬래시 방지)
                if len(full_response) > 1 and full_response.endswith("\\"):
                    print("      ⚠️ [JSON Repair] 후행 이스케이프 감지. 강제 제거")
                    full_response = full_response[:-1]

                if not response.candidates: break
                candidate = response.candidates[0]

                # 토큰 제한(MAX_TOKENS) 발생 시 '비트 3' 유실 방지를 위한 이어쓰기 시퀀스
                if hasattr(candidate, 'finish_reason') and candidate.finish_reason in ["MAX_TOKENS", "LENGTH"]:
                    # 🔒 Circuit Breaker 경고
                    if attempt >= WARN_THRESHOLD:
                        print(f"      ⚠️ [Circuit Breaker] 과도한 continuation 감지 ({attempt+1}/{MAX_CONTINUATIONS}회)")
                        print(f"      ⚠️ [Cost Warning] API 비용 증가 중 - 누적 응답 길이: {len(full_response)} chars")

                    # 🔒 Circuit Breaker 트립 (최대 시도 횟수 도달)
                    if attempt >= MAX_CONTINUATIONS - 1:
                        print(f"      🚨 [Circuit Breaker TRIP] 최대 continuation 횟수 도달 ({MAX_CONTINUATIONS}회)")
                        print(f"      🚨 [WARNING] 응답 불완전 가능 - 수동 검토 필요")
                        break

                    # 마지막 50자를 앵커로 사용하여 다음 응답의 시작점을 강제 고정
                    overlap_anchor = full_response[-50:].strip()
                    print(f"      🔄 [System] 데이터 절단 감지. '{overlap_anchor[:20]}...' 지점부터 인과율 용접 시도 ({attempt+1}/{MAX_CONTINUATIONS})")

                    current_prompt = (
                        f"--- [SYSTEM: CONTINUATION MISSION] ---\n"
                        f"Your previous response was cut off exactly at: '...{overlap_anchor}'\n"
                        f"CONTINUE the JSON structure IMMEDIATELY from the next character.\n"
                        f"Do not summarize. Do not skip any bits (especially 'Beat 3')."
                    )
                    time.sleep(1)
                else:
                    break
            
            return full_response

        except Exception as e:
            # [V44] 에러 타입 분류 및 적절한 복구 전략 선택
            error_type = self._classify_error(e)
            self.last_error_type = error_type
            print(f"      ⚠️ [Warning] 모델 실패 ({error_type}), 백업 가동: {str(e)[:50]}")

            # 부분 응답이 있으면 저장
            if full_response:
                self.last_partial_response = full_response
                print(f"      📝 [Recovery] 부분 응답 {len(full_response)}자 보존")

            try:
                res = self.client.models.generate_content(
                    model=self.backup_model,
                    contents=base_prompt,
                    config=config
                )
                backup_text = res.text if res.text else ""

                # [V44] 응답 검증
                if backup_text:
                    validation = self._validate_response(backup_text)
                    if validation["valid"]:
                        self.requires_human_intervention = False
                        return backup_text
                    else:
                        print(f"      ⚠️ [Validation] 백업 응답 검증 실패: {validation['reason']}")
                        # 부분 응답 병합 시도
                        if self.last_partial_response:
                            merged = self._try_merge_responses(self.last_partial_response, backup_text)
                            if merged:
                                print(f"      ✅ [Recovery] 부분 응답 병합 성공")
                                return merged

                # 빈 응답 처리
                if self.last_partial_response:
                    print(f"      📝 [Fallback] 부분 응답 반환 ({len(self.last_partial_response)}자)")
                    # [V44] 부분 응답은 검증되지 않음 - 플래그 설정
                    self.requires_human_intervention = True
                    return self.last_partial_response

                return self._create_error_response(error_type, "백업 모델 빈 응답")

            except Exception as e_inner:
                inner_error_type = self._classify_error(e_inner)
                print(f"      🚨 [Critical] 백업 실패 ({inner_error_type}): {str(e_inner)[:50]}")

                # [V44] 최후의 복구 시도
                if self.last_partial_response:
                    print(f"      📝 [Last Resort] 부분 응답 반환 ({len(self.last_partial_response)}자)")
                    self.requires_human_intervention = True
                    return self.last_partial_response

                # 빈 JSON 대신 구조화된 에러 응답 반환
                self.requires_human_intervention = True
                return self._create_error_response(inner_error_type, str(e_inner)[:100])

    def _escape_braces(self, text, force=False):
        """
        [V44] 중괄호 에스케이프 (최적화 버전)

        Args:
            text: 에스케이프할 텍스트
            force: True면 중복 검사 없이 강제 에스케이프

        Returns:
            str: 에스케이프된 텍스트
        """
        # V44 유틸리티 사용 (중복 에스케이프 방지 내장)
        if util_escape_braces is not None:
            return util_escape_braces(text, force)

        # 폴백 구현
        if not isinstance(text, str):
            return str(text) if text is not None else ""

        if not text:
            return ""

        # [V44] 중복 에스케이프 방지: 이미 이중 중괄호가 있으면 스킵
        if not force:
            has_double = '{{' in text or '}}' in text
            has_single = '{' in text.replace('{{', '') or '}' in text.replace('}}', '')
            if has_double and not has_single:
                return text  # 이미 에스케이프됨

        return text.replace("{", "{{").replace("}", "}}")

    # [V44] 에러 분류 메서드
    def _classify_error(self, error: Exception) -> str:
        """에러 타입을 분류하여 적절한 복구 전략 결정에 활용"""
        error_str = str(error).lower()

        if "timeout" in error_str or "deadline" in error_str:
            return AgentErrorType.TIMEOUT
        elif "quota" in error_str or "rate" in error_str or "429" in error_str:
            return AgentErrorType.QUOTA_EXCEEDED
        elif "connection" in error_str or "network" in error_str or "ssl" in error_str:
            return AgentErrorType.NETWORK_ERROR
        elif "json" in error_str or "parse" in error_str or "decode" in error_str:
            return AgentErrorType.MALFORMED_RESPONSE
        else:
            return AgentErrorType.UNKNOWN

    def _validate_response(self, response: str) -> dict:
        """응답이 유효한 JSON 구조인지 검증"""
        if not response or not isinstance(response, str):
            return {"valid": False, "reason": "빈 응답 또는 문자열 아님"}

        response = response.strip()

        # 최소 길이 검사
        if len(response) < 10:
            return {"valid": False, "reason": f"응답 너무 짧음 ({len(response)}자)"}

        # JSON 구조 검사
        if not (response.startswith('{') or response.startswith('[')):
            return {"valid": False, "reason": "JSON 시작 문자 없음"}

        # 괄호 균형 검사
        open_braces = response.count('{')
        close_braces = response.count('}')
        if abs(open_braces - close_braces) > 2:
            return {"valid": False, "reason": f"괄호 불균형 ({open_braces} vs {close_braces})"}

        # 핵심 필드 존재 검사 (최소 하나)
        key_fields = ['content', 'tactical_doc', 'integrated_scenario', 'title', 'state_updates']
        has_key_field = any(f'"{field}"' in response for field in key_fields)
        if not has_key_field:
            return {"valid": False, "reason": "핵심 필드 없음"}

        return {"valid": True, "reason": "OK"}

    def _try_merge_responses(self, partial: str, backup: str) -> str:
        """부분 응답과 백업 응답을 병합 시도"""
        if not partial or not backup:
            return None

        try:
            # 두 응답 모두 JSON 파싱 시도
            partial_data = self._extract_json_robust(partial)
            backup_data = self._extract_json_robust(backup)

            if not isinstance(partial_data, dict) or not isinstance(backup_data, dict):
                return None

            # partial에 없는 키만 backup에서 보충
            merged = partial_data.copy()
            for key, value in backup_data.items():
                if key not in merged or merged[key] in [None, "", "None"]:
                    merged[key] = value

            # 병합 결과가 유효한지 확인
            if 'parsing_error' in merged and merged.get('parsing_error'):
                return None

            return json.dumps(merged, ensure_ascii=False)
        except Exception:
            return None

    def _create_error_response(self, error_type: str, message: str) -> str:
        """구조화된 에러 응답 생성 (빈 JSON 대신)"""
        error_response = {
            "error": True,
            "error_type": error_type,
            "error_message": message,
            "requires_human_intervention": True,
            "recovery_hint": self._get_recovery_hint(error_type)
        }
        return json.dumps(error_response, ensure_ascii=False)

    def _get_recovery_hint(self, error_type: str) -> str:
        """에러 타입별 복구 힌트 제공"""
        hints = {
            AgentErrorType.TIMEOUT: "API 응답 시간 초과. 잠시 후 재시도하거나 프롬프트를 줄이세요.",
            AgentErrorType.QUOTA_EXCEEDED: "API 할당량 초과. 잠시 대기 후 재시도하세요.",
            AgentErrorType.NETWORK_ERROR: "네트워크 연결 오류. 인터넷 연결을 확인하세요.",
            AgentErrorType.MALFORMED_RESPONSE: "응답 형식 오류. 프롬프트를 단순화하여 재시도하세요.",
            AgentErrorType.UNKNOWN: "알 수 없는 오류. 로그를 확인하고 재시도하세요."
        }
        return hints.get(error_type, hints[AgentErrorType.UNKNOWN])


    def _extract_json_robust(self, text):
        """
        [V40.5 Ultimate Sovereign] 
        자가 치유(Self-Healing) + 재귀적 평탄화(Flattening) 통합 엔진
        """


        if not text or not isinstance(text, str):
            return {"parsing_error": True, "content": "Empty or Invalid Input"}

        # 1. [Self-Healing] 괄호/따옴표 쌍 검사 및 강제 폐쇄
        open_braces = text.count('{')
        close_braces = text.count('}')
        if open_braces > close_braces:
            text += '}' * (open_braces - close_braces)
        quote_count = len(re.findall(r'(?<!\\\\)"', text))
        if quote_count % 2 != 0:
            text += '"'

        try:
            # 2. 전처리 및 JSON 블록 추출
            clean_text = re.sub(r'```json\s*|```\s*', '', text.strip())
            json_pattern = re.compile(r'(\{.*\}|\[.*\])', re.DOTALL)
            match = json_pattern.search(clean_text)
            raw_json = match.group(1) if match else clean_text

            # 3. 2단계 파싱 (json -> ast)
            data = None
            try:
                data = json.loads(raw_json, strict=False)
            except Exception:
                try:
                    data = ast.literal_eval(raw_json)
                except Exception:
                    # [Hard Repair] 구조 강제 수리 시도
                    repaired = self._parse_and_repair_hard(raw_json)
                    if isinstance(repaired, dict):
                        return repaired
                    # [Fallback] 파싱 실패 시 정규식으로 핵심 전술 데이터 강제 추출
                    doc_match = re.search(r'"tactical_doc"\s*:\s*"(.*?)"', text, re.DOTALL)
                    if doc_match:
                        return {"tactical_doc": doc_match.group(1), "repaired": True}
                    
                    # [V35 Fix] Writer Agent를 위한 content 필드 강제 추출
                    content_match = re.search(r'"content"\s*:\s*"(.*?)"', text, re.DOTALL)
                    if content_match:
                        return {"content": content_match.group(1), "repaired": True}
                    return {"parsing_error": True, "content": text, "status": "RAW_TEXT_ONLY"}

            # 4. 재귀적 데이터 평탄화 엔진 (성경 무결성 보존)
            # [V44] 순환 참조 감지 및 깊이 제한 추가
            final_dict = {}
            seen_ids = set()  # 순환 참조 감지용
            MAX_DEPTH = 20    # 최대 재귀 깊이

            def process_node(node, depth=0):
                nonlocal final_dict
                # [V44] 깊이 제한 체크
                if depth > MAX_DEPTH:
                    return
                # [V44] 순환 참조 체크
                node_id = id(node)
                if node_id in seen_ids:
                    return
                seen_ids.add(node_id)

                try:
                    if isinstance(node, list):
                        for item in node:
                            process_node(item, depth + 1)
                    elif isinstance(node, dict):
                        # 표준 키 우선 추출 (Target, Value 등)
                        t = node.get("target") or node.get("npc_name") or node.get("item") or node.get("name")
                        v = node.get("value") or node.get("misunderstanding") or node.get("description")
                        if t and v is not None:
                            final_dict[str(t).strip("'\" ")] = v

                        # 중첩 구조 해제 루프
                        for k, val in node.items():
                            if k in ['actual_truth', 'state_updates', 'ProjectData', 'MasterBible', 'content'] and isinstance(val, (dict, list)):
                                process_node(val, depth + 1)
                            else:
                                clean_k = str(k).strip("'\" ")
                                if clean_k not in final_dict or val is not None:
                                    final_dict[clean_k] = val
                finally:
                    # 처리 완료 후 seen에서 제거 (다른 경로에서 재방문 허용)
                    seen_ids.discard(node_id)

            process_node(data)

            # 5. 최종 키 정규화 및 반환
            return {str(k).replace('"', '').replace("'", ""): v for k, v in final_dict.items()}

        except Exception as e:
            return {"parsing_error": True, "error": str(e), "fallback_content": str(text)[:100]}



    def _parse_and_repair_hard(self, json_str):
        """[V27.5 Hardened] 물리적 구조 강제 수리"""
        try:
            open_cnt, close_cnt = json_str.count('{'), json_str.count('}')
            if open_cnt > close_cnt: 
                json_str += '}' * (open_cnt - close_cnt)
            
            processed = re.sub(r':\s*null\b', ': None', json_str)
            processed = re.sub(r':\s*true\b', ': True', processed)
            processed = re.sub(r':\s*false\b', ': False', processed)
            
            try:
                return ast.literal_eval(processed)
            except (ValueError, SyntaxError):
                # [V44] JSON 파싱 실패 시 정규식 추출 경고
                print(f"⚠️ [JSON Parser] ast.literal_eval 실패, 정규식 fallback 사용 (길이: {len(json_str)}자)")
                kv_pattern = r'"(\w+)"\s*:\s*"(.*?)"(?="|\s*\}|\s*,)'
                found_pairs = re.findall(kv_pattern, json_str, re.DOTALL)
                if found_pairs:
                    print(f"   → 정규식으로 {len(found_pairs)}개 키-값 추출 성공")
                    return {k: v.replace('\\n', '\n').strip() for k, v in found_pairs}
                print(f"   → 정규식 추출 실패, RAW 반환")
                return {"content": json_str, "status": "REPAIRED_RAW"}
        except Exception as e:
            print(f"🚨 [JSON Parser] CRITICAL_FAILURE: {str(e)[:100]}")
            return {"content": json_str, "error": "CRITICAL_FAILURE"}