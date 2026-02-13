"""
Treatment Builder - 블록 스토리 생성 도구
===========================================
Phase 1: 60개 블록 뼈대 (제목 + 한줄요약) 생성
Phase 2: 3개씩 20회 상세 생성
Phase 3: 메타데이터 추출

사용법:
    python tools/treatment_builder.py --bible path/to/bible.json --output path/to/output_tr.json
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

try:
    from google import genai
    from google.genai import types

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("⚠️ google-genai 패키지가 없습니다. pip install google-genai")


class TreatmentBuilder:
    """Treatment 블록 생성 도구"""

    def __init__(self, bible_path: str, output_path: str, genre: str = "investment"):
        self.bible_path = Path(bible_path)
        self.output_path = Path(output_path)
        self.genre = genre
        self.bible = None
        self.blocks = []
        self.total_blocks = 60
        self.batch_size = 3

        # Gemini 클라이언트
        if GENAI_AVAILABLE:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if api_key:
                self.client = genai.Client(api_key=api_key)
                self.model = "gemini-2.5-flash"
            else:
                self.client = None
                print("⚠️ GOOGLE_API_KEY 환경변수가 없습니다.")
        else:
            self.client = None

    def load_bible(self) -> dict:
        """Bible 로드"""
        if not self.bible_path.exists():
            print(f"❌ Bible 파일 없음: {self.bible_path}")
            return None

        with open(self.bible_path, encoding="utf-8") as f:
            self.bible = json.load(f)

        print(f"✅ Bible 로드 완료: {self.bible_path.name}")
        return self.bible

    def _call_llm(self, prompt: str, temperature: float = 0.8) -> str:
        """LLM 호출"""
        if not self.client:
            return None

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=8192,
                ),
            )
            return response.text
        except Exception as e:
            print(f"❌ LLM 호출 실패: {e}")
            return None

    def _extract_bible_context(self) -> str:
        """Bible에서 컨텍스트 추출"""
        if not self.bible:
            return ""

        mb = self.bible.get("MasterBible", self.bible)

        # 기본 정보
        project = mb.get("ProjectData", {})
        meta = project.get("MetaInfo", {})
        core = project.get("CoreIdentity", {})
        commercial = project.get("CommercialCode", {})

        # HUD (장르별)
        hud = mb.get("FinanceHUD", mb.get("MartialHUD", mb.get("HunterHUD", {})))
        protag = hud.get("Protagonist", {}).get("actual_truth", {})

        # NPC
        assets = mb.get("AssetLibrary", {})
        npcs = assets.get("KeyNPCs", [])
        npc_summary = "\n".join([f"- {n['name']} ({n['role']}): {n.get('desc', '')[:100]}" for n in npcs[:10]])

        # 역사 이벤트
        events = mb.get("HistoricalEvents", {}).get("events", [])
        event_summary = "\n".join([f"- {e['month']}: {e['event']}" for e in events[:10]])

        # 장르 규칙
        rules = mb.get("GenreRules", {})
        must_include = rules.get("must_include", [])
        forbidden = rules.get("forbidden", [])

        context = f"""
## 작품 정보
- 제목: {meta.get("title", "미정")}
- 장르: {meta.get("genre_archetype", self.genre)}
- 로그라인: {meta.get("logline", "")}

## 주인공
- 이름: {core.get("protagonist", "미정")}
- 엣지(강점): {core.get("edge", "")}
- 욕망: {core.get("desire", "")}
- 초기 위기: {core.get("crisis", "")}
- 초기 자산: {protag.get("financial_status", {}).get("total_assets", "미정")}

## 상업적 코드
- 사이다 포인트: {commercial.get("cider_point", "")}
- 태도: {commercial.get("attitude", "")}

## 주요 NPC
{npc_summary}

## 활용 가능한 역사 이벤트
{event_summary}

## 장르 규칙
- 필수: {", ".join(must_include[:3])}
- 금지: {", ".join(forbidden[:3])}
"""
        return context

    # ===========================================
    # Phase 1: 뼈대 생성
    # ===========================================

    def phase1_generate_skeleton(self, user_direction: str = "") -> list:
        """Phase 1: 60개 블록 뼈대 생성"""
        print("\n" + "=" * 60)
        print("📋 Phase 1: 블록 뼈대 생성 (60개)")
        print("=" * 60)

        bible_context = self._extract_bible_context()

        prompt = f"""당신은 웹소설 스토리 설계 전문가입니다.

{bible_context}

## 사용자 방향성
{user_direction if user_direction else "(없음 - 자유롭게 설계)"}

## 요청
위 설정을 바탕으로 60개 블록의 스토리 뼈대를 만들어주세요.
각 블록은 약 5개 에피소드 분량입니다.

