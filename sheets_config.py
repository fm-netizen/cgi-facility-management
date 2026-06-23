# Google Sheets 연동 설정
# 실제 사용 전 아래 값들을 채워주세요

SPREADSHEET_ID = "1ttWrMsylk1rREaC6T9PYDZAaxe18hm8JhX7jJg-c_YY"  # Google Sheets URL에서 복사
# 예: https://docs.google.com/spreadsheets/d/[이 부분]/edit

# 시트 이름 매핑
SHEET_NAMES = {
    "facility":    "시설 상황",
    "equipment":   "설비 상황",
    "maintenance": "메인트넌스",
    "memo":        "메모",
    "task":        "📋 Active Tasks",
}

# 바로가기 URL 설정
QUICK_LINKS = {
    "📊 Master Status Sheet": f"https://docs.google.com/spreadsheets/d/1ttWrMsylk1rREaC6T9PYDZAaxe18hm8JhX7jJg-c_YY/edit",
    "📋 Task Tracker":        "https://docs.google.com/spreadsheets/d/1KklNrOvg-Nov3tkEGBWqCYGs8AQiOCqeUWDJh81UqYY/edit?gid=1564917165#gid=1564917165",
    "📁 Google Drive":        "https://drive.google.com/drive/u/0/folders/1iZGAygQTWYS1U5uHWz5UxfQ6_dRMvsB9",
    "💬 Slack #cgi-facility-dev": "https://app.slack.com/client/T0B6V3G2AM9/C0BC4S9AACS",
}
