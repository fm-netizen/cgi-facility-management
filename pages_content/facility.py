import streamlit as st
from sheets_config import MASTER_SHEET_URL, TASK_TRACKER_URL, DRIVE_FOLDER_URL, SLACK_URL
import pandas as pd
from datetime import date

ZONES = ["수영장", "Gym", "로커룸 (남)", "로커룸 (여)", "사무실", "공용 복도", "기계실"]
STATUS_OPTIONS = ["🟢 정상", "🟡 점검 필요", "🔴 이상 발생", "🔧 수리 중"]

def show():
    st.title("🏢 시설 상황")

    # 상단 바로가기
    st.markdown("**🔗 관련 문서 바로가기**")
    c1, c2, c3 = st.columns(3)
    c1.link_button("📊 Master Status Sheet", MASTER_SHEET_URL, use_container_width=True)
    c2.link_button("📋 Task Tracker", TASK_TRACKER_URL, use_container_width=True)
    c3.link_button("📁 Google Drive", DRIVE_FOLDER_URL, use_container_width=True)
    st.markdown("---")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_status = st.selectbox("상태 필터", ["전체"] + STATUS_OPTIONS)
    with col_f2:
        filter_zone = st.selectbox("구역 필터", ["전체"] + ZONES)

    st.markdown("---")

    if "facility_data" not in st.session_state:
        st.session_state.facility_data = [
            {"구역": "수영장",    "상태": "🟢 정상",    "온도": "82°F", "습도": "55%", "비고": "제습기 교체 예정"},
            {"구역": "Gym",       "상태": "🟡 점검 필요","온도": "70°F", "습도": "45%", "비고": "HVAC 필터 교체 필요"},
            {"구역": "로커룸 (남)","상태": "🟢 정상",   "온도": "72°F", "습도": "50%", "비고": ""},
            {"구역": "로커룸 (여)","상태": "🟢 정상",   "온도": "72°F", "습도": "50%", "비고": ""},
            {"구역": "사무실",    "상태": "🟢 정상",    "온도": "71°F", "습도": "48%", "비고": ""},
            {"구역": "공용 복도", "상태": "🟢 정상",    "온도": "70°F", "습도": "47%", "비고": ""},
            {"구역": "기계실",    "상태": "🔧 수리 중", "온도": "75°F", "습도": "52%", "비고": "RTU 교체 진행 중"},
        ]

    df = pd.DataFrame(st.session_state.facility_data)
    if filter_status != "전체": df = df[df["상태"] == filter_status]
    if filter_zone   != "전체": df = df[df["구역"] == filter_zone]
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("---")

    st.subheader("✏️ 상태 업데이트")
    with st.form("facility_update_form"):
        col1, col2 = st.columns(2)
        with col1:
            zone     = st.selectbox("구역", ZONES)
            status   = st.selectbox("상태", STATUS_OPTIONS)
        with col2:
            temp     = st.text_input("온도 (°F)", placeholder="예: 72")
            humidity = st.text_input("습도 (%)",  placeholder="예: 50")
        note = st.text_area("비고", placeholder="특이사항 입력")
        submitted = st.form_submit_button("업데이트", type="primary", use_container_width=True)

        if submitted:
            for item in st.session_state.facility_data:
                if item["구역"] == zone:
                    item["상태"] = status
                    if temp:     item["온도"] = f"{temp}°F"
                    if humidity: item["습도"] = f"{humidity}%"
                    item["비고"] = note

            # Sheets 저장
            try:
                from sheets_helper import append_row, save_indicator
                row = [str(date.today()), zone, status,
                       f"{temp}°F" if temp else "", f"{humidity}%" if humidity else "", note]
                ok = append_row("시설 상황", row)
                save_indicator(ok, zone)
            except Exception:
                st.warning("⚠️ Sheets 미연결 — 세션에만 저장됨")
            st.rerun()
