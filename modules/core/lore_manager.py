import json
import re

class LoreManager:
    """[V23.5 Optimized] SQLite 성능 + V20 정밀 병합 로직 결합"""

    def __init__(self, context):
        self.context = context
        self.db = context.db
        
        # 페르소나/말투는 성경 JSON의 정수를 그대로 상속
        bible = self.context.master_bible.get('MasterBible', self.context.master_bible)
        self.assets = bible.get('AssetLibrary', bible.get('asset_library', {}))
        self.persona_desc = self.assets.get('Persona', "")
        self.speech_style = self.assets.get('SpeechStyle', self.assets.get('persona', {}))

    def get_v20_fact_sheet(self, context_text):
        """[Stage 4] 맥락 매칭 로어 + 상세 페르소나 가이드 결합"""
        if not context_text: return ""
        info = []
        
        # 1. 페르소나 지침 복구
        if self.persona_desc or self.speech_style:
            tone = self.speech_style.get('tone', '격조 있는 무인')
            keywords = self.speech_style.get('Keywords', self.speech_style.get('words', []))
            info.append(f"[👤 페르소나 가이드]\n- 성격: {self.persona_desc}\n- 말투 톤: {tone}\n- 핵심 키워드: {', '.join(keywords)}")

        # 2. DB 기반 관련 로어 고속 인출
        all_lore = self.db.get_lore_list_by_category(None)
        for lore in all_lore:
            item_name = lore['item']
            if item_name and item_name.lower() in context_text.lower():
                info.append(f"[{lore.get('category', '정보')}: {item_name}] {lore['description']}")

        return "\n[⚠️ V20 절대 준수 FACT SHEET]\n" + "\n".join(info) if info else ""

    def update_v20_assets(self, new_lore_data):
        """[Sovereign Sync] 정규화 및 길이 비교 기반 DB 일괄 박제"""
        if not new_lore_data: return
        
        # 현재 DB 상태와 비교하여 중복 방지 및 정보 보강(더 긴 설명 우선)
        current_db_lore = {l['item'].replace(" ", "").lower(): l for l in self.db.get_lore_list_by_category(None)}
        lore_batch = []
        added_cnt, updated_cnt = 0, 0

        for category, items in new_lore_data.items():
            for name, desc in items.items():
                clean_name = name.replace(" ", "").lower()
                if clean_name in current_db_lore:
                    if len(desc) > len(current_db_lore[clean_name].get('description', '')):
                        lore_batch.append((category, name, desc))
                        updated_cnt += 1
                else:
                    lore_batch.append((category, name, desc))
                    added_cnt += 1
        
        if lore_batch:
            self.db.update_lore_items_batch(lore_batch)
            print(f"      📚 [Librarian] 설정 동기화 완료: 신규 {added_cnt}건 / 보강 {updated_cnt}건")

    def get_persona_prompt(self):
        """말투 예시(Suffix) 인출"""
        suffix = self.speech_style.get('Suffix', self.speech_style.get('suffix', []))
        return f"[🗣️ 말투 예시]: " + " / ".join(suffix) if suffix else ""