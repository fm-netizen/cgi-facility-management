"""🗓 오늘 — 내 할 일 + 팀 공용 + 긴급. 팀장은 배정·팀 현황 추가."""
from datetime import timedelta

import pandas as pd
import streamlit as st

from pages_content.field_input import _check_pin
from todo_store import load_todos, update_status, set_assignee, today
from user_ctx import current_user, is_manager, workers
import wo_store as ws
from pages_content import work_orders as wop

LEAD_TAG = "[팀장 요청]"


def _due_txt(d, t):
    if d is None:
        return "기한 없음"
    if d < t:
        return f"🔴 {(t - d).days}일 지연"
    if d == t:
        return "🟡 오늘"
    return f"{d:%m/%d}"


def _mine(df, me):
    return df["담당자"].fillna("").map(lambda s: me in [x.strip() for x in s.replace("/", ",").split(",")])


def _sort(df, t):
    key = df["마감일"].map(lambda d: (0, d) if d and d <= t else ((1, d) if d else (2, t)))
    urg = df["긴급도"].map(lambda u: u[:2] if u else "P9")
    return df.assign(_k=key, _u=urg).sort_values(["_u", "_k"])


def _open_wo(todo_no):
    d = ws.load_all()
    if d is None:
        return None, None
    wo = d["wo"]
    hit = wo[(wo["할일#"] == str(todo_no)) & wo["상태"].isin(ws.OPEN_WO)]
    return (hit.iloc[-1] if not hit.empty else None), d


def _mine_actions(r, me):
    """WO가 있으면 작업 티켓 카드(시작·일시정지·완료 보고), 없으면 ▶ 시작 / ✅ 바로 완료."""
    w, d = _open_wo(r["번호"])
    if w is not None:
        wop._wo_card(w, d, me, False)
        return
    c1, c2, c3 = st.columns([2, 1, 1])
    note = c1.text_input("메모", key=f"n_{r['_row']}", label_visibility="collapsed",
                         placeholder="완료 메모 (선택)")
    if c2.button("▶ 시작", key=f"s_{r['_row']}", width="stretch",
                 help="작업 시간을 기록합니다 (작업 티켓 자동 발행)"):
        ok, msg = ws.issue_wo({"할일#": r["번호"], "작업유형": "정기점검(PM)" if r["정기 ID"] else "수리",
                               "구역": "기타", "설비·위치": r["구역·설비 ID"], "작업내용": r["할 일"],
                               "우선순위": r["우선순위"] or "보통", "배정구분": "기술", "책임자": me,
                               "예정일": r["마감일"]}, me, also_todo=False)
        if ok:
            ok, msg = ws.start_work(msg.split()[0], me)
        st.session_state.today_flash = (ok, msg)
        st.rerun()
    if c3.button("✅ 완료", key=f"d_{r['_row']}", width="stretch", type="primary"):
        ok, msg = update_status(int(r["_row"]), "완료", note, me, r["비고"])
        st.session_state.today_flash = (ok, f"#{r['번호']} {msg}")
        st.rerun()


def _row(r, t, me, kind):
    """한 줄 카드 + 버튼. kind: mine | pool | lead"""
    with st.container(border=True):
        top = f"**#{r['번호']} {r['할 일']}**"
        meta = [x for x in (r["긴급도"], _due_txt(r["마감일"], t), r["상태"], r["구역·설비 ID"],
                            r["정기 ID"]) if x]
        st.markdown(top + "  \n" + " · ".join(meta))
        if kind == "mine":
            _mine_actions(r, me)
        elif kind == "pool":
            if st.button("✋ 내가 맡기", key=f"c_{r['_row']}", width="stretch"):
                ok, msg = set_assignee(int(r["_row"]), me, "담당 맡음", me, r["비고"])
                st.session_state.today_flash = (ok, f"#{r['번호']} {msg}")
                st.rerun()


