"""Slack 알림 (#fm-team).

Streamlit Secrets
  slack_webhook_url  = "https://hooks.slack.com/services/..."   팀 채널 Incoming Webhook
  slack_lead_user_id = "U0XXXXXXX"                            팀장 멤버 ID (멘션 → Slack 앱 푸시)
설정이 없으면 알림만 생략되고 앱은 정상 동작.
"""
import json
import urllib.request

import streamlit as st


def _secret(key):
    try:
        return st.secrets.get(key, "")
    except Exception:
        return ""


def slack_team(text: str) -> bool:
    url = _secret("slack_webhook_url")
    if not url:
        return False
    try:
        req = urllib.request.Request(url, data=json.dumps({"text": text}).encode("utf-8"),
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=8) as r:
            return 200 <= r.status < 300
    except Exception:
        return False


def call_lead(title: str, body: str) -> bool:
    """팀장 호출 = #fm-team에 팀장 멘션 메시지."""
    lead = _secret("slack_lead_user_id")
    mention = f"<@{lead}> " if lead else ""
    return slack_team(f"{mention}📞 *팀장 요청* — {title}\n{body}")


def result_msg(sent: bool) -> str:
    return "💬 Slack 알림 전송" if sent else "💬 Slack 미설정 — 알림 생략"
