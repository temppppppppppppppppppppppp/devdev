"""
[Phase 3] Performance Dashboard

Streamlit 기반 실시간 성능 모니터링 대시보드
V0128 검증 시스템의 모든 지표를 시각화
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from pathlib import Path


# 페이지 설정
st.set_page_config(
    page_title="Geuldobi Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 타이틀
st.title("📊 Geuldobi V0128 Performance Dashboard")
st.markdown("실시간 검증 시스템 성능 모니터링")

# 사이드바
st.sidebar.header("Settings")
project_name = st.sidebar.text_input("Project Name", "default_project")
refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 5, 60, 10)
show_raw_data = st.sidebar.checkbox("Show Raw Data", False)


# =================================================================
# 데이터 로드 함수
# =================================================================

@st.cache_data(ttl=10)
def load_validation_data(project_name):
    """검증 데이터 로드"""
    data_dir = Path("datasets") / project_name / "approved"

    if not data_dir.exists():
        return pd.DataFrame()

    records = []
    for file in data_dir.glob("*.json"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                result = data.get('validation_result', {})
                v0128_result = result.get('v0128_full_result', result)

                records.append({
                    'ep_num': data.get('ep_num', 0),
                    'timestamp': data.get('timestamp', ''),
                    'decision': result.get('final_decision', result.get('decision', '')),
                    'total_score': v0128_result.get('total_score', result.get('score', 0)),
                    'manuscript_length': data.get('manuscript_length', 0),
                    'blocking_passed': v0128_result.get('blocking_result', {}).get('passed', True),
                    'scoring_passed': v0128_result.get('scoring_result', {}).get('passed', True),
                    'self_consistency_used': v0128_result.get('self_consistency_used', False)
                })
        except Exception as e:
            st.sidebar.error(f"Error loading {file.name}: {e}")
            continue

    if records:
        df = pd.DataFrame(records)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df

    return pd.DataFrame()


@st.cache_data(ttl=10)
def load_rejected_data(project_name):
    """거부된 원고 데이터 로드"""
    data_dir = Path("datasets") / project_name / "rejected"

    if not data_dir.exists():
        return pd.DataFrame()

    records = []
    for file in data_dir.glob("*.json"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                result = data.get('validation_result', {})

                records.append({
                    'ep_num': data.get('ep_num', 0),
                    'timestamp': data.get('timestamp', ''),
                    'score': result.get('total_score', result.get('score', 0)),
                    'reason': result.get('feedback', result.get('reason', ''))
                })
        except Exception:
            continue

    if records:
        df = pd.DataFrame(records)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df

    return pd.DataFrame()


# =================================================================
# 메인 대시보드
# =================================================================

# 데이터 로드
approved_df = load_validation_data(project_name)
rejected_df = load_rejected_data(project_name)

if approved_df.empty and rejected_df.empty:
    st.warning(f"No data found for project: {project_name}")
    st.info("데이터 수집을 시작하려면 DataCollector를 사용하세요.")
    st.code("""
from modules.core.data_collector import DataCollector

