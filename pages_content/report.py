"""🚨 긴급·불시 접수 — 누구나 접수 → '내가 처리' 또는 '팀장 요청'."""
import re
import time

import streamlit as st

import asset_store as A
import notify
import voice
import wo_store as ws
from pages_content.field_input import _check_pin
from todo_store import add_todo, load_todos, today, GROUPS, URGENCY
from user_ctx import current_user

VKEY = "rep_voice"


def _flash():
    f = st.session_state.pop("rep_flash", None)
    if f:
        for ok, msg in f:
            (st.success if ok else st.warning)(msg)


def show():
    st.title("🚨 접수")
    st.caption("고장·민원·요청을 바로 등록합니다. 직접 처리할 수 있으면 '✋ 내가 처리', 어려우면 '📞 팀장 요청'.")
    if not _check_pin():
        return
    me, _ = current_user()
    if not me:
        st.info("먼저 이름을 선택하세요.")
        return
    _flash()

    assets = A.load_assets()
    zones = assets["zones"] if assets else None
    equip = assets["equip"] if assets else None
    zlabels = ["(선택 안 함)"] + ([f"{r['구역ID']} · {r['구역명']}" for _, r in zones.iterrows()]
                                  if zones is not None else [])
    zpick = st.selectbox("📍 구역", zlabels)
    zid = "" if zpick.startswith("(") else zpick.split(" · ")[0]
    elabels = ["(설비 아님 / 모름)"]
    if equip is not None and zid:
        elabels += [f"{r['설비ID']} · {r['설비명']}" for _, r in equip[equip["구역ID"] == zid].iterrows()]
    epick = st.selectbox("⚙️ 설비", elabels)
    eid = "" if epick.startswith("(") else epick.split(" · ")[0]

    spoken = voice.voice_box(VKEY, "🎤 말로 증상 입력 (녹음 후 아래에서 수정 가능)")
    n = st.session_state.get(f"{VKEY}_n", 0)
    with st.form(f"report_form_{n}"):
        what = st.text_area("무슨 일인가요? *", value=spoken, height=110,
                            placeholder="예: 세탁실 건조기가 문을 닫아도 작동하지 않음",
                            key=f"rep_text_{n}_{len(spoken)}")
        c1, c2 = st.columns(2)
        urgency = c1.radio("긴급도", URGENCY, index=1,
                           help="P1 안전·영업중단·누수·정전 / P2 회원 불편 / P3 이번 주 / P4 계획")
        group = c2.selectbox("업무 구분", GROUPS, index=0)
        photo = c2.text_input("사진 링크 (선택)")
        after = st.checkbox("이미 처리 완료 (사후 기록)")
        b1, b2 = st.columns(2)
        mine = b1.form_submit_button("✋ 내가 처리", type="primary", width="stretch")
        lead = b2.form_submit_button("📞 팀장 요청", width="stretch")

    if not (mine or lead):
        return
    if not what.strip():
        st.error("내용을 입력하세요.")
        return
    # 설비를 고르지 않았어도 내용에 설비 ID(예: LD-01)가 있으면 자동 연결
    if not eid and equip is not None:
        ids = set(equip["설비ID"])
        hit = next((m for m in re.findall(r"[A-Z]{2}-\d{2}", what.upper()) if m in ids), "")
        if hit:
            eid = hit
            row = equip.set_index("설비ID").loc[hit]
            epick = f"{hit} · {row['설비명']}"
            if not zid:
                zid = row["구역ID"]
                zname = zones.set_index("구역ID")["구역명"].get(zid, "") if zones is not None else ""
                zpick = f"{zid} · {zname}"

    # 중복 접수 방지: 같은 내용을 2분 안에 다시 누르거나, 오늘 같은 내용이 이미 미완료로 있으면 저장하지 않음
    sig = (what.strip(), urgency, zid, eid, "mine" if mine else "lead")
    last = st.session_state.get("rep_last")
    if last and last[0] == sig and time.time() - last[1] < 120:
        st.warning("방금 같은 내용이 이미 접수되었습니다. 중복 저장하지 않았습니다.")
        return
    df = load_todos()
    if df is not None:
        dup = df[(df["할 일"].str.strip() == what.strip()[:80]) & (df["출처"] == "긴급 접수")
                 & (df["등록일"] == today()) & (df["상태"] != "완료")]
        if not dup.empty:
            st.warning(f"오늘 같은 내용이 이미 #{dup.iloc[0]['번호']}로 접수되어 있습니다. 중복 저장하지 않았습니다.")
            return
    st.session_state.rep_last = (sig, time.time())

    where = " / ".join(x for x in (zpick if zid else "", epick if eid else "") if x)
    title = f"[{urgency.split()[0]}] {what.strip()[:60]}"
    note = f"[접수·{me}] {what.strip()}" + (f" (위치: {where})" if where else "") + \
           (f" 사진: {photo}" if photo else "")
    asset_ref = eid or zid
    msgs = []

    if mine:
        status = "완료" if after else "진행 중"
        ok, msg = add_todo(group, what.strip()[:80], "시설", "높음" if urgency.startswith(("P1", "P2")) else "보통",
                           None, status, note, "", assignee=me, urgency=urgency, asset=asset_ref,
                           source="긴급 접수")
        msgs.append((ok, msg))
        todo_no = msg.split()[0].lstrip("#") if ok else ""
        if ok and not after:
            ok2, m2 = ws.issue_wo({"할일#": todo_no, "작업유형": "긴급" if urgency.startswith("P1") else "수리",
                                   "구역": zpick.split(" · ")[-1] if zid else "기타", "설비·위치": asset_ref,
                                   "작업내용": what.strip()[:120], "우선순위": "높음", "배정구분": "기술",
                                   "책임자": me, "예정일": None}, me, also_todo=False)
            msgs.append((ok2, m2))
            if ok2:
                wo_no = m2.split()[0]
                msgs.append(ws.start_work(wo_no, me))
        sent = notify.slack_team(f"🚨 {title}\n📍 {where or '-'}\n✋ {me} " +
                                 ("처리 완료(사후 기록)" if after else "처리 중"))
        msgs.append((True, "💬 팀 Slack 알림 전송" if sent else "💬 Slack 미설정 — 알림 생략"))
    else:
        ok, msg = add_todo(group, what.strip()[:80], "시설", "높음" if urgency.startswith(("P1", "P2")) else "보통",
                           None, "진행 전", note + " [팀장 요청]", "", assignee="", urgency=urgency,
                           asset=asset_ref, source="긴급 접수")
        msgs.append((ok, msg + " · 팀장 배정 대기"))
        res = notify.call_lead(title, f"{what.strip()}\n📍 {where or '-'}\n접수: {me} ({msg})",
                               urgent=urgency.startswith("P1"))
        msgs.append((res["push"] or res["slack"], notify.status_line(res)))

    if eid and urgency.startswith(("P1", "P2")) and not after:
        msgs.append(A.add_status("설비", eid, "🔴 고장·이상", what.strip(), me))
    voice.clear(VKEY)
    st.session_state.rep_flash = msgs
    st.rerun()
