import json
import os
import re
import time
import ast  # 👈 [필수] literal_eval 가동을 위해 반드시 필요
from google import genai
from google.genai import types

class BaseAgent:
    def __init__(self, context, client, model_tier="gemini-2.0-flash", enable_cascade=False):
        self.context = context
        self.client = client
        self.primary_model = model_tier
        self.backup_model = "gemini-2.0-flash"
        self.cache_name = None
        self.enable_cascade = enable_cascade
        self.cascade = None  # ModelCascade instance (lazy init)

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
                if full_response.endswith("\\"):
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
            print(f"      ⚠️ [Warning] 모델 실패, 백업 가동: {str(e)[:50]}")
            try:
                res = self.client.models.generate_content(
                    model=self.backup_model,
                    contents=base_prompt,
                    config=config
                )
                return res.text if res.text else "{}"
            except Exception as e_inner:
                print(f"      🚨 [Critical] 백업 실패: {str(e_inner)[:50]}")
                return "{}"

    def _escape_braces(self, text):
        """중괄호 {}로 인한 KeyError 방지 및 Prompt Injection 방어"""
        if not isinstance(text, str): 
            return str(text)
        return text.replace("{", "{{").replace("}", "}}")


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
            final_dict = {}

            def process_node(node):
                nonlocal final_dict
                if isinstance(node, list):
                    for item in node: process_node(item)
                elif isinstance(node, dict):
                    # 표준 키 우선 추출 (Target, Value 등)
                    t = node.get("target") or node.get("npc_name") or node.get("item") or node.get("name")
                    v = node.get("value") or node.get("misunderstanding") or node.get("description")
                    if t and v is not None:
                        final_dict[str(t).strip("'\" ")] = v
                    
                    # 중첩 구조 해제 루프
                    for k, val in node.items():
                        if k in ['actual_truth', 'state_updates', 'ProjectData', 'MasterBible', 'content'] and isinstance(val, (dict, list)):
                            process_node(val)
                        else:
                            clean_k = str(k).strip("'\" ")
                            if clean_k not in final_dict or val is not None:
                                final_dict[clean_k] = val

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
            except:
                kv_pattern = r'"(\w+)"\s*:\s*"(.*?)"(?="|\s*\}|\s*,)'
                found_pairs = re.findall(kv_pattern, json_str, re.DOTALL)
                if found_pairs:
                    return {k: v.replace('\\n', '\n').strip() for k, v in found_pairs}
                return {"content": json_str, "status": "REPAIRED_RAW"}
        except Exception:
            return {"content": json_str, "error": "CRITICAL_FAILURE"}