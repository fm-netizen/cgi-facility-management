from datetime import datetime

import pandas as pd
import streamlit as st

from pages_content.field_input import _check_pin
import wo_store as ws


def _say(ok, msg):
    """결과 메시지를 저장해 rerun 후에도 표시."""
    st.session_state["wo_flash"] = (ok, msg)
    (st.success if ok else st.error)(msg)


def _time_override(key, label="실제 시각이 지금과 다름 (일시정지·완료를 늦게 눌렀을 때)"):
    """체크하면 시각 입력. 반환: datetime 또는 None."""
    if not st.checkbox(label, key=f"{key}_chk"):
        return None
    c1, c2 = st.columns(2)
    d = c1.date_input("날짜", value=ws.today(), key=f"{key}_d")
    t = c2.time_input("시각", value=ws.now().time(), step=300, key=f"{key}_t")
    return datetime.combine(d, t)


def _banner(data, me):
    seg = ws.open_segment(data["log"], me)
    if seg is None:
        st.info(f"👷 {me} — 현재 진행 중인 작업 없음")
        return
    h = (ws.now() - seg["시작"]).total_seconds() / 3600
    text = f"▶ 진행 중: **{seg['WO번호']}** · {seg['시작']:%H:%M} 시작 · 경과 {h:.1f}h"
    if h > ws.LONG_RUN_HOURS:
        st.warning(text + f"  \n⚠ {ws.LONG_RUN_HOURS}시간 넘게 기록 중입니다. 쉬는 시간이나 다른 일로 "
                          "멈췄다면 아래 해당 작업에서 **일시정지 → 실제 시각 보정**을 하세요.")
    else:
        st.success(text)


def _wo_card(row, data, me, is_lead):
    wo_no = row["WO번호"]
    mine = ws.open_segment(data["log"], me, wo_no)
    hours = ws.worked_hours(data["log"], wo_no)
    head = f"{wo_no} · [{row['상태']}] {row['작업내용']}"
    with st.expander(head, expanded=mine is not None):
        st.caption(f"{row['작업유형']} · {row['구역']} {row['설비·위치']} · 우선순위 {row['우선순위']} · "
                   f"책임자 {row['책임자'] or '-'} · 예정 {row['예정일'] or '-'} · "
                   f"할 일 #{row['할일#'] or '-'} · 누적 {hours:.2f}h")
        if row["플래그·비고"]:
            st.caption(f"📝 {row['플래그·비고']}")

        if mine is None:
            label = "▶ 시작" if not row["최초 시작"] else "▶ 재개"
            if st.button(label, key=f"start_{wo_no}", type="primary", width="stretch"):
                _say(*ws.start_work(wo_no, me))
                st.rerun()
        else:
            with st.form(f"pause_{wo_no}"):
                st.markdown("**⏸ 일시정지** — 급한 일·휴식·자재 대기")
                at = _time_override(f"p_{wo_no}")
                reason = st.text_input("사유 (선택)", key=f"pr_{wo_no}",
                                       placeholder="예: 점심, 긴급 호출, 부품 대기")
                if st.form_submit_button("⏸ 일시정지", width="stretch"):
                    _say(*ws.pause_work(wo_no, me, at, reason))
                    st.rerun()

        if row["최초 시작"] or mine is not None:
            _complete_form(row, data, me, hours)


