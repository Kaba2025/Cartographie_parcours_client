"""views/agences_canaux.py - Performance stratégique des agences et canaux."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.style import (
    page_title, insight_box, badge, card,
    CHART_COLORS, NSIA_NAVY, NSIA_GOLD,
)
from utils.calculations import (
    apply_filters, pct, safe_mean, indice_satisfaction,
    taux_friction, taux_conversion, apply_dark_theme,
)


# ============================================================
# RÉFÉRENTIELS
# ============================================================

PHASES = {
    "AVANT-VENTE": {
        "label": "Avant-vente",
        "emoji": "🔵",
        "couleur": "#3B82C4",
        "etapes": ["Découverte", "Information / conseil", "Simulation"],
    },
    "VENTE": {
        "label": "Vente",
        "emoji": "🟠",
        "couleur": "#F2B705",
        "etapes": ["Souscription", "Validation du contrat", "Paiement / cotisation"],
    },
    "APRÈS-VENTE": {
        "label": "Après-vente",
        "emoji": "🟢",
        "couleur": "#2E9E6C",
        "etapes": [
            "Suivi du contrat", "Sinistre", "Réclamation",
            "Avance / rachat", "Demande de service",
            "Suspension", "Résiliation", "Terme", "Renouvellement",
        ],
    },
}

VILLE_COORDS = {
    "Abidjan": (5.3600, -4.0083), "Yamoussoukro": (6.8276, -5.2893),
    "Bouaké": (7.6900, -5.0300), "Korhogo": (9.4580, -5.6296),
    "Daloa": (6.8770, -6.4502), "San Pedro": (4.7485, -6.6363),
    "Man": (7.4125, -7.5539), "Abengourou": (6.7297, -3.4964),
}


# ============================================================
# HELPERS PHASES
# ============================================================

def _level_from_friction(taux_fric):
    if taux_fric >= 30:
        return "rouge"
    if taux_fric >= 15:
        return "orange"
    return "vert"


def _compute_phase_sante(parcours_df, phase_key):
    """Calcule la santé d'une phase : nb clients, canaux, friction."""
    phase = PHASES[phase_key]
    sub = parcours_df[parcours_df["etape_parcours"].isin(phase["etapes"])]
    if sub.empty:
        return {"nb_clients": 0, "nb_canaux": 0, "nb_agences": 0,
                "taux_friction": 0.0, "level": "vert", "has_data": False}
    nb_clients = sub["client_id"].nunique()
    nb_canaux = sub["canal"].nunique() if "canal" in sub.columns else 0
    nb_agences = sub["agence"].nunique() if "agence" in sub.columns else 0
    taux_fric = pct((sub["friction"] == "Oui").sum(), len(sub)) \
        if "friction" in sub.columns else 0
    return {
        "nb_clients": nb_clients,
        "nb_canaux": nb_canaux,
        "nb_agences": nb_agences,
        "taux_friction": taux_fric,
        "level": _level_from_friction(taux_fric),
        "has_data": True,
    }