collector = DataCollector(project_name="your_project")
collector.collect_validation_result(ep_num, manuscript, result)
    """)
    st.stop()


# =================================================================
# KPI 카드
# =================================================================

col1, col2, col3, col4 = st.columns(4)

total_manuscripts = len(approved_df) + len(rejected_df)
approved_count = len(approved_df)
approval_rate = approved_count / total_manuscripts if total_manuscripts > 0 else 0
avg_score = approved_df['total_score'].mean() if not approved_df.empty else 0

with col1:
    st.metric("Total Manuscripts", f"{total_manuscripts:,}")

with col2:
    st.metric("Approved", f"{approved_count:,}", f"{approval_rate:.1%}")

with col3:
    st.metric("Average Score", f"{avg_score:.1f}", "/ 100")

with col4:
    st.metric("Rejected", f"{len(rejected_df):,}", f"{1-approval_rate:.1%}")


# =================================================================
# 점수 분포 및 트렌드
# =================================================================

st.markdown("---")
st.subheader("📈 Score Distribution & Trends")

col1, col2 = st.columns(2)

with col1:
    if not approved_df.empty:
        # 점수 분포 히스토그램
        fig_hist = px.histogram(
            approved_df,
            x='total_score',
            nbins=20,
            title="Score Distribution (Approved Manuscripts)",
            labels={'total_score': 'Score', 'count': 'Frequency'}
        )
        fig_hist.add_vline(x=70, line_dash="dash", line_color="red",
                          annotation_text="Pass Threshold (70)")
        fig_hist.add_vline(x=85, line_dash="dash", line_color="green",
                          annotation_text="Excellent (85)")
        st.plotly_chart(fig_hist, use_container_width=True)

with col2:
    if not approved_df.empty:
        # 시간별 점수 트렌드
        fig_trend = px.scatter(
            approved_df.sort_values('timestamp'),
            x='timestamp',
            y='total_score',
            title="Score Trend Over Time",
            labels={'total_score': 'Score', 'timestamp': 'Date'},
            trendline="lowess"
        )
        fig_trend.add_hline(y=70, line_dash="dash", line_color="red")
        fig_trend.add_hline(y=85, line_dash="dash", line_color="green")
        st.plotly_chart(fig_trend, use_container_width=True)


# =================================================================
# 검증 단계별 통과율
# =================================================================

st.markdown("---")
st.subheader("🎯 Validation Tier Pass Rates")

if not approved_df.empty:
    col1, col2, col3 = st.columns(3)

    with col1:
        blocking_pass_rate = approved_df['blocking_passed'].mean()
        st.metric(
            "TIER 1: BLOCKING",
            f"{blocking_pass_rate:.1%}",
            "Hard constraints"
        )

    with col2:
        scoring_pass_rate = approved_df['scoring_passed'].mean()
        st.metric(
            "TIER 2: SCORING",
            f"{scoring_pass_rate:.1%}",
            "Quality metrics"
        )

    with col3:
        sc_usage = approved_df['self_consistency_used'].mean()
        st.metric(
            "Self-Consistency Usage",
            f"{sc_usage:.1%}",
            "3-vote majority"
        )


# =================================================================
# 점수 세부 분석
# =================================================================

st.markdown("---")
st.subheader("📊 Detailed Score Analysis")

if not approved_df.empty:
    # 점수 범위별 분포
    score_ranges = pd.cut(
        approved_df['total_score'],
        bins=[0, 70, 85, 100],
        labels=['Below Pass (0-69)', 'Pass (70-84)', 'Excellent (85-100)']
    )

    range_counts = score_ranges.value_counts()

    fig_pie = px.pie(
        values=range_counts.values,
        names=range_counts.index,
        title="Score Range Distribution",
        color_discrete_sequence=px.colors.sequential.RdYlGn
    )
    st.plotly_chart(fig_pie, use_container_width=True)


# =================================================================
# 거부 사유 분석
# =================================================================

if not rejected_df.empty:
    st.markdown("---")
    st.subheader("❌ Rejection Analysis")

    col1, col2 = st.columns(2)

    with col1:
        # 거부된 원고 점수 분포
        fig_rejected = px.histogram(
            rejected_df,
            x='score',
            nbins=15,
            title="Rejected Manuscripts Score Distribution",
            labels={'score': 'Score', 'count': 'Frequency'}
        )
        fig_rejected.add_vline(x=70, line_dash="dash", line_color="red")
        st.plotly_chart(fig_rejected, use_container_width=True)

    with col2:
        # 거부 사유 워드클라우드 (간단 버전)
        st.markdown("**Common Rejection Reasons:**")
        reasons = rejected_df['reason'].value_counts().head(5)
        for reason, count in reasons.items():
            st.text(f"• {reason[:50]}... ({count})")


# =================================================================
# 원고 길이 vs 점수 상관관계
# =================================================================

st.markdown("---")
st.subheader("📏 Manuscript Length vs Score Correlation")

if not approved_df.empty:
    fig_scatter = px.scatter(
        approved_df,
        x='manuscript_length',
        y='total_score',
        title="Length vs Quality",
        labels={'manuscript_length': 'Length (characters)', 'total_score': 'Score'},
        trendline="ols",
        color='decision',
        hover_data=['ep_num']
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    # 상관계수 표시
    correlation = approved_df['manuscript_length'].corr(approved_df['total_score'])
    st.info(f"Correlation: {correlation:.3f}")


# =================================================================
# 최근 활동 로그
# =================================================================

st.markdown("---")
st.subheader("📝 Recent Activity")

if not approved_df.empty:
    recent = approved_df.sort_values('timestamp', ascending=False).head(10)

    st.dataframe(
        recent[['ep_num', 'timestamp', 'decision', 'total_score', 'manuscript_length']],
        use_container_width=True
    )


# =================================================================
# Raw Data 표시 (옵션)
# =================================================================

if show_raw_data:
    st.markdown("---")
    st.subheader("🔍 Raw Data")

    tab1, tab2 = st.tabs(["Approved", "Rejected"])

    with tab1:
        st.dataframe(approved_df, use_container_width=True)

    with tab2:
        st.dataframe(rejected_df, use_container_width=True)


# =================================================================
# Export 기능
# =================================================================

st.markdown("---")
st.subheader("💾 Export Data")

col1, col2 = st.columns(2)

with col1:
    if st.button("Export Approved to CSV"):
        csv = approved_df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            f"{project_name}_approved.csv",
            "text/csv"
        )

with col2:
    if st.button("Export Rejected to CSV"):
        csv = rejected_df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            f"{project_name}_rejected.csv",
            "text/csv"
        )


# =================================================================
# 자동 새로고침
# =================================================================

st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 자동 새로고침 버튼 (무한 루프 방지)
if st.sidebar.checkbox("Enable Auto-Refresh", value=False):
    st.caption(f"⚠️ Auto-refresh enabled ({refresh_interval}s) - 성능 영향 있을 수 있음")
    import time
    time.sleep(refresh_interval)
    st.rerun()
else:
    st.caption("💡 Auto-refresh는 사이드바에서 활성화할 수 있습니다")
    st.caption("수동 새로고침: F5 또는 브라우저 새로고침")
