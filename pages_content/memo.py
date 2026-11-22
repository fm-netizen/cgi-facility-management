"""메모 — 할 일 관리표 '📝 메모' 탭에 저장 (삭제는 '삭제' 표시로 숨김, 기록 보존)."""
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from sheets_config import TODO_SPREADSHEET_ID, MEMO_SHEET_NAME, TASK_TRACKER_URL, SLACK_URL
from ui_links import link_buttons
import voice

TZ = ZoneInfo("America/New_York")
COLS = ["등록일시", "제목", "태그", "내용", "상태", "작성자"]
TAGS = ["일반", "긴급", "HVAC", "수영장", "Gym", "전기", "배관", "Vendor", "CEO 보고", "공사"]
TAG_ICON = {"긴급": "🔴", "CEO 보고": "🟣", "HVAC": "🔵", "수영장": "🌊", "Gym": "💪", "공사": "🏗"}


def _ws():
    from sheets_helper import get_sheets_client
    c = get_sheets_client()
    return None if c is None else c.open_by_key(TODO_SPREADSHEET_ID).worksheet(MEMO_SHEET_NAME)


@st.cache_data(ttl=60, show_spinner=False)
def load_memos():
    try:
        ws = _ws()
        if ws is None:
            return None
        values = ws.get_all_values()
    except Exception as e:
        st.session_state["memo_error"] = str(e)
        return None
    rows = []
    for i, r in enumerate(values[1:], start=2):
        r = (list(r) + [""] * 6)[:6]
        if r[1].strip() and r[4] != "삭제":
            rows.append(dict(zip(COLS, r), _row=i))
    return pd.DataFrame(rows, columns=COLS + ["_row"]).iloc[::-1]


def _set_status(row, status):
    ws = _ws()
    ws.update(range_name=f"E{row}", values=[[status]], value_input_option="USER_ENTERED")
    load_memos.clear()


def show(embedded=False):
    if not embedded:
        st.title("📝 메모")
        link_buttons([("📋 할 일 관리표", TASK_TRACKER_URL), ("💬 Slack", SLACK_URL)])

    df = load_memos()
    if df is None:
        st.warning("⚠️ 메모 탭을 불러올 수 없습니다. " + st.session_state.get("memo_error", ""))
        return

    with st.expander("➕ 새 메모", expanded=embedded):
        spoken = voice.voice_box("memo_voice", "🎤 말로 메모")
        with st.form(f"memo_form_{st.session_state.get('memo_voice_n', 0)}", clear_on_submit=True):
            c1, c2 = st.columns([3, 1])
            title = c1.text_input("제목")
            tag = c2.selectbox("태그", TAGS)
            content = st.text_area("내용", value=spoken, height=100,
                                   key=f"memo_c_{st.session_state.get('memo_voice_n', 0)}_{len(spoken)}")
            author = st.text_input("작성자", value=st.session_state.get("me") or st.session_state.get("author", ""))
            if st.form_submit_button("저장", type="primary", width="stretch"):
                if not title.strip():
                    st.error("제목을 입력하세요.")
                else:
                    try:
                        now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
                        _ws().append_row([now, title.strip(), tag, content.strip(), "미완료", author.strip()],
                                         value_input_option="USER_ENTERED", table_range="A1:F1")
                        load_memos.clear()
                        voice.clear("memo_voice")
                        st.success("저장 완료")
                    except Exception as e:
                        st.error(f"저장 실패: {e}")

    c1, c2 = st.columns(2)
    f_tag = c1.selectbox("태그 필터", ["전체"] + TAGS)
    f_done = c2.selectbox("완료 여부", ["미완료", "완료", "전체"])
    view = df
    if f_tag != "전체":
        view = view[view["태그"] == f_tag]
    if f_done != "전체":
        view = view[view["상태"] == f_done]
    st.markdown(f"**{len(view)}개** 메모")
    st.markdown("---")

    for _, m in view.iterrows():
        icon = "✅" if m["상태"] == "완료" else "📋"
        a, b, c = st.columns([6, 1, 1])
        a.markdown(f"**{icon} {m['제목']}** &nbsp; {TAG_ICON.get(m['태그'], '⚪')} `{m['태그']}` "
                   f"&nbsp; *{m['등록일시']} · {m['작성자']}*")
        if b.button("미완료" if m["상태"] == "완료" else "완료", key=f"done_{m['_row']}", width="stretch"):
            _set_status(m["_row"], "미완료" if m["상태"] == "완료" else "완료")
            st.rerun()
        if c.button("삭제", key=f"del_{m['_row']}", width="stretch"):
            _set_status(m["_row"], "삭제")
            st.rerun()
        if m["내용"]:
            st.caption(m["내용"])
        st.markdown("---")
