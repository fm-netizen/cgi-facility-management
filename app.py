import streamlit as st

st.set_page_config(
    page_title="CGI Facility Management",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Quick Links 설정 (sheets_config.py에서 관리) ──────────────
from sheets_config import QUICK_LINKS

# ── Sidebar ──────────────────────────────────────────────────
st.sidebar.markdown(
    "<div style='text-align:center; padding:10px 0;'>"
    "<span style='font-size:28px'>🏢</span><br>"
    "<b style='font-size:14px'>CGI Facility</b><br>"
    "<span style='font-size:10px; color:#aaa'>Management System</span>"
    "</div>",
    unsafe_allow_html=True
)
st.sidebar.markdown("---")

# Navigation
st.sidebar.markdown("**📋 메뉴**")
pages = {
    "🗓 오늘":   "today",
    "➕ 등록":   "register",
    "🏢 현황":   "status",
}
MANAGER_PAGES = {"📊 관리 (팀장 전용)": "manage"}
# 예전 화면 이름 → 새 화면 (버튼·링크 호환)
ALIASES = {"report": "register", "field_input": "register", "memo": "register",
           "equipment": "status", "facility": "status",
           "home": "manage", "work_orders": "manage", "maintenance": "manage"}

# 역할 판별 (👷 작업자 탭의 '역할'이 팀장이면 관리자 메뉴)
_role = ""
try:
    from user_ctx import workers as _workers, is_manager as _is_mgr
    _me = st.session_state.get("me") or st.query_params.get("me")
    _w = _workers()
    if _me and _w is not None and _me in _w["이름"].tolist():
        _role = _w.set_index("이름")["역할"].get(_me, "")
        st.sidebar.caption(f"👤 {_me} · {_role or '작업자'}")
except Exception:
    _is_mgr = lambda r: False
if _is_mgr(_role):
    pages = {**pages, **MANAGER_PAGES}

if "page" not in st.session_state:
    st.session_state.page = "today"
st.session_state.page = ALIASES.get(st.session_state.page, st.session_state.page)

def _go(target):
    st.session_state.page = target      # 콜백: 화면을 그리기 전에 페이지 변경 → 버튼 강조가 즉시 일치


for label, key in pages.items():
    st.sidebar.button(
        label,
        key=f"nav_{key}",
        width="stretch",
        type="primary" if st.session_state.page == key else "secondary",
        on_click=_go, args=(key,),
    )

st.sidebar.markdown("---")

# ── Quick Links (사이드바) ────────────────────────────────────
st.sidebar.markdown("**🔗 바로가기**")
for label, url in QUICK_LINKS.items():
    if url.startswith("YOUR"):
        st.sidebar.markdown(
            f"<a style='display:block; padding:6px 8px; margin:3px 0; "
            f"background:#2E4057; color:#aaa; border-radius:6px; "
            f"text-decoration:none; font-size:12px; text-align:center;'>"
            f"{label} ⚙️ 미설정</a>",
            unsafe_allow_html=True
        )
    else:
        st.sidebar.markdown(
            f"<a href='{url}' target='_blank' "
            f"style='display:block; padding:6px 8px; margin:3px 0; "
            f"background:#048A81; color:white; border-radius:6px; "
            f"text-decoration:none; font-size:12px; text-align:center;'>"
            f"{label} ↗</a>",
            unsafe_allow_html=True
        )

# Sheets 연동 상태
st.sidebar.markdown("---")
try:
    from sheets_helper import is_connected
    connected = is_connected()
    status_color = "#1db954" if connected else "#e67e22"
    status_text  = "Sheets 연동됨 ✅" if connected else "Sheets 미연결 ⚙️"
except Exception:
    status_color = "#e67e22"
    status_text  = "Sheets 미연결 ⚙️"

st.sidebar.markdown(
    f"<div style='text-align:center; padding:4px; "
    f"background:{status_color}22; border-radius:6px; "
    f"color:{status_color}; font-size:11px;'>{status_text}</div>",
    unsafe_allow_html=True
)

st.sidebar.markdown("---")
st.sidebar.caption("CGI Holistic Fitness & Spa\n111 Homans Ave, Closter, NJ\nv1.6.1 · 2026")

# ── Page Router ──────────────────────────────────────────────
page = st.session_state.page

if page == "register":
    from pages_content import register; register.show()
elif page == "status":
    from pages_content import status; status.show()
elif page == "manage":
    from pages_content import manage; manage.show()
else:
    from pages_content import today; today.show()
