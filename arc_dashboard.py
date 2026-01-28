# -*- coding: utf-8 -*-
"""
[V40.1] Arc 시각화 대시보드
Streamlit 기반 Arc 편집기
실행: streamlit run arc_dashboard.py
"""

import streamlit as st
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="Arc Dashboard",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .arc-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .arc-card-header {
        font-size: 1.3em;
        font-weight: bold;
        margin-bottom: 10px;
        border-bottom: 2px solid #4a9eff;
        padding-bottom: 8px;
    }
    .arc-card-info {
        font-size: 0.9em;
        opacity: 0.9;
    }
    .volume-header {
        background: linear-gradient(90deg, #4a9eff, #1e3a5f);
        padding: 15px 20px;
        border-radius: 8px;
        color: white;
        font-size: 1.4em;
        font-weight: bold;
        margin: 20px 0 15px 0;
    }
    .stButton > button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


class ArcDashboard:
    def __init__(self):
        self.projects_dir = Path("projects")

    def get_project_list(self):
        """프로젝트 목록 반환"""
        if not self.projects_dir.exists():
            return []
        return [p.name for p in self.projects_dir.iterdir()
                if p.is_dir() and (p / "project_data.db").exists()]

    def load_arcs(self, project_name):
        """DB에서 Arc 데이터 로드"""
        db_path = self.projects_dir / project_name / "project_data.db"
        if not db_path.exists():
            return []

        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT data FROM anchors WHERE key = 'arcs'")
            row = cursor.fetchone()
            conn.close()

            if row:
                return json.loads(row['data'])
            return []
        except Exception as e:
            st.error(f"Arc 로드 실패: {e}")
            return []

    def save_arcs(self, project_name, arcs_data):
        """Arc 데이터를 DB에 저장"""
        db_path = self.projects_dir / project_name / "project_data.db"

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            json_data = json.dumps(arcs_data, ensure_ascii=False)
            cursor.execute("""
                INSERT OR REPLACE INTO anchors (key, data, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, ('arcs', json_data))

            conn.commit()
            conn.close()

            # txt 파일도 저장
            self._save_arcs_to_txt(project_name, arcs_data)

            return True
        except Exception as e:
            st.error(f"저장 실패: {e}")
            return False

    def _save_arcs_to_txt(self, project_name, arcs_data):
        """Arc txt 파일 저장"""
        plans_dir = self.projects_dir / project_name / "plans" / "arcs"
        plans_dir.mkdir(parents=True, exist_ok=True)

        for arc in arcs_data:
            if not isinstance(arc, dict):
                continue

            arc_no = arc.get('arc_no', arc.get('global_arc_no', 0))
            if not arc_no:
                continue

            filename = f"arc_{arc_no:03d}.txt"
            filepath = plans_dir / filename

            lines = [
                f"{'='*60}",
                f"ARC {arc_no}",
                f"{'='*60}",
                f"",
                f"[기본 정보]",
                f"- 볼륨: {arc.get('volume_no', 'N/A')}",
                f"- 에피소드 범위: {arc.get('ep_start', 'N/A')} ~ {arc.get('ep_end', 'N/A')}",
                f"- 에피소드 수: {arc.get('ep_count', 'N/A')}",
                f"",
                f"[전술 문서 (Tactical Doc)]",
                f"{'-'*40}",
                f"{arc.get('tactical_doc', '내용 없음')}",
                f"",
                f"[비트 시퀀스 (Beat Sequence)]",
                f"{'-'*40}",
            ]

            beat_seq = arc.get('beat_sequence', [])
            if isinstance(beat_seq, list):
                for i, beat in enumerate(beat_seq, 1):
                    if isinstance(beat, dict):
                        lines.append(f"Beat {i}: {beat.get('beat', beat.get('description', str(beat)))}")
                    else:
                        lines.append(f"Beat {i}: {beat}")

            filepath.write_text('\n'.join(lines), encoding='utf-8')


def render_arc_card(arc, idx):
    """Arc 카드 렌더링"""
    arc_no = arc.get('arc_no', arc.get('global_arc_no', idx + 1))
    volume_no = arc.get('volume_no', '?')
    ep_start = arc.get('ep_start', '?')
    ep_end = arc.get('ep_end', '?')
    ep_count = arc.get('ep_count', '?')
    tactical_doc = arc.get('tactical_doc', '')

    # 전술 문서 미리보기 (처음 150자)
    preview = tactical_doc[:150] + "..." if len(tactical_doc) > 150 else tactical_doc

    st.markdown(f"""
    <div class="arc-card">
        <div class="arc-card-header">Arc {arc_no}</div>
        <div class="arc-card-info">
            <strong>Vol {volume_no}</strong> |
            EP {ep_start} ~ {ep_end} ({ep_count}화)
        </div>
        <div style="margin-top: 10px; font-size: 0.85em; opacity: 0.8;">
            {preview}
        </div>
    </div>
    """, unsafe_allow_html=True)

    return st.button(f"편집 Arc {arc_no}", key=f"edit_{idx}")


def render_arc_editor(arc, idx):
    """Arc 편집 폼"""
    st.subheader(f"Arc {arc.get('arc_no', idx + 1)} 편집")

    col1, col2 = st.columns(2)

    with col1:
        volume_no = st.number_input("볼륨 번호", value=arc.get('volume_no', 1), min_value=1, key=f"vol_{idx}")
        ep_start = st.number_input("시작 에피소드", value=arc.get('ep_start', 1), min_value=1, key=f"eps_{idx}")
        ep_end = st.number_input("종료 에피소드", value=arc.get('ep_end', 10), min_value=1, key=f"epe_{idx}")

    with col2:
        arc_no = st.number_input("Arc 번호", value=arc.get('arc_no', arc.get('global_arc_no', idx + 1)), min_value=1, key=f"arcno_{idx}")
        ep_count = ep_end - ep_start + 1
        st.metric("에피소드 수", ep_count)

    st.markdown("---")

    tactical_doc = st.text_area(
        "전술 문서 (Tactical Doc)",
        value=arc.get('tactical_doc', ''),
        height=300,
        key=f"tactical_{idx}"
    )

    st.markdown("---")
    st.markdown("**비트 시퀀스**")

    beat_seq = arc.get('beat_sequence', [])
    beat_text = ""
    if isinstance(beat_seq, list):
        for beat in beat_seq:
            if isinstance(beat, dict):
                beat_text += beat.get('beat', beat.get('description', str(beat))) + "\n"
            else:
                beat_text += str(beat) + "\n"
    elif isinstance(beat_seq, str):
        beat_text = beat_seq

    new_beats = st.text_area(
        "비트 (줄바꿈으로 구분)",
        value=beat_text.strip(),
        height=150,
        key=f"beats_{idx}"
    )

    return {
        'arc_no': arc_no,
        'global_arc_no': arc_no,
        'volume_no': volume_no,
        'ep_start': ep_start,
        'ep_end': ep_end,
        'ep_count': ep_count,
        'tactical_doc': tactical_doc,
        'beat_sequence': [{'beat': b.strip()} for b in new_beats.split('\n') if b.strip()],
        # 기존 데이터 유지
        'seed_injection': arc.get('seed_injection', []),
        'seeds': arc.get('seeds', [])
    }


def main():
    st.title("📚 Arc Dashboard")
    st.caption("Arc 시각화 및 편집 도구")

    dashboard = ArcDashboard()

    # 사이드바: 프로젝트 선택
    with st.sidebar:
        st.header("프로젝트 선택")

        projects = dashboard.get_project_list()
        if not projects:
            st.warning("프로젝트가 없습니다.")
            return

        selected_project = st.selectbox("프로젝트", projects)

        st.markdown("---")

        if st.button("🔄 새로고침"):
            st.rerun()

        st.markdown("---")
        st.markdown("**사용법**")
        st.markdown("""
        1. 프로젝트 선택
        2. Arc 카드에서 [편집] 클릭
        3. 내용 수정
        4. [저장] 클릭
        """)

    # Arc 데이터 로드
    arcs = dashboard.load_arcs(selected_project)

    if not arcs:
        st.info(f"'{selected_project}' 프로젝트에 Arc 데이터가 없습니다.")
        st.markdown("Stage 2 (Arc Tactical Design)를 먼저 실행해주세요.")
        return

    # 세션 상태 초기화
    if 'editing_arc' not in st.session_state:
        st.session_state.editing_arc = None
    if 'arcs_data' not in st.session_state:
        st.session_state.arcs_data = arcs.copy()

    # 프로젝트 변경 시 데이터 리로드
    if 'current_project' not in st.session_state or st.session_state.current_project != selected_project:
        st.session_state.current_project = selected_project
        st.session_state.arcs_data = arcs.copy()
        st.session_state.editing_arc = None

    # 메인 영역
    if st.session_state.editing_arc is not None:
        # 편집 모드
        idx = st.session_state.editing_arc
        arc = st.session_state.arcs_data[idx]

        col1, col2 = st.columns([3, 1])
        with col1:
            updated_arc = render_arc_editor(arc, idx)

        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)

            if st.button("💾 저장", type="primary"):
                st.session_state.arcs_data[idx] = updated_arc
                if dashboard.save_arcs(selected_project, st.session_state.arcs_data):
                    st.success("저장 완료!")
                    st.balloons()

            if st.button("❌ 취소"):
                st.session_state.editing_arc = None
                st.rerun()

            st.markdown("---")

            if st.button("🗑️ 이 Arc 삭제", type="secondary"):
                if st.session_state.get('confirm_delete'):
                    del st.session_state.arcs_data[idx]
                    dashboard.save_arcs(selected_project, st.session_state.arcs_data)
                    st.session_state.editing_arc = None
                    st.session_state.confirm_delete = False
                    st.rerun()
                else:
                    st.session_state.confirm_delete = True
                    st.warning("다시 클릭하면 삭제됩니다!")

    else:
        # 목록 모드
        st.markdown(f"### {selected_project}")
        st.markdown(f"총 **{len(st.session_state.arcs_data)}개** Arc")

        # 볼륨별로 그룹화
        volumes = {}
        for idx, arc in enumerate(st.session_state.arcs_data):
            vol = arc.get('volume_no', 1)
            if vol not in volumes:
                volumes[vol] = []
            volumes[vol].append((idx, arc))

        # 볼륨별 렌더링
        for vol_no in sorted(volumes.keys()):
            st.markdown(f'<div class="volume-header">📖 Volume {vol_no}</div>', unsafe_allow_html=True)

            cols = st.columns(3)
            for i, (idx, arc) in enumerate(volumes[vol_no]):
                with cols[i % 3]:
                    if render_arc_card(arc, idx):
                        st.session_state.editing_arc = idx
                        st.session_state.confirm_delete = False
                        st.rerun()

        # 하단 액션
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("➕ 새 Arc 추가"):
                last_arc = st.session_state.arcs_data[-1] if st.session_state.arcs_data else {}
                new_arc = {
                    'arc_no': len(st.session_state.arcs_data) + 1,
                    'global_arc_no': len(st.session_state.arcs_data) + 1,
                    'volume_no': last_arc.get('volume_no', 1),
                    'ep_start': last_arc.get('ep_end', 0) + 1,
                    'ep_end': last_arc.get('ep_end', 0) + 10,
                    'ep_count': 10,
                    'tactical_doc': '',
                    'beat_sequence': []
                }
                st.session_state.arcs_data.append(new_arc)
                st.session_state.editing_arc = len(st.session_state.arcs_data) - 1
                st.rerun()

        with col2:
            if st.button("💾 전체 저장"):
                if dashboard.save_arcs(selected_project, st.session_state.arcs_data):
                    st.success("모든 Arc 저장 완료!")


if __name__ == "__main__":
    main()
