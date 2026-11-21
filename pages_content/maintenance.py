"""정기 업무(PM) 일정 — 할 일 관리표의 정기 ID(L열) 회차를 기준으로 표시."""
from datetime import timedelta

import pandas as pd
import streamlit as st

from sheets_config import TASK_TRACKER_URL, MASTER_SHEET_URL
from todo_store import load_todos, today
from ui_links import link_buttons

COLS = ["번호", "정기 ID", "할 일", "마감일", "상태", "비고"]


def _fmt(df, cols=COLS):
    v = df[cols].copy()
    for c in ("마감일", "완료일"):
        if c in v:
            v[c] = v[c].map(lambda d: d.strftime("%Y-%m-%d") if d else "—")
    return v


def show():
    st.title("🗓️ 메인트넌스 일정")
    st.caption("정기 업무는 '📅 정기 일정 마스터'에서 관리되고, 매월 25일 다음 달 회차가 할 일로 자동 생성됩니다.")
    link_buttons([("📋 할 일 관리표", TASK_TRACKER_URL), ("📊 설비·시설 대장", MASTER_SHEET_URL)])

    df = load_todos()
    if df is None:
        st.warning("⚠️ 할 일 관리표를 불러올 수 없습니다.")
        return
    pm = df[df["정기 ID"].str.strip() != ""].copy()
    if pm.empty:
        st.info("정기 ID가 지정된 할 일이 없습니다.")
        return

    t = today()
    month_start = t.replace(day=1)
    has_due = pm["마감일"].notna()
    done = pm["상태"] == "완료"
    this_month = pm[has_due & pm["마감일"].map(lambda d: d is not None and d >= month_start and d.month == t.month)]
    overdue = pm[has_due & ~done & pm["마감일"].map(lambda d: d is not None and d < t)]
    upcoming = pm[has_due & ~done & pm["마감일"].map(lambda d: d is not None and t <= d <= t + timedelta(days=30))]
    recent = pm[done & pm["완료일"].map(lambda d: d is not None and d >= t - timedelta(days=30))]

    tm_done = this_month[this_month["상태"] == "완료"]
    on_time = [1 for _, r in tm_done.iterrows() if r["완료일"] is not None and r["완료일"] <= r["마감일"]]
    m = st.columns(4)
    m[0].metric("이번 달 정기 회차", f"{len(this_month)}건")
    m[1].metric("이번 달 완료", f"{len(tm_done)}건")
    m[2].metric("기한 준수율", f"{round(len(on_time) / len(tm_done) * 100) if len(tm_done) else 0}%")
    m[3].metric("마감 초과", f"{len(overdue)}건", delta="확인" if len(overdue) else None, delta_color="inverse")

    if st.button("📲 현장 입력에서 완료 처리", type="primary", width="stretch"):
        st.session_state.page = "field_input"
        st.rerun()

    for title, part in (("🔴 마감 초과", overdue), ("🟡 30일 내 예정", upcoming)):
        st.subheader(title)
        if part.empty:
            st.caption("없음")
        else:
            st.dataframe(_fmt(part.sort_values("마감일")), width="stretch", hide_index=True)
    with st.expander(f"✔️ 최근 30일 완료 ({len(recent)}건)"):
        st.dataframe(_fmt(recent.sort_values("완료일", ascending=False),
                          ["번호", "정기 ID", "할 일", "마감일", "완료일"]), width="stretch", hide_index=True)

    with st.expander("📈 정기 업무별 회차 (전체 기간)"):
        g = pm.groupby("정기 ID").agg(회차=("번호", "count"),
                                     완료=("상태", lambda s: int((s == "완료").sum()))).reset_index()
        st.dataframe(g.sort_values("정기 ID"), width="stretch", hide_index=True)
