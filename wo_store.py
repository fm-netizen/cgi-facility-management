"""작업지시서(WO) · 작업 로그 · 자재 사용 · 디렉토리 읽기/쓰기 (CGI FM 할 일 관리표)."""
import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from sheets_config import TODO_SPREADSHEET_ID

TZ = ZoneInfo("America/New_York")

SHEET_WO = "🎫 작업지시서"
SHEET_LOG = "⏱ 작업 로그"
SHEET_MAT = "🔩 자재 사용"
SHEET_DIR = "📦 자재·공구 디렉토리"
SHEET_LOC = "📍 보관 위치"
SHEET_WORKER = "👷 작업자"

WO_COLS = ["WO번호", "할일#", "발행일", "작업유형", "구역", "설비·위치", "작업내용",
           "우선순위", "배정구분", "책임자", "예정일", "상태", "최초 시작", "최종 종료",
           "순작업(h)", "차감(분)", "작업자", "인원", "인시(Man-h)", "자재비(US$)",
           "외주비(US$)", "총비용(US$)", "결과 코멘트", "사진 링크", "검수", "플래그·비고"]
LOG_COLS = ["로그ID", "WO번호", "기록자", "시작", "종료", "시간(h)", "종료 방식", "비고"]
DIR_COLS = ["품목코드", "구분", "카테고리", "품명", "규격·모델", "제조사", "단위", "단가(US$)",
            "입고 누계", "사용 누계", "현재고", "안전재고", "재고 상태", "보관위치코드",
            "위치 설명", "구매처", "관련 설비", "공구 사용 현황", "비고"]
LOC_COLS = ["위치코드", "구역코드", "구역명", "보관설비", "단", "칸", "위치 설명", "비고"]
WORKER_COLS = ["이름", "역할", "배정구분", "활성", "연락처", "비고"]
MAT_COLS = ["WO번호", "일시", "품목코드", "품명", "수량", "단위", "단가(US$)", "금액(US$)",
            "입력자", "비고", "직접입력 품명", "직접입력 단위", "직접입력 단가(US$)", "등록 상태"]

WORK_TYPES = ["수리", "서비스", "정기점검(PM)", "긴급", "설치", "행정", "기타"]
ZONES = ["수영장", "Gym", "락커룸(남)", "락커룸(여)", "스파·사우나", "기계실", "지붕",
         "외부·조경", "주차장", "사무실", "하우스", "기타"]
PRIORITIES = ["높음", "보통", "낮음"]
ASSIGN = ["기술", "행정"]
OPEN_WO = ["발행", "진행 중", "일시정지", "보류"]

LONG_RUN_HOURS = 3          # 연속 기록이 이 시간을 넘으면 경고
SHIFT_END = time(17, 0)     # 전날 이전 미종료 구간은 이 시각으로 자동 종료
_EPOCH = datetime(1899, 12, 30)


# ── 공통 ─────────────────────────────────────────────────────
def now() -> datetime:
    return datetime.now(TZ).replace(tzinfo=None, second=0, microsecond=0)


def today() -> date:
    return now().date()


def fmt_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M") if dt else ""


def fmt_d(d) -> str:
    return d.strftime("%Y-%m-%d") if d else ""


def to_dt(v):
    """시트 값(시리얼 숫자 또는 문자열) → datetime. 실패 시 None."""
    if v in ("", None):
        return None
    if isinstance(v, (int, float)):
        return _EPOCH + timedelta(days=float(v))
    try:
        return pd.to_datetime(str(v)).to_pydatetime()
    except Exception:
        return None


