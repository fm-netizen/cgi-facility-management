import streamlit as st
import plotly.express as px

from sheets_config import MASTER_SHEET_URL, TASK_TRACKER_URL, DRIVE_FOLDER_URL, SLACK_URL, PROJECT_FOLDERS
import asset_store as A
from ui_links import link_buttons
from todo_store import load_todos, summarize, today

LIST_COLS = ["번호", "할 일", "우선순위", "마감일", "상태"]


def _table(df, cols=LIST_COLS, empty="없음"):
    if df.empty:
        st.caption(empty)
    else:
        view = df[cols].copy()
        for c in ("마감일", "완료일", "등록일"):
            if c in view:
                view[c] = view[c].map(lambda d: d.strftime("%Y-%m-%d") if d else "—")
        st.dataframe(view, width="stretch", hide_index=True)


def _asset_strip():
    """시설·설비 현황 한 줄 요약 (상세는 시설·설비 화면 / 대장 시트)."""
    st.subheader("🏢 시설·설비 현황")
    data = A.load_assets()
    if data is None:
        st.caption("설비·시설 대장을 불러올 수 없습니다.")
        return
    z, e = A.counts(data["zones"]), A.counts(data["equip"])
    c = st.columns(4)
    c[0].metric("시설 구역 이상", f"{z['이상']} / {z['전체']}")
    c[1].metric("설비 이상", f"{e['이상']} / {e['전체']}")
    c[2].metric("🔴 고장·이상", f"{z['🔴 고장·이상'] + e['🔴 고장·이상']}건")
    c[3].metric("🔧 수리·공사 중", f"{z['🔧 수리·공사 중'] + e['🔧 수리·공사 중']}건")
    eq = data["equip"]
    bad = eq[eq["현재 상태"] != A.NORMAL]
    order = {s: i for i, s in enumerate(["🔴 고장·이상", "🔧 수리·공사 중", "🟡 점검 필요", "🔄 교체 예정"])}
    bad = bad.assign(_o=bad["현재 상태"].map(lambda s: order.get(s, 9))).sort_values(["_o", "설비ID"])
    if bad.empty:
        st.caption("모든 설비 정상")
    else:
        st.dataframe(bad[["설비ID", "설비명", "현재 상태", "최근 비고"]].head(8),
                     width="stretch", hide_index=True)
        if len(bad) > 8:
            st.caption(f"외 {len(bad) - 8}건 — ⚙️ 설비 상황 화면에서 전체 확인")
    if st.button("⚙️ 설비 상태 기록하기", width="stretch"):
        st.session_state.page = "equipment"
        st.rerun()


def show():
    t = today()
    st.title("🏠 CGI Facility Management")
    st.caption(f"111 Homans Ave, Closter, NJ · {t.strftime('%Y년 %m월 %d일')}")

    link_buttons([("📊 설비·시설 대장", MASTER_SHEET_URL),
                  ("📋 할 일 관리표", TASK_TRACKER_URL),
                  ("📁 공사 폴더", DRIVE_FOLDER_URL),
                  ("💬 Slack #fm-team", SLACK_URL)])
    with st.expander("📁 공사 프로젝트 폴더"):
        for name, links in PROJECT_FOLDERS.items():
            st.markdown(f"**{name}**")
            link_buttons(links)
    st.markdown("---")
    _asset_strip()
    st.markdown("---")

    df = load_todos()
    if df is None:
        st.warning("⚠️ Google Sheets 미연결 — 할 일 데이터를 불러올 수 없습니다. "
                   "Streamlit Secrets의 서비스 계정 설정과 시트 공유를 확인하세요.")
        err = st.session_state.get("todo_error")
        if err:
            st.caption(f"오류: {err}")
        return

    s = summarize(df)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("미완료", f"{s['open']}건")
    c2.metric("진행 중", f"{s['in_progress']}건")
    c3.metric("마감 초과", f"{len(s['overdue'])}건",
              delta="즉시 확인" if len(s["overdue"]) else None, delta_color="inverse")
    c4.metric("7일 내 마감", f"{len(s['due_soon'])}건")
    rate = round(s["done"] / s["total"] * 100) if s["total"] else 0
    c5.metric("완료", f"{s['done']}건", delta=f"완료율 {rate}%", delta_color="off")

    if st.button("📲 현장 입력 (할 일 등록·상태 변경)", type="primary", width="stretch"):
        st.session_state.page = "field_input"
        st.rerun()

    st.markdown("---")
    left, right = st.columns(2)
    with left:
        st.subheader("🔴 마감 초과")
        _table(s["overdue"])
        st.subheader("🟡 7일 내 마감")
        _table(s["due_soon"])
    with right:
        st.subheader("⭐ 우선순위 높음 (미완료)")
        _table(s["high_open"], ["번호", "할 일", "마감일", "상태"])
        st.subheader("✔️ 최근 7일 완료")
        _table(s["done_week"], ["번호", "할 일", "완료일"])

    st.markdown("---")
    st.subheader("📊 구분별 미완료")
    open_df = df[df["상태"] != "완료"]
    if open_df.empty:
        st.caption("미완료 항목 없음")
    else:
        g = open_df.groupby(["프로젝트/구분", "상태"]).size().reset_index(name="건수")
        fig = px.bar(g, x="건수", y="프로젝트/구분", color="상태", orientation="h",
                     color_discrete_map={"진행 전": "#9AA5B1", "진행 중": "#F2B705", "보류": "#F28C38"})
        fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0), legend_title=None,
                          yaxis_title=None)
        st.plotly_chart(fig, width="stretch")

    with st.expander("📋 전체 미완료 목록"):
        _table(open_df, ["번호", "프로젝트/구분", "할 일", "우선순위", "마감일", "상태", "비고"])
    st.caption(f"데이터: CGI FM 할 일 관리표 · 1분마다 갱신 · 총 {s['total']}건")