def _complete_form(row, data, me, hours):
    wo_no = row["WO번호"]
    names = data["workers"]["이름"].tolist()
    d = data["directory"]
    opts = [""] + [f"{r['품목코드']} | {r['품명']}" for _, r in d.iterrows()]
    with st.form(f"done_{wo_no}"):
        st.markdown("**■ 완료 보고**")
        at = _time_override(f"c_{wo_no}", "실제 종료 시각이 지금과 다름")
        crew = st.multiselect("작업자 (실제 작업한 사람 모두)", names,
                              default=[me] if me in names else None, key=f"crew_{wo_no}")
        st.caption(f"기록된 작업시간 {hours:.2f}h — 기록에 휴식·대기 시간이 섞였다면 차감하세요.")
        c1, c2 = st.columns(2)
        deduct = c1.selectbox("휴식·대기 차감(분)", [0, 15, 30, 45, 60, 90, 120], key=f"dd_{wo_no}")
        outside = c2.number_input("외주비 (US$)", min_value=0.0, step=10.0, key=f"oc_{wo_no}")
        comment = st.text_area("결과 코멘트 *", key=f"cm_{wo_no}",
                               placeholder="원인 / 조치 내용 / 후속 필요 사항")
        photo = st.text_input("사진 링크 (선택)", key=f"ph_{wo_no}",
                              placeholder="Google Drive·Photos 공유 링크")
        st.markdown("사용 자재·부품 (없으면 비워두기) — 목록에 없으면 **직접 입력 품명**에 적으세요")
        mats = st.data_editor(
            pd.DataFrame({"목록에서 선택": [""] * 3, "직접 입력 품명": [""] * 3,
                          "수량": [0.0] * 3, "단위": [""] * 3, "단가(US$)": [0.0] * 3}),
            column_config={
                "목록에서 선택": st.column_config.SelectboxColumn("목록에서 선택", options=opts, width="medium"),
                "직접 입력 품명": st.column_config.TextColumn("직접 입력 품명", width="medium",
                                                             help="예: 1/2\" PVC 엘보, GFCI 콘센트 20A"),
                "수량": st.column_config.NumberColumn("수량", min_value=0.0, step=1.0),
                "단위": st.column_config.TextColumn("단위", help="EA, ft, gal, Box 등 (직접 입력 시)"),
                "단가(US$)": st.column_config.NumberColumn("단가(US$)", min_value=0.0, step=0.5,
                                                          format="$%.2f", help="모르면 0"),
            },
            num_rows="dynamic", hide_index=True, key=f"mt_{wo_no}", width="stretch")
        if st.form_submit_button("■ 완료 저장", type="primary", width="stretch"):
            if not comment.strip():
                st.error("결과 코멘트를 입력하세요.")
                return
            used, bad = [], 0
            for _, r in mats.iterrows():
                code = str(r["목록에서 선택"] or "").split(" | ")[0].strip()
                name = str(r["직접 입력 품명"] or "").strip()
                qty = float(r["수량"] or 0)
                if not code and not name:
                    continue
                if qty <= 0:
                    bad += 1
                    continue
                used.append({"code": code, "name": name if not code else "", "qty": qty,
                             "unit": str(r["단위"] or ""), "price": float(r["단가(US$)"] or 0)})
            if bad:
                st.error(f"수량이 0인 자재 {bad}건이 있습니다. 수량을 입력하거나 행을 비우세요.")
                return
            _say(*ws.complete_work(wo_no, me, at=at, workers=crew or [me],
                                   deduct_min=deduct, outside_cost=outside,
                                   comment=comment.strip(), photo=photo.strip(), materials=used))
            st.rerun()


def _tab_my(data, me, role):
    wo = data["wo"]
    open_wo = wo[wo["상태"].isin(ws.OPEN_WO)]
    is_lead = role == "팀장"
    show_all = st.toggle("전체 작업 보기", value=is_lead, key="show_all")
    if not show_all:
        assign = data["workers"].set_index("이름")["배정구분"].get(me, "")
        open_wo = open_wo[(open_wo["책임자"] == me) | (open_wo["배정구분"] == assign)
                          | open_wo["작업자"].str.contains(me, regex=False)]
    if open_wo.empty:
        st.info("처리할 작업이 없습니다.")
        return
    order = {"진행 중": 0, "일시정지": 1, "발행": 2, "보류": 3}
    pri = {"높음": 0, "보통": 1, "낮음": 2}
    open_wo = open_wo.assign(_o=open_wo["상태"].map(order), _p=open_wo["우선순위"].map(pri).fillna(1))
    for _, row in open_wo.sort_values(["_o", "_p", "WO번호"]).iterrows():
        _wo_card(row, data, me, is_lead)


