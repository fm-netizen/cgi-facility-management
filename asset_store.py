"""설비·시설 대장 (Asset Register) 읽기/쓰기.

구조
- 🏢 시설 구역 / ⚙️ 설비 대장: 기준정보(행 1 제목, 행 2 헤더, 행 3부터 데이터)
- 📝 상태 기록: 상태 변경 이력(행 1 헤더). 대장의 '현재 상태'는 이 탭의 최신 기록을 수식으로 표시
앱은 항상 '📝 상태 기록'에 한 줄 추가하는 방식으로만 상태를 바꾼다(이력 보존).
"""
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from sheets_config import SPREADSHEET_ID, SHEET_NAMES

TZ = ZoneInfo("America/New_York")

SHEET_ZONE = SHEET_NAMES["zone"]
SHEET_EQUIP = SHEET_NAMES["equipment"]
SHEET_LOG = SHEET_NAMES["status_log"]

ZONE_COLS = ["구역ID", "구역명", "층·위치", "현재 상태", "최근 기록", "온도(°F)", "습도(%)",
             "최근 비고", "관련 할 일#", "비고"]
EQUIP_COLS = ["설비ID", "설비명", "카테고리", "구역ID", "위치 상세", "제조사·모델", "담당",
              "정기 PM ID", "다음 점검", "관련 할 일#", "현재 상태", "최근 기록", "최근 비고", "비고"]
LOG_COLS = ["기록일시", "대상", "ID", "상태", "온도(°F)", "습도(%)", "비고", "기록자", "관련 할 일#/WO#"]

STATUSES = ["🟢 정상", "🟡 점검 필요", "🔧 수리·공사 중", "🔴 고장·이상", "🔄 교체 예정"]
NORMAL = STATUSES[0]
ALERT = ["🔴 고장·이상", "🔧 수리·공사 중"]
CATEGORIES = ["HVAC", "배관", "전기", "수처리", "스파", "세탁", "Gym 장비", "AV", "소방",
              "제설", "조경", "제어", "차량", "기타"]

EQUIP_EDIT_LAST_COL = "J"     # A~J는 입력, K~M은 수식(쓰지 않음)


def now_str() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M")


def _ss():
    from sheets_helper import get_sheets_client
    client = get_sheets_client()
    return None if client is None else client.open_by_key(SPREADSHEET_ID)


def _frame(values, cols, first_row):
    rows = []
    for idx, raw in enumerate(values[first_row - 1:], start=first_row):
        r = [("" if v is None else str(v)).strip() for v in raw]
        r = (r + [""] * len(cols))[:len(cols)]
        if not r[0]:
            continue
        rec = dict(zip(cols, r))
        rec["_row"] = idx
        rows.append(rec)
    return pd.DataFrame(rows, columns=cols + ["_row"])


@st.cache_data(ttl=60, show_spinner="설비·시설 현황 불러오는 중...")
def load_assets():
    """{'zones': df, 'equip': df} 반환. 미연결/오류 시 None."""
    try:
        ss = _ss()
        if ss is None:
            return None
        res = ss.values_batch_get([f"'{SHEET_ZONE}'!A1:J100", f"'{SHEET_EQUIP}'!A1:N300"])
        vr = res.get("valueRanges", [])
        zv = vr[0].get("values", []) if len(vr) > 0 else []
        ev = vr[1].get("values", []) if len(vr) > 1 else []
    except Exception as e:
        st.session_state["asset_error"] = str(e)
        return None
    return {"zones": _frame(zv, ZONE_COLS, 3), "equip": _frame(ev, EQUIP_COLS, 3)}


@st.cache_data(ttl=60, show_spinner=False)
def load_history(asset_id: str, limit: int = 20):
    """특정 ID의 최근 상태 기록 (최신순)."""
    try:
        ss = _ss()
        if ss is None:
            return None
        values = ss.worksheet(SHEET_LOG).get_all_values()
    except Exception:
        return None
    rows = [(list(r) + [""] * len(LOG_COLS))[:len(LOG_COLS)] for r in values[1:]]
    df = pd.DataFrame([r for r in rows if r[2] == asset_id], columns=LOG_COLS)
    return df.iloc[::-1].head(limit)


def counts(df, col="현재 상태"):
    c = {s: int((df[col] == s).sum()) for s in STATUSES}
    c["전체"] = len(df)
    c["이상"] = len(df) - c[NORMAL]
    return c


def add_status(kind, asset_id, status, note="", author="", temp="", humidity="", ref=""):
    """상태 기록 한 줄 추가. kind = '시설' | '설비'. (성공여부, 메시지)"""
    if status not in STATUSES:
        return False, "상태 값 오류"
    try:
        ss = _ss()
        if ss is None:
            return False, "Sheets 미연결"
        row = [now_str(), kind, asset_id, status, temp, humidity, note.strip(), author.strip(), ref]
        ss.worksheet(SHEET_LOG).append_row(row, value_input_option="USER_ENTERED",
                                           table_range="A1:I1")
        load_assets.clear()
        load_history.clear()
        return True, f"{asset_id} 상태 기록 완료"
    except Exception as e:
        return False, f"저장 실패: {e}"


def next_equip_id(equip_df, zone_id: str) -> str:
    nums = [int(i.split("-")[-1]) for i in equip_df["설비ID"]
            if i.startswith(f"{zone_id}-") and i.split("-")[-1].isdigit()]
    return f"{zone_id}-{(max(nums) + 1) if nums else 1:02d}"


def add_equipment(equip_df, rec: dict, status, note, author):
    """설비 대장에 새 설비 추가(A~J만 기록) 후 초기 상태 기록."""
    try:
        ss = _ss()
        if ss is None:
            return False, "Sheets 미연결"
        ws = ss.worksheet(SHEET_EQUIP)
        col_a = ws.col_values(1)
        target = max(len(col_a) + 1, 3)
        new_id = next_equip_id(equip_df, rec["구역ID"])
        row = [new_id, rec["설비명"], rec["카테고리"], rec["구역ID"], rec.get("위치 상세", ""),
               rec.get("제조사·모델", ""), rec.get("담당", ""), rec.get("정기 PM ID", ""),
               rec.get("다음 점검", ""), rec.get("관련 할 일#", "")]
        ws.update(range_name=f"A{target}:{EQUIP_EDIT_LAST_COL}{target}", values=[row],
                  value_input_option="USER_ENTERED")
        ok, msg = add_status("설비", new_id, status, note or "신규 등록", author)
        load_assets.clear()
        return ok, f"{new_id} 등록 완료" if ok else msg
    except Exception as e:
        return False, f"저장 실패: {e}"