## 출력 형식 (JSON)
```json
[
  {{"block_id": "Block 1", "title": "제목", "summary": "한줄 요약", "arc": 1}},
  {{"block_id": "Block 2", "title": "제목", "summary": "한줄 요약", "arc": 1}},
  ...
]
```

## 규칙
1. Arc는 6개 블록씩 묶음 (Arc 1: Block 1-6, Arc 2: Block 7-12, ...)
2. 각 Arc는 기승전결 구조
3. 자본/능력 성장 곡선 고려
4. 복선 심기와 회수 고려
5. 주요 빌런과의 대결 배치
6. 60개 블록 모두 출력

JSON만 출력하세요.
"""

        print("\n🤖 AI가 뼈대를 생성 중...")
        response = self._call_llm(prompt, temperature=0.9)

        if not response:
            print("❌ AI 응답 실패. 수동 입력 모드로 전환합니다.")
            return self._manual_skeleton_input()

        # JSON 파싱
        try:
            # ```json ... ``` 제거
            json_str = response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            skeleton = json.loads(json_str.strip())
            print(f"✅ {len(skeleton)}개 블록 뼈대 생성 완료")
            return skeleton
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 실패: {e}")
            print("응답 일부:", response[:500])
            return []

    def phase1_review_skeleton(self, skeleton: list) -> list:
        """Phase 1: 뼈대 검토 및 수정"""
        print("\n" + "-" * 60)
        print("📝 뼈대 검토")
        print("-" * 60)

        # 뼈대 출력
        for i, block in enumerate(skeleton[:10]):  # 처음 10개만 미리보기
            print(f"  {block['block_id']}: {block['title']}")
            print(f"    → {block['summary']}")

        if len(skeleton) > 10:
            print(f"  ... 외 {len(skeleton) - 10}개")

        print("\n옵션:")
        print("  [1] 승인 (다음 단계로)")
        print("  [2] 전체 보기")
        print("  [3] 특정 블록 수정")
        print("  [4] 전체 재생성")
        print("  [5] 저장 후 종료")

        choice = input("\n선택: ").strip()

        if choice == "1":
            return skeleton
        elif choice == "2":
            for block in skeleton:
                print(f"  {block['block_id']}: {block['title']}")
                print(f"    → {block['summary']}")
            return self.phase1_review_skeleton(skeleton)
        elif choice == "3":
            block_num = input("수정할 블록 번호 (예: 5): ").strip()
            try:
                idx = int(block_num) - 1
                if 0 <= idx < len(skeleton):
                    print(f"\n현재: {skeleton[idx]['title']}")
                    print(f"  → {skeleton[idx]['summary']}")
                    new_title = input("새 제목 (엔터=유지): ").strip()
                    new_summary = input("새 요약 (엔터=유지): ").strip()
                    if new_title:
                        skeleton[idx]["title"] = new_title
                    if new_summary:
                        skeleton[idx]["summary"] = new_summary
            except ValueError:
                pass
            return self.phase1_review_skeleton(skeleton)
        elif choice == "4":
            direction = input("새 방향성 입력 (엔터=이전과 동일): ").strip()
            return self.phase1_generate_skeleton(direction)
        elif choice == "5":
            self._save_progress(skeleton, phase=1)
            print("✅ 저장 완료. 종료합니다.")
            sys.exit(0)

        return skeleton

    def _manual_skeleton_input(self) -> list:
        """수동 뼈대 입력"""
        print("\n수동 입력 모드")
        skeleton = []
        for i in range(1, self.total_blocks + 1):
            title = input(f"Block {i} 제목: ").strip() or f"Block {i}"
            summary = input(f"Block {i} 요약: ").strip() or "..."
            arc = (i - 1) // 6 + 1
            skeleton.append({"block_id": f"Block {i}", "title": title, "summary": summary, "arc": arc})
        return skeleton

    # ===========================================
    # Phase 2: 상세 생성 (3개씩)
    # ===========================================

    def phase2_generate_details(self, skeleton: list) -> list:
        """Phase 2: 상세 content 생성 (3개씩)"""
        print("\n" + "=" * 60)
        print("📖 Phase 2: 상세 생성 (3개씩 × 20회)")
        print("=" * 60)

        detailed_blocks = []
        total_batches = (len(skeleton) + self.batch_size - 1) // self.batch_size

        for batch_idx in range(total_batches):
            start = batch_idx * self.batch_size
            end = min(start + self.batch_size, len(skeleton))
            batch_skeleton = skeleton[start:end]

            print(f"\n--- Batch {batch_idx + 1}/{total_batches}: Block {start + 1}-{end} ---")

            # 이전 배치 요약 (컨텍스트)
            prev_summary = ""
            if detailed_blocks:
                prev_summary = self._summarize_previous_blocks(detailed_blocks[-6:])

            # 현재 배치 생성
            batch_details = self._generate_batch_details(batch_skeleton, prev_summary, start + 1)

            if batch_details:
                # 검토
                batch_details = self._review_batch(batch_details, batch_idx + 1, total_batches)
                detailed_blocks.extend(batch_details)
            else:
                print("⚠️ 배치 생성 실패, 수동 입력")
                for block in batch_skeleton:
                    manual = self._manual_block_input(block)
                    detailed_blocks.append(manual)

        return detailed_blocks

    def _generate_batch_details(self, batch_skeleton: list, prev_summary: str, start_num: int) -> list:
        """배치 상세 생성"""
        bible_context = self._extract_bible_context()

        skeleton_text = "\n".join([f"- {b['block_id']}: {b['title']} - {b['summary']}" for b in batch_skeleton])

        prompt = f"""당신은 웹소설 스토리 작가입니다.

