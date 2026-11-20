"""바로가기 버튼 — 브라우저 링크(<a>)로 즉시 열림 (st.link_button 대체)."""
from html import escape

import streamlit as st

_CSS = """
<style>
.cgi-links{display:flex;flex-wrap:wrap;gap:10px;margin:4px 0 8px}
.cgi-links a{flex:1 1 180px;text-align:center;padding:9px 10px;border-radius:8px;
  border:1px solid rgba(49,51,63,.2);background:#fff;color:#31333F !important;
  text-decoration:none !important;font-size:14px;white-space:nowrap}
.cgi-links a:hover{border-color:#048A81;color:#048A81 !important}
</style>
"""


def link_buttons(links):
    """links: [(라벨, URL), ...] — 한 줄에 균등 배치, 좁은 화면에서는 자동 줄바꿈."""
    items = "".join(
        f"<a href='{escape(url, quote=True)}' target='_blank' rel='noopener noreferrer'>"
        f"{escape(label)} ↗</a>"
        for label, url in links if url and not url.startswith("YOUR"))
    st.markdown(_CSS + f"<div class='cgi-links'>{items}</div>", unsafe_allow_html=True)
