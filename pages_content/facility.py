import streamlit as st

import asset_store as A
from pages_content.field_input import _check_pin
from sheets_config import MASTER_SHEET_URL, TASK_TRACKER_URL, DRIVE_FOLDER_URL
from ui_links import link_buttons

VIEW = ["구역ID", "구역명", "현재 상태", "최근 기록", "온도(°F)", "습도(%)", "최근 비고", "관련 할 일#"]


def _author():
    a = st.text_input("기록자", value=st.session_state.get("me") or st.session_state.get("author", ""),
                      placeholder="예: SeungOh Suh").strip()
    st.session_state.author = a
    return a


def show():
    st.title("🏢 시설 상황")
    link_buttons([("📊 설비·시설 대장", MASTER_SHEET_URL),
                  ("📋 할 일 관리표", TASK_TRACKER_URL),
                  ("📁 공사 폴더", DRIVE_FOLDER_URL)])

    data = A.load_assets()
    if data is None:
        st.warning("⚠️ 설비·시설 대장을 불러올 수 없습니다. " + st.session_state.get("asset_error", ""))
        return
    zones = data["zones"]
    c = A.counts(zones)
    m = st.columns(5)
    m[0].metric("전체 구역", c["전체"])
    m[1].metric("🟢 정상", c["🟢 정상"])
    m[2].metric("🟡 점검 필요", c["🟡 점검 필요"])
    m[3].metric("🔧 수리·공사 중", c["🔧 수리·공사 중"])
    m[4].metric("🔴 고장·이상", c["🔴 고장·이상"])

    f = st.selectbox("상태 필터", ["전체", "정상 아님"] + A.STATUSES)
    view = zones
    if f == "정상 아님":
        view = zones[zones["현재 상태"] != A.NORMAL]
    elif f != "전체":
        view = zones[zones["현재 상태"] == f]
    st.dataframe(view[VIEW], width="stretch", hide_index=True)

    st.markdown("---")
    st.subheader("✏️ 상태 기록")
    st.caption("기록은 '📝 상태 기록' 탭에 한 줄씩 쌓이고, 표는 가장 최근 기록을 보여줍니다.")
    if not _check_pin():
        return
    labels = [f"{r['구역ID']} · {r['구역명']}" for _, r in zones.iterrows()]
    if not labels:
        st.info("구역이 없습니다. 대장의 '🏢 시설 구역' 탭에 먼저 등록하세요.")
        return
    author = _author()
    pick = st.selectbox("구역", labels)
    zid = pick.split(" · ")[0]
    cur = zones.set_index("구역ID")["현재 상태"].get(zid, A.NORMAL)
    st.caption(f"현재: {cur}")
    with st.form("zone_status", clear_on_submit=True):
        status = st.selectbox("상태", A.STATUSES,
                              index=A.STATUSES.index(cur) if cur in A.STATUSES else 0)
        col1, col2, col3 = st.columns(3)
        temp = col1.text_input("온도 (°F)", placeholder="예: 82")
        hum = col2.text_input("습도 (%)", placeholder="예: 55")
        ref = col3.text_input("관련 할 일#/WO#", placeholder="선택")
        note = st.text_area("비고", placeholder="점검 결과·특이사항")
        if st.form_submit_button("기록", type="primary", width="stretch"):
            if not author:
                st.error("기록자 이름을 입력하세요.")
            else:
                ok, msg = A.add_status("시설", zid, status, note, author, temp, hum, ref)
                (st.success if ok else st.error)(msg)

    with st.expander("🕘 구역별 기록 이력"):
        hz = st.selectbox("구역 선택", labels, key="zone_hist").split(" · ")[0]
        h = A.load_history(hz)
        if h is None or h.empty:
            st.caption("기록 없음")
        else:
            st.dataframe(h, width="stretch", hide_index=True)
