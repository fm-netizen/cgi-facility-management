import streamlit as st
import pandas as pd

STATUS_OPTIONS = ["🟢 정상", "🟡 점검 필요", "🔴 고장", "🔧 수리 중", "🔄 교체 예정"]
CATEGORIES = ["HVAC", "수영장", "Gym 장비", "전기", "배관", "기타"]

def show():
    st.title("⚙️ 설비 상황")
    st.markdown("---")

    # Filter row
    col1, col2 = st.columns(2)
    with col1:
        filter_cat = st.selectbox("카테고리", ["전체"] + CATEGORIES)
    with col2:
        filter_status = st.selectbox("상태", ["전체"] + STATUS_OPTIONS)

    st.markdown("---")

    if "equipment_data" not in st.session_state:
        st.session_state.equipment_data = [
            # HVAC
            {"설비명": "RTU #1 (York 5-ton)", "카테고리": "HVAC", "위치": "옥상", "상태": "🔄 교체 예정",
             "마지막점검": "2026-05-01", "다음점검": "2026-07-01", "비고": "Johnstone Supply 발주 중"},
            {"설비명": "RTU #2 (York 7.5-ton)", "카테고리": "HVAC", "위치": "옥상", "상태": "🔄 교체 예정",
             "마지막점검": "2026-05-01", "다음점검": "2026-07-01", "비고": "R-454B A2L 냉매"},
            {"설비명": "RTU #3 (York 7.5-ton)", "카테고리": "HVAC", "위치": "옥상", "상태": "🔄 교체 예정",
             "마지막점검": "2026-05-01", "다음점검": "2026-07-01", "비고": "R-454B A2L 냉매"},
            # Pool
            {"설비명": "제습기 (DCA3600Y)", "카테고리": "수영장", "위치": "수영장", "상태": "🔄 교체 예정",
             "마지막점검": "2026-06-01", "다음점검": "2026-07-15", "비고": "ADE Systems PO 완료"},
            {"설비명": "수영장 펌프 #1", "카테고리": "수영장", "위치": "기계실", "상태": "🟢 정상",
             "마지막점검": "2026-06-10", "다음점검": "2026-07-10", "비고": ""},
            {"설비명": "수영장 히터", "카테고리": "수영장", "위치": "기계실", "상태": "🟢 정상",
             "마지막점검": "2026-06-10", "다음점검": "2026-07-10", "비고": ""},
            # Gym
            {"설비명": "Life Fitness CPQ-51716", "카테고리": "Gym 장비", "위치": "Gym", "상태": "🔄 교체 예정",
             "마지막점검": "2026-06-01", "다음점검": "-", "비고": "계약 완료"},
            {"설비명": "Life Fitness CPQ-51815", "카테고리": "Gym 장비", "위치": "Gym", "상태": "🔄 교체 예정",
             "마지막점검": "2026-06-01", "다음점검": "-", "비고": "계약 완료"},
            {"설비명": "Hoist RS-2201", "카테고리": "Gym 장비", "위치": "Gym", "상태": "🟡 점검 필요",
             "마지막점검": "2026-05-15", "다음점검": "2026-06-30", "비고": "별도 진행 중"},
            {"설비명": "Precor AMT 885", "카테고리": "Gym 장비", "위치": "Gym", "상태": "🟡 점검 필요",
             "마지막점검": "2026-05-15", "다음점검": "2026-06-30", "비고": "별도 진행 중"},
        ]

    data = st.session_state.equipment_data
    df = pd.DataFrame(data)

    if filter_cat != "전체":
        df = df[df["카테고리"] == filter_cat]
    if filter_status != "전체":
        df = df[df["상태"] == filter_status]

    # Status summary metrics
    all_df = pd.DataFrame(st.session_state.equipment_data)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("전체 설비", len(all_df))
    c2.metric("🟢 정상", len(all_df[all_df["상태"] == "🟢 정상"]))
    c3.metric("⚠️ 점검·교체", len(all_df[all_df["상태"].isin(["🟡 점검 필요", "🔄 교체 예정"])]))
    c4.metric("🔴 고장·수리", len(all_df[all_df["상태"].isin(["🔴 고장", "🔧 수리 중"])]))

    st.markdown("---")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # --- Update / Add ---
    tab1, tab2 = st.tabs(["✏️ 상태 업데이트", "➕ 설비 추가"])

    with tab1:
        with st.form("equipment_update"):
            equip_names = [e["설비명"] for e in st.session_state.equipment_data]
            selected = st.selectbox("설비 선택", equip_names)
            col_a, col_b = st.columns(2)
            with col_a:
                new_status = st.selectbox("새 상태", STATUS_OPTIONS)
                next_check = st.date_input("다음 점검일")
            with col_b:
                note = st.text_area("비고")
            if st.form_submit_button("업데이트", type="primary", use_container_width=True):
                for item in st.session_state.equipment_data:
                    if item["설비명"] == selected:
                        item["상태"] = new_status
                        item["다음점검"] = str(next_check)
                        item["비고"] = note
                st.success(f"✅ {selected} 업데이트 완료")
                st.rerun()

    with tab2:
        with st.form("equipment_add"):
            col_a, col_b = st.columns(2)
            with col_a:
                name = st.text_input("설비명")
                category = st.selectbox("카테고리", CATEGORIES)
                location = st.text_input("위치")
            with col_b:
                status = st.selectbox("상태", STATUS_OPTIONS)
                last_check = st.date_input("마지막 점검일")
                next_check = st.date_input("다음 점검일")
            note = st.text_input("비고")
            if st.form_submit_button("추가", type="primary", use_container_width=True):
                if name:
                    st.session_state.equipment_data.append({
                        "설비명": name, "카테고리": category, "위치": location,
                        "상태": status, "마지막점검": str(last_check),
                        "다음점검": str(next_check), "비고": note
                    })
                    st.success(f"✅ {name} 추가 완료")
                    st.rerun()
