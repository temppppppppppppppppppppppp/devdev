# Treatment 전수조사 오더 (Sonnet TF)

> 대상: `treatments/` 내 8개 TR JSON (각 70블록)
> 실행: 각 파일별 독립 세션에서 병렬 수행
> 모델: Claude Sonnet

---

## 실행 명령 (터미널 8개에서 각각)

```bash
# 1. aegis_city
claude -p "아래 지시에 따라 감사하세요. 파일: treatments/aegis_city_tr_block_070_draft.json $(cat treatments/_audit_instructions.md)" --model sonnet

# 2. aurora_media
claude -p "아래 지시에 따라 감사하세요. 파일: treatments/aurora_media_tr_block_070_draft.json $(cat treatments/_audit_instructions.md)" --model sonnet

# 3. dynasty_heir
claude -p "아래 지시에 따라 감사하세요. 파일: treatments/dynasty_heir_possession_tr_block_070_draft.json $(cat treatments/_audit_instructions.md)" --model sonnet

# 4. empire_reborn
claude -p "아래 지시에 따라 감사하세요. 파일: treatments/empire_reborn_tr_block_070_draft.json $(cat treatments/_audit_instructions.md)" --model sonnet

# 5. entertainment_ceo
claude -p "아래 지시에 따라 감사하세요. 파일: treatments/entertainment_ceo_possession_tr_block_070_draft.json $(cat treatments/_audit_instructions.md)" --model sonnet

# 6. franchise_tycoon
claude -p "아래 지시에 따라 감사하세요. 파일: treatments/franchise_tycoon_possession_tr_block_070_draft.json $(cat treatments/_audit_instructions.md)" --model sonnet

# 7. northstar_logistics
claude -p "아래 지시에 따라 감사하세요. 파일: treatments/northstar_logistics_tr_block_070_draft.json $(cat treatments/_audit_instructions.md)" --model sonnet

# 8. quantum_bio
claude -p "아래 지시에 따라 감사하세요. 파일: treatments/quantum_bio_tr_block_070_draft.json $(cat treatments/_audit_instructions.md)" --model sonnet
```

---

## 대상 파일 목록

| # | 파일명 | 작품 | 장르 |
|---|--------|------|------|
| 1 | `aegis_city_tr_block_070_draft.json` | 이지스 시티 | 투자물 |
| 2 | `aurora_media_tr_block_070_draft.json` | 오로라 미디어 | 투자물 |
| 3 | `dynasty_heir_possession_tr_block_070_draft.json` | 왕조의 후계자 빙의 | 투자물+빙의 |
| 4 | `empire_reborn_tr_block_070_draft.json` | 제국 재건 | 투자물 |
| 5 | `entertainment_ceo_possession_tr_block_070_draft.json` | 엔터 CEO 빙의 | 투자물+빙의 |
| 6 | `franchise_tycoon_possession_tr_block_070_draft.json` | 프랜차이즈 타이쿤 빙의 | 투자물+빙의 |
| 7 | `northstar_logistics_tr_block_070_draft.json` | 노스스타 물류 | 투자물 |
| 8 | `quantum_bio_tr_block_070_draft.json` | 퀀텀 바이오 | 투자물 |

---

## 완료 후 취합

리포트가 8개 나오면 Opus에게:
> "treatments/audit_reports/ 안의 8개 리포트 취합해서 종합 요약 만들어줘"
