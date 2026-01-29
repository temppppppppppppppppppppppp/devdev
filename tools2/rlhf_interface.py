"""
[Phase 3] RLHF (Reinforcement Learning from Human Feedback) Interface

인간 편집자가 AI 평가를 리뷰하고 피드백을 제공하는 웹 인터페이스
Streamlit 기반
"""
import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime
from modules.core.data_collector import RLHFCollector


# 페이지 설정
st.set_page_config(
    page_title="RLHF Feedback Interface",
    page_icon="👤",
    layout="wide"
)

# 타이틀
st.title("👤 RLHF Feedback Interface")
st.markdown("AI 평가를 검토하고 인간 피드백을 제공하세요")

# 세션 상태 초기화
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'manuscripts' not in st.session_state:
    st.session_state.manuscripts = []
if 'feedback_submitted' not in st.session_state:
    st.session_state.feedback_submitted = False


# =================================================================
# 사이드바
# =================================================================

st.sidebar.header("Settings")
project_name = st.sidebar.text_input("Project Name", "default_project")
editor_name = st.sidebar.text_input("Your Name", "Editor")

# RLHF Collector 초기화
if 'rlhf_collector' not in st.session_state:
    st.session_state.rlhf_collector = RLHFCollector(project_name)


# =================================================================
# 데이터 로드
# =================================================================

@st.cache_data
def load_manuscripts_for_review(project_name):
    """리뷰할 원고 로드"""
    data_dir = Path("datasets") / project_name / "approved"

    if not data_dir.exists():
        return []

    manuscripts = []
    for file in sorted(data_dir.glob("*.json")):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                manuscripts.append(data)
        except Exception:
            continue

    return manuscripts


# 원고 로드
if st.sidebar.button("Load Manuscripts"):
    st.session_state.manuscripts = load_manuscripts_for_review(project_name)
    st.session_state.current_index = 0
    st.sidebar.success(f"Loaded {len(st.session_state.manuscripts)} manuscripts")

# 통계
st.sidebar.markdown("---")
st.sidebar.markdown("### Progress")
if st.session_state.manuscripts:
    st.sidebar.progress(
        st.session_state.current_index / len(st.session_state.manuscripts)
    )
    st.sidebar.text(
        f"{st.session_state.current_index + 1} / {len(st.session_state.manuscripts)}"
    )


# =================================================================
# 메인 인터페이스
# =================================================================

if not st.session_state.manuscripts:
    st.info("👈 Load manuscripts from the sidebar to start reviewing")
    st.stop()

# 현재 원고
current_ms = st.session_state.manuscripts[st.session_state.current_index]
ep_num = current_ms.get('ep_num', 0)
manuscript = current_ms.get('manuscript', '')
validation_result = current_ms.get('validation_result', {})

# AI 평가 결과
v0128_result = validation_result.get('v0128_full_result', validation_result)
ai_score = v0128_result.get('total_score', validation_result.get('score', 0))
ai_decision = validation_result.get('final_decision', validation_result.get('decision', ''))

# 레이아웃
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"📝 Episode {ep_num}")
    st.markdown("---")

    # 원고 표시
    with st.expander("📖 Manuscript", expanded=True):
        st.text_area(
            "Content",
            manuscript,
            height=400,
            disabled=True,
            label_visibility="collapsed"
        )

    # 통계
    st.markdown(f"**Length:** {len(manuscript):,} characters")

with col2:
    st.subheader("🤖 AI Evaluation")

    # AI 평가 결과
    st.metric("AI Score", f"{ai_score}/100")
    st.metric("AI Decision", ai_decision)

    # 세부 점수
    with st.expander("Detailed Scores"):
        breakdown = v0128_result.get('scoring_result', {}).get('breakdown', {})

        if breakdown:
            for category, data in breakdown.items():
                if isinstance(data, dict):
                    score = data.get('score', 0)
                    max_score = data.get('max', 100)
                    st.text(f"{category}: {score}/{max_score}")
        else:
            st.text("No detailed scores available")

    # AI 피드백
    with st.expander("AI Feedback"):
        feedback = validation_result.get('detailed_feedback', validation_result.get('feedback', ''))
        st.markdown(feedback if feedback else "No feedback available")

# =================================================================
# 인간 피드백 입력
# =================================================================

st.markdown("---")
st.subheader("👤 Your Evaluation")

col1, col2, col3 = st.columns(3)

with col1:
    human_score = st.slider(
        "Your Score",
        min_value=0,
        max_value=100,
        value=int(ai_score),
        step=5,
        help="AI와 다른 점수를 주셔도 됩니다"
    )

with col2:
    human_decision = st.selectbox(
        "Your Decision",
        ["APPROVE", "REVISE", "REJECT"],
        help="AI 판정과 다른 결정을 내리셔도 됩니다"
    )

with col3:
    score_diff = human_score - ai_score
    st.metric("Score Difference", f"{score_diff:+d}", "vs AI")

# 피드백 입력
human_feedback = st.text_area(
    "Your Feedback",
    placeholder="왜 AI와 다른 점수/판정을 내렸는지 설명해주세요...",
    height=150
)

