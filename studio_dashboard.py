# -*- coding: utf-8 -*-
"""
[V40.1] 글도비 Studio - 통합 대시보드
노드 기반 모던 다크 테마
실행: streamlit run studio_dashboard.py
"""

import streamlit as st
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import time

# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(
    page_title="글도비 Studio",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 모던 다크 테마 CSS (가독성 개선)
# ============================================================
st.markdown("""
<style>
    /* 메인 배경 */
    .stApp {
        background: linear-gradient(180deg, #0e1117 0%, #1a1a2e 50%, #16213e 100%);
    }

    /* 전체 텍스트 색상 - 흰색으로 가독성 향상 */
    .stApp, .stApp p, .stApp span, .stApp label, .stApp div {
        color: #ffffff !important;
    }

    /* 캡션/부제목 */
    .stApp .stCaption, small, .stApp small {
        color: #b8c5d6 !important;
    }

    /* 사이드바 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%);
        border-right: 1px solid #2d2d44;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    /* 장르 선택 강조 */
    .genre-selector {
        background: linear-gradient(135deg, #7c3aed 0%, #4a9eff 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        border: 2px solid #9d5cff;
        box-shadow: 0 0 20px rgba(124, 58, 237, 0.4);
    }
    .genre-title {
        font-size: 1.4em !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        text-shadow: 0 0 10px rgba(255,255,255,0.5);
        margin-bottom: 15px;
    }

    /* 라디오 버튼 강조 */
    [data-testid="stSidebar"] .stRadio > label {
        font-size: 1.1em !important;
        font-weight: 600 !important;
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stRadio > div {
        background: rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 10px;
    }

    /* 노드 카드 스타일 */
    .node-card {
        background: linear-gradient(135deg, #1e2140 0%, #2a2d4a 100%);
        border: 1px solid #3d4167;
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        transition: all 0.3s ease;
    }
    .node-card:hover {
        border-color: #4a9eff;
        box-shadow: 0 8px 32px rgba(74, 158, 255, 0.2);
        transform: translateY(-2px);
    }
    .node-card * {
        color: #ffffff !important;
    }

    /* 노드 헤더 */
    .node-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 15px;
        padding-bottom: 12px;
        border-bottom: 2px solid #4a9eff;
    }
    .node-title {
        font-size: 1.2em;
        font-weight: 600;
        color: #ffffff !important;
    }
    .node-badge {
        background: linear-gradient(90deg, #4a9eff, #7c3aed);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75em;
        color: white !important;
    }

    /* Arc 카드 */
    .arc-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        border: 1px solid #4a9eff;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        color: white !important;
        box-shadow: 0 4px 16px rgba(74, 158, 255, 0.15);
        transition: all 0.3s ease;
    }
    .arc-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(74, 158, 255, 0.25);
    }
    .arc-card * {
        color: #ffffff !important;
    }

    /* 볼륨 헤더 */
    .volume-header {
        background: linear-gradient(90deg, #4a9eff 0%, #7c3aed 100%);
        padding: 12px 20px;
        border-radius: 8px;
        color: white !important;
        font-size: 1.1em;
        font-weight: 600;
        margin: 25px 0 15px 0;
        box-shadow: 0 4px 16px rgba(74, 158, 255, 0.3);
    }

    /* 진행 상태 아이콘 */
    .status-complete { color: #00d4aa !important; }
    .status-progress { color: #ffa726 !important; }
    .status-pending { color: #b8c5d6 !important; }
    .status-skip { color: #7c3aed !important; }

    /* API 사용량 박스 */
    .api-usage-box {
        background: linear-gradient(135deg, #2d1b4e 0%, #1a1a2e 100%);
        border: 1px solid #7c3aed;
        border-radius: 12px;
        padding: 15px;
        margin-top: 20px;
    }
    .api-usage-box * {
        color: #ffffff !important;
    }

    /* 로그 박스 */
    .log-box {
        background: #0a0a0f;
        border: 1px solid #2d2d44;
        border-radius: 8px;
        padding: 15px;
        font-family: 'Consolas', monospace;
        font-size: 0.85em;
        color: #ffffff !important;
        max-height: 200px;
        overflow-y: auto;
    }
    .log-info { color: #4a9eff !important; }
    .log-success { color: #00d4aa !important; }
    .log-warning { color: #ffa726 !important; }
    .log-error { color: #ff5252 !important; }

    /* HUD 카드 */
    .hud-card {
        background: linear-gradient(135deg, #1a2744 0%, #243b55 100%);
        border: 1px solid #3d5a80;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
    }
    .hud-card * {
        color: #ffffff !important;
    }

    /* 버튼 스타일 */
    .stButton > button {
        background: linear-gradient(135deg, #4a9eff 0%, #7c3aed 100%);
        border: none;
        border-radius: 8px;
        color: white !important;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        box-shadow: 0 4px 16px rgba(74, 158, 255, 0.4);
        transform: translateY(-1px);
    }

    /* 텍스트 영역 */
    .stTextArea textarea {
        background: #1a1a2e !important;
        border: 1px solid #3d4167 !important;
        border-radius: 8px;
        color: #ffffff !important;
    }
    .stTextArea label {
        color: #ffffff !important;
    }

    /* 텍스트 입력 */
    .stTextInput input {
        background: #1a1a2e !important;
        border: 1px solid #3d4167 !important;
        color: #ffffff !important;
    }
    .stTextInput label {
        color: #ffffff !important;
    }

    /* 셀렉트 박스 */
    .stSelectbox > div > div {
        background: #1a1a2e !important;
        border-color: #3d4167 !important;
        color: #ffffff !important;
    }
    .stSelectbox label {
        color: #ffffff !important;
    }

    /* 넘버 인풋 */
    .stNumberInput input {
        background: #1a1a2e !important;
        border: 1px solid #3d4167 !important;
        color: #ffffff !important;
    }
    .stNumberInput label {
        color: #ffffff !important;
    }

    /* 메트릭 */
    [data-testid="stMetricValue"] {
        color: #4a9eff !important;
    }
    [data-testid="stMetricLabel"] {
        color: #ffffff !important;
    }

    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background: #1e2140;
        border: 1px solid #3d4167;
        border-radius: 8px;
        color: #ffffff !important;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4a9eff 0%, #7c3aed 100%);
        border-color: #4a9eff;
        color: white !important;
    }

    /* 구분선 */
    hr {
        border-color: #2d2d44;
    }

    /* 익스팬더 - 검은 배경 흰 글씨 강제 */
    .streamlit-expanderHeader {
        background: #0a0a0f !important;
        border: 1px solid #3d4167;
        border-radius: 8px;
        color: #ffffff !important;
    }
    .streamlit-expanderContent {
        background: #0a0a0f !important;
        border: 1px solid #3d4167;
        color: #ffffff !important;
    }
    .streamlit-expanderContent * {
        color: #ffffff !important;
        background: transparent !important;
    }
    .streamlit-expanderContent pre {
        background: #1a1a2e !important;
        color: #ffffff !important;
    }

    /* Block 카드 */
    .block-card {
        background: #0f0f1a !important;
        border: 1px solid #3d4167;
        border-radius: 8px;
        padding: 15px;
        margin: 8px 0;
        color: #ffffff !important;
    }
    .block-card * {
        color: #ffffff !important;
    }

    /* 체크박스 */
    .stCheckbox label {
        color: #ffffff !important;
    }

    /* 경고/정보 박스 */
    .stAlert {
        color: #ffffff !important;
    }

    /* 제목 */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }

    /* 시나리오 박스 - 크게 */
    .scenario-box {
        background: #1a1a2e;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #3d4167;
        line-height: 1.8;
        font-size: 1.05em;
        color: #ffffff !important;
        min-height: 400px;
        max-height: 600px;
        overflow-y: auto;
    }

    /* 원고 뷰어 - 가로 줄임 */
    .manuscript-viewer {
        background: #1a1a2e;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #3d4167;
        line-height: 2.0;
        font-size: 1.1em;
        color: #ffffff !important;
        max-width: 50%;
        margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# 유틸리티 클래스
# ============================================================
class StudioDB:
    """데이터베이스 연결 관리"""

    def __init__(self, project_path):
        self.db_path = Path(project_path) / "project_data.db"
        self._ensure_tables()

    def _ensure_tables(self):
        """필요한 테이블이 존재하는지 확인"""
        if not self.db_path.exists():
            return
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            # blueprints 테이블 확인 및 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blueprints (
                    ep_num INTEGER PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            pass  # 에러 무시 (읽기 전용 등)

    def get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def load_anchor(self, key):
        """앵커 데이터 로드"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM anchors WHERE key = ?", (key,))
            row = cursor.fetchone()
            conn.close()
            return json.loads(row['data']) if row else None
        except:
            return None

    def save_anchor(self, key, data):
        """앵커 데이터 저장"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            json_data = json.dumps(data, ensure_ascii=False)
            cursor.execute("""
                INSERT OR REPLACE INTO anchors (key, data, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, json_data))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            st.error(f"저장 실패: {e}")
            return False

    def get_manuscripts(self, limit=10):
        """원고 목록 조회"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ep_num, title, content FROM manuscripts
                ORDER BY ep_num DESC LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            conn.close()
            return [dict(row) for row in rows]
        except:
            return []

    def get_blueprints(self):
        """블루프린트 목록 조회"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ep_num, data FROM blueprints ORDER BY ep_num")
            rows = cursor.fetchall()
            conn.close()
            return [(row['ep_num'], json.loads(row['data'])) for row in rows]
        except:
            return []

    def get_blueprint(self, ep_num):
        """특정 에피소드 블루프린트 조회"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM blueprints WHERE ep_num = ?", (ep_num,))
            row = cursor.fetchone()
            conn.close()
            return json.loads(row['data']) if row else None
        except:
            return None


class ProjectManager:
    """프로젝트 관리"""

    def __init__(self):
        self.projects_dir = Path("projects")

    def get_project_list(self):
        """프로젝트 목록"""
        if not self.projects_dir.exists():
            return []
        return [p.name for p in self.projects_dir.iterdir()
                if p.is_dir() and (p / "project_data.db").exists()]

    def get_project_path(self, name):
        return self.projects_dir / name

    def get_stage_status(self, project_name):
        """각 Stage 완료 상태 확인"""
        db = StudioDB(self.get_project_path(project_name))

        status = {
            0: False,
            1: False,
            2: False,
            3: False,
            4: False
        }

        bible = db.load_anchor('bible')
        if bible:
            status[0] = True

        volumes = db.load_anchor('volumes')
        if volumes and len(volumes) > 0:
            status[1] = True

        arcs = db.load_anchor('arcs')
        if arcs and len(arcs) > 0:
            status[2] = True

        blueprints = db.get_blueprints()
        if blueprints and len(blueprints) > 0:
            status[3] = True

        manuscripts = db.get_manuscripts(1)
        if manuscripts and len(manuscripts) > 0:
            status[4] = True

        return status

    def get_author_directives(self, project_name):
        """작가 지시사항 로드"""
        path = self.get_project_path(project_name) / "config" / "author_directives.txt"
        if path.exists():
            return path.read_text(encoding='utf-8')
        return ""

    def save_author_directives(self, project_name, content):
        """작가 지시사항 저장"""
        path = self.get_project_path(project_name) / "config" / "author_directives.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')


# ============================================================
# 세션 상태 초기화
# ============================================================
def init_session_state():
    defaults = {
        'current_project': None,
        'current_genre': 'wuxia',
        'current_tab': 'stage',
        'current_stage': 0,
        'editing_arc': None,
        'editing_blueprint': None,
        'viewing_blueprint': None,
        'skip_stage1': False,
        'logs': [],
        'api_usage': {'tokens': 0, 'cost': 0.0},
        'show_block_selector': False,
        'auto_generate_mode': False,
        'roadmap_page': 0,
        'uploaded_bible': None,
        'uploaded_treatment': None,
        'confirm_delete_arc': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()


# ============================================================
# 사이드바 렌더링
# ============================================================
def render_sidebar():
    with st.sidebar:
        # 로고
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <span style="font-size: 2.5em;">🎭</span>
            <h2 style="margin: 10px 0 5px 0; color: #ffffff !important;">글도비_V0127</h2>
            <span style="color: #b8c5d6; font-size: 0.85em;">AI 소설 생성 스튜디오</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # 장르 선택 (강조)
        st.markdown("""
        <div class="genre-selector">
            <div class="genre-title">🎯 장르 선택</div>
        </div>
        """, unsafe_allow_html=True)

        genres = {
            'wuxia': '⚔️ 무협 (武俠)',
            'hunter': '🏹 헌터 (Hunter)',
            'investment': '💰 투자 (Investment)'
        }
        selected_genre = st.radio(
            "장르",
            options=list(genres.keys()),
            format_func=lambda x: genres[x],
            label_visibility="collapsed"
        )
        st.session_state.current_genre = selected_genre

        st.markdown("---")

        # 프로젝트 선택
        st.markdown("**📁 프로젝트**")
        pm = ProjectManager()
        projects = pm.get_project_list()

        if projects:
            selected_project = st.selectbox(
                "프로젝트 선택",
                options=projects,
                label_visibility="collapsed"
            )
            st.session_state.current_project = selected_project

            # 진행 상태
            status = pm.get_stage_status(selected_project)

            st.markdown("---")
            st.markdown("**📊 진행 상태**")

            stage_names = {
                0: "Bible 로드",
                1: "Volume 전략",
                2: "Arc 설계",
                3: "Blueprint",
                4: "원고 생성"
            }

            for stage_num, name in stage_names.items():
                if status[stage_num]:
                    icon = "✅"
                    css_class = "status-complete"
                elif stage_num == 1 and st.session_state.skip_stage1:
                    icon = "⏭️"
                    css_class = "status-skip"
                else:
                    icon = "⏳"
                    css_class = "status-pending"

                st.markdown(f"<span class='{css_class}'>{icon}</span> Stage {stage_num}: {name}",
                           unsafe_allow_html=True)

            st.markdown("---")

            # 작가 지시사항
            st.markdown("**📝 작가 지시사항**")
            with st.expander("편집"):
                directives = pm.get_author_directives(selected_project)
                new_directives = st.text_area(
                    "지시사항",
                    value=directives,
                    height=150,
                    label_visibility="collapsed"
                )
                if st.button("💾 저장", key="save_directives"):
                    pm.save_author_directives(selected_project, new_directives)
                    st.success("저장됨")

            st.markdown("---")

            # 백업/롤백
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 백업", use_container_width=True):
                    add_log("백업 기능 준비 중", "info")
            with col2:
                if st.button("↩️ 롤백", use_container_width=True):
                    add_log("롤백 기능 준비 중", "info")

        else:
            st.info("프로젝트가 없습니다.")
            st.markdown("main_a.py에서 프로젝트를 먼저 생성하세요.")

        # API 사용량
        st.markdown("---")
        st.markdown("""
        <div class="api-usage-box">
            <div style="color: #b8c5d6; font-size: 0.85em;">💎 API 사용량</div>
            <div style="color: #7c3aed; font-size: 1.3em; font-weight: 600; margin-top: 5px;">
                ${:.4f}
            </div>
            <div style="color: #b8c5d6; font-size: 0.75em;">
                {} tokens
            </div>
        </div>
        """.format(
            st.session_state.api_usage['cost'],
            st.session_state.api_usage['tokens']
        ), unsafe_allow_html=True)


# ============================================================
# 로그 관리
# ============================================================
def add_log(message, level="info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append({
        'time': timestamp,
        'message': message,
        'level': level
    })
    if len(st.session_state.logs) > 50:
        st.session_state.logs = st.session_state.logs[-50:]


def render_logs():
    st.markdown("**📋 실시간 로그**")

    log_html = '<div class="log-box">'
    for log in reversed(st.session_state.logs[-10:]):
        css_class = f"log-{log['level']}"
        log_html += f'<div class="{css_class}">[{log["time"]}] {log["message"]}</div>'
    if not st.session_state.logs:
        log_html += '<div style="color: #6b7280;">로그가 없습니다.</div>'
    log_html += '</div>'

    st.markdown(log_html, unsafe_allow_html=True)


# ============================================================
# Stage 탭 렌더링
# ============================================================
def render_stage_tabs():
    if not st.session_state.current_project:
        st.info("👈 사이드바에서 프로젝트를 선택하세요.")
        return

    project_path = ProjectManager().get_project_path(st.session_state.current_project)
    db = StudioDB(project_path)

    tabs = st.tabs([
        "🏛️ Stage 0: Bible",
        "📜 Stage 1: Volume",
        "🗺️ Stage 2: Arc",
        "📋 Stage 3: Blueprint",
        "✍️ Stage 4: 원고",
        "👤 HUD",
        "👥 캐릭터",
        "📌 주요 사건",
        "🌱 복선",
        "📖 원고 뷰어"
    ])

    with tabs[0]:
        render_stage_0(db)
    with tabs[1]:
        render_stage_1(db)
    with tabs[2]:
        render_stage_2(db)
    with tabs[3]:
        render_stage_3(db)
    with tabs[4]:
        render_stage_4(db)
    with tabs[5]:
        render_hud_editor(db)
    with tabs[6]:
        render_character_manager(db)
    with tabs[7]:
        render_event_manager(db)
    with tabs[8]:
        render_seeds_tracker(db)
    with tabs[9]:
        render_manuscript_viewer(db)


# ============================================================
# Stage 0: Bible (수정 가능 + JSON 업로드)
# ============================================================
def render_stage_0(db):
    st.markdown("""
    <div class="node-card">
        <div class="node-header">
            <span class="node-title">🏛️ Stage 0: Bible & 초기화</span>
            <span class="node-badge">설정</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    bible = db.load_anchor('bible')

    # JSON 업로드 섹션
    st.markdown("### 📤 JSON 업로드")
    upload_col1, upload_col2, upload_col3 = st.columns(3)

    with upload_col1:
        bible_file = st.file_uploader("📘 Bible JSON", type=['json'], key="bible_upload")
        if bible_file:
            try:
                bible_data = json.loads(bible_file.read().decode('utf-8'))
                st.session_state['uploaded_bible'] = bible_data
                st.success("Bible JSON 로드됨")
            except Exception as e:
                st.error(f"파싱 오류: {e}")

    with upload_col2:
        treatment_file = st.file_uploader("📗 Treatment JSON", type=['json'], key="treatment_upload")
        if treatment_file:
            try:
                treatment_data = json.loads(treatment_file.read().decode('utf-8'))
                st.session_state['uploaded_treatment'] = treatment_data
                st.success(f"Treatment JSON 로드됨 ({len(treatment_data)}개 Block)")
            except Exception as e:
                st.error(f"파싱 오류: {e}")

    with upload_col3:
        if st.button("🔀 Bible + Treatment 합치기", type="primary"):
            uploaded_bible = st.session_state.get('uploaded_bible')
            uploaded_treatment = st.session_state.get('uploaded_treatment')

            if uploaded_bible and uploaded_treatment:
                merged = merge_bible_and_treatment(uploaded_bible, uploaded_treatment)
                if db.save_anchor('bible', merged):
                    st.success("✅ 합쳐진 Bible이 저장되었습니다!")
                    add_log("Bible + Treatment 병합 완료", "success")
                    st.rerun()
            elif uploaded_bible:
                if db.save_anchor('bible', uploaded_bible):
                    st.success("✅ Bible이 저장되었습니다!")
                    add_log("Bible 업로드 완료", "success")
                    st.rerun()
            else:
                st.warning("Bible JSON을 먼저 업로드하세요.")

    st.markdown("---")

    if bible:
        st.success("✅ Bible 데이터가 로드되어 있습니다.")

        bible_root = bible.get('MasterBible', bible)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            project_data = bible_root.get('ProjectData', {})
            meta_info = project_data.get('MetaInfo', project_data)
            st.metric("프로젝트명", meta_info.get('title', meta_info.get('Title', 'N/A')))
        with col2:
            seeds = bible_root.get('Seeds', [])
            st.metric("복선 수", len(seeds))
        with col3:
            npcs = bible_root.get('AssetLibrary', {}).get('KeyNPCs', [])
            st.metric("주요 NPC", len(npcs))
        with col4:
            roadmap = bible_root.get('plot_roadmap', [])
            st.metric("Block 수", len(roadmap))

        # Bible 편집
        st.markdown("---")
        st.markdown("### 📝 Bible 편집")

        edit_tab1, edit_tab2, edit_tab3 = st.tabs(["프로젝트 정보", "주요 NPC", "Plot Roadmap (50 Blocks)"])

        with edit_tab1:
            project_data = bible_root.get('ProjectData', {})
            meta_info = project_data.get('MetaInfo', project_data)
            core_identity = project_data.get('CoreIdentity', {})

            new_title = st.text_input("제목", value=meta_info.get('title', meta_info.get('Title', '')))
            new_logline = st.text_area("로그라인", value=meta_info.get('logline', meta_info.get('Logline', '')), height=100)
            new_objective = st.text_area("대목표", value=meta_info.get('grand_objective', ''), height=80)

            if st.button("💾 프로젝트 정보 저장", key="save_project_info"):
                if 'MetaInfo' not in project_data:
                    bible_root['ProjectData'] = {'MetaInfo': {}, 'CoreIdentity': core_identity}
                bible_root['ProjectData']['MetaInfo']['title'] = new_title
                bible_root['ProjectData']['MetaInfo']['logline'] = new_logline
                bible_root['ProjectData']['MetaInfo']['grand_objective'] = new_objective
                if db.save_anchor('bible', bible):
                    st.success("저장 완료!")
                    add_log("Bible 프로젝트 정보 수정", "success")

        with edit_tab2:
            st.markdown("**등록된 NPC**")
            npcs = bible_root.get('AssetLibrary', {}).get('KeyNPCs', [])

            for i, npc in enumerate(npcs):
                with st.expander(f"👤 {npc.get('name', npc.get('Name', f'NPC {i+1}'))}"):
                    npc_name = st.text_input("이름", value=npc.get('name', ''), key=f"npc_name_{i}")
                    npc_role = st.text_input("역할", value=npc.get('role', ''), key=f"npc_role_{i}")
                    npc_desc = st.text_area("설명", value=npc.get('desc', npc.get('Description', '')), key=f"npc_desc_{i}", height=100)

                    if st.button("수정", key=f"update_npc_{i}"):
                        npcs[i]['name'] = npc_name
                        npcs[i]['role'] = npc_role
                        npcs[i]['desc'] = npc_desc
                        if db.save_anchor('bible', bible):
                            st.success("NPC 수정됨")

                    if st.button("🗑️ 삭제", key=f"del_npc_{i}"):
                        del npcs[i]
                        if db.save_anchor('bible', bible):
                            st.rerun()

            # NPC 추가
            st.markdown("---")
            st.markdown("**➕ 새 NPC 추가**")
            new_npc_name = st.text_input("새 NPC 이름", key="new_npc_name")
            new_npc_role = st.text_input("새 NPC 역할", key="new_npc_role")
            new_npc_desc = st.text_area("새 NPC 설명", key="new_npc_desc", height=100)

            if st.button("➕ NPC 추가"):
                if new_npc_name:
                    bible_root.setdefault('AssetLibrary', {}).setdefault('KeyNPCs', []).append({
                        'name': new_npc_name,
                        'role': new_npc_role,
                        'desc': new_npc_desc
                    })
                    if db.save_anchor('bible', bible):
                        st.success(f"NPC '{new_npc_name}' 추가됨")
                        add_log(f"NPC 추가: {new_npc_name}", "success")
                        st.rerun()

        with edit_tab3:
            render_plot_roadmap_editor(db, bible, bible_root)

    else:
        st.warning("⚠️ Bible 데이터가 없습니다.")
        st.markdown("위에서 Bible JSON을 업로드하거나, main_a.py에서 Phase 0을 실행하세요.")


