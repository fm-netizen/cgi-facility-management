"""📊 관리 (팀장 전용) — 대시보드 · 팀 현황 · 작업 티켓(검수) · 정기 업무 · 시트 바로가기."""
import streamlit as st

from pages_content import home, maintenance, today
from pages_content import work_orders as wop
from pages_content.field_input import _check_pin
from sheets_config import PROJECT_FOLDERS
from ui_links import link_buttons
from user_ctx import current_user, is_manager


def show():
    st.title("📊 관리 (팀장 전용)")
    if not _check_pin():
        return
    me, role = current_user(show_picker=False)
    if not is_manager(role):
        st.warning("팀장 전용 화면입니다.")
        return
    t1, t2, t3, t4 = st.tabs(["📊 대시보드", "👥 팀 현황", "🎫 작업 티켓·검수", "🗓️ 정기 업무"])
    with t1:
        home.show(embedded=True)
    with t2:
        today.team_status()
        with st.expander("📁 공사 프로젝트 폴더"):
            for name, links in PROJECT_FOLDERS.items():
                st.markdown(f"**{name}**")
                link_buttons(links)
    with t3:
        wop.show(embedded=True)
    with t4:
        maintenance.show(embedded=True)
