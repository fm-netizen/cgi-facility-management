import streamlit as st
from datetime import datetime, date

TAGS = ["일반", "긴급", "HVAC", "수영장", "Gym", "전기", "배관", "Vendor", "CEO 보고"]

def show():
    st.title("📝 메모")

    # 바로가기
    st.markdown("**🔗 관련 문서 바로가기**")
    c1, c2, c3 = st.columns(3)
    c1.link_button("📋 Task Tracker",  "YOUR_TASK_TRACKER_URL", use_container_width=True)
    c2.link_button("💬 Slack",         "https://app.slack.com/client/YOUR_WORKSPACE/C0BC4S9AACS", use_container_width=True)
    c3.link_button("📁 Google Drive",  "YOUR_DRIVE_FOLDER_URL", use_container_width=True)
    st.markdown("---")

    if "memos" not in st.session_state:
        st.session_state.memos = [
            {"제목": "RTU 교체 Johnstone 담당자 연락처", "내용": "담당: Mike Johnson / 201-555-0192\n견적 유효기간: 2026-07-31", "태그": "HVAC",    "작성일": "2026-06-10 09:00", "완료": False},
            {"제목": "ADE Systems 설치 일정 확인 필요",  "내용": "PO 발행 완료. 설치 날짜 확정 요청.",                          "태그": "수영장",   "작성일": "2026-06-15 14:30", "완료": False},
            {"제목": "CEO 보고 — 6월 격주 미팅",         "내용": "RTU, 제습기, Gym 장비 현황 보고 준비.",                        "태그": "CEO 보고", "작성일": "2026-06-18 10:00", "완료": False},
        ]

    # 새 메모
    with st.expander("➕ 새 메모 작성", expanded=False):
        with st.form("memo_form"):
            col1, col2 = st.columns([3, 1])
            with col1: title = st.text_input("제목")
            with col2: tag   = st.selectbox("태그", TAGS)
            content = st.text_area("내용", height=100)
            if st.form_submit_button("저장", type="primary", use_container_width=True):
                if title:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.memos.insert(0, {
                        "제목": title, "내용": content, "태그": tag,
                        "작성일": now, "완료": False
                    })
                    try:
                        from sheets_helper import append_row, save_indicator
                        row = [str(date.today()), now, title, tag, content, "미완료"]
                        ok = append_row("메모", row)
                        save_indicator(ok, title)
                    except Exception:
                        st.warning("⚠️ Sheets 미연결 — 세션에만 저장됨")
                    st.rerun()

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1: f_tag  = st.selectbox("태그 필터", ["전체"] + TAGS)
    with col2: f_done = st.selectbox("완료 여부", ["전체", "미완료", "완료"])

    memos = st.session_state.memos
    if f_tag  != "전체":   memos = [m for m in memos if m["태그"] == f_tag]
    if f_done == "미완료": memos = [m for m in memos if not m["완료"]]
    elif f_done == "완료": memos = [m for m in memos if m["완료"]]

    st.markdown(f"**{len(memos)}개** 메모")
    st.markdown("---")

    tag_icons = {"긴급": "🔴", "CEO 보고": "🟣", "HVAC": "🔵", "수영장": "🌊", "Gym": "💪"}

    for memo in memos:
        orig_idx = st.session_state.memos.index(memo)
        icon = "✅" if memo["완료"] else "📋"
        tag_icon = tag_icons.get(memo["태그"], "⚪")

        col_title, col_btn1, col_btn2 = st.columns([6, 1, 1])
        with col_title:
            st.markdown(f"**{icon} {memo['제목']}** &nbsp; {tag_icon} `{memo['태그']}` &nbsp; *{memo['작성일']}*")
        with col_btn1:
            if st.button("완료" if not memo["완료"] else "미완료", key=f"done_{orig_idx}", use_container_width=True):
                st.session_state.memos[orig_idx]["완료"] = not memo["완료"]
                st.rerun()
        with col_btn2:
            if st.button("삭제", key=f"del_{orig_idx}", use_container_width=True):
                st.session_state.memos.pop(orig_idx)
                st.rerun()
        if memo["내용"]:
            st.caption(memo["내용"])
        st.markdown("---")