def merge_bible_and_treatment(bible_data, treatment_data):
    """Bible과 Treatment를 합쳐서 plot_roadmap 생성"""
    bible_root = bible_data.get('MasterBible', bible_data)

    # Treatment를 plot_roadmap 형식으로 변환
    plot_roadmap = []
    for block in treatment_data:
        block_id = block.get('block_id', '')
        # "Block 1" -> 1
        try:
            block_no = int(block_id.replace('Block', '').strip())
        except:
            block_no = len(plot_roadmap) + 1

        content = block.get('content', {})
        plot_roadmap.append({
            'block_no': block_no,
            'title': block.get('title', ''),
            'logic': {
                'title': block.get('title', ''),
                'context': content.get('context', ''),
                'event_villain': content.get('event_villain', ''),
                'solution': content.get('solution', ''),
                'reward': content.get('reward', ''),
                'objective': content.get('context', '')[:200]  # 축약
            }
        })

    bible_root['plot_roadmap'] = plot_roadmap
    return bible_data


def render_plot_roadmap_editor(db, bible, bible_root):
    """Plot Roadmap 전체 편집 UI (50 Blocks)"""
    roadmap = bible_root.get('plot_roadmap', [])
    st.markdown(f"**총 {len(roadmap)}개 Block** (전체 표시)")

    # 페이지네이션
    blocks_per_page = 10
    total_pages = max(1, (len(roadmap) + blocks_per_page - 1) // blocks_per_page)

    if 'roadmap_page' not in st.session_state:
        st.session_state.roadmap_page = 0

    page_col1, page_col2, page_col3 = st.columns([1, 2, 1])
    with page_col1:
        if st.button("◀ 이전", key="prev_page") and st.session_state.roadmap_page > 0:
            st.session_state.roadmap_page -= 1
            st.rerun()
    with page_col2:
        st.markdown(f"<div style='text-align: center;'>페이지 {st.session_state.roadmap_page + 1} / {total_pages}</div>", unsafe_allow_html=True)
    with page_col3:
        if st.button("다음 ▶", key="next_page") and st.session_state.roadmap_page < total_pages - 1:
            st.session_state.roadmap_page += 1
            st.rerun()

    # 현재 페이지의 Block 표시
    start_idx = st.session_state.roadmap_page * blocks_per_page
    end_idx = min(start_idx + blocks_per_page, len(roadmap))

    for i in range(start_idx, end_idx):
        block = roadmap[i]
        block_no = block.get('block_no', i + 1)
        logic = block.get('logic', block)
        title = logic.get('title', block.get('title', f'Block {block_no}'))

        with st.expander(f"📦 Block {block_no}: {title[:50]}{'...' if len(title) > 50 else ''}"):
            # 검은 배경에 흰 글씨로 표시
            st.markdown(f"""
            <div class="block-card">
                <p><strong>🎯 Context:</strong><br>{logic.get('context', 'N/A')[:300]}{'...' if len(logic.get('context', '')) > 300 else ''}</p>
                <p><strong>⚔️ Event/Villain:</strong><br>{logic.get('event_villain', 'N/A')[:300]}{'...' if len(logic.get('event_villain', '')) > 300 else ''}</p>
                <p><strong>💡 Solution:</strong><br>{logic.get('solution', 'N/A')[:300]}{'...' if len(logic.get('solution', '')) > 300 else ''}</p>
                <p><strong>🏆 Reward:</strong><br>{logic.get('reward', 'N/A')[:300]}{'...' if len(logic.get('reward', '')) > 300 else ''}</p>
            </div>
            """, unsafe_allow_html=True)

            # 편집 기능
            if st.checkbox(f"편집 모드", key=f"edit_block_{i}"):
                new_title = st.text_input("제목", value=title, key=f"block_title_{i}")
                new_context = st.text_area("Context", value=logic.get('context', ''), height=100, key=f"block_ctx_{i}")
                new_event = st.text_area("Event/Villain", value=logic.get('event_villain', ''), height=100, key=f"block_evt_{i}")
                new_solution = st.text_area("Solution", value=logic.get('solution', ''), height=100, key=f"block_sol_{i}")
                new_reward = st.text_area("Reward", value=logic.get('reward', ''), height=80, key=f"block_rwd_{i}")

                if st.button("💾 Block 저장", key=f"save_block_{i}"):
                    roadmap[i] = {
                        'block_no': block_no,
                        'title': new_title,
                        'logic': {
                            'title': new_title,
                            'context': new_context,
                            'event_villain': new_event,
                            'solution': new_solution,
                            'reward': new_reward,
                            'objective': new_context[:200]
                        }
                    }
                    if db.save_anchor('bible', bible):
                        st.success(f"Block {block_no} 저장됨")
                        add_log(f"Block {block_no} 수정", "success")

    # Block 추가
    st.markdown("---")
    st.markdown("### ➕ 새 Block 추가")

    new_block_no = len(roadmap) + 1
    st.markdown(f"새 Block 번호: **{new_block_no}**")

    new_b_title = st.text_input("제목", key="new_block_title")
    new_b_context = st.text_area("Context", key="new_block_context", height=100)
    new_b_event = st.text_area("Event/Villain", key="new_block_event", height=100)
    new_b_solution = st.text_area("Solution", key="new_block_solution", height=100)
    new_b_reward = st.text_area("Reward", key="new_block_reward", height=80)

    if st.button("➕ Block 추가", key="add_new_block"):
        if new_b_title:
            roadmap.append({
                'block_no': new_block_no,
                'title': new_b_title,
                'logic': {
                    'title': new_b_title,
                    'context': new_b_context,
                    'event_villain': new_b_event,
                    'solution': new_b_solution,
                    'reward': new_b_reward,
                    'objective': new_b_context[:200]
                }
            })
            bible_root['plot_roadmap'] = roadmap
            if db.save_anchor('bible', bible):
                st.success(f"Block {new_block_no} 추가됨")
                add_log(f"Block {new_block_no} 추가", "success")
                st.rerun()


# ============================================================
# Stage 1: Volume
# ============================================================
def render_stage_1(db):
    st.markdown("""
    <div class="node-card">
        <div class="node-header">
            <span class="node-title">📜 Stage 1: Volume 전략</span>
            <span class="node-badge">선택적</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    skip = st.checkbox("⏭️ Stage 1 스킵 (Arc 중심으로 진행)", value=st.session_state.skip_stage1)
    st.session_state.skip_stage1 = skip

    if skip:
        st.info("Stage 1을 스킵합니다. Stage 2에서 바로 Arc 설계를 진행합니다.")
        return

    volumes = db.load_anchor('volumes')

    if volumes and len(volumes) > 0:
        st.success(f"✅ {len(volumes)}권 전략이 설계되어 있습니다.")

        for vol in volumes:
            with st.expander(f"📖 제 {vol.get('vol_no', '?')}권"):
                st.text_area(
                    "전략 문서",
                    value=vol.get('strategy_doc', '')[:2000],
                    height=200,
                    disabled=True,
                    label_visibility="collapsed"
                )
    else:
        st.warning("⚠️ Volume 전략이 없습니다.")
        if st.button("▶️ AI 자동 생성 실행", type="primary"):
            st.info("main_a.py에서 Stage 1을 실행하세요.")
            add_log("Stage 1 실행 요청", "info")


# ============================================================
# Stage 2: Arc (Block 기반)
# ============================================================
def render_stage_2(db):
    st.markdown("""
    <div class="node-card">
        <div class="node-header">
            <span class="node-title">🗺️ Stage 2: Arc 설계</span>
            <span class="node-badge">핵심</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    arcs = db.load_anchor('arcs') or []
    bible = db.load_anchor('bible')

    # Block 데이터 가져오기
    blocks = []
    if bible:
        bible_root = bible.get('MasterBible', bible)
        blocks = bible_root.get('plot_roadmap', [])

    if not arcs:
        st.warning("⚠️ Arc 데이터가 없습니다.")
        if st.button("▶️ AI 자동 생성 실행", type="primary", key="gen_arcs"):
            st.info("main_a.py에서 Stage 2를 실행하세요.")
            add_log("Stage 2 실행 요청", "info")
        return

    # 편집 모드
    if st.session_state.editing_arc is not None:
        render_arc_editor(db, arcs, blocks)
        return

    # Block 선택 모드
    if st.session_state.show_block_selector:
        render_block_selector(db, arcs, blocks)
        return

    # 카드 뷰
    st.markdown(f"**총 {len(arcs)}개 Arc** | 가변 페이싱 적용")

    # 볼륨별 그룹화
    volumes = {}
    for idx, arc in enumerate(arcs):
        vol = arc.get('volume_no', 1)
        if vol not in volumes:
            volumes[vol] = []
        volumes[vol].append((idx, arc))

    for vol_no in sorted(volumes.keys()):
        st.markdown(f'<div class="volume-header">📖 Volume {vol_no}</div>', unsafe_allow_html=True)

        cols = st.columns(4)
        for i, (idx, arc) in enumerate(volumes[vol_no]):
            with cols[i % 4]:
                arc_no = arc.get('arc_no', idx + 1)
                ep_start = arc.get('ep_start', '?')
                ep_end = arc.get('ep_end', '?')
                ep_count = arc.get('ep_count', '?')

                st.markdown(f"""
                <div class="arc-card">
                    <div style="font-weight: 600; margin-bottom: 8px;">Arc {arc_no}</div>
                    <div style="font-size: 0.85em; opacity: 0.9;">
                        EP {ep_start}~{ep_end} ({ep_count}화)
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"편집", key=f"edit_arc_{idx}"):
                    st.session_state.editing_arc = idx
                    st.rerun()

    st.markdown("---")

    # Arc 추가 옵션
    st.markdown("### ➕ Arc 추가")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📦 Block에서 선택하여 추가", use_container_width=True):
            st.session_state.show_block_selector = True
            st.rerun()
    with col2:
        if st.button("🤖 Block 기반 자동 생성", use_container_width=True):
            # 다음 사용할 Block 찾기
            used_blocks = set()
            for arc in arcs:
                if 'block_no' in arc:
                    used_blocks.add(arc['block_no'])

            next_block = None
            for block in blocks:
                if block.get('block_no') not in used_blocks:
                    next_block = block
                    break

            if next_block:
                last = arcs[-1] if arcs else {}
                new_arc = create_arc_from_block(next_block, len(arcs) + 1, last)
                arcs.append(new_arc)
                db.save_anchor('arcs', arcs)
                save_arcs_to_txt(st.session_state.current_project, arcs)
                st.success(f"Block {next_block.get('block_no')} 기반 Arc 생성됨")
                st.rerun()
            else:
                st.warning("사용 가능한 Block이 없습니다.")

    st.markdown("---")
    if st.button("💾 전체 저장", type="primary"):
        if db.save_anchor('arcs', arcs):
            save_arcs_to_txt(st.session_state.current_project, arcs)
            st.success("저장 완료!")
            add_log("Arc 전체 저장 완료", "success")


def render_block_selector(db, arcs, blocks):
    """Block 선택 UI (가변 페이싱 지원)"""
    st.markdown("### 📦 Block 선택")
    st.markdown("Arc로 만들 Block을 선택하세요. **화수는 가변 페이싱**으로 조절됩니다.")

    # 이미 사용된 Block 확인
    used_blocks = set()
    for arc in arcs:
        if 'block_no' in arc:
            used_blocks.add(arc['block_no'])

    available_blocks = [b for b in blocks if b.get('block_no') not in used_blocks]

    # 가변 페이싱 옵션
    st.markdown("---")
    pacing_col1, pacing_col2 = st.columns(2)
    with pacing_col1:
        pacing_mode = st.radio(
            "화수 결정 방식",
            ["🤖 자동 (내용 복잡도)", "✏️ 수동 지정"],
            horizontal=True
        )
    with pacing_col2:
        if "수동" in pacing_mode:
            manual_ep_count = st.slider("화수", min_value=3, max_value=20, value=8)
        else:
            manual_ep_count = None
            st.info("내용 복잡도에 따라 5~12화 자동 결정")

    st.markdown("---")

    if not available_blocks:
        st.info("사용 가능한 Block이 없습니다.")
    else:
        for block in available_blocks[:15]:  # 15개까지 표시
            block_no = block.get('block_no', '?')
            logic = block.get('logic', {})
            title = logic.get('title', block.get('title', 'N/A'))

            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**Block {block_no}**: {title[:40]}{'...' if len(title) > 40 else ''}")
                context_preview = logic.get('context', logic.get('objective', ''))[:80]
                st.caption(context_preview)
            with col2:
                # 자동 예상 화수
                content_len = len(logic.get('context', '')) + len(logic.get('event_villain', ''))
                auto_ep = 12 if content_len > 1000 else (8 if content_len > 500 else 5)
                st.markdown(f"~{auto_ep}화")
            with col3:
                if st.button("✅ 선택", key=f"select_block_{block_no}"):
                    last = arcs[-1] if arcs else {}
                    ep_count_val = manual_ep_count if manual_ep_count else None
                    new_arc = create_arc_from_block(block, len(arcs) + 1, last, ep_count_val)
                    arcs.append(new_arc)
                    db.save_anchor('arcs', arcs)
                    save_arcs_to_txt(st.session_state.current_project, arcs)
                    st.session_state.show_block_selector = False
                    st.success(f"Block {block_no} 기반 Arc 생성됨 ({new_arc['ep_count']}화)")
                    add_log(f"Arc {new_arc['arc_no']} 생성 (Block {block_no}, {new_arc['ep_count']}화)", "success")
                    st.rerun()

    st.markdown("---")
    if st.button("❌ 취소", use_container_width=True):
        st.session_state.show_block_selector = False
        st.rerun()


def create_arc_from_block(block, arc_no, last_arc, ep_count=None):
    """Block에서 Arc 생성 (가변 페이싱 지원)"""
    logic = block.get('logic', {})
    ep_start = last_arc.get('ep_end', 0) + 1

    # 가변 페이싱: 사용자 지정 또는 기본값
    if ep_count is None:
        # Block 내용 복잡도에 따른 자동 추정 (기본 5~15화)
        content_len = len(logic.get('context', '')) + len(logic.get('event_villain', ''))
        if content_len > 1000:
            ep_count = 12
        elif content_len > 500:
            ep_count = 8
        else:
            ep_count = 5

    # 전술 문서 자동 생성
    tactical_doc = f"""[Block {block.get('block_no')}] {logic.get('title', '')}

▣ CONTEXT
{logic.get('context', '내용 없음')}

▣ EVENT/VILLAIN
{logic.get('event_villain', '내용 없음')}

▣ SOLUTION
{logic.get('solution', '내용 없음')}

▣ REWARD
{logic.get('reward', '내용 없음')}
"""

    return {
        'arc_no': arc_no,
        'global_arc_no': arc_no,
        'block_no': block.get('block_no'),
        'volume_no': ((arc_no - 1) // 5) + 1,
        'ep_start': ep_start,
        'ep_end': ep_start + ep_count - 1,
        'ep_count': ep_count,
        'tactical_doc': tactical_doc,
        'beat_sequence': []
    }


def render_arc_editor(db, arcs, blocks):
    """Arc 편집 UI (화별 전술문서 + 비트 시퀀스)"""
    idx = st.session_state.editing_arc
    arc = arcs[idx]

    col_edit, col_action = st.columns([3, 1])

    with col_edit:
        st.markdown(f"### Arc {arc.get('arc_no', idx + 1)} 편집")

        # 기본 정보
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            arc_no = st.number_input("Arc 번호", value=arc.get('arc_no', idx + 1), min_value=1)
        with c2:
            volume_no = st.number_input("볼륨", value=arc.get('volume_no', 1), min_value=1)
        with c3:
            ep_start = st.number_input("시작 EP", value=arc.get('ep_start', 1), min_value=1)
        with c4:
            ep_end = st.number_input("종료 EP", value=arc.get('ep_end', 10), min_value=1)

        ep_count = ep_end - ep_start + 1
        st.markdown(f"**에피소드 수: {ep_count}화** (가변 페이싱)")

        # Block 정보 표시
        if arc.get('block_no'):
            st.caption(f"📦 Block {arc.get('block_no')} 기반")

        st.markdown("---")

        # 전술 문서 (Arc 전체)
        st.markdown("### 📜 Arc 전술 문서 (전체 방향)")
        tactical_doc = st.text_area(
            "Arc 전체 전술 문서",
            value=arc.get('tactical_doc', ''),
            height=200,
            label_visibility="collapsed",
            help="이 Arc 전체의 방향성과 핵심 내용을 기술합니다."
        )

        st.markdown("---")

        # 화별 전술문서 + 비트 시퀀스
        st.markdown("### 🎬 화별 전술문서 & 비트 시퀀스")
        st.caption("각 에피소드별로 세부 내용과 비트를 작성합니다.")

        beat_seq = arc.get('beat_sequence', [])
        ep_tactical_docs = arc.get('ep_tactical_docs', {})

        # 기존 비트를 화별로 파싱
        beats_by_ep = {}
        for beat in beat_seq:
            if isinstance(beat, dict):
                ep = beat.get('ep', 1)
                beats_by_ep.setdefault(ep, []).append(beat.get('beat', ''))
            else:
                beats_by_ep.setdefault(1, []).append(str(beat))

        # 화별 입력 UI
        new_beats = []
        new_ep_tactical = {}

        for ep in range(ep_start, ep_end + 1):
            arc_pos = ep - ep_start + 1  # 이 Arc에서 몇 번째 화인지

            with st.expander(f"📍 EP {ep} (Arc 내 {arc_pos}/{ep_count}화)", expanded=(arc_pos == 1)):
                # 화별 전술 문서
                ep_tac_existing = ep_tactical_docs.get(str(ep), '')
                ep_tactical = st.text_area(
                    f"EP {ep} 전술 문서",
                    value=ep_tac_existing,
                    height=100,
                    key=f"ep_tac_{ep}",
                    help="이 에피소드에서 달성해야 할 목표와 핵심 장면"
                )
                new_ep_tactical[str(ep)] = ep_tactical

                # 비트 시퀀스
                existing_beats = '\n'.join(beats_by_ep.get(ep, beats_by_ep.get(arc_pos, [])))
                beat_text = st.text_area(
                    f"EP {ep} 비트 (줄바꿈으로 구분)",
                    value=existing_beats,
                    height=80,
                    key=f"beat_ep_{ep}",
                    help="이 에피소드의 주요 장면/비트를 나열합니다."
                )
                for line in beat_text.split('\n'):
                    if line.strip():
                        new_beats.append({'ep': ep, 'beat': line.strip()})

    with col_action:
        st.markdown("<br><br>", unsafe_allow_html=True)

        if st.button("💾 저장", type="primary", use_container_width=True):
            arcs[idx] = {
                'arc_no': arc_no,
                'global_arc_no': arc_no,
                'block_no': arc.get('block_no'),
                'volume_no': volume_no,
                'ep_start': ep_start,
                'ep_end': ep_end,
                'ep_count': ep_count,
                'tactical_doc': tactical_doc,
                'ep_tactical_docs': new_ep_tactical,
                'beat_sequence': new_beats,
                'seed_injection': arc.get('seed_injection', [])
            }
            db.save_anchor('arcs', arcs)
            save_arcs_to_txt(st.session_state.current_project, arcs)
            st.success("저장 완료!")
            add_log(f"Arc {arc_no} 저장 ({ep_count}화)", "success")

        if st.button("❌ 취소", use_container_width=True):
            st.session_state.editing_arc = None
            st.rerun()

        st.markdown("---")

        # 화수 조정 단축 버튼
        st.markdown("**⚡ 화수 조정**")
        adj_col1, adj_col2 = st.columns(2)
        with adj_col1:
            if st.button("➖ 1화", key="dec_ep"):
                if ep_count > 1:
                    st.session_state[f"ep_end_adj"] = ep_end - 1
                    st.rerun()
        with adj_col2:
            if st.button("➕ 1화", key="inc_ep"):
                st.session_state[f"ep_end_adj"] = ep_end + 1
                st.rerun()

        st.markdown("---")

        if st.button("🗑️ Arc 삭제", use_container_width=True):
            if st.session_state.get('confirm_delete_arc'):
                del arcs[idx]
                db.save_anchor('arcs', arcs)
                st.session_state.editing_arc = None
                st.session_state.confirm_delete_arc = False
                st.rerun()
            else:
                st.session_state.confirm_delete_arc = True
                st.warning("다시 클릭하면 삭제!")


def save_arcs_to_txt(project_name, arcs):
    """Arc txt 파일 저장 (화별 전술문서 + 비트 시퀀스)"""
    plans_dir = Path("projects") / project_name / "plans" / "arcs"
    plans_dir.mkdir(parents=True, exist_ok=True)

    for arc in arcs:
        arc_no = arc.get('arc_no', 0)
        if not arc_no:
            continue

        ep_start = arc.get('ep_start', 1)
        ep_end = arc.get('ep_end', ep_start)
        ep_count = arc.get('ep_count', ep_end - ep_start + 1)

        filepath = plans_dir / f"arc_{arc_no:03d}.txt"
        lines = [
            f"{'='*60}",
            f"ARC {arc_no}",
            f"{'='*60}",
            f"Volume: {arc.get('volume_no', 'N/A')}",
            f"Block: {arc.get('block_no', 'N/A')}",
            f"Episodes: EP {ep_start} ~ EP {ep_end} ({ep_count}화)",
            f"",
            f"[Arc 전술 문서]",
            f"{'-'*40}",
            arc.get('tactical_doc', ''),
            f"",
            f"{'='*60}",
            f"[화별 세부 설계]",
            f"{'='*60}"
        ]

        # 화별 전술 문서와 비트 정리
        ep_tactical_docs = arc.get('ep_tactical_docs', {})
        beats = arc.get('beat_sequence', [])

        beats_by_ep = {}
        for beat in beats:
            if isinstance(beat, dict):
                ep = beat.get('ep', 1)
                beats_by_ep.setdefault(ep, []).append(beat.get('beat', ''))
            else:
                beats_by_ep.setdefault(1, []).append(str(beat))

        for ep in range(ep_start, ep_end + 1):
            arc_pos = ep - ep_start + 1
            lines.append(f"\n{'─'*40}")
            lines.append(f"EP {ep} (Arc 내 {arc_pos}/{ep_count}화)")
            lines.append(f"{'─'*40}")

            # 화별 전술 문서
            ep_tac = ep_tactical_docs.get(str(ep), '')
            if ep_tac:
                lines.append(f"[전술 문서]")
                lines.append(ep_tac)
                lines.append("")

            # 비트 시퀀스
            ep_beats = beats_by_ep.get(ep, [])
            if ep_beats:
                lines.append(f"[비트 시퀀스]")
                for i, b in enumerate(ep_beats, 1):
                    lines.append(f"  {i}. {b}")
            else:
                lines.append("[비트 시퀀스] (미작성)")

        filepath.write_text('\n'.join(lines), encoding='utf-8')


# ============================================================
# Stage 3: Blueprint (시나리오 확대 + 생성 기능)
# ============================================================
def render_stage_3(db):
    st.markdown("""
    <div class="node-card">
        <div class="node-header">
            <span class="node-title">📋 Stage 3: Blueprint</span>
            <span class="node-badge">설계</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    blueprints = db.get_blueprints()
    arcs = db.load_anchor('arcs') or []

    # Arc에서 필요한 Blueprint 범위 계산
    total_ep_needed = 0
    if arcs:
        last_arc = arcs[-1]
        total_ep_needed = last_arc.get('ep_end', 0)

    existing_eps = [ep for ep, _ in blueprints] if blueprints else []
    missing_eps = [ep for ep in range(1, total_ep_needed + 1) if ep not in existing_eps]

    # 통계
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("생성된 Blueprint", len(blueprints))
    with col2:
        st.metric("필요한 총 EP", total_ep_needed)
    with col3:
        st.metric("미생성 EP", len(missing_eps))

    st.markdown("---")

    # Blueprint 생성 섹션
    st.markdown("### 🔧 Blueprint 생성")

    if not arcs:
        st.warning("⚠️ Arc 데이터가 없습니다. Stage 2를 먼저 완료하세요.")
    elif missing_eps:
        st.info(f"미생성 에피소드: {missing_eps[:10]}{'...' if len(missing_eps) > 10 else ''}")

        gen_col1, gen_col2 = st.columns(2)
        with gen_col1:
            # 수동 생성
            next_ep_to_gen = missing_eps[0] if missing_eps else 1
            ep_to_generate = st.number_input("생성할 EP 번호", min_value=1, value=next_ep_to_gen)

            if st.button("📝 수동 Blueprint 작성", type="primary"):
                st.session_state.editing_blueprint = ep_to_generate
                st.rerun()

        with gen_col2:
            if st.button("🤖 AI 자동 생성 (main_a.py)", use_container_width=True):
                st.info("""
                **main_a.py에서 Stage 3를 실행하세요.**

                ```bash
                python main_a.py
                → 메뉴 3번 (Blueprint) 선택
                ```
                """)
                add_log("Stage 3 AI 생성 요청", "info")
    else:
        st.success("✅ 모든 Blueprint가 생성되었습니다!")

    # Blueprint 수동 작성/편집 모드
    if st.session_state.get('editing_blueprint'):
        render_blueprint_editor(db, arcs)
        return

    st.markdown("---")

    if not blueprints:
        st.warning("⚠️ Blueprint 데이터가 없습니다.")
        return

    st.markdown(f"**총 {len(blueprints)}개 Blueprint**")

    cols = st.columns(8)
    for i, (ep_num, bp_data) in enumerate(blueprints):
        with cols[i % 8]:
            st.markdown(f"""
            <div class="arc-card" style="background: linear-gradient(135deg, #2d4a3f 0%, #1e3a2f 100%); border-color: #4a9e7f; padding: 10px; text-align: center;">
                <div style="font-weight: 600;">EP {ep_num}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"보기", key=f"view_bp_{ep_num}"):
                st.session_state.viewing_blueprint = ep_num

    # 상세 보기 (시나리오 크게)
    if st.session_state.get('viewing_blueprint'):
        ep = st.session_state.viewing_blueprint
        bp = next((b for e, b in blueprints if e == ep), None)
        if bp:
            st.markdown("---")
            st.markdown(f"## Episode {ep} Blueprint")

            view_col1, view_col2 = st.columns([4, 1])
            with view_col2:
                if st.button("✏️ 편집", key="edit_bp_btn"):
                    st.session_state.editing_blueprint = ep
                    st.session_state.viewing_blueprint = None
                    st.rerun()
                if st.button("❌ 닫기", key="close_bp"):
                    st.session_state.viewing_blueprint = None
                    st.rerun()

            with view_col1:
                # 통합 시나리오 - 크게
                st.markdown("### 📝 통합 시나리오")
                scenario = bp.get('integrated_scenario', '')
                st.markdown(f"""
                <div class="scenario-box">
                    {scenario.replace(chr(10), '<br>')}
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # 씬 분해
            st.markdown("### 🎬 씬 분해")
            with st.expander("씬 분해 상세", expanded=True):
                scene_breakdown = bp.get('scene_breakdown', {})
                if isinstance(scene_breakdown, dict):
                    for scene_key, scene_data in scene_breakdown.items():
                        st.markdown(f"**{scene_key}**")
                        if isinstance(scene_data, dict):
                            for k, v in scene_data.items():
                                st.markdown(f"- {k}: {v}")
                        else:
                            st.markdown(f"{scene_data}")
                        st.markdown("")


def render_blueprint_editor(db, arcs):
    """Blueprint 수동 작성/편집"""
    ep_num = st.session_state.editing_blueprint

    # 해당 EP의 Arc 찾기
    arc_data = None
    for arc in arcs:
        if arc.get('ep_start', 0) <= ep_num <= arc.get('ep_end', 0):
            arc_data = arc
            break

    st.markdown(f"### ✏️ Episode {ep_num} Blueprint 작성")

    if arc_data:
        st.info(f"📌 Arc {arc_data.get('arc_no')} (EP {arc_data.get('ep_start')}~{arc_data.get('ep_end')})")

        # Arc 정보 표시
        with st.expander("📜 Arc 전술 문서 참고"):
            st.markdown(f"""
            <div class="block-card">
                {arc_data.get('tactical_doc', '내용 없음').replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)

    # 기존 Blueprint 로드
    existing_bp = db.get_blueprint(ep_num)

    col1, col2 = st.columns([3, 1])

    with col1:
        # 통합 시나리오
        integrated_scenario = st.text_area(
            "📝 통합 시나리오",
            value=existing_bp.get('integrated_scenario', '') if existing_bp else '',
            height=400,
            help="이 에피소드의 전체 흐름을 서술하세요."
        )

        # 씬 분해
        st.markdown("---")
        st.markdown("**🎬 씬 분해 (Scene Breakdown)**")

        scene_count = st.number_input("씬 개수", min_value=1, max_value=10, value=4)

        scenes = {}
        existing_scenes = existing_bp.get('scene_breakdown', {}) if existing_bp else {}

        for s in range(1, scene_count + 1):
            with st.expander(f"Scene {s}", expanded=s == 1):
                scene_key = f"scene_{s}"
                existing_scene = existing_scenes.get(scene_key, {}) if isinstance(existing_scenes, dict) else {}

                location = st.text_input(f"장소", value=existing_scene.get('location', ''), key=f"loc_{s}")
                characters = st.text_input(f"등장인물", value=existing_scene.get('characters', ''), key=f"char_{s}")
                action = st.text_area(f"액션/내용", value=existing_scene.get('action', ''), height=100, key=f"act_{s}")
                hook = st.text_input(f"훅/전환점", value=existing_scene.get('hook', ''), key=f"hook_{s}")

                scenes[scene_key] = {
                    'location': location,
                    'characters': characters,
                    'action': action,
                    'hook': hook
                }

    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)

        if st.button("💾 저장", type="primary", use_container_width=True):
            blueprint_data = {
                'ep_num': ep_num,
                'integrated_scenario': integrated_scenario,
                'scene_breakdown': scenes,
                'arc_no': arc_data.get('arc_no') if arc_data else None,
                'created_at': datetime.now().isoformat()
            }

            # DB에 저장
            try:
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO blueprints (ep_num, data, created_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (ep_num, json.dumps(blueprint_data, ensure_ascii=False)))
                conn.commit()
                conn.close()

                st.success(f"Episode {ep_num} Blueprint 저장됨!")
                add_log(f"Blueprint EP{ep_num} 저장", "success")

                # txt 파일로도 저장
                save_blueprint_to_txt(st.session_state.current_project, ep_num, blueprint_data)

                st.session_state.editing_blueprint = None
                st.rerun()
            except Exception as e:
                st.error(f"저장 실패: {e}")

        if st.button("❌ 취소", use_container_width=True):
            st.session_state.editing_blueprint = None
            st.rerun()


def save_blueprint_to_txt(project_name, ep_num, blueprint_data):
    """Blueprint txt 파일 저장"""
    plans_dir = Path("projects") / project_name / "plans" / "blueprints"
    plans_dir.mkdir(parents=True, exist_ok=True)

    filepath = plans_dir / f"blueprint_ep{ep_num:04d}.txt"

    lines = [
        f"{'='*60}",
        f"EPISODE {ep_num} BLUEPRINT",
        f"{'='*60}",
        f"",
        f"[통합 시나리오]",
        blueprint_data.get('integrated_scenario', ''),
        f"",
        f"[씬 분해]",
    ]

    scenes = blueprint_data.get('scene_breakdown', {})
    for scene_key, scene_data in scenes.items():
        if isinstance(scene_data, dict):
            lines.append(f"\n{scene_key.upper()}:")
            lines.append(f"  장소: {scene_data.get('location', '')}")
            lines.append(f"  등장인물: {scene_data.get('characters', '')}")
            lines.append(f"  액션: {scene_data.get('action', '')}")
            lines.append(f"  훅: {scene_data.get('hook', '')}")

    filepath.write_text('\n'.join(lines), encoding='utf-8')


# ============================================================
# Stage 4: 원고 생성
# ============================================================
def render_stage_4(db):
    st.markdown("""
    <div class="node-card">
        <div class="node-header">
            <span class="node-title">✍️ Stage 4: 원고 생성</span>
            <span class="node-badge">생산</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    manuscripts = db.get_manuscripts(5)
    all_manuscripts = db.get_manuscripts(1000)

    col1, col2 = st.columns([2, 1])
    with col1:
        if manuscripts:
            latest = manuscripts[0]
            st.success(f"✅ 최신 원고: 제 {latest['ep_num']}화")
            st.metric("총 작성된 원고", f"{len(all_manuscripts)}화")
        else:
            st.warning("⚠️ 생성된 원고가 없습니다.")

    # 다음 화 생성
    st.markdown("---")
    st.markdown("### 📝 다음 화 생성")

    next_ep = len(all_manuscripts) + 1
    st.markdown(f"**생성할 에피소드: 제 {next_ep}화**")

    # Blueprint 미리보기
    blueprint = db.get_blueprint(next_ep)

    if blueprint:
        st.markdown("#### 📋 해당 화 Blueprint")
        with st.expander("Blueprint 미리보기", expanded=True):
            scenario = blueprint.get('integrated_scenario', '')
            st.markdown(f"""
            <div class="scenario-box" style="min-height: 200px;">
                {scenario[:1000].replace(chr(10), '<br>')}{'...' if len(scenario) > 1000 else ''}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # 생성 옵션
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Blueprint 승인 후 생성", type="primary", use_container_width=True):
                st.info("📌 main_a.py에서 Stage 4를 실행하세요.")
                st.code("python main_a.py → 메뉴 4번 선택", language="bash")
                add_log(f"제 {next_ep}화 생성 요청 (승인)", "info")
        with col2:
            if st.button("🤖 Blueprint 기반 자동 진행", use_container_width=True):
                st.info("📌 main_a.py에서 자동 모드로 실행하세요.")
                st.code("python main_a.py → 메뉴 4번 선택", language="bash")
                add_log(f"제 {next_ep}화 자동 생성 요청", "info")
    else:
        st.warning(f"⚠️ 제 {next_ep}화 Blueprint가 없습니다. Stage 3를 먼저 실행하세요.")

    st.markdown("---")
    st.info("""
    **💡 안내**: 원고 생성은 main_a.py에서 진행됩니다.
    - AI 품질 검사, 재시도 로직 등 복잡한 파이프라인이 필요합니다.
    - 대시보드에서는 Blueprint 확인 및 승인을 진행하세요.
    """)


# ============================================================
# HUD 편집기
# ============================================================
def render_hud_editor(db):
    st.markdown("""
    <div class="node-card">
        <div class="node-header">
            <span class="node-title">👤 HUD 상태 편집</span>
            <span class="node-badge">실시간</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    bible = db.load_anchor('bible')
    if not bible:
        st.warning("Bible 데이터가 없습니다.")
        return

    bible_root = bible.get('MasterBible', bible)
    genre = st.session_state.current_genre

    hud_keys = {
        'wuxia': 'MartialHUD',
        'hunter': 'HunterHUD',
        'investment': 'FinanceHUD'
    }

    hud_key = hud_keys.get(genre, 'MartialHUD')
    hud_data = bible_root.get(hud_key, {}).get('Protagonist', {}).get('actual_truth', {})

    st.markdown(f"**{genre.upper()} HUD**")

    if genre == 'wuxia':
        fields = ['name', 'alias', 'realm', 'internal_energy', 'mental_method',
                  'wealth', 'causal_injuries', 'current_objective', 'reputation']
    elif genre == 'hunter':
        fields = ['name', 'awakening_rank', 'mana', 'level', 'skills',
                  'guild', 'wealth', 'injuries', 'current_objective']
    else:
        fields = ['name', 'capital', 'total_assets', 'stocks', 'companies',
                  'reputation', 'connections', 'current_objective']

    col1, col2 = st.columns(2)
    updated_hud = {}

    for i, field in enumerate(fields):
        with col1 if i % 2 == 0 else col2:
            value = hud_data.get(field, '')
            updated_hud[field] = st.text_input(
                field.replace('_', ' ').title(),
                value=str(value) if value else '',
                key=f"hud_{field}"
            )

    if st.button("💾 HUD 저장", type="primary"):
        if hud_key not in bible_root:
            bible_root[hud_key] = {}
        if 'Protagonist' not in bible_root[hud_key]:
            bible_root[hud_key]['Protagonist'] = {}
        bible_root[hud_key]['Protagonist']['actual_truth'] = updated_hud

        if db.save_anchor('bible', bible):
            st.success("HUD 저장 완료!")
            add_log("HUD 업데이트", "success")


# ============================================================
# 캐릭터 관리
# ============================================================
def render_character_manager(db):
    st.markdown("""
    <div class="node-card">
        <div class="node-header">
            <span class="node-title">👥 주요 캐릭터</span>
            <span class="node-badge">NPC</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    bible = db.load_anchor('bible')
    if not bible:
        st.warning("Bible 데이터가 없습니다.")
        return

    bible_root = bible.get('MasterBible', bible)
    npcs = bible_root.get('AssetLibrary', {}).get('KeyNPCs', [])

    if not npcs:
        st.info("등록된 NPC가 없습니다. Stage 0 탭에서 추가하세요.")
        return

    for i, npc in enumerate(npcs):
        name = npc.get('name', npc.get('Name', f'NPC {i+1}'))
        with st.expander(f"👤 {name}"):
            st.json(npc)


# ============================================================
# 주요 사건 관리
# ============================================================
def render_event_manager(db):
    st.markdown("""
    <div class="node-card">
        <div class="node-header">
            <span class="node-title">📌 주요 사건</span>
            <span class="node-badge">메모</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    events_path = Path("projects") / st.session_state.current_project / "config" / "major_events.json"

    events = []
    if events_path.exists():
        try:
            events = json.loads(events_path.read_text(encoding='utf-8'))
        except:
            events = []

    st.markdown("**등록된 사건**")

    for i, event in enumerate(events):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**EP {event.get('ep', '?')}**: {event.get('title', '')}")
            st.caption(event.get('description', ''))
        with col2:
            if st.button("🗑️", key=f"del_event_{i}"):
                del events[i]
                events_path.write_text(json.dumps(events, ensure_ascii=False), encoding='utf-8')
                st.rerun()

    st.markdown("---")
    st.markdown("**새 사건 추가**")

    c1, c2 = st.columns([1, 3])
    with c1:
        new_ep = st.number_input("EP", min_value=1, value=1, key="new_event_ep")
    with c2:
        new_title = st.text_input("제목", key="new_event_title")

    new_desc = st.text_area("설명", key="new_event_desc")

    if st.button("➕ 추가"):
        events.append({
            'ep': new_ep,
            'title': new_title,
            'description': new_desc
        })
        events_path.parent.mkdir(parents=True, exist_ok=True)
        events_path.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding='utf-8')
        st.success("사건 추가됨")
        st.rerun()


# ============================================================
# 복선 트래커
# ============================================================
def render_seeds_tracker(db):
    st.markdown("""
    <div class="node-card">
        <div class="node-header">
            <span class="node-title">🌱 복선 트래커</span>
            <span class="node-badge">Seeds</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    bible = db.load_anchor('bible')
    if not bible:
        st.warning("Bible 데이터가 없습니다.")
        return

    bible_root = bible.get('MasterBible', bible)
    seeds = bible_root.get('Seeds', [])

    if not seeds:
        st.info("등록된 복선이 없습니다.")
        return

    planted = [s for s in seeds if s.get('status') == 'planted']
    recovered = [s for s in seeds if s.get('status') == 'recovered']
    pending = [s for s in seeds if s.get('status') not in ['planted', 'recovered']]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("심어진 복선", len(planted))
    with col2:
        st.metric("회수된 복선", len(recovered))
    with col3:
        st.metric("대기 중", len(pending))

    st.markdown("---")

    for seed in seeds:
        status = seed.get('status', 'pending')
        status_icon = "🌱" if status == 'planted' else "✅" if status == 'recovered' else "⏳"

        with st.expander(f"{status_icon} {seed.get('id', 'Unknown')}"):
            st.markdown(f"**힌트**: {seed.get('hint', 'N/A')}")
            st.markdown(f"**심은 화**: {seed.get('planted_ep', 'N/A')}")
            st.markdown(f"**회수 예정**: {seed.get('target_ep', 'N/A')}")


# ============================================================
# 원고 뷰어 (가로 50%)
# ============================================================
def render_manuscript_viewer(db):
    st.markdown("""
    <div class="node-card">
        <div class="node-header">
            <span class="node-title">📖 원고 뷰어</span>
            <span class="node-badge">읽기</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    manuscripts = db.get_manuscripts(100)

    if not manuscripts:
        st.info("생성된 원고가 없습니다.")
        return

    # 가운데 정렬을 위한 컬럼
    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_center:
        ep_options = [m['ep_num'] for m in reversed(manuscripts)]
        selected_ep = st.selectbox("에피소드 선택", ep_options)

        manuscript = next((m for m in manuscripts if m['ep_num'] == selected_ep), None)

        if manuscript:
            st.markdown(f"### 제 {selected_ep}화: {manuscript.get('title', '')}")
            st.markdown("---")

            content = manuscript.get('content', '')
            st.markdown(f"""
            <div class="manuscript-viewer" style="max-width: 100%;">
                {content.replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")
            st.download_button(
                label="📥 TXT 다운로드",
                data=f"{manuscript.get('title', '')}\n\n{content}",
                file_name=f"ep_{selected_ep:04d}.txt",
                mime="text/plain"
            )


# ============================================================
# 메인
# ============================================================
def main():
    render_sidebar()

    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h1 style="margin: 0; color: #ffffff !important;">🎭 글도비_V0127</h1>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.current_project:
        st.caption(f"현재 프로젝트: **{st.session_state.current_project}**")

    render_stage_tabs()

    st.markdown("---")
    render_logs()


if __name__ == "__main__":
    main()
