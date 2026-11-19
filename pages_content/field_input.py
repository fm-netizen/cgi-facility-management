import hmac

import streamlit as st

from todo_store import (load_todos, add_todo, update_status, today,
                        GROUPS, CATEGORIES, PRIORITIES, STATUSES, OPEN_STATUSES)


def _check_pin():
    """Secrets의 app_pin과 비교. 설정이 없으면 입력 차단."""
    if st.session_state.get("pin_ok"):
        return True
    try:
        pin = st.secrets.get("app_pin")
    except Exception:
        pin = None
    if not pin:
        st.error("입력 기능 잠금: Streamlit Secrets에 app_pin이 설정되지 않았습니다.")
        return False
    with st.form("pin_form"):
        entered = st.text_input("직원 PIN", type="password")
        if st.form_submit_button("확인", type="primary"):
            if hmac.compare_digest(str(entered), str(pin)):
                st.session_state.pin_ok = True
                st.rerun()
            else:
                st.error("PIN이 맞지 않습니다.")
    return False


def show():
    st.title("📲 현장 입력")
    st.caption("할 일 관리표에 바로 저장됩니다. 휴대폰에서도 사용할 수 있습니다.")

    if not _check_pin():
        return

    df = load_todos()
    if df is None:
        st.warning("⚠️ Google Sheets 미연결 — 저장할 수 없습니다.")
        return

    author = st.text_input("입력자 이름", value=st.session_state.get("author", ""),
                           placeholder="예: 강성근").strip()
    st.session_state.author = author

    tab_new, tab_update = st.tabs(["➕ 새 할 일·고장 접수", "🔄 상태 변경"])

    with tab_new:
        with st.form("new_todo", clear_on_submit=True):
            task = st.text_input("할 일 / 고장 내용 *", placeholder="예: 남 락커룸 샤워기 3번 수압 약함")
            c1, c2 = st.columns(2)
            group = c1.selectbox("구분", GROUPS)
            category = c2.selectbox("분류", CATEGORIES)
            c3, c4 = st.columns(2)
            priority = c3.selectbox("우선순위", PRIORITIES, index=1)
            status = c4.selectbox("상태", STATUSES, index=0)
            has_due = st.checkbox("마감일 지정")
            due = st.date_input("마감일", value=today(), disabled=not has_due)
            note = st.text_area("비고 (위치·증상·연락처 등)", height=80)
            if st.form_submit_button("등록", type="primary", width="stretch"):
                if not task.strip():
                    st.error("할 일 내용을 입력하세요.")
                elif not author:
                    st.error("입력자 이름을 입력하세요.")
                else:
                    ok, msg = add_todo(group, task.strip(), category, priority,
                                       due if has_due else None, status, note.strip(), author)
                    (st.success if ok else st.error)(msg)

    with tab_update:
        open_df = df[df["상태"].isin(OPEN_STATUSES)]
        if open_df.empty:
            st.info("변경할 미완료 항목이 없습니다.")
            return
        options = {f"#{r['번호']} [{r['상태']}] {r['할 일']}": r for _, r in open_df.iterrows()}
        with st.form("update_todo"):
            label = st.selectbox("항목 선택", list(options.keys()))
            new_status = st.radio("변경할 상태", STATUSES, index=3, horizontal=True)
            note = st.text_input("진행 메모 (비고에 추가)", placeholder="예: 부품 주문 완료")
            if st.form_submit_button("저장", type="primary", width="stretch"):
                r = options[label]
                if not author:
                    st.error("입력자 이름을 입력하세요.")
                else:
                    ok, msg = update_status(int(r["_row"]), new_status, note, author, r["비고"])
                    (st.success if ok else st.error)(f"#{r['번호']} {msg}" if ok else msg)
