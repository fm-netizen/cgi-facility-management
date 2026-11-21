"""로그인 사용자(작업자) 선택·역할 판별.

- 👷 작업자 탭(할 일 관리표)의 이름·역할 사용. 역할 '팀장' → 관리자 화면
- URL에 ?me=이름 을 붙여 휴대폰 홈 화면에 저장하면 매번 선택하지 않아도 됨
"""
import streamlit as st


def workers():
    import wo_store as ws
    d = ws.load_all()
    if d is None:
        return None
    return d["workers"]


def current_user(show_picker=True):
    """(이름, 역할) 반환. 미선택이면 (None, None)."""
    w = workers()
    if w is None or w.empty:
        return None, None
    names = w["이름"].tolist()
    qp = st.query_params.get("me")
    if qp in names and not st.session_state.get("me"):
        st.session_state.me = qp
    me = st.session_state.get("me")
    if show_picker:
        idx = names.index(me) if me in names else None
        pick = st.selectbox("👤 나는", names, index=idx, placeholder="이름 선택", key="me_pick")
        if pick and pick != me:
            st.session_state.me = pick
            st.query_params["me"] = pick
            me = pick
    if me not in names:
        return None, None
    role = w.set_index("이름")["역할"].get(me, "")
    return me, role


def is_manager(role) -> bool:
    return str(role).strip() in ("팀장", "관리자", "Manager", "Lead")
