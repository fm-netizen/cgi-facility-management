import streamlit as st

st.set_page_config(
    page_title="CGI Facility Management",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Quick Links 설정 (실제 URL로 교체) ──────────────────────
QUICK_LINKS = {
    "📊 Master Status Sheet": "YOUR_MASTER_SHEET_URL",
    "📋 Task Tracker":        "YOUR_TASK_TRACKER_URL",
    "📁 Google Drive":        "YOUR_DRIVE_FOLDER_URL",
    "💬 Slack":               "https://app.slack.com/client/YOUR_WORKSPACE/C0BC4S9AACS",
}

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
    "🏠 홈":              "home",
    "🏢 시설 상황":        "facility",
    "⚙️ 설비 상황":        "equipment",
    "🗓️ 메인트넌스 일정":  "maintenance",
    "📝 메모":             "memo",
}

if "page" not in st.session_state:
    st.session_state.page = "home"

for label, key in pages.items():
    if st.sidebar.button(
        label,
        use_container_width=True,
        type="primary" if st.session_state.page == key else "secondary"
    ):
        st.session_state.page = key

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
st.sidebar.caption("CGI Holistic Fitness & Spa\n111 Homans Ave, Closter, NJ\nv1.1 · 2026")

# ── Page Router ──────────────────────────────────────────────
page = st.session_state.page

if page == "home":
    from pages_content import home; home.show()
elif page == "facility":
    from pages_content import facility; facility.show()
elif page == "equipment":
    from pages_content import equipment; equipment.show()
elif page == "maintenance":
    from pages_content import maintenance; maintenance.show()
elif page == "memo":
    from pages_content import memo; memo.show()
