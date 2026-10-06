"""style.py - Injection du CSS personnalisé (charte NSIA Vie Assurances)."""

from contextlib import contextmanager
from pathlib import Path
import base64
import streamlit as st

NSIA_NAVY = "#0B1F4D"
NSIA_NAVY_DARK = "#081736"
NSIA_GOLD = "#F2B705"
NSIA_GOLD_DARK = "#D9A300"
NSIA_WHITE = "#FFFFFF"
NSIA_BG = "#0A1A3A"
NSIA_BG_LIGHT = "#0F2557"
NSIA_CARD = "#132B5C"
NSIA_CARD_HOVER = "#1A3671"
NSIA_TEXT = "#F4F7FB"
NSIA_MUTED = "#A9BDD1"
NSIA_BORDER = "#1E3A6B"

CHART_COLORS = ["#F2B705", "#3B82C4", "#2E9E6C", "#B23A48", "#7C5CBF", "#4FA8A0", "#C97A2E", "#0B1F4D"]


# ============================================================
# CHARGEMENT DU LOGO
# ============================================================

def _logo_base64():
    """Charge le logo depuis assets/ et le convertit en base64."""
    candidates = [
        Path("assets/Logo-NSIA-Vie-Assurances.png"),
        Path("assets/logo-nsia-vie-assurances.png"),
        Path("assets/Logo-NSIA-Vie-Assurances.PNG"),
        Path("assets/logo.png"),
        Path("Logo-NSIA-Vie-Assurances.png"),
    ]
    for p in candidates:
        if p.exists():
            try:
                with open(p, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
            except Exception:
                continue
    return None


def _logo_html(height="48px"):
    """Retourne le HTML du logo ou un fallback texte."""
    b64 = _logo_base64()
    if b64:
        return (
            f'<img src="data:image/png;base64,{b64}" '
            f'style="height:{height};width:auto;" />'
        )
    return (
        f'<div style="font-weight:900;color:{NSIA_GOLD};font-size:1.4rem;'
        f'letter-spacing:0.05em;line-height:1;">NSIA'
        f'<div style="font-size:0.6rem;letter-spacing:0.3em;font-weight:600;'
        f'margin-top:3px;color:{NSIA_GOLD};">VIE</div></div>'
    )


# ============================================================
# CSS GLOBAL
# ============================================================

def inject_css():
    st.markdown(
        f"""
        <style>
        /* ============ FOND GLOBAL BLEU MARINE ============ */
        .stApp {{
            background: linear-gradient(160deg, #071530 0%, #0A1A3A 40%, #0B1F4D 100%) !important;
            color: {NSIA_TEXT};
        }}
        section.main {{
            background: transparent !important;
        }}
        .main .block-container {{
            background: transparent !important;
            padding-top: 0.5rem !important;
            padding-bottom: 1rem !important;
            max-width: 1700px;
        }}
        section.main > div {{
            padding-top: 0rem !important;
        }}
        #MainMenu, footer {{visibility: hidden;}}
        div[data-testid="stToolbar"] {{visibility: hidden;}}
        .stApp > header {{display: none !important;}}

        /* ============ SIDEBAR — FORCER L'AFFICHAGE ============ */
        section[data-testid="stSidebar"] {{
            display: block !important;
            visibility: visible !important;
            transform: none !important;
            margin-left: 0 !important;
            min-width: 280px !important;
            width: 280px !important;
            background: linear-gradient(180deg, #081736 0%, #050F26 100%) !important;
            border-right: 1px solid rgba(242,183,5,0.15) !important;
        }}
        section[data-testid="stSidebar"] * {{ color: #E7ECFB; }}
        section[data-testid="stSidebar"] .stButton>button {{
            width: 100%;
            text-align: left;
            background: transparent;
            border: none;
            color: #C9D2EE;
            font-weight: 600;
            font-size: 1.05rem;
            padding: 12px 16px;
            border-radius: 10px;
            margin-bottom: 3px;
        }}
        section[data-testid="stSidebar"] .stButton>button:hover {{
            background: rgba(242,183,5,0.12);
            color: {NSIA_GOLD};
        }}
        section[data-testid="stSidebar"] .stButton>button:focus {{
            box-shadow: none !important;
        }}

        /* Bouton pour réouvrir la sidebar si fermée */
        [data-testid="collapsedControl"] {{
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: fixed !important;
            left: 0.5rem !important;
            top: 0.5rem !important;
            z-index: 999999 !important;
            background: {NSIA_GOLD} !important;
            color: {NSIA_NAVY} !important;
            border-radius: 8px !important;
            padding: 8px 12px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4) !important;
        }}
        [data-testid="collapsedControl"]:hover {{
            background: {NSIA_GOLD_DARK} !important;
        }}
        [data-testid="collapsedControl"] svg {{
            fill: {NSIA_NAVY} !important;
            color: {NSIA_NAVY} !important;
        }}

        /* ============ EN-TÊTE ============ */
        .nsia-header {{
            background: linear-gradient(120deg, #081736 0%, #0B1F4D 100%);
            border-radius: 12px;
            padding: 14px 26px;
            margin-bottom: 12px;
            color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid rgba(242,183,5,0.25);
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}
        .nsia-header h1 {{
            font-size: 1.5rem;
            font-weight: 400;
            margin: 0;
            color: #E7ECFB;
        }}
        .nsia-header h1 span {{
            color: {NSIA_GOLD};
            font-weight: 800;
        }}
        .nsia-header .nsia-user {{
            text-align: right;
            font-size: 1rem;
            color: #C9D2EE;
        }}
        .nsia-header .nsia-user b {{ color: white; font-size: 1.1rem; }}

        /* ============ TITRES DE PAGE ============ */
        .nsia-page-title {{
            font-size: 2.2rem;
            font-weight: 800;
            color: #F4F7FB;
            margin-bottom: 6px;
            letter-spacing: -0.01em;
        }}
        .nsia-page-sub {{
            border-left: 5px solid {NSIA_GOLD};
            padding-left: 14px;
            color: {NSIA_MUTED};
            font-size: 1.05rem;
            line-height: 1.5;
            margin-bottom: 20px;
        }}

        /* ============ CARTES KPI ============ */
        .kpi-card {{
            background: linear-gradient(135deg, #132B5C 0%, #0F2557 100%);
            border-radius: 14px;
            padding: 20px 22px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.25);
            border: 1px solid {NSIA_BORDER};
            height: 100%;
            color: {NSIA_TEXT};
        }}
        .kpi-label {{
            font-size: 0.9rem;
            color: {NSIA_MUTED};
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        .kpi-value {{
            font-size: 2.1rem;
            font-weight: 800;
            color: {NSIA_GOLD};
            margin: 6px 0 6px 0;
            line-height: 1.1;
        }}
        .kpi-delta-up {{ color: #4ADE80; font-size: 0.95rem; font-weight: 700; }}
        .kpi-delta-down {{ color: #F87171; font-size: 0.95rem; font-weight: 700; }}
        .kpi-delta-flat {{ color: {NSIA_MUTED}; font-size: 0.95rem; font-weight: 700; }}

        /* ============ CARTES GÉNÉRIQUES ============ */
        div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="stVerticalBlock"] {{
            background: linear-gradient(135deg, #132B5C 0%, #0F2557 100%) !important;
            border-radius: 14px;
            padding: 8px 10px 16px 10px;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 14px !important;
            border: 1px solid {NSIA_BORDER} !important;
            box-shadow: 0 4px 16px rgba(0,0,0,0.2);
            margin-bottom: 14px;
            background: transparent !important;
        }}
        .card-title {{
            color: {NSIA_GOLD};
            font-size: 1.2rem;
            font-weight: 800;
            margin-top: 6px;
            margin-bottom: 10px;
            letter-spacing: -0.01em;
        }}
        .nsia-card {{
            background: linear-gradient(135deg, #132B5C 0%, #0F2557 100%);
            border-radius: 14px;
            padding: 20px 24px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.2);
            border: 1px solid {NSIA_BORDER};
            margin-bottom: 14px;
            color: {NSIA_TEXT};
        }}
        .nsia-card h4 {{
            color: {NSIA_GOLD};
            font-size: 1.2rem;
            margin-top: 0;
            margin-bottom: 12px;
        }}

        /* ============ ENCADRÉ INSIGHT ============ */
        .nsia-insight {{
            background: linear-gradient(135deg, rgba(242,183,5,0.15) 0%, rgba(242,183,5,0.05) 100%);
            border: 1px solid {NSIA_GOLD}66;
            border-left: 5px solid {NSIA_GOLD};
            border-radius: 12px;
            padding: 16px 20px;
            color: #FFE9A8;
            font-size: 1.05rem;
            line-height: 1.6;
        }}
        .nsia-insight b {{ color: {NSIA_GOLD}; }}

        /* ============ BADGES ============ */
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 700;
        }}
        .badge-critique {{ background:rgba(220,38,38,0.25); color:#FCA5A5; }}
        .badge-eleve {{ background:rgba(220,38,38,0.25); color:#FCA5A5; }}
        .badge-moyen {{ background:rgba(242,183,5,0.25); color:#FCD34D; }}
        .badge-faible {{ background:rgba(16,185,129,0.25); color:#6EE7B7; }}
        .badge-vert {{ background:rgba(16,185,129,0.25); color:#6EE7B7; }}
        .badge-orange {{ background:rgba(242,183,5,0.25); color:#FCD34D; }}
        .badge-rouge {{ background:rgba(220,38,38,0.25); color:#FCA5A5; }}
        .badge-neutre {{ background:rgba(255,255,255,0.12); color:#E7ECFB; }}

        /* ============ BOUTONS GLOBAUX ============ */
        div.stButton > button[kind="primary"] {{
            background-color: {NSIA_GOLD} !important;
            color: {NSIA_NAVY} !important;
            border: none !important;
            font-weight: 800 !important;
            font-size: 1.05rem;
        }}
        div.stButton > button[kind="primary"] * {{
            color: {NSIA_NAVY} !important;
            font-weight: 800 !important;
        }}
        .stButton>button {{
            border-radius: 10px;
            font-weight: 700;
            font-size: 1rem;
        }}

        /* ============ SÉPARATEUR ============ */
        hr {{ margin: 0.8rem 0; border-color: {NSIA_BORDER}; }}

        /* ============ ST.METRIC ============ */
        div[data-testid="stMetric"] {{
            background: linear-gradient(135deg, #132B5C 0%, #0F2557 100%);
            padding: 18px 20px;
            border-radius: 12px;
            border: 1px solid {NSIA_BORDER};
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] label p {{
            font-size: 0.95rem !important;
            font-weight: 700 !important;
            color: {NSIA_MUTED} !important;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}
        div[data-testid="stMetricValue"] {{
            font-size: 2rem !important;
            font-weight: 800 !important;
            color: {NSIA_GOLD} !important;
        }}
        div[data-testid="stMetricDelta"] {{
            color: #4ADE80 !important;
        }}

        /* ============ DATAFRAME (dark) ============ */
        div[data-testid="stDataFrame"] {{
            background: #0F2557 !important;
            border-radius: 12px !important;
            border: 1px solid {NSIA_BORDER} !important;
            padding: 8px !important;
        }}
        div[data-testid="stDataFrame"] * {{
            color: {NSIA_TEXT} !important;
            font-size: 1rem !important;
        }}
        div[data-testid="stDataFrame"] thead tr th {{
            background: #0B1F4D !important;
            color: {NSIA_GOLD} !important;
            font-weight: 800 !important;
            font-size: 1rem !important;
            border-bottom: 1px solid {NSIA_BORDER} !important;
            padding: 12px 14px !important;
        }}
        div[data-testid="stDataFrame"] tbody tr {{
            background: #0F2557 !important;
            border-bottom: 1px solid {NSIA_BORDER} !important;
        }}
        div[data-testid="stDataFrame"] tbody tr:hover {{
            background: {NSIA_CARD_HOVER} !important;
        }}
        div[data-testid="stDataFrame"] tbody td {{
            color: {NSIA_TEXT} !important;
            font-size: 1rem !important;
            border-bottom: 1px solid {NSIA_BORDER} !important;
            padding: 10px 14px !important;
        }}

        /* ============ EXPANDEUR PILOTAGE ============ */
        details[data-testid="stExpander"] {{
            background: linear-gradient(135deg, #0B1F4D 0%, #081736 100%) !important;
            border-radius: 14px !important;
            border: 1px solid {NSIA_BORDER} !important;
            margin-top: 16px !important;
            margin-bottom: 16px !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3) !important;
            overflow: hidden !important;
        }}
        details[data-testid="stExpander"] summary {{
            padding: 22px 28px !important;
            cursor: pointer !important;
            list-style: none !important;
            background: transparent !important;
            border: none !important;
            display: flex !important;
            align-items: center !important;
            gap: 14px !important;
        }}
        details[data-testid="stExpander"] summary:hover {{
            background: rgba(242,183,5,0.08) !important;
        }}
        details[data-testid="stExpander"] summary::-webkit-details-marker {{
            display: none !important;
        }}
        details[data-testid="stExpander"] summary p {{
            color: {NSIA_GOLD} !important;
            font-weight: 800 !important;
            font-size: 1.4rem !important;
            letter-spacing: 0.02em !important;
            margin: 0 !important;
            line-height: 1.3 !important;
        }}
        details[data-testid="stExpander"] summary svg {{
            fill: {NSIA_GOLD} !important;
            color: {NSIA_GOLD} !important;
            width: 24px !important;
            height: 24px !important;
        }}
        details[data-testid="stExpander"] > div {{
            background: #0A1A3A !important;
            padding: 26px !important;
            border-radius: 0 0 14px 14px !important;
        }}
        details[data-testid="stExpander"][open] summary {{
            border-bottom: 2px solid {NSIA_GOLD} !important;
        }}

        details[data-testid="stExpander"] label,
        details[data-testid="stExpander"] .stMarkdown,
        details[data-testid="stExpander"] .stCaption,
        details[data-testid="stExpander"] p,
        details[data-testid="stExpander"] span {{
            font-size: 1.1rem !important;
            line-height: 1.6 !important;
            color: {NSIA_TEXT} !important;
        }}

        /* ============ WIDGETS FILTRES — FOND BLANC, TEXTE NOIR ============ */
        div[data-baseweb="select"] > div {{
            background-color: #FFFFFF !important;
            border-color: #1E3A6B !important;
        }}
        div[data-baseweb="select"] * {{
            color: #0B1F4D !important;
            font-weight: 600 !important;
        }}
        div[data-baseweb="select"] svg {{
            fill: #0B1F4D !important;
        }}
        div[data-baseweb="input"] > div {{
            background-color: #FFFFFF !important;
            border-color: #1E3A6B !important;
        }}
        div[data-baseweb="input"] input {{
            color: #0B1F4D !important;
            font-weight: 600 !important;
        }}
        div[data-testid="stDateInput"] input {{
            color: #0B1F4D !important;
            font-weight: 600 !important;
        }}
        div[data-baseweb="popover"],
        div[data-baseweb="popover"] * {{
            background-color: #FFFFFF !important;
            color: #0B1F4D !important;
        }}
        li[role="option"] {{
            color: #0B1F4D !important;
        }}
        li[role="option"]:hover {{
            background-color: rgba(242,183,5,0.2) !important;
        }}

        /* ============ TITRES MARKDOWN (##, ###) EN BLANC ============ */
        h1, h2, h3, h4, h5, h6 {{
            color: #F4F7FB !important;
        }}
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
        .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {{
            color: #F4F7FB !important;
        }}
        .stMarkdown strong, .stMarkdown b {{
            color: #F4F7FB !important;
        }}
        .stMarkdown p, .stMarkdown span, .stMarkdown li {{
            color: #F4F7FB !important;
        }}
        .stMarkdown a {{
            color: #F2B705 !important;
        }}
        label[data-testid="stWidgetLabel"] p {{
            color: #F4F7FB !important;
        }}
        div[data-testid="stCaptionContainer"] p {{
            color: #A9BDD1 !important;
        }}

        /* ============ ALERTES STREAMLIT (warning, info) ============ */
        div[data-testid="stAlert"] {{
            background-color: #132B5C !important;
            color: #F4F7FB !important;
            border: 1px solid #1E3A6B !important;
        }}
        div[data-testid="stAlert"] * {{
            color: #F4F7FB !important;
        }}
        div[data-testid="stAlert"] svg {{
            fill: #F2B705 !important;
        }}

        /* ============ BOUTONS SECONDAIRES (étapes non actives) ============ */
        div.stButton > button[kind="secondary"] {{
            background-color: #132B5C !important;
            color: #F4F7FB !important;
            border: 1px solid #1E3A6B !important;
        }}
        div.stButton > button[kind="secondary"]:hover {{
            background-color: #1A3671 !important;
            border-color: #F2B705 !important;
        }}
        div.stButton > button[kind="secondary"] * {{
            color: #F4F7FB !important;
        }}

        /* ============ BOUTONS RADIO ============ */
        div[role="radiogroup"] label {{
            color: #F4F7FB !important;
        }}
        div[role="radiogroup"] label p {{
            color: #F4F7FB !important;
        }}

        /* ============ GRAPHIQUES PLOTLY (fond transparent) ============ */
        .js-plotly-plot {{
            background: transparent !important;
        }}
        .js-plotly-plot .plotly .main-svg {{
            background: transparent !important;
        }}
        .js-plotly-plot .plotly .bg {{
            fill: transparent !important;
        }}

        /* ============ TABS ============ */
        div[data-baseweb="tab-list"] {{
            background: transparent !important;
            gap: 4px;
        }}
        button[data-baseweb="tab"] {{
            background: rgba(255,255,255,0.05) !important;
            color: #F4F7FB !important;
            border-radius: 10px 10px 0 0 !important;
            font-weight: 700 !important;
            font-size: 1rem !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            background: #F2B705 !important;
            color: #0B1F4D !important;
        }}
        button[data-baseweb="tab"] p {{
            color: inherit !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# HEADER
# ============================================================

def render_header(user_name="Kabs Mohamed", role="Manager", notif=3):
    logo = _logo_html(height="52px")
    html = (
        f'<div class="nsia-header">'
        f'<div style="display:flex;align-items:center;gap:18px;">'
        f'{logo}'
        f'<div style="border-left:2px solid {NSIA_GOLD};padding-left:18px;">'
        f'<h1>Protéger aujourd\'hui, <span>préparer demain</span></h1>'
        f'</div>'
        f'</div>'
        f'<div class="nsia-user">'
        f'🔔 {notif} &nbsp;&nbsp; <b>{user_name}</b><br/>{role}'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ============================================================
# COMPOSANTS
# ============================================================

@contextmanager
def card(title: str = None, subtitle: str = None):
    with st.container(border=True):
        if title:
            st.markdown(f'<div class="card-title">{title}</div>', unsafe_allow_html=True)
        if subtitle:
            st.caption(subtitle)
        yield


def page_title(icon: str, title: str, subtitle: str):
    st.markdown(f'<div class="nsia-page-title">{icon} {title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="nsia-page-sub">{subtitle}</div>', unsafe_allow_html=True)


def insight_box(html_text: str):
    st.markdown(f'<div class="nsia-insight">💡 {html_text}</div>', unsafe_allow_html=True)


def badge(text: str, level: str = "neutre"):
    level = (level or "neutre").lower()
    mapping = {
        "élevé": "eleve", "eleve": "eleve", "critique": "critique", "high": "eleve",
        "moyen": "moyen", "medium": "moyen",
        "faible": "faible", "low": "faible",
        "vert": "vert", "orange": "orange", "rouge": "rouge",
    }
    cls = mapping.get(level, "neutre")
    return f'<span class="badge badge-{cls}">{text}</span>'


# ================================================================
# FONCTIONS V2 — Vue d'ensemble
# ================================================================

def health_banner(level: str, score: float, cause: str, impact: str, action: str):
    colors = {
        "vert":   ("#10B981", "rgba(16,185,129,0.15)", "#A7F3D0"),
        "orange": ("#F59E0B", "rgba(245,158,11,0.15)", "#FDE68A"),
        "rouge":  ("#DC2626", "rgba(220,38,38,0.15)", "#FCA5A5"),
    }
    bg, light, text = colors.get(level, colors["orange"])
    icon = {"vert": "🟢", "orange": "🟠", "rouge": "🔴"}.get(level, "🟠")
    label = {"vert": "SATISFAISANT", "orange": "À SURVEILLER", "rouge": "CRITIQUE"}.get(level, "À SURVEILLER")

    html = (
        f'<div style="background:linear-gradient(135deg,{light} 0%,rgba(0,0,0,0) 100%);'
        f'border-radius:16px;padding:26px 32px;margin-bottom:22px;'
        f'box-shadow:0 4px 16px rgba(0,0,0,0.25);border-left:8px solid {bg};'
        f'border:1px solid {bg}55;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">'
        f'<div style="font-size:1.45rem;font-weight:800;color:{text};letter-spacing:0.02em;">'
        f'{icon} SANTÉ DU PARCOURS CLIENT : {label}</div>'
        f'<div style="background:rgba(0,0,0,0.3);border-radius:30px;padding:8px 20px;'
        f'font-weight:800;color:{text};font-size:1.15rem;">Score : {score:.0f} / 100</div>'
        f'</div>'
        f'<div style="color:{text};font-size:1.1rem;line-height:1.8;">'
        f'<div><b>Cause n°1 :</b> {cause}</div>'
        f'<div><b>Impact estimé :</b> {impact}</div>'
        f'<div><b>Action prioritaire :</b> {action}</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def alert_card(severity: str, category: str, title: str, metric: str, owner: str):
    colors = {
        "rouge":  ("#DC2626", "rgba(220,38,38,0.15)"),
        "orange": ("#F59E0B", "rgba(245,158,11,0.15)"),
        "jaune":  ("#EAB308", "rgba(234,179,8,0.15)"),
    }
    main, light = colors.get(severity, colors["orange"])

    html = (
        f'<div style="background:linear-gradient(135deg, #132B5C 0%, #0F2557 100%);'
        f'border-radius:14px;padding:22px 24px;'
        f'border:1px solid {main}55;border-top:5px solid {main};'
        f'box-shadow:0 4px 16px rgba(0,0,0,0.25);min-height:220px;">'
        f'<div style="font-size:0.9rem;font-weight:800;color:{main};'
        f'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px;">{category}</div>'
        f'<div style="font-size:1.3rem;font-weight:800;color:#F4F7FB;margin-bottom:12px;'
        f'line-height:1.3;min-height:2.6em;">{title}</div>'
        f'<div style="background:{light};border-radius:8px;padding:12px 14px;'
        f'font-weight:700;color:{main};font-size:1.1rem;margin-bottom:14px;">{metric}</div>'
        f'<div style="font-size:1rem;color:{NSIA_MUTED};">'
        f'→ Responsable : <b style="color:{NSIA_GOLD};">{owner}</b></div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def kpi_card_v2(label: str, value: str, delta_pct: float = None, invert: bool = False):
    if delta_pct is None:
        delta_html = '<div style="height:24px;"></div>'
    else:
        is_positive = delta_pct >= 0
        good = (is_positive and not invert) or (not is_positive and invert)
        color = "#4ADE80" if good else "#F87171"
        arrow = "▲" if is_positive else "▼"
        delta_html = (
            f'<div style="color:{color};font-size:1rem;font-weight:700;">'
            f'{arrow} {delta_pct:+.1f} % vs préc.</div>'
        )

    html = (
        f'<div style="background:linear-gradient(135deg, #132B5C 0%, #0F2557 100%);'
        f'border-radius:14px;padding:22px 24px;'
        f'border:1px solid {NSIA_BORDER};box-shadow:0 4px 16px rgba(0,0,0,0.25);'
        f'min-height:140px;">'
        f'<div style="font-size:0.92rem;color:{NSIA_MUTED};font-weight:700;'
        f'text-transform:uppercase;letter-spacing:0.04em;">{label}</div>'
        f'<div style="font-size:2.1rem;font-weight:800;color:{NSIA_GOLD};'
        f'margin:8px 0 6px 0;line-height:1.1;">{value}</div>'
        f'{delta_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ================================================================
# FONCTIONS PILOTAGE V2
# ================================================================

def pilotage_header():
    now = "14 octobre 2026 · 10:24"
    logo = _logo_html(height="56px")
    html = (
        '<div style="background:linear-gradient(135deg,#081736 0%,#0B1F4D 100%);'
        'border-radius:16px 16px 0 0;padding:28px 32px;margin-bottom:0;'
        'display:flex;justify-content:space-between;align-items:center;'
        'border:1px solid rgba(242,183,5,0.25);border-bottom:none;'
        'box-shadow:0 4px 20px rgba(0,0,0,0.3);">'
        '<div style="display:flex;align-items:center;gap:24px;">'
        f'{logo}'
        '<div style="border-left:3px solid #F2B705;padding-left:24px;">'
        '<div style="font-size:2rem;font-weight:800;color:white;'
        'letter-spacing:-0.02em;line-height:1.1;">Pilotage &amp; actions managériales</div>'
        '<div style="color:#B8C4E0;font-size:1.05rem;margin-top:10px;line-height:1.6;">'
        'Fusion des indicateurs de performance et du plan d\'actions issu de la feuille <b>Pilotage</b>.<br>'
        'Le champ <i>Échéance</i> n\'existant pas dans le fichier source, une échéance indicative est calculée.'
        '</div></div></div>'
        '<div style="text-align:right;color:#B8C4E0;font-size:1rem;">'
        '<div style="display:flex;align-items:center;gap:10px;justify-content:flex-end;">'
        '<span style="font-size:1.4rem;">📅</span>'
        '<div><div style="font-weight:700;color:white;font-size:1.05rem;">Dernière mise à jour</div>'
        f'<div style="font-size:1rem;">{now}</div></div></div></div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def pilotage_kpi_cards(kpis: list):
    cols = st.columns(4)
    for col, k in zip(cols, kpis):
        with col:
            html = (
                f'<div style="background:linear-gradient(135deg,#132B5C 0%,#0F2557 100%);'
                f'border-radius:14px;padding:22px 24px;border:1px solid {NSIA_BORDER};'
                f'border-left:5px solid {k.get("border_color","#3B82C4")};'
                f'box-shadow:0 4px 16px rgba(0,0,0,0.25);min-height:130px;">'
                f'<div style="display:flex;align-items:center;gap:16px;">'
                f'<div style="background:{k.get("icon_bg","#3B82C4")};border-radius:50%;'
                f'width:56px;height:56px;display:flex;align-items:center;justify-content:center;'
                f'font-size:1.7rem;flex-shrink:0;">{k.get("icon","📊")}</div>'
                f'<div style="flex:1;">'
                f'<div style="color:{NSIA_MUTED};font-size:0.88rem;font-weight:700;'
                f'text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;">'
                f'{k.get("label","")}</div>'
                f'<div style="color:{NSIA_GOLD};font-size:2rem;font-weight:800;'
                f'line-height:1;margin-bottom:8px;">{k.get("value","0")}</div>'
                f'<div style="color:{k.get("delta_color","#4ADE80")};font-size:0.92rem;'
                f'font-weight:700;">{k.get("delta","")}</div>'
                f'</div></div></div>'
            )
            st.markdown(html, unsafe_allow_html=True)


def pilotage_filters_header():
    html = (
        '<div style="background:linear-gradient(135deg,#132B5C 0%,#0F2557 100%);'
        'border-radius:14px;padding:16px 24px;margin:18px 0 12px 0;'
        f'border:1px solid {NSIA_BORDER};display:flex;align-items:center;gap:14px;">'
        '<span style="font-size:1.5rem;">🔽</span>'
        f'<span style="color:{NSIA_GOLD};font-weight:800;font-size:1.3rem;letter-spacing:0.02em;">Filtres</span>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def pilotage_table_header(nb_actions: int):
    html = (
        '<div style="background:linear-gradient(135deg,#0B1F4D 0%,#081736 100%);'
        'border-radius:14px 14px 0 0;padding:22px 28px;margin-top:18px;'
        f'border:1px solid {NSIA_BORDER};border-bottom:none;'
        'display:flex;justify-content:space-between;align-items:center;">'
        f'<div><div style="color:{NSIA_GOLD};font-weight:800;font-size:1.4rem;">'
        '📋 Liste des actions managériales</div>'
        f'<div style="color:{NSIA_MUTED};font-size:1rem;margin-top:6px;">'
        'Suivez l\'avancement des actions, identifiez les risques et pilotez efficacement la performance.'
        '</div></div>'
        f'<div style="background:{NSIA_GOLD};color:{NSIA_NAVY};font-weight:800;'
        f'padding:10px 20px;border-radius:20px;font-size:1.05rem;">'
        f'{nb_actions} actions au total</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)