{bible_context}

## 이전 스토리 요약
{prev_summary if prev_summary else "(첫 번째 배치)"}

## 이번에 작성할 블록
{skeleton_text}

## 요청
위 블록들의 상세 content를 작성해주세요.

## 출력 형식 (JSON)
```json
[
  {{
    "block_id": "Block {start_num}",
    "title": "제목",
    "content": {{
      "context": "배경/상황 설명 (200-300자)",
      "event_villain": "빌런/장애물의 행동 (200-300자)",
      "solution": "주인공의 해결 방식 (200-300자)",
      "reward": "결과/보상 (100-200자)"
    }}
  }},
  ...
]
```

## 규칙
1. 이전 스토리와 자연스럽게 연결
2. 구체적인 숫자/이름 사용 (자산, NPC 등)
3. 감각적 묘사 포함 (시각, 청각 등)
4. 복선과 긴장감 유지

JSON만 출력하세요.
"""

        response = self._call_llm(prompt, temperature=0.85)

        if not response:
            return None

        try:
            json_str = response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]

            return json.loads(json_str.strip())
        except json.JSONDecodeError:
            return None

    def _summarize_previous_blocks(self, blocks: list) -> str:
        """이전 블록 요약"""
        summaries = []
        for b in blocks:
            content = b.get("content", {})
            summaries.append(f"- {b['block_id']}: {content.get('reward', '')[:100]}")
        return "\n".join(summaries)

    def _review_batch(self, batch: list, batch_num: int, total: int) -> list:
        """배치 검토"""
        print(f"\n📝 Batch {batch_num}/{total} 검토")

        for block in batch:
            content = block.get("content", {})
            print(f"\n  {block['block_id']}: {block['title']}")
            print(f"    context: {content.get('context', '')[:80]}...")
            print(f"    reward: {content.get('reward', '')[:80]}...")

        choice = input("\n[1] 승인 [2] 수정 [3] 재생성: ").strip()

        if choice == "1":
            return batch
        elif choice == "2":
            block_id = input("수정할 블록 ID (예: Block 1): ").strip()
            for block in batch:
                if block["block_id"] == block_id:
                    print("\n현재 content:")
                    for key, val in block["content"].items():
                        print(f"  {key}: {val[:100]}...")

                    field = input("수정할 필드 (context/event_villain/solution/reward): ").strip()
                    if field in block["content"]:
                        new_val = input(f"새 {field}: ").strip()
                        if new_val:
                            block["content"][field] = new_val
            return self._review_batch(batch, batch_num, total)
        elif choice == "3":
            # 재생성 로직은 생략 (복잡도)
            return batch

        return batch

    def _manual_block_input(self, skeleton: dict) -> dict:
        """수동 블록 입력"""
        print(f"\n수동 입력: {skeleton['block_id']} - {skeleton['title']}")
        return {
            "block_id": skeleton["block_id"],
            "title": skeleton["title"],
            "content": {
                "context": input("  context: ").strip() or "...",
                "event_villain": input("  event_villain: ").strip() or "...",
                "solution": input("  solution: ").strip() or "...",
                "reward": input("  reward: ").strip() or "...",
            },
        }

    # ===========================================
    # Phase 3: 메타데이터 추출
    # ===========================================

    def phase3_extract_metadata(self, blocks: list) -> list:
        """Phase 3: 메타데이터 추출"""
        print("\n" + "=" * 60)
        print("🔧 Phase 3: 메타데이터 추출")
        print("=" * 60)

        enriched_blocks = []

        for i, block in enumerate(blocks):
            print(f"  처리 중: {block['block_id']} ({i + 1}/{len(blocks)})")

            enriched = self._extract_block_metadata(block, blocks[:i])
            enriched_blocks.append(enriched)

        return enriched_blocks

    def _extract_block_metadata(self, block: dict, prev_blocks: list) -> dict:
        """단일 블록 메타데이터 추출"""
        content = block.get("content", {})

        # 이전 블록에서 마지막 자본 추출
        prev_capital = "미정"
        if prev_blocks:
            last = prev_blocks[-1]
            prev_capital = last.get("genre_ext", {}).get("capital_after", "미정")

        prompt = f"""다음 블록에서 메타데이터를 추출하세요.

