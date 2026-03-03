#!/bin/bash
cd /c/Users/User/Desktop/글도비
FINDINGS="docs/codex_findings_v2.md"
MAX_CHECKS=36  # 30분 × 36 = 18시간
CHECK_INTERVAL=1800  # 30분

for i in $(seq 1 $MAX_CHECKS); do
    sleep $CHECK_INTERVAL

    if [ ! -f "$FINDINGS" ]; then
        echo "[CHECK $i] $(date +%H:%M) — 파일 미생성"
        continue
    fi

    LINES=$(wc -l < "$FINDINGS")
    # 통계 줄에서 총 발견 수 추출
    TOTAL_BUGS=$(grep -oP '총 발견: \K[0-9]+' "$FINDINGS" 2>/dev/null || echo "?")
    # 라운드 진행 수 추출
    ROUND_PROGRESS=$(grep -oP '라운드 진행: \K[0-9]+' "$FINDINGS" 2>/dev/null || echo "?")
    # 완료된 라운드 수 (## Round N 완료 패턴)
    COMPLETED=$(grep -c "## Round .* 완료" "$FINDINGS" 2>/dev/null || echo "0")
    # 자체 검증 결과 존재 여부
    HAS_SELF_CHECK=$(grep -c "자체 검증 결과" "$FINDINGS" 2>/dev/null || echo "0")

    echo "[CHECK $i] $(date +%H:%M) — ${LINES}줄, 라운드 진행: ${ROUND_PROGRESS}/100, 완료 태그: ${COMPLETED}개, 총 발견: ${TOTAL_BUGS}건"

    # 100라운드 완료 판정: 완료 태그 95개 이상 + 자체 검증 존재
    if [ "$COMPLETED" -ge 95 ] && [ "$HAS_SELF_CHECK" -ge 1 ]; then
        echo "===== CODEX 100라운드 작업 완료 감지! ====="
        echo "최종: ${LINES}줄, 완료 라운드: ${COMPLETED}개, 총 발견: ${TOTAL_BUGS}건"
        echo ""
        echo "=== 발견된 버그 목록 ==="
        grep -n '### \[CRITICAL\|### \[HIGH\|### \[MEDIUM' "$FINDINGS" 2>/dev/null
        echo ""
        echo "=== 5-D 읽기 증명 통계 ==="
        echo "5-D 섹션 수: $(grep -c '### 5-D' "$FINDINGS" 2>/dev/null || echo 0)"
        echo "마지막 함수 항목: $(grep -c '마지막 함수' "$FINDINGS" 2>/dev/null || echo 0)"
        echo "특징적 문자열 항목: $(grep -c '특징적 문자열' "$FINDINGS" 2>/dev/null || echo 0)"
        echo ""
        echo "=== 자체 검증 결과 ==="
        grep -A 10 "자체 검증 결과" "$FINDINGS" 2>/dev/null
        exit 0
    fi
done

echo "===== 타임아웃: ${MAX_CHECKS}회 체크 완료, 아직 미완성 ====="
COMPLETED=$(grep -c "## Round .* 완료" "$FINDINGS" 2>/dev/null || echo "0")
echo "현재 완료 라운드: ${COMPLETED}/100"
