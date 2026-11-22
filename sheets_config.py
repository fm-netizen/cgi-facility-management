# Google Sheets 연동 설정

# 설비·시설 대장 (Asset Register) — 기준정보 + 상태 기록
SPREADSHEET_ID = "1ttWrMsylk1rREaC6T9PYDZAaxe18hm8JhX7jJg-c_YY"

SHEET_NAMES = {
    "summary":   "📊 요약",
    "zone":      "🏢 시설 구역",
    "equipment": "⚙️ 설비 대장",
    "status_log": "📝 상태 기록",
    "vendor":    "🤝 업체(Vendor)",
}

# 할 일 관리표 (작업 기록: 할 일·WO·작업 로그·자재·정기 마스터·메모)
TODO_SPREADSHEET_ID = "1ZKARUthXvulkId6pPKD4iaCjy9Wg2FSMRsS_WXYK3RE"
TODO_SHEET_NAME     = "할 일"
MEMO_SHEET_NAME     = "📝 메모"
PM_MASTER_SHEET_NAME = "📅 정기 일정 마스터"


def _folder(fid):
    return f"https://drive.google.com/drive/folders/{fid}"


# 바로가기 URL (여기 한 곳만 수정하면 앱 전체에 반영됨)
MASTER_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit"
TASK_TRACKER_URL = f"https://docs.google.com/spreadsheets/d/{TODO_SPREADSHEET_ID}/edit"
DRIVE_FOLDER_URL = _folder("1BiHhsdzzhNzFjAvgnCN-a-TXUOyzQ6SL")   # 23.공사관련
SYSTEM_FOLDER_URL = _folder("1iZGAygQTWYS1U5uHWz5UxfQ6_dRMvsB9")  # CGI_Facility_Management_Cording (시스템 전용)
SLACK_URL        = "https://app.slack.com/client/T0B6V3G2AM9/C0CLRAGJV4G"  # #fm-team (비공개 채널, 앱 알림 채널)

# 공사 프로젝트 폴더 (폴더 ID 기준 — 이름을 바꿔도 링크 유지)
PROJECT_FOLDERS = {
    "2026-CGI-Renovation": [
        ("📁 2026 전체", _folder("1euAh8JxCvB0MBEUZ7imbKdxewnF7f460")),
        ("00 공통", _folder("1e2RZMXWQ0GbnhygJspBkwviQ28wY1Gsr")),
        ("01 지붕설비(RTU)", _folder("12t4t8r7IgpYm8lOpCZV28PjiL0zKV8ie")),
        ("02 수영장 제습기", _folder("1Vbe1wLhJ6_9aglFB8gWPS0zBNebAl3BX")),
        ("03 Gym 리노베이션", _folder("19vZHXfc0x3tKHmuzHcqXqEn0GIgUTOAX")),
        ("04 운동기구 교체", _folder("1BFnNm1elmaGhYXo3tKcvcNsOYCua0H9Q")),
        ("05 구매발주(PO)", _folder("1k6AnstM4uW1pYJWzq1qHzAyhGuOvLs3K")),
        ("06 기타(시설)", _folder("1AiyegHsaC71IaPXRZYt__yjG6G-hQCL1")),
    ],
    "2027-CGI-Renovation": [
        ("📁 2027 전체", _folder("1yO08gQZHGjjjzOLQVW9SVh9SCEgSMne2")),
        ("00 공통", _folder("1DX5_4_MIEnrnDeirGxaXwXg8h9K_wHLR")),
        ("01 설계", _folder("1jvGNnFcelxJAVjojz8wajUuoRd3ZnLtH")),
        ("02 허가", _folder("1nXed5cB-cyB-OSBPwL2ef-Sp8Y9Wbf-w")),
        ("03 견적·입찰", _folder("1Ba_rL1Sb3oByuMshP954UirT6lXqbXvm")),
        ("04 계약", _folder("1DEJhOvrV8bprOTJRYSv9f-jf73R74w3A")),
        ("05 구매발주(PO)", _folder("198SYnUwgd291K9JBTTeD-TOTjmR8N_MK")),
        ("06 시공", _folder("19DM3URW9qb0Wja6BHm5To50YuaiOazug")),
        ("07 준공", _folder("1PKisKvNMy_xvU3YbZzW4G46y9VBE2XdF")),
    ],
}

QUICK_LINKS = {
    "📊 설비·시설 대장":          MASTER_SHEET_URL,
    "📋 할 일 관리표":            TASK_TRACKER_URL,
    "📁 공사 폴더":               DRIVE_FOLDER_URL,
    "💬 Slack #fm-team":          SLACK_URL,
}