def _tab_issue(data, me):
    from todo_store import load_todos
    todos = load_todos()
    linked = set(data["wo"]["할일#"])
    src = st.radio("발행 방식", ["할 일에서 선택", "신규 작업"], horizontal=True, key="iss_src")
    todo_no, default_task = "", ""
    if src == "할 일에서 선택":
        if todos is None:
            st.warning("할 일 목록을 불러올 수 없습니다.")
            return
        cand = todos[(todos["상태"] != "완료") & todos["분류"].isin(["시설", "공사"])
                     & ~todos["번호"].astype(str).isin(linked)]
        if cand.empty:
            st.info("발행할 할 일이 없습니다.")
            return
        pick = st.selectbox("할 일", [f"#{r['번호']} {r['할 일']}" for _, r in cand.iterrows()],
                            key="iss_pick")
        todo_no = pick.split(" ")[0].lstrip("#")
        default_task = pick.split(" ", 1)[1]

    workers = data["workers"]
    with st.form("issue_form", clear_on_submit=True):
        task = st.text_input("작업내용 *", value=default_task)
        c1, c2, c3 = st.columns(3)
        wtype = c1.selectbox("작업유형", ws.WORK_TYPES)
        zone = c2.selectbox("구역", ws.ZONES)
        pri = c3.selectbox("우선순위", ws.PRIORITIES, index=1)
        where = st.text_input("설비·위치", placeholder="예: 지하 기계실 Boiler #2")
        c4, c5, c6 = st.columns(3)
        assign = c4.selectbox("배정구분", ws.ASSIGN)
        lead = c5.selectbox("책임자", [""] + workers["이름"].tolist())
        due = c6.date_input("예정일", value=ws.today())
        also = True
        if src == "신규 작업":
            also = st.checkbox("할 일 관리표에도 등록", value=True)
        if st.form_submit_button("🎫 발행", type="primary", width="stretch"):
            if not task.strip():
                st.error("작업내용을 입력하세요.")
                return
            data_in = {"할일#": todo_no, "작업유형": wtype, "구역": zone, "설비·위치": where.strip(),
                       "작업내용": task.strip(), "우선순위": pri, "배정구분": assign,
                       "책임자": lead, "예정일": due}
            _say(*ws.issue_wo(data_in, me, also_todo=also))


def _tab_review(data, me, role):
    if role != "팀장":
        st.info("검수는 팀장만 할 수 있습니다.")
        return
    done = data["wo"][data["wo"]["상태"] == "완료"]
    if done.empty:
        st.info("검수 대기 작업이 없습니다.")
        return
    for _, r in done.iterrows():
        hours = ws.worked_hours(data["log"], r["WO번호"])
        with st.expander(f"{r['WO번호']} · {r['작업내용']}"):
            st.markdown(f"- 작업자: **{r['작업자'] or '-'}** · 기록 {hours:.2f}h · 차감 {r['차감(분)'] or 0}분\n"
                        f"- 순작업 {r['순작업(h)']}h · 인시 {r['인시(Man-h)']} · 자재비 ${r['자재비(US$)'] or 0} · "
                        f"외주비 ${r['외주비(US$)'] or 0}\n- 코멘트: {r['결과 코멘트']}")
            if r["사진 링크"]:
                st.markdown(f"- [사진 보기]({r['사진 링크']})")
            if r["플래그·비고"]:
                st.warning(r["플래그·비고"])
            logs = data["log"][data["log"]["WO번호"] == r["WO번호"]][["기록자", "시작", "종료", "종료 방식"]]
            st.dataframe(logs, hide_index=True, width="stretch")
            note = st.text_input("검수 메모", key=f"rv_{r['WO번호']}")
            c1, c2 = st.columns(2)
            if c1.button("✅ 검수완료", key=f"ok_{r['WO번호']}", type="primary", width="stretch"):
                _say(*ws.review_wo(r["WO번호"], me, True, note))
                st.rerun()
            if c2.button("↩ 재작업", key=f"ng_{r['WO번호']}", width="stretch"):
                _say(*ws.review_wo(r["WO번호"], me, False, note))
                st.rerun()


