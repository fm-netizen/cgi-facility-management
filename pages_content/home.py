import streamlit as st
from sheets_config import MASTER_SHEET_URL, TASK_TRACKER_URL, DRIVE_FOLDER_URL, SLACK_URL
from datetime import date

def show():
    st.title("🏠 CGI Facility Management")
    st.caption(f"111 Homans Ave, Closter, NJ · {date.today().strftime('%Y년 %m월 %d일')}")

    # ── 상단 바로가기 버튼 ──────────────────────────────────
    st.markdown("**🔗 빠른 바로가기**")
    q1, q2, q3, q4 = st.columns(4)
    q1.link_button("📊 Master Status Sheet", MASTER_SHEET_URL,  use_container_width=True)
    q2.link_button("📋 Task Tracker",        TASK_TRACKER_URL,  use_container_width=True)
    q3.link_button("📁 Google Drive",        DRIVE_FOLDER_URL,  use_container_width=True)
    q4.link_button("💬 Slack #cgi-facility-dev", SLACK_URL, use_container_width=True)
    st.markdown("---")

    # ── KPI ────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("전체 시설 상태", "양호",  delta="정상 운영 중")
    with col2: st.metric("설비 이상 건수", "2건",   delta="점검 필요",    delta_color="inverse")
    with col3: st.metric("이번 달 작업",   "4건",   delta="1건 완료")
    with col4: st.metric("미완료 메모",    "3건")
    st.markdown("---")

    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("📊 시설 현황 요약")
        facility_data = {
            "구역":       ["수영장", "Gym",    "로커룸 (남)", "로커룸 (여)", "사무실",    "공용 복도"],
            "상태":       ["🟢 정상","🟡 점검중","🟢 정상",   "🟢 정상",    "🟢 정상",   "🟢 정상"],
            "마지막 점검":["2026-06-15","2026-06-20","2026-06-18","2026-06-18","2026-06-10","2026-06-19"],
        }
        st.dataframe(facility_data, use_container_width=True, hide_index=True)

    with col_r:
        st.subheader("⚠️ 긴급 알림")
        st.warning("⚙️ **Gym HVAC 필터 교체** 필요 — 2026-06-25 예정")
        st.warning("💧 **수영장 pH 수치** 재확인 필요 — 오늘 측정값 이상")
        st.info("✅ 수영장 제습기 교체 PO 발행 완료 (ADE Systems)")

    st.markdown("---")

    # ── 내부 메뉴 이동 ──────────────────────────────────────
    st.subheader("📋 화면 이동")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        if st.button("🏢 시설 상황",      use_container_width=True): st.session_state.page = "facility";    st.rerun()
    with m2:
        if st.button("⚙️ 설비 상황",      use_container_width=True): st.session_state.page = "equipment";   st.rerun()
    with m3:
        if st.button("🗓️ 메인트넌스",     use_container_width=True): st.session_state.page = "maintenance"; st.rerun()
    with m4:
        if st.button("📝 메모",           use_container_width=True): st.session_state.page = "memo";        st.rerun()
