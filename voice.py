"""말하면 기록 (Speech-to-Text).

- 녹음: st.audio_input (휴대폰·PC 브라우저 마이크)
- 변환: Google Cloud Speech-to-Text (기존 서비스 계정 사용, 한국어 + 영어 자동 인식)
  GCP 프로젝트에서 'Cloud Speech-to-Text API' 사용 설정 필요. 1회 최대 1분.
- API가 아직 꺼져 있어도 앱은 정상 동작하며, 휴대폰 키보드의 🎤 받아쓰기로 대체 가능.
"""
import base64

import streamlit as st

_ENDPOINT = "https://speech.googleapis.com/v1p1beta1/speech:recognize"


def _session():
    from google.oauth2.service_account import Credentials
    from google.auth.transport.requests import AuthorizedSession
    info = st.secrets.get("gcp_service_account", None)
    if not info:
        return None
    creds = Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/cloud-platform"])
    return AuthorizedSession(creds)


def transcribe(wav_bytes: bytes) -> tuple[bool, str]:
    try:
        s = _session()
        if s is None:
            return False, "서비스 계정 미설정"
        body = {
            "config": {"languageCode": "ko-KR", "alternativeLanguageCodes": ["en-US"],
                       "enableAutomaticPunctuation": True},
            "audio": {"content": base64.b64encode(wav_bytes).decode("ascii")},
        }
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