def _tab_parts(data):
    d = data["directory"]
    q = st.text_input("🔍 품목 검색", placeholder="품명·코드·설비 (예: 필터, RTU, MAT-FLT)")
    kinds = st.multiselect("구분", ["자재", "부품", "공구", "약품"])
    view = d.copy()
    if q:
        hay = (view["품목코드"] + " " + view["품명"] + " " + view["카테고리"] + " "
               + view["관련 설비"] + " " + view["규격·모델"]).str.lower()
        view = view[hay.str.contains(q.lower(), regex=False)]
    if kinds:
        view = view[view["구분"].isin(kinds)]
    st.dataframe(view[["품목코드", "품명", "규격·모델", "현재고", "단위", "재고 상태",
                       "보관위치코드", "위치 설명", "공구 사용 현황"]],
                 hide_index=True, width="stretch")
    pending = ws.unregistered_summary(data["mat"])
    with st.expander(f"🆕 직접 입력 자재 (디렉토리 미등록) {len(pending)}종"):
        if pending.empty:
            st.caption("아직 없습니다.")
        else:
            st.caption("자주 쓰는 품목부터 디렉토리에 코드를 부여해 등록하세요. "
                       "등록 후 '🔩 자재 사용' 탭의 해당 행 품목코드 칸에 코드를 넣으면 재고에 반영됩니다.")
            st.dataframe(pending, hide_index=True, width="stretch",
                         column_config={"최근단가": st.column_config.NumberColumn(format="$%.2f")})
    with st.expander("📍 보관 위치 코드 목록"):
        st.dataframe(data["locations"][["위치코드", "구역명", "보관설비", "위치 설명"]],
                     hide_index=True, width="stretch")


def show():
    st.title("🎫 작업 티켓")
    st.caption("작업지시서 발행 · 시작/일시정지/완료 기록 · 자재 위치 찾기")
    if not _check_pin():
        return
    data = ws.load_all()
    if data is None:
        st.warning("⚠️ Google Sheets 미연결 — " + st.session_state.get("wo_error", ""))
        return

    names = data["workers"]["이름"].tolist()
    if not names:
        st.error("'👷 작업자' 탭에 작업자를 등록하세요.")
        return
    idx = names.index(st.session_state["me"]) if st.session_state.get("me") in names else 0
    me = st.selectbox("👷 작업자", names, index=idx)
    st.session_state.me = me
    role = data["workers"].set_index("이름")["역할"].get(me, "")

    key = f"stale_{ws.today()}"
    if not st.session_state.get(key):
        n = ws.auto_close_stale()
        st.session_state[key] = True
        if n:
            st.warning(f"⚠ 어제 이전에 종료되지 않은 기록 {n}건을 퇴근 시각({ws.SHIFT_END:%H:%M})으로 "
                       "자동 종료했습니다. 검수 때 시간을 확인하세요.")
            data = ws.load_all()

    flash = st.session_state.pop("wo_flash", None)
    if flash:
        (st.success if flash[0] else st.error)(flash[1])
    _banner(data, me)
    t1, t2, t3, t4 = st.tabs(["📋 내 작업", "🎫 발행", "✅ 검수", "📦 자재 찾기"])
    with t1:
        _tab_my(data, me, role)
    with t2:
        _tab_issue(data, me)
    with t3:
        _tab_review(data, me, role)
    with t4:
        _tab_parts(data)
