"""
app.py
------
Point d'entrée de l'application NSIA Vie Assurances CI — Cockpit de pilotage
du parcours client.
"""

import streamlit as st

from components.style import inject_css, render_header
from components.filters import render_filter_bar
from utils.data_loader import load_all_data, get_filter_options

from views import (
    vue_ensemble,
    parcours_client,
    arbre_decisions,
    frictions_blocages,
    reclamations_incidents,
    agences_canaux,
    produits,
    guide,
)

st.set_page_config(
    page_title="NSIA Vie Assurances — Pilotage Parcours Client",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

NAV_ITEMS = [
    ("vue_ensemble", "🏠", "Vue d'ensemble"),
    ("parcours_client", "👥", "Parcours Client"),
    ("arbre_decisions", "🔀", "Arbre des décisions"),
    ("frictions_blocages", "⚠️", "Frictions & Blocages"),
    ("reclamations_incidents", "💬", "Réclamations & Incidents"),
    ("agences_canaux", "🏢", "Agences & Canaux"),
    ("produits", "📦", "Produits"),
    ("guide", "📖", "Guide d'utilisation"),
]

VIEW_MODULES = {
    "vue_ensemble": vue_ensemble,
    "parcours_client": parcours_client,
    "arbre_decisions": arbre_decisions,
    "frictions_blocages": frictions_blocages,
    "reclamations_incidents": reclamations_incidents,
    "agences_canaux": agences_canaux,
    "produits": produits,
    "guide": guide,
}

if "current_view" not in st.session_state:
    st.session_state["current_view"] = "vue_ensemble"

# ---------------- Chargement des données ----------------
try:
    data = load_all_data()
except FileNotFoundError:
    st.error(
        "❌ Fichier de données introuvable. Vérifiez que le fichier "
        "`NSIA_Vie_CI_Cartographie_Parcours_Client_Pilotage.xlsx` est bien présent dans le dossier `data/`."
    )
    st.stop()
except Exception as e:
    st.error(f"❌ Une erreur est survenue lors du chargement des données : {e}")
    st.stop()

filter_options = get_filter_options(data)

# ---------------- Sidebar : navigation ----------------
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center;padding:10px 0 18px 0;">
            <div style="font-size:1.6rem;font-weight:800;color:#F2B705;letter-spacing:0.05em;">NSIA</div>
            <div style="font-size:0.7rem;color:#C9D2EE;letter-spacing:0.15em;">VIE ASSURANCES</div>
        </div>
        <hr style="border-color:rgba(255,255,255,0.15);">
        """,
        unsafe_allow_html=True,
    )
    for key, icon, label in NAV_ITEMS:
        active = st.session_state["current_view"] == key
        if st.button(
            f"{icon}  {label}",
            key=f"nav_{key}",
            use_container_width=True,
            type="primary" if active else "secondary",
        ):
            st.session_state["current_view"] = key
            st.rerun()

    st.markdown(
        """
        <div style="position:relative;margin-top:40px;padding:14px;background:rgba(242,183,5,0.08);
        border-radius:12px;font-size:0.78rem;color:#C9D2EE;">
        Ensemble<br/><b style="color:#F2B705;">pour votre avenir</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------- En-tête ----------------
render_header()

# ---------------- Page Guide (pas de filtres) ----------------
current = st.session_state["current_view"]

if current == "guide":
    guide.render()
else:
    # ---------------- Barre de filtres globale ----------------
    filters = render_filter_bar(filter_options, key_prefix="global")
    # ---------------- Rendu du module sélectionné ----------------
    VIEW_MODULES[current].render(data, filters)