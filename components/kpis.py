"""kpis.py - Composant carte KPI réutilisable."""

import streamlit as st


def kpi_card(label: str, value: str, delta: str = None, delta_dir: str = "flat", help_text: str = None):
    """Affiche une carte KPI. delta_dir: 'up' | 'down' | 'flat'."""
    delta_html = ""
    if delta:
        arrow = {"up": "▲", "down": "▼", "flat": "–"}.get(delta_dir, "–")
        cls = {"up": "kpi-delta-up", "down": "kpi-delta-down", "flat": "kpi-delta-flat"}.get(delta_dir, "kpi-delta-flat")
        delta_html = f'<div class="{cls}">{arrow} {delta}</div>'

    tooltip = f' title="{help_text}"' if help_text else ""
    st.markdown(
        f"""
        <div class="kpi-card"{tooltip}>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_row(items: list):
    """items: liste de dicts {label, value, delta, delta_dir, help_text}"""
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            kpi_card(
                item.get("label", ""),
                item.get("value", ""),
                item.get("delta"),
                item.get("delta_dir", "flat"),
                item.get("help_text"),
            )
