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

# 바로가기 URL 설정 (여기 한 곳만 수정하면 앱 전체에 반영됨)
MASTER_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"
TASK_TRACKER_URL = "https://docs.google.com/spreadsheets/d/1KklNrOvg-Nov3tkEGBWqCYGs8AQiOCqeUWDJh81UqYY/edit?gid=1564917165#gid=1564917165"
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1iZGAygQTWYS1U5uHWz5UxfQ6_dRMvsB9"
SLACK_URL        = "https://app.slack.com/client/T0B6V3G2AM9/C0BC4S9AACS"  # #cgi-facility-dev (비공개 채널)

QUICK_LINKS = {
    "📊 Master Status Sheet":    MASTER_SHEET_URL,
    "📋 Task Tracker":           TASK_TRACKER_URL,
    "📁 Google Drive":           DRIVE_FOLDER_URL,
    "💬 Slack #cgi-facility-dev": SLACK_URL,
}