def _render_phase_selector(parcours_f, session_key):
    """3 cartes phases — fond plein coloré selon niveau."""
    st.markdown(
        '<div style="font-size:1.15rem;font-weight:800;color:#F4F7FB;'
        'margin:8px 0 14px 0;letter-spacing:-0.01em;">🎯 Piloter par phase du parcours</div>',
        unsafe_allow_html=True,
    )

    if session_key not in st.session_state:
        st.session_state[session_key] = None
    current_phase = st.session_state[session_key]

    level_styles = {
        "vert":   {"bg": "#10B981", "border": "#047857", "icon": "🟢", "label": "SAIN"},
        "orange": {"bg": "#F59E0B", "border": "#B45309", "icon": "🟠", "label": "À SURVEILLER"},
        "rouge":  {"bg": "#DC2626", "border": "#7F1D1D", "icon": "🔴", "label": "CRITIQUE"},
    }

    cols_data = []
    for key, phase in PHASES.items():
        sante = _compute_phase_sante(parcours_f, key)
        cols_data.append((key, phase, sante, level_styles[sante["level"]]))

    html = '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:14px;">'
    for key, phase, sante, style in cols_data:
        is_active = current_phase == key
        border_width = "5px" if is_active else "3px"
        html += (
            f'<div style="background:{style["bg"]};border-radius:14px;'
            f'padding:20px 22px;border:{border_width} solid {style["border"]};'
            f'box-shadow:0 6px 20px rgba(0,0,0,0.35);">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">'
            f'<div style="font-size:1.25rem;font-weight:800;color:#FFFFFF;'
            f'text-shadow:0 1px 3px rgba(0,0,0,0.3);">'
            f'{phase["emoji"]} {phase["label"]}</div>'
            f'<div style="background:rgba(0,0,0,0.3);color:#FFFFFF;'
            f'border-radius:20px;padding:5px 14px;font-weight:800;font-size:0.85rem;">'
            f'{style["icon"]} {style["label"]}</div>'
            f'</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">'
            f'<div><div style="color:rgba(255,255,255,0.9);font-size:0.72rem;'
            f'font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">Clients</div>'
            f'<div style="color:#FFFFFF;font-size:1.7rem;font-weight:800;'
            f'line-height:1.1;margin-top:3px;text-shadow:0 2px 4px rgba(0,0,0,0.25);">'
            f'{sante["nb_clients"]:,}</div></div>'.replace(",", " ") +
            f'<div><div style="color:rgba(255,255,255,0.9);font-size:0.72rem;'
            f'font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">Friction</div>'
            f'<div style="color:#FFFFFF;font-size:1.7rem;font-weight:800;'
            f'line-height:1.1;margin-top:3px;text-shadow:0 2px 4px rgba(0,0,0,0.25);">'
            f'{sante["taux_friction"]:.0f} %</div></div>'
            f'<div><div style="color:rgba(255,255,255,0.9);font-size:0.72rem;'
            f'font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">Canaux</div>'
            f'<div style="color:#FFFFFF;font-size:1.2rem;font-weight:800;'
            f'line-height:1.1;margin-top:3px;text-shadow:0 2px 4px rgba(0,0,0,0.25);">'
            f'{sante["nb_canaux"]}</div></div>'
            f'<div><div style="color:rgba(255,255,255,0.9);font-size:0.72rem;'
            f'font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">Agences</div>'
            f'<div style="color:#FFFFFF;font-size:1.2rem;font-weight:800;'
            f'line-height:1.1;margin-top:3px;text-shadow:0 2px 4px rgba(0,0,0,0.25);">'
            f'{sante["nb_agences"]}</div></div>'
            f'</div></div>'
        )
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    cols = st.columns(3)
    for col, (key, phase, sante, style) in zip(cols, cols_data):
        is_active = current_phase == key
        with col:
            if is_active:
                if st.button("✅ Phase active — Vue globale",
                             key=f"{session_key}_reset_{key}",
                             use_container_width=True, type="primary"):
                    st.session_state[session_key] = None
                    st.rerun()
            else:
                if st.button("🔍 Voir cette phase",
                             key=f"{session_key}_btn_{key}",
                             use_container_width=True):
                    st.session_state[session_key] = key
                    st.rerun()


