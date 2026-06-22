import streamlit as st
import pandas as pd
from datetime import date, timedelta

PRIORITY = ["🔴 긴급", "🟡 보통", "🟢 일반"]
STATUS_OPTIONS = ["📋 예정", "🔧 진행 중", "✅ 완료", "⏸️ 보류"]
CATEGORIES = ["HVAC", "수영장", "Gym 장비", "전기", "배관", "청소", "기타"]

def show():
    st.title("🗓️ 메인트넌스 일정")

    # 바로가기
    st.markdown("**🔗 관련 문서 바로가기**")
    c1, c2, c3 = st.columns(3)
    c1.link_button("📊 Master Status Sheet", "YOUR_MASTER_SHEET_URL", use_container_width=True)
    c2.link_button("📋 Task Tracker",        "YOUR_TASK_TRACKER_URL", use_container_width=True)
    c3.link_button("💬 Slack",               "https://app.slack.com/client/YOUR_WORKSPACE/C0BC4S9AACS", use_container_width=True)
    st.markdown("---")

    if "maintenance_data" not in st.session_state:
        today = date.today()
        st.session_state.maintenance_data = [
            {"작업명": "Gym HVAC 필터 교체",        "카테고리": "HVAC",    "담당": "FM 강성근",      "예정일": str(today + timedelta(days=4)),  "우선순위": "🔴 긴급", "상태": "📋 예정",    "비용($)": 350, "비고": ""},
            {"작업명": "수영장 pH 체크 및 약품 투입","카테고리": "수영장",  "담당": "FM 강성근",      "예정일": str(today),                     "우선순위": "🔴 긴급", "상태": "🔧 진행 중", "비용($)": 120, "비고": "오늘 측정값 이상"},
            {"작업명": "RTU 교체 공사 착공",         "카테고리": "HVAC",    "담당": "Johnstone Supply","예정일": str(today + timedelta(days=10)), "우선순위": "🟡 보통", "상태": "📋 예정",    "비용($)": 0,   "비고": "별도 계약"},
            {"작업명": "수영장 제습기 교체",         "카테고리": "수영장",  "담당": "ADE Systems",    "예정일": str(today + timedelta(days=14)), "우선순위": "🟡 보통", "상태": "📋 예정",    "비용($)": 0,   "비고": "PO 발행 완료"},
        ]

    df = pd.DataFrame(st.session_state.maintenance_data)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("전체 작업", len(df))
    c2.metric("🔴 긴급",   len(df[df["우선순위"] == "🔴 긴급"]))
    c3.metric("🔧 진행 중",len(df[df["상태"] == "🔧 진행 중"]))
    c4.metric("✅ 완료",   len(df[df["상태"] == "✅ 완료"]))
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1: f_cat      = st.selectbox("카테고리", ["전체"] + CATEGORIES)
    with col2: f_priority = st.selectbox("우선순위", ["전체"] + PRIORITY)
    with col3: f_status   = st.selectbox("상태",     ["전체"] + STATUS_OPTIONS)

    fdf = df.copy()
    if f_cat      != "전체": fdf = fdf[fdf["카테고리"] == f_cat]
    if f_priority != "전체": fdf = fdf[fdf["우선순위"] == f_priority]
    if f_status   != "전체": fdf = fdf[fdf["상태"] == f_status]
    st.dataframe(fdf, use_container_width=True, hide_index=True)
    st.markdown("---")

    tab1, tab2 = st.tabs(["✏️ 상태 업데이트", "➕ 작업 추가"])

    with tab1:
        with st.form("maint_update"):
            task_names = [m["작업명"] for m in st.session_state.maintenance_data]
            selected   = st.selectbox("작업 선택", task_names)
            col_a, col_b = st.columns(2)
            with col_a:
                new_status = st.selectbox("상태 변경", STATUS_OPTIONS)
                new_date   = st.date_input("예정일 변경")
            with col_b:
                new_cost = st.number_input("실제 비용 ($)", min_value=0, step=50)
                note     = st.text_input("비고")
            if st.form_submit_button("업데이트", type="primary", use_container_width=True):
                for item in st.session_state.maintenance_data:
                    if item["작업명"] == selected:
                        item["상태"] = new_status
                        item["예정일"] = str(new_date)
                        if new_cost > 0: item["비용($)"] = new_cost
                        if note: item["비고"] = note
                try:
                    from sheets_helper import append_row, save_indicator
                    row = [str(date.today()), selected, new_status, str(new_date), new_cost, note]
                    ok = append_row("메인트넌스", row)
                    save_indicator(ok, selected)
                except Exception:
                    st.warning("⚠️ Sheets 미연결 — 세션에만 저장됨")
                st.rerun()

    with tab2:
        with st.form("maint_add"):
            col_a, col_b = st.columns(2)
            with col_a:
                name      = st.text_input("작업명")
                category  = st.selectbox("카테고리", CATEGORIES)
                assignee  = st.text_input("담당자", value="FM 강성근")
            with col_b:
                priority  = st.selectbox("우선순위", PRIORITY)
                plan_date = st.date_input("예정일")
                cost      = st.number_input("예상 비용 ($)", min_value=0, step=50)
            note = st.text_input("비고")
            if st.form_submit_button("추가", type="primary", use_container_width=True):
                if name:
                    new_item = {
                        "작업명": name, "카테고리": category, "담당": assignee,
                        "예정일": str(plan_date), "우선순위": priority,
                        "상태": "📋 예정", "비용($)": cost, "비고": note
                    }
                    st.session_state.maintenance_data.append(new_item)
                    try:
                        from sheets_helper import append_row, save_indicator
                        row = [str(date.today()), name, category, assignee,
                               str(plan_date), priority, "📋 예정", cost, note]
                        ok = append_row("메인트넌스", row)
                        save_indicator(ok, name)
                    except Exception:
                        st.warning("⚠️ Sheets 미연결 — 세션에만 저장됨")
                    st.rerun()
