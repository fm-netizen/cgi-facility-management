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
    "📋 Task Tracker":        "YOUR_TASK_TRACKER_URL",
    "📁 Google Drive":        "https://drive.google.com/drive/folders/YOUR_FOLDER_ID",
    "💬 Slack #cgi-facility-dev": "https://app.slack.com/client/YOUR_WORKSPACE/C0BC4S9AACS",
}