def show():
    st.title("🗓 오늘")
    if not _check_pin():
        return
    me, role = current_user()
    if not me:
        st.info("이름을 선택하면 내 할 일이 표시됩니다. 휴대폰 홈 화면에 저장해 두면 다음부터 자동으로 열립니다.")
        return
    t = today()
    f = st.session_state.pop("today_flash", None) or st.session_state.pop("wo_flash", None)
    if f:
        (st.success if f[0] else st.error)(f[1])

    df = load_todos()
    if df is None:
        st.warning("⚠️ 할 일 관리표를 불러올 수 없습니다.")
        return
    open_df = df[df["상태"] != "완료"].copy()
    soon = open_df["마감일"].map(lambda d: d is not None and d <= t + timedelta(days=7))
    urgent = open_df["긴급도"].str.startswith(("P1", "P2"))
    unassigned = open_df["담당자"].str.strip() == ""
    lead_wait = unassigned & open_df["비고"].str.contains(LEAD_TAG, regex=False)

    mine = _sort(open_df[_mine(open_df, me)], t)
    mine_now = mine[mine["마감일"].map(lambda d: d is None or d <= t + timedelta(days=3))
                    | (mine["상태"] == "진행 중")]
    pool = _sort(open_df[unassigned & ~lead_wait & (soon | urgent)], t)
    emerg = open_df[urgent]

    c = st.columns(4)
    c[0].metric("내 할 일 (3일 내)", f"{len(mine_now)}건")
    c[1].metric("지연", f"{int(mine['마감일'].map(lambda d: d is not None and d < t).sum())}건")
    c[2].metric("팀 공용 (7일 내)", f"{len(pool)}건")
    c[3].metric("🚨 긴급 진행", f"{len(emerg)}건")

    if st.button("➕ 등록 (고장·할 일·메모)", type="primary", width="stretch"):
        st.session_state.page = "register"
        st.rerun()

    if is_manager(role):
        st.subheader(f"📞 팀장 요청 대기 ({int(lead_wait.sum())})")
        waiting = _sort(open_df[lead_wait], t)
        names = workers()["이름"].tolist() if workers() is not None else [me]
        if waiting.empty:
            st.caption("없음")
        for _, r in waiting.iterrows():
            with st.container(border=True):
                st.markdown(f"**#{r['번호']} {r['할 일']}**  \n{r['긴급도']} · {r['구역·설비 ID'] or '-'}")
                st.caption(r["비고"][-200:])
                a1, a2 = st.columns([3, 1])
                who = a1.multiselect("처리자", names, default=[me], key=f"a_{r['_row']}",
                                     label_visibility="collapsed")
                if a2.button("배정", key=f"as_{r['_row']}", width="stretch") and who:
                    ok, msg = set_assignee(int(r["_row"]), ", ".join(who), f"팀장 배정 → {', '.join(who)}",
                                           me, r["비고"])
                    try:
                        import notify
                        notify.slack_team(f"📌 #{r['번호']} {r['할 일']} → {', '.join(who)} 배정 (by {me})")
                    except Exception:
                        pass
                    st.session_state.today_flash = (ok, f"#{r['번호']} {msg}")
                    st.rerun()

    st.subheader(f"👤 내 할 일 ({len(mine_now)})")
    if mine_now.empty:
        st.caption("3일 내 할 일 없음")
    for _, r in mine_now.head(30).iterrows():
        _row(r, t, me, "mine")
    rest = len(mine) - len(mine_now)
    if rest > 0:
        with st.expander(f"이후 예정 {rest}건"):
            v = mine[~mine.index.isin(mine_now.index)][["번호", "할 일", "마감일", "상태"]]
            v["마감일"] = v["마감일"].map(lambda d: d.strftime("%Y-%m-%d") if d else "—")
            st.dataframe(v, width="stretch", hide_index=True)

    st.subheader(f"👥 팀 공용 — 먼저 맡는 사람 ({len(pool)})")
    if pool.empty:
        st.caption("없음")
    for _, r in pool.head(30).iterrows():
        _row(r, t, me, "pool")



def team_status():
    """팀장 관리 화면용 — 사람별 미완료·지연·진행 중·오늘 완료."""
    df = load_todos()
    if df is None:
        st.caption("할 일 관리표를 불러올 수 없습니다.")
        return
    t = today()
    open_df = df[df["상태"] != "완료"]
    unassigned = open_df["담당자"].str.strip() == ""
    rows = []
    for n in (workers()["이름"].tolist() if workers() is not None else []):
        m = open_df[_mine(open_df, n)]
        rows.append({"이름": n, "미완료": len(m),
                     "지연": int(m["마감일"].map(lambda d: d is not None and d < t).sum()),
                     "진행 중": int((m["상태"] == "진행 중").sum()),
                     "오늘 완료": int(((df["상태"] == "완료") & (df["완료일"] == t) & _mine(df, n)).sum())})
    rows.append({"이름": "(미배정)", "미완료": int(unassigned.sum()), "지연": int(
        open_df[unassigned]["마감일"].map(lambda d: d is not None and d < t).sum()),
        "진행 중": 0, "오늘 완료": 0})
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