def _txt(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def _ss():
    from sheets_helper import get_sheets_client
    client = get_sheets_client()
    if client is None:
        return None
    return client.open_by_key(TODO_SPREADSHEET_ID)


def _frame(rows, cols, key_idx=0):
    out = []
    for i, raw in enumerate(rows[1:], start=2):
        r = (list(raw) + [""] * len(cols))[:len(cols)]
        if not _txt(r[key_idx]):
            continue
        rec = dict(zip(cols, r))
        rec["_row"] = i
        out.append(rec)
    return pd.DataFrame(out, columns=cols + ["_row"])


# ── 읽기 ─────────────────────────────────────────────────────
@st.cache_data(ttl=30, show_spinner="작업 데이터 불러오는 중...")
def load_all():
    """WO·로그·작업자·디렉토리·위치를 한 번의 API 호출로 읽음. 실패 시 None."""
    try:
        ss = _ss()
        if ss is None:
            return None
        names = [SHEET_WO, SHEET_LOG, SHEET_WORKER, SHEET_DIR, SHEET_LOC, SHEET_MAT]
        res = ss.values_batch_get(
            [f"'{n}'!A1:Z" for n in names],
            params={"valueRenderOption": "UNFORMATTED_VALUE",
                    "dateTimeRenderOption": "SERIAL_NUMBER"})
        vr = [x.get("values", []) for x in res.get("valueRanges", [])]
    except Exception as e:
        st.session_state["wo_error"] = str(e)
        return None

    wo = _frame(vr[0], WO_COLS)
    for c in ["WO번호", "할일#", "작업내용", "책임자", "상태", "작업자", "플래그·비고",
              "결과 코멘트", "검수", "설비·위치", "구역", "작업유형", "우선순위", "배정구분"]:
        wo[c] = wo[c].map(_txt)
    for c in ["최초 시작", "최종 종료"]:
        wo[c] = wo[c].map(to_dt)
    for c in ["발행일", "예정일"]:
        wo[c] = wo[c].map(lambda v: (to_dt(v).date() if to_dt(v) else None))

    log = _frame(vr[1], LOG_COLS)
    for c in ["로그ID", "WO번호", "기록자", "종료 방식"]:
        log[c] = log[c].map(_txt)
    log["시작"] = log["시작"].map(to_dt)
    log["종료"] = log["종료"].map(to_dt)

    workers = _frame(vr[2], WORKER_COLS)
    for c in WORKER_COLS:
        workers[c] = workers[c].map(_txt)
    workers = workers[workers["활성"].str.upper() != "N"]

    directory = _frame(vr[3], DIR_COLS)
    for c in ["품목코드", "구분", "카테고리", "품명", "규격·모델", "단위", "재고 상태",
              "보관위치코드", "위치 설명", "관련 설비", "공구 사용 현황"]:
        directory[c] = directory[c].map(_txt)

    locations = _frame(vr[4], LOC_COLS)
    mat = _frame(vr[5] if len(vr) > 5 else [], MAT_COLS)
    for c in ["WO번호", "품목코드", "직접입력 품명", "직접입력 단위", "입력자"]:
        mat[c] = mat[c].map(_txt)
    return {"wo": wo, "log": log, "workers": workers,
            "directory": directory, "locations": locations, "mat": mat}


def unregistered_summary(mat):
    """직접 입력(코드 없는) 자재를 품명별로 집계 — 디렉토리 등록 후보."""
    m = mat[(mat["품목코드"] == "") & (mat["직접입력 품명"] != "")].copy()
    if m.empty:
        return m
    m["수량"] = pd.to_numeric(m["수량"], errors="coerce").fillna(0)
    m["단가"] = pd.to_numeric(m["직접입력 단가(US$)"], errors="coerce")
    m["key"] = m["직접입력 품명"].str.strip().str.lower()
    g = m.groupby("key").agg(품명=("직접입력 품명", "last"), 사용횟수=("WO번호", "count"),
                             총수량=("수량", "sum"), 단위=("직접입력 단위", "last"),
                             최근단가=("단가", "last"), 최근WO=("WO번호", "last"))
    return g.sort_values("사용횟수", ascending=False).reset_index(drop=True)


def clear_cache():
    load_all.clear()
    try:
        from todo_store import load_todos
        load_todos.clear()
    except Exception:
        pass


# ── 조회 도우미 ───────────────────────────────────────────────
def open_segment(log, worker, wo_no=None):
    """작업자의 미종료 구간(행) 반환. 없으면 None."""
    m = (log["기록자"] == worker) & log["종료"].isna()
    if wo_no:
        m &= log["WO번호"] == wo_no
    hit = log[m]
    return None if hit.empty else hit.iloc[-1]


def worked_hours(log, wo_no, until=None):
    """해당 WO의 기록 시간 합계(h). 미종료 구간은 until(기본 지금)까지 포함."""
    until = until or now()
    total = 0.0
    for _, r in log[log["WO번호"] == wo_no].iterrows():
        end = r["종료"] or until
        if r["시작"]:
            total += max(0.0, (end - r["시작"]).total_seconds() / 3600)
    return round(total, 2)


def next_wo_number(wo):
    prefix = f"WO-{now():%y%m}-"
    seqs = [int(m.group(1)) for v in wo["WO번호"]
            if (m := re.match(re.escape(prefix) + r"(\d+)$", v))]
    return f"{prefix}{(max(seqs) + 1 if seqs else 1):03d}"


def _next_row(ws):
    col = ws.col_values(1)
    return len(col) + 1


# ── 쓰기 ─────────────────────────────────────────────────────
def _write(ws, updates):
    """updates: [(A1범위, [[값...]])] — 수식 열은 건드리지 않도록 범위를 나눠 씀."""
    ws.batch_update([{"range": r, "values": v} for r, v in updates],
                    value_input_option="USER_ENTERED")


def _flag(current, text):
    return f"{current} / {text}" if current else text


def _todo_row(todo_no):
    from todo_store import load_todos
    df = load_todos()
    if df is None or not todo_no:
        return None
    hit = df[df["번호"].astype(str) == str(todo_no)]
    return None if hit.empty else hit.iloc[0]


def issue_wo(data, worker, also_todo=True):
    """WO 발행. data: dict(할일#, 작업유형, 구역, 설비·위치, 작업내용, 우선순위, 배정구분, 책임자, 예정일)."""
    try:
        d = load_all()
        ss = _ss()
        if d is None or ss is None:
            return False, "Sheets 미연결"
        todo_no = _txt(data.get("할일#"))
        if not todo_no and also_todo:
            from todo_store import add_todo
            group = "행정(일반)" if data["배정구분"] == "행정" else "시설 운영"
            ok, msg = add_todo(group, data["작업내용"], "시설", data["우선순위"],
                               data.get("예정일"), "진행 전", "작업지시서 발행", worker)
            m = re.search(r"#(\d+)", msg)
            if ok and m:
                todo_no = m.group(1)
        wo_no = next_wo_number(d["wo"])
        ws = ss.worksheet(SHEET_WO)
        r = _next_row(ws)
        row = [wo_no, todo_no, fmt_d(today()), data["작업유형"], data["구역"],
               data.get("설비·위치", ""), data["작업내용"], data["우선순위"],
               data["배정구분"], data["책임자"], fmt_d(data.get("예정일")), "발행"]
        _write(ws, [(f"A{r}:L{r}", [row]), (f"Z{r}", [[f"발행: {worker}"]])])
        clear_cache()
        return True, f"{wo_no} 발행 완료" + (f" (할 일 #{todo_no} 연결)" if todo_no else "")
    except Exception as e:
        return False, f"발행 실패: {e}"


def _close_segment(ss, seg, end, how, note=""):
    ws = ss.worksheet(SHEET_LOG)
    end = max(end, seg["시작"]) if seg["시작"] else end
    ups = [(f"E{seg['_row']}", [[fmt_dt(end)]]), (f"G{seg['_row']}", [[how]])]
    if note:
        ups.append((f"H{seg['_row']}", [[note]]))
    _write(ws, ups)
    return end


def _wo_row(d, wo_no):
    hit = d["wo"][d["wo"]["WO번호"] == wo_no]
    return None if hit.empty else hit.iloc[0]


def start_work(wo_no, worker):
    """시작/재개. 같은 작업자가 다른 WO를 진행 중이면 그 구간을 자동 일시정지."""
    try:
        d = load_all()
        ss = _ss()
        if d is None or ss is None:
            return False, "Sheets 미연결"
        t = now()
        msgs = []
        cur = open_segment(d["log"], worker)
        ws_wo = ss.worksheet(SHEET_WO)
        if cur is not None:
            if cur["WO번호"] == wo_no:
                return False, "이미 진행 중입니다."
            _close_segment(ss, cur, t, "자동전환", f"{wo_no} 시작으로 자동 일시정지")
            prev = _wo_row(d, cur["WO번호"])
            if prev is not None and prev["상태"] == "진행 중":
                _write(ws_wo, [(f"L{prev['_row']}", [["일시정지"]])])
            msgs.append(f"{cur['WO번호']} 자동 일시정지")

        ws_log = ss.worksheet(SHEET_LOG)
        r = _next_row(ws_log)
        log_id = f"L{t:%y%m%d%H%M}-{r}"
        _write(ws_log, [(f"A{r}:E{r}", [[log_id, wo_no, worker, fmt_dt(t), ""]])])

        w = _wo_row(d, wo_no)
        ups = [(f"L{w['_row']}", [["진행 중"]])]
        if not w["최초 시작"]:
            ups.append((f"M{w['_row']}", [[fmt_dt(t)]]))
        _write(ws_wo, ups)

        todo = _todo_row(w["할일#"])
        if todo is not None and todo["상태"] in ("진행 전", "보류"):
            from todo_store import update_status
            update_status(int(todo["_row"]), "진행 중", f"{wo_no} 작업 시작", worker, todo["비고"])
        clear_cache()
        msgs.insert(0, f"▶ {wo_no} 시작 {t:%H:%M}")
        return True, " · ".join(msgs)
    except Exception as e:
        return False, f"시작 실패: {e}"


def pause_work(wo_no, worker, at=None, reason=""):
    try:
        d = load_all()
        ss = _ss()
        if d is None or ss is None:
            return False, "Sheets 미연결"
        seg = open_segment(d["log"], worker, wo_no)
        if seg is None:
            return False, "진행 중인 기록이 없습니다."
        how = "수동(시각보정)" if at else "수동"
        end = _close_segment(ss, seg, at or now(), how, reason)
        w = _wo_row(d, wo_no)
        _write(ss.worksheet(SHEET_WO), [(f"L{w['_row']}", [["일시정지"]])])
        clear_cache()
        return True, f"⏸ {wo_no} 일시정지 {end:%H:%M}"
    except Exception as e:
        return False, f"일시정지 실패: {e}"


def complete_work(wo_no, worker, *, at=None, workers=None, deduct_min=0,
                  outside_cost=0.0, comment="", photo="", materials=None):
    """완료 보고. materials: [dict(code, name, qty, unit, price)] — code 없으면 직접 입력으로 저장."""
    try:
        d = load_all()
        ss = _ss()
        if d is None or ss is None:
            return False, "Sheets 미연결"
        w = _wo_row(d, wo_no)
        if w is None:
            return False, "WO를 찾을 수 없습니다."
        t = at or now()
        flags = []
        seg = open_segment(d["log"], worker, wo_no)
        if seg is not None:
            span = (t - seg["시작"]).total_seconds() / 3600 if seg["시작"] else 0
            if span > LONG_RUN_HOURS and not deduct_min:
                flags.append(f"⚠ 연속 {span:.1f}h 기록(차감 없음) — 확인 필요")
            _close_segment(ss, seg, t, "완료(시각보정)" if at else "완료")
        # 다른 작업자가 같은 WO에 열어둔 구간도 함께 종료
        for _, s in d["log"][(d["log"]["WO번호"] == wo_no) & d["log"]["종료"].isna()
                             & (d["log"]["기록자"] != worker)].iterrows():
            _close_segment(ss, s, t, "완료(일괄)")

        names = workers or [worker]
        ws_wo = ss.worksheet(SHEET_WO)
        r = w["_row"]
        flag_txt = w["플래그·비고"]
        for f in flags:
            flag_txt = _flag(flag_txt, f)
        _write(ws_wo, [
            (f"L{r}", [["완료"]]),
            (f"N{r}", [[fmt_dt(t)]]),
            (f"P{r}:Q{r}", [[int(deduct_min or 0), ", ".join(names)]]),
            (f"U{r}", [[float(outside_cost or 0)]]),
            (f"W{r}:X{r}", [[comment, photo]]),
            (f"Z{r}", [[flag_txt]]),
        ])

        mats = [m for m in (materials or [])
                if (m.get("code") or m.get("name")) and (m.get("qty") or 0) > 0]
        if mats:
            ws_m = ss.worksheet(SHEET_MAT)
            start = _next_row(ws_m)
            ups = []
            for i, m in enumerate(mats):
                rr = start + i
                code = m.get("code") or ""
                ups += [(f"A{rr}:C{rr}", [[wo_no, fmt_dt(t), code]]),
                        (f"E{rr}", [[m["qty"]]]), (f"I{rr}", [[worker]])]
                if not code:
                    price = m.get("price")
                    ups.append((f"K{rr}:M{rr}", [[m["name"].strip(), (m.get("unit") or "").strip(),
                                                  price if price else ""]]))
            _write(ws_m, ups)

        todo = _todo_row(w["할일#"])
        if todo is not None and todo["상태"] != "완료":
            from todo_store import update_status
            update_status(int(todo["_row"]), "완료", f"{wo_no} 완료({', '.join(names)})",
                          worker, todo["비고"])
        clear_cache()
        return True, f"■ {wo_no} 완료 보고 저장" + (" — ⚠ 확인 필요 표시됨" if flags else "")
    except Exception as e:
        return False, f"완료 저장 실패: {e}"


def review_wo(wo_no, reviewer, approve=True, note=""):
    try:
        d = load_all()
        ss = _ss()
        if d is None or ss is None:
            return False, "Sheets 미연결"
        w = _wo_row(d, wo_no)
        r = w["_row"]
        ws = ss.worksheet(SHEET_WO)
        if approve:
            _write(ws, [(f"L{r}", [["검수완료"]]),
                        (f"Y{r}", [[f"{reviewer} {today():%m/%d}" + (f" {note}" if note else "")]])])
            msg = f"✅ {wo_no} 검수완료"
        else:
            _write(ws, [(f"L{r}", [["발행"]]),
                        (f"Z{r}", [[_flag(w['플래그·비고'], f'재작업 {today():%m/%d} {reviewer}: {note}')]])])
            msg = f"↩ {wo_no} 재작업 지시"
        clear_cache()
        return True, msg
    except Exception as e:
        return False, f"검수 저장 실패: {e}"


def auto_close_stale():
    """어제 이전에 시작해 아직 열린 구간을 해당일 퇴근 시각으로 자동 종료 + WO에 ⚠ 표시."""
    d = load_all()
    ss = _ss()
    if d is None or ss is None:
        return 0
    stale = d["log"][d["log"]["종료"].isna() & d["log"]["시작"].notna()]
    stale = stale[stale["시작"].map(lambda x: x.date() < today())]
    if stale.empty:
        return 0
    ws_wo = ss.worksheet(SHEET_WO)
    for _, s in stale.iterrows():
        end = datetime.combine(s["시작"].date(), SHIFT_END)
        if end <= s["시작"]:
            end = s["시작"] + timedelta(hours=1)
        _close_segment(ss, s, end, "자동종료(퇴근)", "일시정지 누락 추정")
        w = _wo_row(d, s["WO번호"])
        if w is not None:
            ups = [(f"Z{w['_row']}", [[_flag(w['플래그·비고'],
                    f"⚠ {s['시작']:%m/%d} {s['기록자']} 미종료→{end:%H:%M} 자동종료, 시간 확인")]])]
            if w["상태"] == "진행 중":
                ups.append((f"L{w['_row']}", [["일시정지"]]))
            _write(ws_wo, ups)
    clear_cache()
    return len(stale)
