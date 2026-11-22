import streamlit as st

import asset_store as A
from pages_content.field_input import _check_pin
from sheets_config import MASTER_SHEET_URL, TASK_TRACKER_URL
from ui_links import link_buttons
import voice

VIEW = ["설비ID", "설비명", "카테고리", "구역ID", "현재 상태", "최근 비고", "다음 점검", "정기 PM ID",
        "담당", "관련 할 일#"]


def show(embedded=False):
    if not embedded:
        st.title("⚙️ 설비 상황")
        link_buttons([("📊 설비·시설 대장", MASTER_SHEET_URL),
                      ("📋 할 일 관리표", TASK_TRACKER_URL)])

    data = A.load_assets()
    if data is None:
        st.warning("⚠️ 설비·시설 대장을 불러올 수 없습니다. 시트가 서비스 계정(fm-assistant)에 편집자로 공유되어 있는지 확인하세요. "
                   + st.session_state.get("asset_error", ""))
        return
    eq, zones = data["equip"], data["zones"]
    c = A.counts(eq)
    m = st.columns(5)
    m[0].metric("전체 설비", c["전체"])
    m[1].metric("🟢 정상", c["🟢 정상"])
    m[2].metric("🟡 점검 필요", c["🟡 점검 필요"])
    m[3].metric("🔧·🔴 수리·고장", c["🔧 수리·공사 중"] + c["🔴 고장·이상"])
    m[4].metric("🔄 교체 예정", c["🔄 교체 예정"])

    f1, f2, f3 = st.columns(3)
    fs = f1.selectbox("상태", ["전체", "정상 아님"] + A.STATUSES, key="eq_fs")
    fc = f2.selectbox("카테고리", ["전체"] + sorted(eq["카테고리"].replace("", "기타").unique().tolist()))
    fz = f3.selectbox("구역", ["전체"] + zones["구역ID"].tolist())
    view = eq
    if fs == "정상 아님":
        view = view[view["현재 상태"] != A.NORMAL]
    elif fs != "전체":
        view = view[view["현재 상태"] == fs]
    if fc != "전체":
        view = view[view["카테고리"] == fc]
    if fz != "전체":
        view = view[view["구역ID"] == fz]
    st.dataframe(view[VIEW], width="stretch", hide_index=True)

    st.markdown("---")
    if not embedded and not _check_pin():
        return
    author = st.text_input("기록자", value=st.session_state.get("me") or st.session_state.get("author", ""),
                           placeholder="예: Jay Choi").strip()
    st.session_state.author = author
    tab1, tab2, tab3 = st.tabs(["✏️ 상태 기록", "🕘 이력", "➕ 설비 추가"])
    labels = [f"{r['설비ID']} · {r['설비명']}" for _, r in eq.iterrows()]

    with tab1:
        if not labels:
            st.info("등록된 설비가 없습니다.")
        else:
            pick = st.selectbox("설비", labels, key="eq_pick")
            eid = pick.split(" · ")[0]
            cur = eq.set_index("설비ID")["현재 상태"].get(eid, A.NORMAL)
            st.caption(f"현재: {cur}")
            spoken = voice.voice_box("eq_voice", "🎤 말로 점검 결과 입력")
            vn = st.session_state.get("eq_voice_n", 0)
            with st.form(f"eq_status_{vn}", clear_on_submit=True):
                status = st.selectbox("상태", A.STATUSES,
                                      index=A.STATUSES.index(cur) if cur in A.STATUSES else 0)
                ref = st.text_input("관련 할 일#/WO#", placeholder="선택")
                note = st.text_area("비고", value=spoken, placeholder="점검 결과·고장 증상·조치 내용",
                                    key=f"eq_note_{vn}_{len(spoken)}")
                if st.form_submit_button("기록", type="primary", width="stretch"):
                    if not author:
                        st.error("기록자 이름을 입력하세요.")
                    else:
                        ok, msg = A.add_status("설비", eid, status, note, author, ref=ref)
                        (st.success if ok else st.error)(msg)
                        if ok:
                            voice.clear("eq_voice")

    with tab2:
        if labels:
            hid = st.selectbox("설비", labels, key="eq_hist").split(" · ")[0]
            h = A.load_history(hid)
            if h is None or h.empty:
                st.caption("기록 없음")
            else:
                st.dataframe(h, width="stretch", hide_index=True)

    with tab3:
        zlabels = [f"{r['구역ID']} · {r['구역명']}" for _, r in zones.iterrows()]
        with st.form("eq_add", clear_on_submit=True):
            a1, a2 = st.columns(2)
            name = a1.text_input("설비명 *")
            cat = a2.selectbox("카테고리", A.CATEGORIES)
            zone = a1.selectbox("구역 *", zlabels) if zlabels else ""
            loc = a2.text_input("위치 상세")
            model = a1.text_input("제조사·모델")
            owner = a2.text_input("담당 (내부/업체)", value="기술")
            pm = a1.text_input("정기 PM ID", placeholder="예: PM-04")
            nxt = a2.text_input("다음 점검 (YYYY-MM-DD)")
            status = st.selectbox("초기 상태", A.STATUSES)
            note = st.text_input("비고")
            if st.form_submit_button("추가", type="primary", width="stretch"):
                if not name or not zone:
                    st.error("설비명과 구역은 필수입니다.")
                elif not author:
                    st.error("기록자 이름을 입력하세요.")
                else:
                    rec = {"설비명": name, "카테고리": cat, "구역ID": zone.split(" · ")[0],
                           "위치 상세": loc, "제조사·모델": model, "담당": owner,
                           "정기 PM ID": pm, "다음 점검": nxt}
                    ok, msg = A.add_equipment(eq, rec, status, note, author)
                    (st.success if ok else st.error)(msg)