## 블록 정보
- ID: {block["block_id"]}
- 제목: {block["title"]}
- context: {content.get("context", "")}
- event_villain: {content.get("event_villain", "")}
- solution: {content.get("solution", "")}
- reward: {content.get("reward", "")}

## 이전 블록 자본: {prev_capital}

## 추출할 필드 (JSON)
```json
{{
  "stakes": "실패 시 위험",
  "power_shift": {{
    "protagonist": "주인공 위상 변화",
    "antagonist": "적대자 위상 변화"
  }},
  "relationship_delta": [
    {{"target": "NPC이름", "delta": 0, "note": "변화 이유"}}
  ],
  "foreshadow": ["복선1"],
  "callback": ["회수된 복선"],
  "emotional_beat": {{"type": "triumph|setback|tension", "intensity": 7}},
  "tension_level": 7,
  "location": "장소",
  "time_span": {{"duration": "기간", "in_story_month": "YYYY-MM"}},
  "npcs_involved": ["NPC1", "NPC2"],
  "genre_ext": {{
    "capital_before": "{prev_capital}",
    "capital_after": "변화 후 자본",
    "capital_delta": "+/-금액",
    "investment_type": "주식|부동산|외환|협상",
    "method": "방법",
    "risk_level": "저|중|고|극고"
  }}
}}
```

JSON만 출력하세요.
"""

        response = self._call_llm(prompt, temperature=0.3)

        metadata = {}
        if response:
            try:
                json_str = response
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]
                metadata = json.loads(json_str.strip())
            except json.JSONDecodeError:
                pass

        # 기존 블록에 메타데이터 병합
        enriched = {"block_id": block["block_id"], "title": block["title"], "content": block["content"], **metadata}

        return enriched

    # ===========================================
    # 저장/로드
    # ===========================================

    def _save_progress(self, data: list, phase: int):
        """진행 상황 저장"""
        save_path = self.output_path.with_suffix(f".phase{phase}.json")
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 저장: {save_path}")

    def save_final(self, blocks: list):
        """최종 저장"""
        output = {
            "_schema_version": "2.0",
            "_bible_ref": self.bible_path.name,
            "work_name": self.bible.get("MasterBible", {})
            .get("ProjectData", {})
            .get("MetaInfo", {})
            .get("title", "미정"),
            "genre": self.genre,
            "total_blocks": len(blocks),
            "treatments": blocks,
        }

        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 최종 저장: {self.output_path}")
        print(f"   총 {len(blocks)}개 블록")

    # ===========================================
    # 메인 실행
    # ===========================================

    def run(self):
        """전체 파이프라인 실행"""
        print("\n" + "=" * 60)
        print("🚀 Treatment Builder 시작")
        print("=" * 60)

        # Bible 로드
        if not self.load_bible():
            return

        # 사용자 방향성 입력
        print("\n📌 스토리 방향성을 입력하세요 (선택사항)")
        print("   예: '주인공이 IMF를 이용해 100억을 만들고 복수하는 이야기'")
        print("   예: '초반에 고난, 중반에 성장, 후반에 복수'")
        user_direction = input("\n방향성 (엔터=AI 자유 생성): ").strip()

        # Phase 1: 뼈대
        skeleton = self.phase1_generate_skeleton(user_direction)
        if not skeleton:
            print("❌ 뼈대 생성 실패")
            return

        skeleton = self.phase1_review_skeleton(skeleton)
        self._save_progress(skeleton, phase=1)

        # Phase 2: 상세
        detailed = self.phase2_generate_details(skeleton)
        self._save_progress(detailed, phase=2)

        # Phase 3: 메타데이터
        enriched = self.phase3_extract_metadata(detailed)

        # 최종 저장
        self.save_final(enriched)

        print("\n🎉 완료!")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Treatment Builder")
    parser.add_argument("--bible", required=True, help="Bible JSON 파일 경로")
    parser.add_argument("--output", required=True, help="출력 Treatment JSON 경로")
    parser.add_argument("--genre", default="investment", help="장르 (기본: investment)")

    args = parser.parse_args()

    builder = TreatmentBuilder(bible_path=args.bible, output_path=args.output, genre=args.genre)
    builder.run()


if __name__ == "__main__":
    main()
