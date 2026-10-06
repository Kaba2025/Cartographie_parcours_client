"""views/frictions_blocages.py - Frictions & Blocages : phases colorées + analyse stratégique."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.style import (
    page_title, insight_box, badge, card,
    CHART_COLORS, NSIA_NAVY, NSIA_GOLD,
)
from utils.calculations import apply_filters, pct, safe_mean, apply_dark_theme


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

NIVEAU_COULEURS = {
    "Faible": "#10B981",
    "Moyen": "#F2B705",
    "Élevé": "#DC2626",
    "Critique": "#991B1B",
}
NIVEAU_ORDRE = ["Faible", "Moyen", "Élevé", "Critique"]


# ============================================================
# HELPERS PHASES
# ============================================================

def _level_from_delai(delai_moy):
    """Niveau selon délai moyen de résolution."""
    if delai_moy >= 15:
        return "rouge"
    if delai_moy >= 8:
        return "orange"
    return "vert"


def _compute_phase_sante(frictions_df, phase_key):
    phase = PHASES[phase_key]
    sub = frictions_df[frictions_df["etape_parcours"].isin(phase["etapes"])]
    if sub.empty:
        return {"nb_frictions": 0, "clients_impactes": 0,
                "delai_moy": 0, "level": "vert", "has_data": False}
    nb_fric = len(sub)
    clients_impactes = sub["client_id"].nunique()
    delai_moy = safe_mean(sub["delai_resolution_jours"])
    return {
        "nb_frictions": nb_fric,
        "clients_impactes": clients_impactes,
        "delai_moy": delai_moy,
        "level": _level_from_delai(delai_moy),
        "has_data": True,
    }


def _render_phase_selector(frictions_f, session_key):
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
        sante = _compute_phase_sante(frictions_f, key)
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
            f'font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">Frictions</div>'
            f'<div style="color:#FFFFFF;font-size:1.7rem;font-weight:800;'
            f'line-height:1.1;margin-top:3px;text-shadow:0 2px 4px rgba(0,0,0,0.25);">'
            f'{sante["nb_frictions"]}</div></div>'
            f'<div><div style="color:rgba(255,255,255,0.9);font-size:0.72rem;'
            f'font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">Clients</div>'
            f'<div style="color:#FFFFFF;font-size:1.7rem;font-weight:800;'
            f'line-height:1.1;margin-top:3px;text-shadow:0 2px 4px rgba(0,0,0,0.25);">'
            f'{sante["clients_impactes"]:,}</div></div>'.replace(",", " ") +
            f'<div><div style="color:rgba(255,255,255,0.9);font-size:0.72rem;'
            f'font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">Délai</div>'
            f'<div style="color:#FFFFFF;font-size:1.2rem;font-weight:800;'
            f'line-height:1.1;margin-top:3px;text-shadow:0 2px 4px rgba(0,0,0,0.25);">'
            f'{sante["delai_moy"]:.0f} j</div></div>'
            f'<div><div style="color:rgba(255,255,255,0.9);font-size:0.72rem;'
            f'font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">Étapes</div>'
            f'<div style="color:#FFFFFF;font-size:1.2rem;font-weight:800;'
            f'line-height:1.1;margin-top:3px;text-shadow:0 2px 4px rgba(0,0,0,0.25);">'
            f'{len(phase["etapes"])}</div></div>'
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


def _bandeau_phase_active(frictions_f, phase_key):
    """Bandeau récapitulatif de la phase sélectionnée."""
    phase = PHASES[phase_key]
    sante = _compute_phase_sante(frictions_f, phase_key)

    level_styles = {
        "vert":   ("#10B981", "rgba(16,185,129,0.15)", "🟢", "SAIN"),
        "orange": ("#F2B705", "rgba(242,183,5,0.15)", "🟠", "À SURVEILLER"),
        "rouge":  ("#DC2626", "rgba(220,38,38,0.15)", "🔴", "CRITIQUE"),
    }
    main_color, light_color, icon, label = level_styles[sante["level"]]

    sub = frictions_f[frictions_f["etape_parcours"].isin(phase["etapes"])]

    cause_txt = "Aucune friction significative"
    if not sub.empty and "cause_racine" in sub.columns:
        top_cause_s = sub["cause_racine"].value_counts()
        if not top_cause_s.empty:
            cause_txt = f"{top_cause_s.index[0]} ({top_cause_s.iloc[0]} cas)"

    etape_top = "—"
    if not sub.empty:
        etape_s = sub["etape_parcours"].value_counts()
        if not etape_s.empty:
            etape_top = etape_s.index[0]

    owner_top = "—"
    if "owner" in sub.columns:
        owner_s = sub["owner"].value_counts()
        if not owner_s.empty:
            owner_top = owner_s.index[0]

    html = (
        f'<div style="background:linear-gradient(135deg,{light_color} 0%,rgba(0,0,0,0) 100%);'
        f'border-radius:16px;padding:20px 26px;margin:16px 0;'
        f'border-left:8px solid {main_color};border:1px solid {main_color}55;'
        f'box-shadow:0 4px 16px rgba(0,0,0,0.25);">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
        f'<div style="font-size:1.3rem;font-weight:800;color:#F4F7FB;">'
        f'{phase["emoji"]} PHASE {phase["label"].upper()} — {sante["nb_frictions"]} frictions · '
        f'{sante["clients_impactes"]} clients</div>'
        f'<div style="background:{main_color}33;color:{main_color};'
        f'border-radius:30px;padding:8px 20px;font-weight:800;font-size:1rem;">'
        f'{icon} {label} · Délai {sante["delai_moy"]:.0f} j</div>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;'
        f'color:#F4F7FB;font-size:1rem;line-height:1.6;">'
        f'<div><b>🎯 Cause n°1 :</b><br/>{cause_txt}</div>'
        f'<div><b>⚠️ Étape critique :</b><br/>{etape_top}</div>'
        f'<div><b>👤 Responsable clé :</b><br/>{owner_top}</div>'
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
            f'délai moyen &gt; 15 j. Priorité : « <b>{etape_top}</b> ». '
            f'Cause : <b>{cause_txt}</b>. Responsable : <b>{owner_top}</b>.'
            f'</div>',
            unsafe_allow_html=True,
        )


# ============================================================
# HELPERS KPI / CARDS
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


def _bandeau_sante(frictions_f):
    nb_fric = len(frictions_f)
    clients_impactes = frictions_f["client_id"].nunique()

    taux_non_resolu = 0
    if "statut" in frictions_f.columns:
        taux_non_resolu = pct((frictions_f["statut"] != "Résolu").sum(), nb_fric)

    delai_moy = safe_mean(frictions_f["delai_resolution_jours"])
    score_risque = min(100, taux_non_resolu * 0.5 + min(delai_moy * 3, 50))

    if score_risque >= 60:
        level_color = "#DC2626"; level_label = "CRITIQUE"; level_icon = "🔴"
        bg_grad = "linear-gradient(135deg,rgba(220,38,38,0.2) 0%,rgba(0,0,0,0) 100%)"
    elif score_risque >= 35:
        level_color = "#F2B705"; level_label = "À SURVEILLER"; level_icon = "🟠"
        bg_grad = "linear-gradient(135deg,rgba(242,183,5,0.2) 0%,rgba(0,0,0,0) 100%)"
    else:
        level_color = "#10B981"; level_label = "MAÎTRISÉ"; level_icon = "🟢"
        bg_grad = "linear-gradient(135deg,rgba(16,185,129,0.2) 0%,rgba(0,0,0,0) 100%)"

    cause_top = "Aucune"; cause_nb = 0
    if not frictions_f.empty and "cause_racine" in frictions_f.columns:
        top_cause_s = frictions_f["cause_racine"].value_counts()
        if not top_cause_s.empty:
            cause_top = top_cause_s.index[0]; cause_nb = top_cause_s.iloc[0]

    etape_top = "—"
    if not frictions_f.empty:
        etape_top_s = frictions_f["etape_parcours"].value_counts()
        if not etape_top_s.empty:
            etape_top = etape_top_s.index[0]

    owner_top = "—"
    if "owner" in frictions_f.columns:
        owner_s = frictions_f["owner"].value_counts()
        if not owner_s.empty:
            owner_top = owner_s.index[0]

    html = (
        f'<div style="background:{bg_grad};border-radius:16px;padding:22px 28px;'
        f'margin-bottom:20px;border-left:8px solid {level_color};'
        f'border:1px solid {level_color}55;box-shadow:0 4px 16px rgba(0,0,0,0.25);">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">'
        f'<div style="font-size:1.25rem;font-weight:800;color:#F4F7FB;">'
        f'{level_icon} SITUATION GLOBALE DES FRICTIONS : {level_label}</div>'
        f'<div style="background:rgba(0,0,0,0.3);border-radius:30px;padding:8px 20px;'
        f'font-weight:800;color:#F4F7FB;font-size:1.05rem;">'
        f'Score risque : {score_risque:.0f} / 100</div>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;'
        f'color:#F4F7FB;font-size:0.95rem;line-height:1.7;">'
        f'<div><b>🎯 Cause n°1 :</b><br/>{cause_top} ({cause_nb} cas)</div>'
        f'<div><b>⚠️ Étape critique :</b><br/>{etape_top}</div>'
        f'<div><b>👤 Responsable clé :</b><br/>{owner_top}</div>'
        f'</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ============================================================
# RENDU PRINCIPAL
# ============================================================

def render(data: dict, filters: dict):
    page_title(
        "⚠️", "Frictions & Blocages",
        "Identifiez où ça bloque, pourquoi, et quel est l'impact sur vos clients."
    )

    frictions_f_global = apply_filters(data["frictions"], filters, date_col="date_ref")
    parcours_f_global = apply_filters(data["parcours"], filters, date_col="date_ref")

    if frictions_f_global.empty:
        st.warning("⚠️ Aucune friction ne correspond à la combinaison de filtres sélectionnée.")
        return

    # ============ SÉLECTEUR DE PHASE ============
    _render_phase_selector(frictions_f_global, "frictions_phase_select")

    phase_active = st.session_state.get("frictions_phase_select", None)

    # ============ FILTRAGE PAR PHASE ============
    if phase_active and phase_active in PHASES:
        etapes_phase = PHASES[phase_active]["etapes"]
        frictions_f = frictions_f_global[
            frictions_f_global["etape_parcours"].isin(etapes_phase)
        ].copy()
        parcours_f = parcours_f_global[
            parcours_f_global["etape_parcours"].isin(etapes_phase)
        ].copy()
        _bandeau_phase_active(frictions_f_global, phase_active)
    else:
        frictions_f = frictions_f_global
        parcours_f = parcours_f_global

    if frictions_f.empty:
        st.warning(f"Aucune friction pour la phase sélectionnée.")
        return

    # ============ BANDEAU SANTÉ GLOBAL ============
    _bandeau_sante(frictions_f)

    # ============ KPI ============
    nb_frictions = len(frictions_f)
    clients_impactes = frictions_f["client_id"].nunique()
    delai_moy = safe_mean(frictions_f["delai_resolution_jours"])
    taux_resolution = pct(
        (frictions_f["statut"] == "Résolu").sum(), nb_frictions
    ) if "statut" in frictions_f.columns else 0

    taux_friction_global = 0
    if not parcours_f.empty:
        taux_friction_global = pct(
            (parcours_f["friction"] == "Oui").sum(), len(parcours_f)
        )

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(_kpi_card("Frictions détectées", f"{nb_frictions:,}".replace(",", " "),
                              "sur la période", "#F2B705", "⚠️"), unsafe_allow_html=True)
    with k2:
        st.markdown(_kpi_card("Clients impactés", f"{clients_impactes:,}".replace(",", " "),
                              "clients uniques", "#3B82C4", "👥"), unsafe_allow_html=True)
    with k3:
        color_delai = "#DC2626" if delai_moy > 15 else ("#F2B705" if delai_moy > 7 else "#10B981")
        st.markdown(_kpi_card("Délai moyen résolution", f"{delai_moy} j",
                              "objectif < 7 j", color_delai, "⏱"), unsafe_allow_html=True)
    with k4:
        color_res = "#10B981" if taux_resolution >= 70 else ("#F2B705" if taux_resolution >= 40 else "#DC2626")
        st.markdown(_kpi_card("Taux de résolution", f"{taux_resolution} %",
                              f"{100-taux_resolution:.0f}% encore ouverts", color_res, "✅"), unsafe_allow_html=True)
    with k5:
        color_tf = "#DC2626" if taux_friction_global > 30 else ("#F2B705" if taux_friction_global > 15 else "#10B981")
        st.markdown(_kpi_card("Taux friction global", f"{taux_friction_global} %",
                              "part du parcours", color_tf, "📊"), unsafe_allow_html=True)

    st.write("")

    # ============ TOP 3 ACTIONS PRIORITAIRES ============
    st.markdown(
        f'<div style="font-size:1.15rem;font-weight:800;color:#F4F7FB;'
        f'margin:12px 0 10px 0;">🎯 Top 3 des actions prioritaires</div>',
        unsafe_allow_html=True,
    )

    priorités = (
        frictions_f[frictions_f["statut"] != "Résolu"] if "statut" in frictions_f.columns
        else frictions_f
    ).groupby(["cause_racine", "etape_parcours"]).agg(
        clients=("client_id", "nunique"),
        nb=("friction_id", "count"),
        delai=("delai_resolution_jours", "mean"),
        owner=("owner", lambda s: s.mode().iloc[0] if not s.mode().empty else "—"),
    ).reset_index().sort_values("clients", ascending=False).head(3)

    if not priorités.empty:
        action_cols = st.columns(3)
        severities = ["rouge", "orange", "jaune"]
        for i, (col, (_, p)) in enumerate(zip(action_cols, priorités.iterrows())):
            sev = severities[i]
            action_text = "Analyser la cause racine et mettre en place un plan de suivi."
            if p["delai"] > 15:
                action_text = "Revoir les délais de traitement — escalade au responsable."
            elif p["clients"] > 20:
                action_text = "Prioriser la résolution — impact client important."
            with col:
                st.markdown(
                    _action_card(
                        rank=i + 1, severity=sev,
                        title=f"{p['cause_racine']} → {p['etape_parcours']}",
                        metric=f"{p['clients']} clients · {p['nb']} cas · délai {p['delai']:.0f} j",
                        owner=p["owner"], action=action_text,
                    ),
                    unsafe_allow_html=True,
                )
    else:
        st.info("✅ Aucune friction non résolue sur la période.")

    st.write("")

    # ============ TIMELINE ÉVOLUTION ============
    with card("📈 Évolution des frictions (12 derniers mois)"):
        if "date_ref" in frictions_f.columns:
            tmp = frictions_f.dropna(subset=["date_ref"]).copy()
            if not tmp.empty:
                tmp["mois"] = tmp["date_ref"].dt.to_period("M").dt.to_timestamp()
                monthly = tmp.groupby("mois").size().reset_index(name="n")

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=monthly["mois"], y=monthly["n"],
                    mode="lines+markers",
                    line=dict(color="#F2B705", width=3),
                    marker=dict(size=9, color="#F2B705",
                                line=dict(color="#0B1F4D", width=1)),
                    fill="tozeroy",
                    fillcolor="rgba(242,183,5,0.15)",
                    hovertemplate="<b>%{x|%b %Y}</b><br>%{y} frictions<extra></extra>",
                ))
                fig.update_layout(
                    height=320, margin=dict(l=15, r=15, t=20, b=20),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#F4F7FB", size=12),
                    yaxis=dict(gridcolor="#1E3A6B", tickfont=dict(color="#F4F7FB"), title=""),
                    xaxis=dict(gridcolor="#1E3A6B", tickfont=dict(color="#F4F7FB"), title=""),
                    hovermode="x unified",
                )
                apply_dark_theme(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Pas assez de données datées.")

    # ============ GRAPHIQUES PRINCIPAUX (3 colonnes) ============
    c1, c2, c3 = st.columns(3)

    with c1:
        with card("🎯 Répartition par niveau"):
            niveau_order = [n for n in NIVEAU_ORDRE if n in frictions_f["niveau"].unique()]
            if niveau_order:
                rep = frictions_f["niveau"].value_counts().reindex(niveau_order).reset_index()
                rep.columns = ["niveau", "n"]
                colors_niv = [NIVEAU_COULEURS.get(n, "#94A3B8") for n in rep["niveau"]]
                fig = go.Figure(go.Bar(
                    x=rep["niveau"], y=rep["n"],
                    text=[f"{v} ({pct(v, len(frictions_f))}%)" for v in rep["n"]],
                    textposition="outside",
                    textfont=dict(size=12, color="#F2B705", family="Arial Black"),
                    marker=dict(color=colors_niv),
                ))
                fig.update_layout(
                    height=300, margin=dict(l=10, r=10, t=30, b=10),
                    yaxis=dict(title="", gridcolor="#1E3A6B",
                               range=[0, rep["n"].max() * 1.25] if not rep.empty else 10,
                               tickfont=dict(color="#F4F7FB")),
                    xaxis=dict(title="", tickfont=dict(color="#F4F7FB")),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=False, font=dict(color="#F4F7FB"),
                )
                st.plotly_chart(fig, use_container_width=True)

    with c2:
        with card("📍 Top étapes impactées"):
            rep2 = frictions_f["etape_parcours"].value_counts().reset_index().head(7)
            rep2.columns = ["etape", "n"]
            rep2 = rep2.sort_values("n", ascending=True)
            fig = go.Figure(go.Bar(
                x=rep2["n"], y=rep2["etape"], orientation="h",
                text=rep2["n"], textposition="outside",
                textfont=dict(size=12, color="#F2B705", family="Arial Black"),
                marker=dict(color="#3B82C4"),
            ))
            fig.update_layout(
                height=300, margin=dict(l=10, r=50, t=10, b=10),
                yaxis=dict(categoryorder="total ascending", title="",
                           tickfont=dict(size=10, color="#F4F7FB")),
                xaxis=dict(title="", showgrid=False,
                           range=[0, rep2["n"].max() * 1.25] if not rep2.empty else 10,
                           tickfont=dict(color="#F4F7FB")),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False, font=dict(color="#F4F7FB"),
            )
            st.plotly_chart(fig, use_container_width=True)

    with c3:
        with card("🏷️ Répartition par type"):
            rep3 = frictions_f["type_friction"].value_counts().reset_index()
            rep3.columns = ["type", "n"]
            if not rep3.empty:
                fig = px.pie(
                    rep3, names="type", values="n", hole=0.55,
                    color_discrete_sequence=CHART_COLORS,
                )
                fig.update_traces(
                    textposition="inside", textinfo="percent",
                    textfont=dict(size=11, color="white", family="Arial Black"),
                )
                fig.update_layout(
                    height=300, margin=dict(l=5, r=5, t=10, b=10),
                    showlegend=True,
                    legend=dict(font=dict(size=10, color="#F4F7FB"), orientation="v"),
                )
                apply_dark_theme(fig)
                st.plotly_chart(fig, use_container_width=True)

    st.write("")

    # ============ MATRICE RISQUE × VOLUME ============
    with card("🎯 Matrice Risque × Volume (par étape)"):
        mat = frictions_f.groupby("etape_parcours").agg(
            clients=("client_id", "nunique"),
            nb=("friction_id", "count"),
            delai=("delai_resolution_jours", "mean"),
        ).reset_index()

        if not mat.empty:
            vol_med = mat["clients"].median()
            delai_med = mat["delai"].median()

            def _quadrant(row):
                high_delai = row["delai"] >= delai_med
                high_vol = row["clients"] >= vol_med
                if high_delai and high_vol:
                    return "🔴 Priorité haute"
                if high_delai and not high_vol:
                    return "🟠 Surveiller"
                if not high_delai and high_vol:
                    return "🟡 Attention"
                return "🟢 À suivre"

            mat["quadrant"] = mat.apply(_quadrant, axis=1)
            qcolors = {
                "🔴 Priorité haute": "#DC2626",
                "🟠 Surveiller": "#F59E0B",
                "🟡 Attention": "#EAB308",
                "🟢 À suivre": "#10B981",
            }

            fig = px.scatter(
                mat, x="clients", y="delai",
                size="nb", color="quadrant",
                hover_name="etape_parcours",
                color_discrete_map=qcolors,
                size_max=30,
            )
            fig.add_vline(x=vol_med, line_dash="dot", line_color="#3E5A76")
            fig.add_hline(y=delai_med, line_dash="dot", line_color="#3E5A76")
            fig.update_layout(
                height=420, margin=dict(l=20, r=20, t=20, b=20),
                xaxis_title="Clients impactés", yaxis_title="Délai moyen (j)",
                legend=dict(font=dict(color="#F4F7FB")),
            )
            apply_dark_theme(fig)
            st.plotly_chart(fig, use_container_width=True)

    # ============ COMPARAISON INTER-PHASES ============
    with card("📊 Comparaison inter-phases (frictions par phase)"):
        phase_stats = []
        for pk, ph in PHASES.items():
            sub_p = frictions_f_global[frictions_f_global["etape_parcours"].isin(ph["etapes"])]
            phase_stats.append({
                "Phase": f"{ph['emoji']} {ph['label']}",
                "Frictions": len(sub_p),
                "Clients": sub_p["client_id"].nunique() if not sub_p.empty else 0,
            })
        df_phases = pd.DataFrame(phase_stats)

        if not df_phases.empty:
            colors_phases = ["#3B82C4", "#F2B705", "#2E9E6C"]
            fig = go.Figure(go.Bar(
                x=df_phases["Phase"], y=df_phases["Frictions"],
                text=df_phases["Frictions"], textposition="outside",
                textfont=dict(size=14, color="#F2B705", family="Arial Black"),
                marker=dict(color=colors_phases),
            ))
            fig.update_layout(
                height=320, margin=dict(l=20, r=20, t=20, b=20),
                yaxis=dict(title="", gridcolor="#1E3A6B",
                           range=[0, df_phases["Frictions"].max() * 1.25] if not df_phases.empty else 10,
                           tickfont=dict(color="#F4F7FB")),
                xaxis=dict(title="", tickfont=dict(color="#F4F7FB", size=13)),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False, font=dict(color="#F4F7FB"),
            )
            st.plotly_chart(fig, use_container_width=True)

    st.write("")

    # ============ TOP 10 + FOCUS ============
    left, right = st.columns([1.3, 1])

    with left:
        with card("🔝 Top 10 des blocages (cause × étape)"):
            top = (
                frictions_f.groupby(["cause_racine", "etape_parcours"])
                .agg(
                    clients=("client_id", "nunique"),
                    frictions=("friction_id", "count"),
                    delai=("delai_resolution_jours", "mean"),
                    owner=("owner", lambda s: s.mode().iloc[0] if not s.mode().empty else "—"),
                )
                .reset_index()
                .sort_values("clients", ascending=False)
                .head(10)
            )
            top["delai"] = top["delai"].round(1)
            top = top.rename(columns={
                "cause_racine": "Cause", "etape_parcours": "Étape",
                "clients": "Clients", "frictions": "Cas",
                "delai": "Délai (j)", "owner": "Responsable",
            })
            st.dataframe(
                top, use_container_width=True, hide_index=True, height=420,
                column_config={
                    "Clients": st.column_config.NumberColumn("Clients", format="%d"),
                    "Cas": st.column_config.NumberColumn("Cas", format="%d"),
                    "Délai (j)": st.column_config.NumberColumn("Délai (j)", format="%.1f"),
                },
            )

    with right:
        with card("🔍 Focus par dimension"):
            dim_choice = st.radio(
                "Analyser par :",
                ["Produit", "Agence", "Canal", "Responsable"],
                horizontal=True, key="friction_dim_focus",
            )
            col_map = {"Produit": "produit", "Agence": "agence",
                       "Canal": "canal", "Responsable": "owner"}
            col = col_map[dim_choice]

            if col in frictions_f.columns:
                rep4 = frictions_f[col].value_counts().reset_index().head(10)
                rep4.columns = [dim_choice, "n"]
                rep4 = rep4.sort_values("n", ascending=True)

                fig = go.Figure(go.Bar(
                    x=rep4["n"], y=rep4[dim_choice], orientation="h",
                    text=rep4["n"], textposition="outside",
                    textfont=dict(size=11, color="#F2B705", family="Arial Black"),
                    marker=dict(color="#F2B705"),
                ))
                fig.update_layout(
                    height=420, margin=dict(l=10, r=50, t=10, b=10),
                    yaxis=dict(categoryorder="total ascending", title="",
                               tickfont=dict(size=10, color="#F4F7FB")),
                    xaxis=dict(title="", showgrid=False,
                               range=[0, rep4["n"].max() * 1.25] if not rep4.empty else 10,
                               tickfont=dict(color="#F4F7FB")),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=False, font=dict(color="#F4F7FB"),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.caption(f"Donnée non disponible pour « {dim_choice} ».")

    # ============ INSIGHT ============
    if not frictions_f.empty:
        top_cause = frictions_f["cause_racine"].mode().iloc[0]
        top_etape = frictions_f["etape_parcours"].mode().iloc[0]
        top_owner = "—"
        if "owner" in frictions_f.columns:
            owner_s = frictions_f["owner"].value_counts()
            if not owner_s.empty:
                top_owner = owner_s.index[0]

        insight_box(
            f"<b>À retenir :</b> la cause « <b>{top_cause}</b> » sur l'étape "
            f"« <b>{top_etape}</b> » concentre le plus de blocages. "
            f"Responsable principal : <b>{top_owner}</b>. "
            f"Priorité de traitement recommandée."
        )