# 제출
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("◀️ Previous"):
        if st.session_state.current_index > 0:
            st.session_state.current_index -= 1
            st.session_state.feedback_submitted = False
            st.rerun()

with col2:
    if st.button("✅ Submit Feedback", type="primary"):
        # 피드백 저장
        st.session_state.rlhf_collector.collect_feedback(
            ep_num=ep_num,
            manuscript=manuscript,
            ai_score=ai_score,
            human_score=human_score,
            human_feedback=human_feedback,
            human_decision=human_decision
        )

        st.session_state.feedback_submitted = True
        st.success("✅ Feedback submitted!")

        # 다음 원고로
        if st.session_state.current_index < len(st.session_state.manuscripts) - 1:
            st.session_state.current_index += 1
            st.session_state.feedback_submitted = False
            st.rerun()
        else:
            st.info("🎉 All manuscripts reviewed!")

with col3:
    if st.button("Skip ▶️"):
        if st.session_state.current_index < len(st.session_state.manuscripts) - 1:
            st.session_state.current_index += 1
            st.session_state.feedback_submitted = False
            st.rerun()


# =================================================================
# 불일치 분석
# =================================================================

st.markdown("---")
st.subheader("📊 Disagreement Analysis")

if st.button("Analyze AI vs Human"):
    analysis = st.session_state.rlhf_collector.analyze_disagreement()

    if 'error' not in analysis:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Feedback", analysis['total_feedback'])

        with col2:
            st.metric("Agreement Rate", f"{analysis['agreement_rate']:.1%}")

        with col3:
            st.metric("Avg Score Diff", f"{analysis['avg_score_difference']:+.1f}")

        # 세부 분석
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**AI Overestimated**")
            st.text(f"{analysis['overestimated_count']} cases")
            st.caption("AI gave higher scores than human")

        with col2:
            st.markdown("**AI Underestimated**")
            st.text(f"{analysis['underestimated_count']} cases")
            st.caption("AI gave lower scores than human")

        # Export
        if st.button("Export RLHF Data"):
            filepath = st.session_state.rlhf_collector.export_for_rlhf()
            st.success(f"Exported to: {filepath}")
    else:
        st.warning(analysis['error'])


# =================================================================
# 통계 대시보드
# =================================================================

st.markdown("---")
st.subheader("📈 Statistics")

# 통계 로드
rlhf_dir = Path("rlhf_data") / project_name
if rlhf_dir.exists():
    feedback_files = list(rlhf_dir.glob("feedback_*.json"))

    if feedback_files:
        feedback_data = []
        for file in feedback_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    feedback_data.append(data)
            except Exception:
                continue

        if feedback_data:
            import pandas as pd
            df = pd.DataFrame(feedback_data)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Reviews", len(df))

            with col2:
                avg_human_score = df['human_score'].mean()
                st.metric("Avg Human Score", f"{avg_human_score:.1f}")

            with col3:
                avg_ai_score = df['ai_score'].mean()
                st.metric("Avg AI Score", f"{avg_ai_score:.1f}")

            # 점수 비교 차트
            import plotly.express as px

            fig = px.scatter(
                df,
                x='ai_score',
                y='human_score',
                title="AI Score vs Human Score",
                labels={'ai_score': 'AI Score', 'human_score': 'Human Score'},
                trendline="ols"
            )
            fig.add_shape(
                type="line",
                x0=0, y0=0, x1=100, y1=100,
                line=dict(color="red", dash="dash")
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No feedback data yet. Start reviewing to see statistics.")
else:
    st.info("No feedback directory found.")


# =================================================================
# 가이드라인
# =================================================================

with st.expander("📖 Review Guidelines"):
    st.markdown("""
    ### How to Provide Good Feedback

    **점수 기준:**
    - 85-100: 출판 가능한 최상급 품질
    - 70-84: 통과 가능, 소폭 개선 권장
    - 50-69: 재작성 필요
    - 0-49: 심각한 문제 있음

    **평가 항목:**
    1. **설정 일관성**: 캐릭터/세계관 오류 없음?
    2. **문장력**: 읽기 편하고 리듬감 있음?
    3. **감정 몰입**: 독자가 공감할 수 있음?
    4. **상업성**: 다음 화가 궁금함?
    5. **신선함**: 클리셰를 피했음?

    **피드백 작성:**
    - 구체적으로: "재미없음" → "절벽걸기가 약함, 후반부 전개 예측 가능"
    - 건설적으로: 문제 지적 + 개선 방향 제시
    - 일관되게: 동일 기준을 모든 원고에 적용

    **AI와 의견 차이 시:**
    - AI가 놓친 문제를 발견했다면 명확히 지적
    - AI가 과대/과소평가했다면 이유 설명
    - 당신의 피드백이 AI를 더 나은 평가자로 만듭니다!
    """)


# =================================================================
# 푸터
# =================================================================

st.markdown("---")
st.caption(f"Reviewer: {editor_name} | Project: {project_name}")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