def _bandeau_phase_active(parcours_f, phase_key):
    phase = PHASES[phase_key]
    sante = _compute_phase_sante(parcours_f, phase_key)

    level_styles = {
        "vert":   ("#10B981", "rgba(16,185,129,0.15)", "🟢", "SAIN"),
        "orange": ("#F2B705", "rgba(242,183,5,0.15)", "🟠", "À SURVEILLER"),
        "rouge":  ("#DC2626", "rgba(220,38,38,0.15)", "🔴", "CRITIQUE"),
    }
    main_color, light_color, icon, label = level_styles[sante["level"]]

    sub = parcours_f[parcours_f["etape_parcours"].isin(phase["etapes"])]

    top_agence = "—"
    if not sub.empty and "agence" in sub.columns:
        top_a = sub.groupby("agence")["client_id"].nunique().sort_values(ascending=False)
        if not top_a.empty:
            top_agence = f"{top_a.index[0]} ({top_a.iloc[0]} clients)"

    top_canal = "—"
    if not sub.empty:
        top_c = sub["canal"].value_counts()
        if not top_c.empty:
            top_canal = f"{top_c.index[0]} ({top_c.iloc[0]} interactions)"

    html = (
        f'<div style="background:linear-gradient(135deg,{light_color} 0%,rgba(0,0,0,0) 100%);'
        f'border-radius:16px;padding:20px 26px;margin:16px 0;'
        f'border-left:8px solid {main_color};border:1px solid {main_color}55;'
        f'box-shadow:0 4px 16px rgba(0,0,0,0.25);">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
        f'<div style="font-size:1.3rem;font-weight:800;color:#F4F7FB;">'
        f'{phase["emoji"]} PHASE {phase["label"].upper()} — {sante["nb_clients"]} clients · '
        f'{sante["nb_agences"]} agences · {sante["nb_canaux"]} canaux</div>'
        f'<div style="background:{main_color}33;color:{main_color};'
        f'border-radius:30px;padding:8px 20px;font-weight:800;font-size:1rem;">'
        f'{icon} {label} · Friction {sante["taux_friction"]:.0f} %</div>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;'
        f'color:#F4F7FB;font-size:1rem;line-height:1.6;">'
        f'<div><b>🏆 Top agence :</b><br/>{top_agence}</div>'
        f'<div><b>📞 Top canal :</b><br/>{top_canal}</div>'
        f'</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)

    if sante["level"] == "rouge":
        st.markdown(
            f'<div style="background:rgba(220,38,38,0.2);'
            f'border-left:5px solid #DC2626;border-radius:10px;'
            f'padding:14px 20px;margin-bottom:18px;color:#FCA5A5;'
            f'font-size:1rem;line-height:1.6;">'
            f'<b>🔴 ALERTE CRITIQUE sur la phase {phase["label"]} :</b> '
            f'taux de friction {sante["taux_friction"]:.0f} % (> 30 %). '
            f'Audit du réseau recommandé. Top agence à risque : <b>{top_agence}</b>.'
            f'</div>',
            unsafe_allow_html=True,
        )


# ============================================================
# HELPERS KPI / ACTIONS
# ============================================================

def _kpi_card(label, value, subtext="", color="#F2B705", icon=""):
    return (
        f'<div style="background:linear-gradient(135deg,#132B5C 0%,#0F2557 100%);'
        f'border-radius:12px;padding:16px 18px;'
        f'border:1px solid #1E3A6B;box-shadow:0 4px 12px rgba(0,0,0,0.2);'
        f'min-height:115px;">'
        f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">'
        f'<span style="font-size:1rem;">{icon}</span>'
        f'<span style="font-size:0.72rem;color:#A9BDD1;font-weight:700;'
        f'text-transform:uppercase;letter-spacing:0.03em;">{label}</span></div>'
        f'<div style="font-size:1.7rem;font-weight:800;color:{color};'
        f'line-height:1.1;">{value}</div>'
        f'<div style="font-size:0.72rem;color:#9CA3AF;margin-top:6px;">{subtext}</div>'
        f'</div>'
    )


def _action_card(rank, severity, title, metric, owner, action):
    colors = {
        "rouge": ("#DC2626", "rgba(220,38,38,0.15)"),
        "orange": ("#F2B705", "rgba(242,183,5,0.15)"),
        "jaune":  ("#EAB308", "rgba(234,179,8,0.15)"),
    }
    main, light = colors.get(severity, colors["orange"])
    return (
        f'<div style="background:linear-gradient(135deg,#132B5C 0%,#0F2557 100%);'
        f'border-radius:12px;padding:16px 18px;'
        f'border:1px solid #1E3A6B;border-left:5px solid {main};'
        f'box-shadow:0 4px 12px rgba(0,0,0,0.2);min-height:180px;">'
        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">'
        f'<div style="background:{main};color:white;border-radius:50%;'
        f'width:26px;height:26px;display:flex;align-items:center;justify-content:center;'
        f'font-weight:800;font-size:0.85rem;">{rank}</div>'
        f'<div style="font-size:0.95rem;font-weight:800;color:#F4F7FB;">{title}</div>'
        f'</div>'
        f'<div style="background:{light};border-radius:6px;padding:8px 12px;'
        f'font-weight:700;color:{main};font-size:0.85rem;margin-bottom:10px;">{metric}</div>'
        f'<div style="font-size:0.78rem;color:#A9BDD1;margin-bottom:8px;">'
        f'👤 <b style="color:#F2B705;">{owner}</b></div>'
        f'<div style="font-size:0.75rem;color:#A9BDD1;background:rgba(0,0,0,0.2);'
        f'border-radius:6px;padding:8px;line-height:1.4;">'
        f'💡 {action}</div>'
        f'</div>'
    )


def _bandeau_sante(parcours_f, reclamations_f, contrats_f):
    nb_agences = parcours_f["agence"].nunique() if "agence" in parcours_f.columns else 0
    nb_canaux = parcours_f["canal"].nunique() if not parcours_f.empty else 0
    taux_fric = taux_friction(parcours_f) if not parcours_f.empty else 0

    score_sante = max(0, min(100, 100 - (taux_fric * 1.5)))

    if score_sante >= 75:
        level_color, level_label, level_icon = "#10B981", "SATISFAISANT", "🟢"
        bg_grad = "linear-gradient(135deg,rgba(16,185,129,0.2) 0%,rgba(0,0,0,0) 100%)"
    elif score_sante >= 50:
        level_color, level_label, level_icon = "#F2B705", "À SURVEILLER", "🟠"
        bg_grad = "linear-gradient(135deg,rgba(242,183,5,0.2) 0%,rgba(0,0,0,0) 100%)"
    else:
        level_color, level_label, level_icon = "#DC2626", "CRITIQUE", "🔴"
        bg_grad = "linear-gradient(135deg,rgba(220,38,38,0.2) 0%,rgba(0,0,0,0) 100%)"

    top_agence = "—"
    top_agence_nb = 0
    if not parcours_f.empty and "agence" in parcours_f.columns:
        top_a = parcours_f.groupby("agence")["client_id"].nunique().sort_values(ascending=False)
        if not top_a.empty:
            top_agence = top_a.index[0]
            top_agence_nb = top_a.iloc[0]

    top_canal = "—"
    top_canal_nb = 0
    if not parcours_f.empty:
        top_c = parcours_f["canal"].value_counts()
        if not top_c.empty:
            top_canal = top_c.index[0]
            top_canal_nb = top_c.iloc[0]

    html = (
        f'<div style="background:{bg_grad};border-radius:16px;padding:22px 28px;'
        f'margin-bottom:20px;border-left:8px solid {level_color};'
        f'border:1px solid {level_color}55;box-shadow:0 4px 16px rgba(0,0,0,0.25);">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">'
        f'<div style="font-size:1.25rem;font-weight:800;color:#F4F7FB;">'
        f'{level_icon} SANTÉ DU RÉSEAU : {level_label}</div>'
        f'<div style="background:rgba(0,0,0,0.3);border-radius:30px;padding:8px 20px;'
        f'font-weight:800;color:#F4F7FB;font-size:1.05rem;">'
        f'Score : {score_sante:.0f} / 100</div>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;'
        f'color:#F4F7FB;font-size:0.95rem;line-height:1.7;">'
        f'<div><b>🏆 Top agence :</b><br/>{top_agence} ({top_agence_nb} clients)</div>'
        f'<div><b>📞 Top canal :</b><br/>{top_canal} ({top_canal_nb} interactions)</div>'
        f'<div><b>📊 Réseau :</b><br/>{nb_agences} agences · {nb_canaux} canaux</div>'
        f'</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _render_carte(by_ville):
    """Carte compatible toutes versions Plotly (fallback automatique)."""
    try:
        fig = px.scatter_map(
            by_ville, lat="lat", lon="lon", size="clients", color="clients",
            hover_name="ville", zoom=5, height=340,
            color_continuous_scale=["#F2B705", "#0B1F4D"],
        )
        fig.update_layout(map_style="carto-positron",
                          margin=dict(l=0, r=0, t=0, b=0),
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        return
    except (AttributeError, Exception):
        pass

    try:
        fig = px.scatter_mapbox(
            by_ville, lat="lat", lon="lon", size="clients", color="clients",
            hover_name="ville", zoom=5, height=340,
            color_continuous_scale=["#F2B705", "#0B1F4D"],
        )
        fig.update_layout(mapbox_style="carto-positron",
                          margin=dict(l=0, r=0, t=0, b=0),
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
        return
    except (AttributeError, Exception):
        pass

    st.caption("🗺️ Carte indisponible — affichage sous forme de barres")
    bv = by_ville.sort_values("clients", ascending=True)
    fig = go.Figure(go.Bar(
        x=bv["clients"], y=bv["ville"], orientation="h",
        text=bv["clients"], textposition="outside",
        textfont=dict(size=11, color="#F2B705", family="Arial Black"),
        marker=dict(color="#3B82C4"),
    ))
    fig.update_layout(
        height=340, margin=dict(l=10, r=50, t=10, b=10),
        yaxis=dict(categoryorder="total ascending", title="",
                   tickfont=dict(size=10, color="#F4F7FB")),
        xaxis=dict(title="", showgrid=False,
                   range=[0, bv["clients"].max() * 1.25] if not bv.empty else 10,
                   tickfont=dict(color="#F4F7FB")),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False, font=dict(color="#F4F7FB"),
    )
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# RENDU PRINCIPAL
# ============================================================

def render(data: dict, filters: dict):
    page_title(
        "🏢", "Agences & Canaux",
        "Analysez la performance de vos agences et canaux de distribution."
    )

    clients = data["clients"]
    contrats_f = apply_filters(data["contrats"], filters, date_col="date_ref")
    parcours_f_global = apply_filters(data["parcours"], filters, date_col="date_ref")
    reclamations_f = apply_filters(data["reclamations"], filters, date_col="date_ref")
    frictions_f = apply_filters(data["frictions"], filters, date_col="date_ref")

    if contrats_f.empty and parcours_f_global.empty:
        st.warning("⚠️ Aucune donnée pour la combinaison de filtres actuelle.")
        return

    # ============ SÉLECTEUR DE PHASE ============
    _render_phase_selector(parcours_f_global, "agences_phase_select")

    phase_active = st.session_state.get("agences_phase_select", None)

    # ============ FILTRAGE PAR PHASE ============
    if phase_active and phase_active in PHASES:
        etapes_phase = PHASES[phase_active]["etapes"]
        parcours_f = parcours_f_global[
            parcours_f_global["etape_parcours"].isin(etapes_phase)
        ].copy()
        _bandeau_phase_active(parcours_f_global, phase_active)
    else:
        parcours_f = parcours_f_global

    clients_ids = parcours_f["client_id"].unique().tolist() if not parcours_f.empty else []
    clients_f = clients[clients["client_id"].isin(clients_ids)] if clients_ids else clients.iloc[0:0]

    # ============ BANDEAU SANTÉ ============
    _bandeau_sante(parcours_f, reclamations_f, contrats_f)

    # ============ 5 KPI ============
    nb_agences = clients_f["agence"].nunique() if not clients_f.empty else 0
    clients_par_agence = round(len(clients_f) / nb_agences, 0) if nb_agences else 0
    nb_canaux = parcours_f["canal"].nunique() if not parcours_f.empty else 0
    tconv = taux_conversion(parcours_f, clients_f)
    csat = indice_satisfaction(parcours_f, reclamations_f, sur_5=True)
    tfric = taux_friction(parcours_f)

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(_kpi_card("Agences actives", f"{nb_agences}",
                              f"{int(clients_par_agence)} clients/agence", "#F2B705", "🏢"),
                    unsafe_allow_html=True)
    with k2:
        st.markdown(_kpi_card("Canaux de distribution", f"{nb_canaux}",
                              "actifs sur la période", "#3B82C4", "📞"), unsafe_allow_html=True)
    with k3:
        color_conv = "#10B981" if tconv >= 60 else ("#F2B705" if tconv >= 40 else "#DC2626")
        st.markdown(_kpi_card("Taux de conversion", f"{tconv} %",
                              "objectif ≥ 60 %", color_conv, "🎯"), unsafe_allow_html=True)
    with k4:
        color_fric = "#DC2626" if tfric > 30 else ("#F2B705" if tfric > 15 else "#10B981")
        st.markdown(_kpi_card("Taux de friction", f"{tfric} %",
                              "objectif < 15 %", color_fric, "⚠️"), unsafe_allow_html=True)
    with k5:
        color_csat = "#10B981" if csat >= 4 else ("#F2B705" if csat >= 3 else "#DC2626")
        st.markdown(_kpi_card("Satisfaction (estimée)", f"{csat} / 5",
                              "indice estimé", color_csat, "⭐"), unsafe_allow_html=True)

    st.write("")

    # ============ TOP 3 ACTIONS ============
    st.markdown(
        '<div style="font-size:1.15rem;font-weight:800;color:#F4F7FB;'
        'margin:12px 0 10px 0;">🎯 Top 3 des agences à risque</div>',
        unsafe_allow_html=True,
    )

    priorités = pd.DataFrame()
    if not parcours_f.empty and "agence" in parcours_f.columns:
        par_agence = (
            parcours_f.groupby("agence")
            .agg(
                clients=("client_id", "nunique"),
                frictions=("friction", lambda s: (s == "Oui").sum()),
            )
            .reset_index()
        )
        par_agence["taux_friction"] = (
            par_agence["frictions"] / par_agence["clients"].replace(0, 1) * 100
        ).round(1)
        par_agence = par_agence.sort_values("taux_friction", ascending=False).head(3)
        priorités = par_agence

    if not priorités.empty:
        action_cols = st.columns(3)
        severities = ["rouge", "orange", "jaune"]
        for i, (col, (_, p)) in enumerate(zip(action_cols, priorités.iterrows())):
            sev = severities[i]
            action_text = "Analyser la cause racine et mettre en place un plan de suivi."
            if p["taux_friction"] > 30:
                action_text = "Audit agence recommandé — taux de friction critique."
            elif p["taux_friction"] > 20:
                action_text = "Renforcer la formation des conseillers."
            elif p["frictions"] > 5:
                action_text = "Suivi rapproché de l'agence — plusieurs frictions."
            with col:
                st.markdown(
                    _action_card(
                        rank=i + 1, severity=sev,
                        title=f"Agence {p['agence']}",
                        metric=f"{p['clients']} clients · {p['frictions']} frictions · {p['taux_friction']} %",
                        owner="Direction Réseau", action=action_text,
                    ),
                    unsafe_allow_html=True,
                )
    else:
        st.info("✅ Aucune agence à risque identifiée.")

    st.write("")

    # ============ GRAPHIQUES ============
    c1, c2, c3 = st.columns([1.3, 1, 1])

    with c1:
        with card("🏢 Performance des agences (clients)"):
            if not clients_f.empty and not parcours_f.empty and "agence" in parcours_f.columns:
                perf = clients_f.groupby("agence")["client_id"].nunique().reset_index(name="clients")
                perf = perf.sort_values("clients", ascending=True).head(10)

                fig = go.Figure(go.Bar(
                    y=perf["agence"], x=perf["clients"], orientation="h",
                    text=perf["clients"], textposition="outside",
                    textfont=dict(size=11, color="#F2B705", family="Arial Black"),
                    marker=dict(color="#3B82C4"),
                ))
                fig.update_layout(
                    height=340, margin=dict(l=10, r=60, t=10, b=10),
                    yaxis=dict(categoryorder="total ascending", title="",
                               tickfont=dict(size=10, color="#F4F7FB")),
                    xaxis=dict(title="", showgrid=False,
                               range=[0, perf["clients"].max() * 1.25] if not perf.empty else 10,
                               tickfont=dict(color="#F4F7FB")),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=False, font=dict(color="#F4F7FB"),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.caption("Données indisponibles.")

    with c2:
        with card("📞 Répartition clients par canal"):
            if not parcours_f.empty:
                rep = parcours_f["canal"].value_counts().reset_index()
                rep.columns = ["canal", "n"]
                fig = px.pie(rep, names="canal", values="n", hole=0.55,
                             color_discrete_sequence=CHART_COLORS)
                fig.update_traces(textposition="inside", textinfo="percent",
                                  textfont=dict(size=11, color="white", family="Arial Black"))
                fig.add_annotation(text=f"<b>{parcours_f['client_id'].nunique()}</b><br>clients",
                                   showarrow=False, font=dict(size=12, color="#F2B705"))
                fig.update_layout(height=340, margin=dict(l=5, r=5, t=10, b=10),
                                  showlegend=True,
                                  legend=dict(font=dict(size=10, color="#F4F7FB"), orientation="v"))
                apply_dark_theme(fig)
                st.plotly_chart(fig, use_container_width=True)

    with c3:
        with card("🗺️ Carte des agences"):
            if not clients_f.empty:
                by_ville = clients_f.groupby("ville")["client_id"].nunique().reset_index(name="clients")
                by_ville["lat"] = by_ville["ville"].map(lambda v: VILLE_COORDS.get(v, (None, None))[0])
                by_ville["lon"] = by_ville["ville"].map(lambda v: VILLE_COORDS.get(v, (None, None))[1])
                by_ville = by_ville.dropna(subset=["lat", "lon"])
                if not by_ville.empty:
                    _render_carte(by_ville)
                else:
                    st.caption("Coordonnées indisponibles.")
            else:
                st.caption("Données indisponibles.")

    st.write("")

    # ============ VOLUME + CONVERSION CANAUX ============
    c4, c5 = st.columns(2)

    with c4:
        with card("📊 Volume des canaux"):
            if not parcours_f.empty:
                can = parcours_f["canal"].value_counts().reset_index()
                can.columns = ["canal", "n"]
                can = can.sort_values("n", ascending=True)

                fig = go.Figure(go.Bar(
                    x=can["n"], y=can["canal"], orientation="h",
                    text=can["n"], textposition="outside",
                    textfont=dict(size=11, color="#F2B705", family="Arial Black"),
                    marker=dict(color="#3B82C4"),
                ))
                fig.update_layout(
                    height=300, margin=dict(l=10, r=50, t=10, b=10),
                    yaxis=dict(categoryorder="total ascending", title="",
                               tickfont=dict(size=10, color="#F4F7FB")),
                    xaxis=dict(title="", showgrid=False,
                               range=[0, can["n"].max() * 1.25] if not can.empty else 10,
                               tickfont=dict(color="#F4F7FB")),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=False, font=dict(color="#F4F7FB"),
                )
                st.plotly_chart(fig, use_container_width=True)

    with c5:
        with card("🎯 Taux de conversion par canal"):
            if not parcours_f.empty:
                rows = []
                for canal in parcours_f["canal"].dropna().unique():
                    sub_c = parcours_f[parcours_f["canal"] == canal]
                    rows.append({"canal": canal,
                                 "conversion": taux_conversion(sub_c, clients_f)})
                conv_df = pd.DataFrame(rows).sort_values("conversion", ascending=True)

                colors_conv = []
                for v in conv_df["conversion"]:
                    if v >= 60: colors_conv.append("#10B981")
                    elif v >= 40: colors_conv.append("#F2B705")
                    else: colors_conv.append("#DC2626")

                fig = go.Figure(go.Bar(
                    x=conv_df["conversion"], y=conv_df["canal"], orientation="h",
                    text=[f"{v} %" for v in conv_df["conversion"]],
                    textposition="outside",
                    textfont=dict(size=11, color="#F2B705", family="Arial Black"),
                    marker=dict(color=colors_conv),
                ))
                fig.update_layout(
                    height=300, margin=dict(l=10, r=60, t=10, b=10),
                    yaxis=dict(categoryorder="total ascending", title="",
                               tickfont=dict(size=10, color="#F4F7FB")),
                    xaxis=dict(title="", showgrid=False, ticksuffix="%",
                               range=[0, max(conv_df["conversion"].max() * 1.25, 10)] if not conv_df.empty else 10,
                               tickfont=dict(color="#F4F7FB")),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=False, font=dict(color="#F4F7FB"),
                )
                st.plotly_chart(fig, use_container_width=True)

    st.write("")

    # ============ TABLEAU DÉTAIL ============
    with card("📋 Détail agence × canal : clients, friction, réclamations"):
        if not parcours_f.empty and "agence" in parcours_f.columns:
            agg = parcours_f.groupby("agence").agg(
                clients=("client_id", "nunique"),
                friction_pct=("friction", lambda s: pct((s == "Oui").sum(), len(s))),
            ).reset_index()

            reclam_by_agence = (
                reclamations_f.groupby("agence")["reclamation_id"].count().reset_index(name="reclamations")
                if not reclamations_f.empty and "agence" in reclamations_f.columns
                else pd.DataFrame(columns=["agence", "reclamations"])
            )
            agg = agg.merge(reclam_by_agence, on="agence", how="left").fillna({"reclamations": 0})
            agg["reclamations"] = agg["reclamations"].astype(int)
            agg = agg.rename(columns={
                "agence": "Agence", "clients": "Clients",
                "friction_pct": "Friction (%)", "reclamations": "Réclamations",
            })
            st.dataframe(
                agg.sort_values("Clients", ascending=False),
                use_container_width=True, hide_index=True,
                column_config={
                    "Clients": st.column_config.NumberColumn("Clients", format="%d"),
                    "Friction (%)": st.column_config.NumberColumn("Friction (%)", format="%.1f %%"),
                    "Réclamations": st.column_config.NumberColumn("Réclamations", format="%d"),
                },
            )

    # ============ INSIGHT ============
    if not clients_f.empty:
        top_agence = clients_f["agence"].value_counts().idxmax()
        top_canal = parcours_f["canal"].value_counts().idxmax() if not parcours_f.empty else "—"
        insight_box(
            f"<b>À retenir :</b> l'agence « <b>{top_agence}</b> » concentre le plus grand "
            f"volume de clients. Le canal le plus utilisé est « <b>{top_canal}</b> ». "
            f"Taux de conversion global : <b>{tconv} %</b>. "
            f"Taux de friction : <b>{tfric} %</b>."
        )