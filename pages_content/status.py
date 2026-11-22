"""🏢 현황 — 시설 구역 / 설비 / 자재 찾기."""
import streamlit as st

import wo_store as ws
from pages_content import equipment, facility
from pages_content import work_orders as wop
from pages_content.field_input import _check_pin


def show():
    st.title("🏢 현황")
    if not _check_pin():
        return
    t1, t2, t3 = st.tabs(["⚙️ 설비", "🏢 시설 구역", "📦 자재 찾기"])
    with t1:
        equipment.show(embedded=True)
    with t2:
        facility.show(embedded=True)
    with t3:
        d = ws.load_all()
        if d is None:
            st.caption("자재 데이터를 불러올 수 없습니다.")
        else:
            wop._tab_parts(d)
