"""말하면 기록 (Speech-to-Text).

- 녹음: st.audio_input (휴대폰·PC 브라우저 마이크)
- 변환: Google Cloud Speech-to-Text (기존 서비스 계정 사용, 한국어 + 영어 자동 인식)
  GCP 프로젝트에서 'Cloud Speech-to-Text API' 사용 설정 필요. 1회 최대 1분.
- API가 아직 꺼져 있어도 앱은 정상 동작하며, 휴대폰 키보드의 🎤 받아쓰기로 대체 가능.
"""
import base64

import streamlit as st

_ENDPOINT = "https://speech.googleapis.com/v1p1beta1/speech:recognize"

# 휴대폰에서 누르기 쉽게 녹음/정지 버튼 확대 (지름 64px, 아이콘 36px)
_CSS = """
<style>
[data-testid="stAudioInput"] > div:last-child{min-height:88px;align-items:center}
[data-testid="stAudioInputActionButton"]{
  width:64px !important;height:64px !important;min-width:64px !important;
  border-radius:50% !important;background:#E8F4F3 !important;
  border:2px solid #048A81 !important;margin:0 6px !important}
[data-testid="stAudioInputActionButton"] svg{width:36px !important;height:36px !important;color:#048A81}
[data-testid="stAudioInputActionButton"][aria-label*="Stop"]{background:#FDE8E8 !important;border-color:#D93025 !important}
[data-testid="stAudioInputActionButton"][aria-label*="Stop"] svg{color:#D93025}
[data-testid="stAudioInputWaveformTimeCode"]{font-size:16px}
</style>
"""


def _session():
    from google.oauth2.service_account import Credentials
    from google.auth.transport.requests import AuthorizedSession
    info = st.secrets.get("gcp_service_account", None)
    if not info:
        return None
    creds = Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/cloud-platform"])
    return AuthorizedSession(creds)


# 현장 용어 힌트 (인식률 향상). 설비 대장의 구역·설비명은 자동으로 추가됨
BASE_PHRASES = [
    "RTU", "제습기", "덕트", "콘덴서", "냉매", "Gutter", "Heating Cable", "AHU", "벤틸레이터",
    "V-Belt", "에어필터", "백워시", "Shock", "약품기", "약품 조절장치", "온탕", "냉탕", "허브탕",
    "스팀사우나", "소금방", "맥반석", "찜질방", "락커룸", "세탁실", "건조기", "린트 커버", "감지 스위치",
    "트레드밀", "체스트 프레스", "타오로빅", "BnB 센터", "기계실", "지하 기계실", "Snow Plow",
    "Snow Blower", "제설", "Irrigation", "스프링클러", "작업지시서", "WO", "PM", "Life Fitness",
    "Hoist", "Precor", "Cybex", "Johnstone", "ADE Systems", "Heroes", "GS Labs", "Closter",
    "Exit Sign", "비상등", "누수", "정전", "차단기", "브레이커", "밸브", "펌프", "히터", "보일러",
]


def _phrases():
    words = list(BASE_PHRASES)
    try:
        import asset_store as A
        d = A.load_assets()
        if d:
            words += d["zones"]["구역명"].tolist() + d["equip"]["설비명"].tolist()
    except Exception:
        pass
    out, seen = [], set()
    for w in words:
        w = str(w).strip()[:100]
        if w and w not in seen:
            seen.add(w)
            out.append(w)
    return out[:500]


def transcribe(wav_bytes: bytes) -> tuple[bool, str]:
    try:
        s = _session()
        if s is None:
            return False, "서비스 계정 미설정"
        body = {
            "config": {"languageCode": "ko-KR", "alternativeLanguageCodes": ["en-US"],
                       "enableAutomaticPunctuation": True,
                       "speechContexts": [{"phrases": _phrases(), "boost": 10}]},
            "audio": {"content": base64.b64encode(wav_bytes).decode("ascii")},
        }
        r = s.post(_ENDPOINT, json=body, timeout=30)
        if r.status_code == 400:            # 힌트 형식 문제 시 힌트 없이 재시도
            body["config"].pop("speechContexts", None)
            r = s.post(_ENDPOINT, json=body, timeout=30)
        if r.status_code == 403:
            return False, "Speech-to-Text API가 꺼져 있습니다 (GCP에서 사용 설정 필요)"
        if r.status_code != 200:
            return False, f"변환 실패 ({r.status_code})"
        results = r.json().get("results", [])
        text = " ".join(x["alternatives"][0]["transcript"].strip()
                        for x in results if x.get("alternatives"))
        return (True, text) if text else (False, "인식된 말이 없습니다. 다시 녹음해 주세요.")
    except Exception as e:
        return False, f"변환 오류: {e}"


def voice_box(key: str, label: str = "🎤 말로 입력") -> str:
    """녹음 → 텍스트. 결과는 st.session_state[f'{key}_text']에 누적되어 반환.

    폼 밖에서 호출하고, 폼의 text_area value로 반환값을 넣어 사용."""
    tkey, hkey = f"{key}_text", f"{key}_hash"
    st.markdown(_CSS, unsafe_allow_html=True)
    n = st.session_state.get(f"{key}_n", 0)
    audio = st.audio_input(label, key=f"{key}_audio_{n}")
    if audio is not None:
        data = audio.getvalue()
        h = hash(data)
        if st.session_state.get(hkey) != h:
            st.session_state[hkey] = h
            with st.spinner("음성을 글로 바꾸는 중..."):
                ok, text = transcribe(data)
            if ok:
                prev = st.session_state.get(tkey, "")
                st.session_state[tkey] = f"{prev} {text}".strip()
            else:
                st.warning(f"🎤 {text} — 휴대폰 키보드의 🎤 받아쓰기를 사용하세요.")
    return st.session_state.get(tkey, "")


def clear(key: str):
    for k in (f"{key}_text", f"{key}_hash"):
        st.session_state.pop(k, None)
    st.session_state[f"{key}_n"] = st.session_state.get(f"{key}_n", 0) + 1
