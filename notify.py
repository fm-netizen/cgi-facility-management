"""알림: 팀 전체 = Slack 채널(Incoming Webhook), 팀장 호출 = 휴대폰 푸시(ntfy) + Slack 멘션.

Streamlit Secrets
  slack_webhook_url   = "https://hooks.slack.com/services/..."   (팀 채널)
  slack_lead_user_id  = "U0XXXXXXX"                            (팀장 Slack 멤버 ID, 멘션 → Slack 앱 푸시)
  ntfy_topic          = "cgi-fm-xxxxxxxx"                       (팀장 휴대폰 ntfy 앱에서 구독한 토픽)
설정이 없으면 해당 알림만 건너뜀(앱 동작에는 영향 없음).
"""
import json
import urllib.request

import streamlit as st


def _secret(key):
    try:
        return st.secrets.get(key, "")
    except Exception:
        return ""


def _post(url, data: bytes, headers: dict):
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=8) as r:
        return 200 <= r.status < 300


def slack_team(text: str) -> bool:
    url = _secret("slack_webhook_url")
    if not url:
        return False
    try:
        return _post(url, json.dumps({"text": text}).encode("utf-8"),
                     {"Content-Type": "application/json"})
    except Exception:
        return False


def call_lead(title: str, body: str, urgent: bool = True) -> dict:
    """팀장 호출: ntfy 푸시 + Slack 채널 멘션. 결과 dict 반환."""
    res = {"push": False, "slack": False}
    topic = _secret("ntfy_topic")
    if topic:
        try:
            payload = {"topic": topic, "title": title, "message": body,
                       "priority": 5 if urgent else 4, "tags": ["rotating_light"]}
            res["push"] = _post("https://ntfy.sh/", json.dumps(payload).encode("utf-8"),
                                {"Content-Type": "application/json"})
        except Exception:
            res["push"] = False
    lead = _secret("slack_lead_user_id")
    mention = f"<@{lead}> " if lead else ""
    res["slack"] = slack_team(f"{mention}📞 *팀장 요청* — {title}\n{body}")
    return res


def status_line(res: dict) -> str:
    parts = []
    parts.append("📱 푸시 전송" if res.get("push") else "📱 푸시 미설정/실패")
    parts.append("💬 Slack 전송" if res.get("slack") else "💬 Slack 미설정/실패")
    return " · ".join(parts)
