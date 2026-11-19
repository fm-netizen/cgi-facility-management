"""CGI FM 할 일 관리표 ('할 일' 탭) 읽기/쓰기."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from sheets_config import TODO_SPREADSHEET_ID, TODO_SHEET_NAME

TZ = ZoneInfo("America/New_York")
HEADER_ROW = 5            # 시트의 헤더 행 번호 (1-based)
FIRST_DATA_ROW = 6
COLUMNS = ["번호", "프로젝트/구분", "할 일", "분류", "우선순위",
           "등록일", "마감일", "완료일", "상태", "출처", "비고"]

GROUPS = ["시설 운영", "공사 (RTU·제습기)", "공사 (Gym)", "행정(일반)",
          "행정(인스펙션)", "하우스", "BR 지역", "기타"]
CATEGORIES = ["시설", "공사", "재무", "인사", "기타"]
PRIORITIES = ["높음", "보통", "낮음"]
STATUSES = ["진행 전", "진행 중", "보류", "완료"]
OPEN_STATUSES = ["진행 전", "진행 중", "보류"]


def today() -> date:
    return datetime.now(TZ).date()


def _worksheet():
    from sheets_helper import get_sheets_client
    client = get_sheets_client()
    if client is None:
        return None
    return client.open_by_key(TODO_SPREADSHEET_ID).worksheet(TODO_SHEET_NAME)


@st.cache_data(ttl=60, show_spinner="할 일 목록 불러오는 중...")
def load_todos():
    """할 일 목록 DataFrame 반환. 미연결/오류 시 None."""
    try:
        ws = _worksheet()
        if ws is None:
            return None
        values = ws.get_all_values()
    except Exception as e:
        st.session_state["todo_error"] = str(e)
        return None
    return to_frame(values)


def to_frame(values):
    rows = []
    for idx, raw in enumerate(values[FIRST_DATA_ROW - 1:], start=FIRST_DATA_ROW):
        r = (list(raw) + [""] * len(COLUMNS))[:len(COLUMNS)]
        if not r[2].strip():          # '할 일'이 빈 행은 제외
            continue
        rec = dict(zip(COLUMNS, r))
        rec["_row"] = idx
        rows.append(rec)
    df = pd.DataFrame(rows, columns=COLUMNS + ["_row"])
    for c in ["등록일", "마감일", "완료일"]:
        df[c] = pd.to_datetime(df[c], errors="coerce").dt.date
    return df


def summarize(df):
    t = today()
    open_df = df[df["상태"] != "완료"]
    overdue = open_df[open_df["마감일"].notna() & (open_df["마감일"] < t)]
    due_soon = open_df[open_df["마감일"].notna()
                       & (open_df["마감일"] >= t)
                       & (open_df["마감일"] <= t + pd.Timedelta(days=7))]
    return {
        "total": len(df),
        "open": len(open_df),
        "in_progress": int((df["상태"] == "진행 중").sum()),
        "not_started": int((df["상태"] == "진행 전").sum()),
        "on_hold": int((df["상태"] == "보류").sum()),
        "done": int((df["상태"] == "완료").sum()),
        "overdue": overdue.sort_values("마감일"),
        "due_soon": due_soon.sort_values("마감일"),
        "high_open": open_df[open_df["우선순위"] == "높음"],
        "done_week": df[(df["상태"] == "완료") & df["완료일"].notna()
                        & (df["완료일"] >= t - pd.Timedelta(days=7))]
                       .sort_values("완료일", ascending=False),
    }


def _fmt(d):
    return d.strftime("%Y-%m-%d") if d else ""


def add_todo(group, task, category, priority, due, status, note, author):
    """다음 빈 행(번호만 있는 행 포함)에 할 일 추가. (성공여부, 메시지)"""
    try:
        ws = _worksheet()
        if ws is None:
            return False, "Sheets 미연결"
        values = ws.get_all_values()
        target, number = None, None
        for idx in range(FIRST_DATA_ROW, len(values) + 1):
            row = values[idx - 1] + [""] * 3
            if not row[2].strip():
                target, number = idx, row[0].strip()
                break
        if target is None:
            target = len(values) + 1
        if not number:
            nums = [int(v[0]) for v in values[FIRST_DATA_ROW - 1:]
                    if v and v[0].strip().isdigit()]
            number = str(max(nums) + 1 if nums else 1)
        t = today()
        note_text = f"[현장입력·{author}] {note}".strip() if author else note
        row = [number, group, task, category, priority, _fmt(t), _fmt(due),
               _fmt(t) if status == "완료" else "", status, "직접 입력", note_text]
        ws.update(range_name=f"A{target}:K{target}", values=[row],
                  value_input_option="USER_ENTERED")
        load_todos.clear()
        return True, f"#{number} 등록 완료"
    except Exception as e:
        return False, f"저장 실패: {e}"


def update_status(sheet_row, new_status, note, author, current_note=""):
    """상태 변경. 완료 시 완료일 자동 입력, 메모는 비고에 덧붙임."""
    try:
        ws = _worksheet()
        if ws is None:
            return False, "Sheets 미연결"
        t = today()
        done = _fmt(t) if new_status == "완료" else ""
        ws.update(range_name=f"H{sheet_row}:I{sheet_row}", values=[[done, new_status]],
                  value_input_option="USER_ENTERED")
        if note.strip():
            tag = f"{t.month}/{t.day} {author}: " if author else f"{t.month}/{t.day}: "
            merged = f"{current_note} / {tag}{note.strip()}" if current_note else f"{tag}{note.strip()}"
            ws.update(range_name=f"K{sheet_row}", values=[[merged]],
                      value_input_option="USER_ENTERED")
        load_todos.clear()
        return True, "상태 변경 완료"
    except Exception as e:
        return False, f"저장 실패: {e}"
