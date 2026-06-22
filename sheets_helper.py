import streamlit as st
import json
from datetime import datetime

def get_sheets_client():
    """Google Sheets 클라이언트 반환. 미연결 시 None."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        creds_json = st.secrets.get("gcp_service_account", None)
        if not creds_json:
            return None

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
        return gspread.authorize(creds)
    except Exception:
        return None


def is_connected():
    return get_sheets_client() is not None


def append_row(sheet_name: str, row_data: list, spreadsheet_id: str = None):
    """시트에 행 추가. 실패 시 False 반환."""
    try:
        from sheets_config import SPREADSHEET_ID
        sid = spreadsheet_id or SPREADSHEET_ID
        if sid == "YOUR_SPREADSHEET_ID":
            return False

        client = get_sheets_client()
        if not client:
            return False

        sh = client.open_by_key(sid)
        ws = sh.worksheet(sheet_name)
        ws.append_row(row_data, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.error(f"Sheets 저장 실패: {e}")
        return False


def read_sheet(sheet_name: str, spreadsheet_id: str = None):
    """시트 전체 데이터 반환. 실패 시 None."""
    try:
        from sheets_config import SPREADSHEET_ID
        sid = spreadsheet_id or SPREADSHEET_ID
        if sid == "YOUR_SPREADSHEET_ID":
            return None

        client = get_sheets_client()
        if not client:
            return None

        sh = client.open_by_key(sid)
        ws = sh.worksheet(sheet_name)
        return ws.get_all_records()
    except Exception:
        return None


def save_indicator(success: bool, label: str = ""):
    """저장 결과 표시."""
    if success:
        st.success(f"✅ Google Sheets 저장 완료 {f'— {label}' if label else ''}")
    else:
        st.warning("⚠️ Sheets 미연결 — 세션에만 저장됨 (연동 후 자동 동기화)")
