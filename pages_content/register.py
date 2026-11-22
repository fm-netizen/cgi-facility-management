"""➕ 등록 — 고장·긴급 / 할 일 / 메모를 한 곳에서."""
import streamlit as st

import voice
from pages_content import memo, report
from pages_content.field_input import _check_pin
from todo_store import add_todo, GROUPS, PRIORITIES
from user_ctx import current_user

KINDS = ["🚨 고장·긴급", "📋 할 일", "📝 메모"]


def _todo_form(me):
    st.caption("계획된 일·요청을 등록합니다. 담당을 비우면 팀 공용 목록에 올라갑니다.")
    spoken = voice.voice_box("todo_voice", "🎤 말로 입력")
    n = st.session_state.get("todo_voice_n", 0)
    with st.form(f"todo_form_{n}"):
        task = st.text_area("할 일 *", value=spoken, height=90, key=f"todo_t_{n}_{len(spoken)}")
        c1, c2 = st.columns(2)
        group = c1.selectbox("업무 구분", GROUPS)
        prio = c2.selectbox("우선순위", PRIORITIES, index=1)
        due = c1.date_input("마감일", value=None)
        who = c2.radio("담당", ["나", "팀 공용"], horizontal=True)
        if st.form_submit_button("등록", type="primary", width="stretch"):
            if not task.strip():
                st.error("할 일을 입력하세요.")
                return
            ok, msg = add_todo(group, task.strip()[:120], "시설", prio, due, "진행 전",
                               task.strip() if len(task.strip()) > 120 else "", "",
                               assignee=me if who == "나" else "")
            (st.success if ok else st.error)(msg)
            if ok:
                voice.clear("todo_voice")


def show():
    st.title("➕ 등록")
    if not _check_pin():
        return
    me, _ = current_user()
    if not me:
        st.info("먼저 이름을 선택하세요.")
        return
    kind = st.radio("무엇을 등록하나요?", KINDS, horizontal=True, key="reg_kind")
    st.markdown("---")
    if kind == KINDS[0]:
        report.show(embedded=True)
    elif kind == KINDS[1]:
        _todo_form(me)
    else:
        memo.show(embedded=True)
