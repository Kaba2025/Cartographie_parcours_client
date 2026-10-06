"""views/produits.py - Performance stratégique du portefeuille produits."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.style import (
    page_title, insight_box, badge, card,
    CHART_COLORS, NSIA_NAVY, NSIA_GOLD,
)
from utils.calculations import (
    apply_filters, pct, safe_mean, taux_conversion, taux_friction,
    apply_dark_theme,
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


# ============================================================
# HELPERS
# ============================================================

def _fmt_fcfa(v):
    try:
        v = float(v)
    except Exception:
        return "0 FCFA"
    if v >= 1e9:
        return f"{v/1e9:.2f} Md FCFA".replace(".", ",")
    if v >= 1e6:
        return f"{v/1e6:.1f} M FCFA".replace(".", ",")
    if v >= 1e3:
        return f"{v/1e3:.0f} K FCFA"
    return f"{v:,.0f} FCFA".replace(",", " ")


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
    phase = PHASES[phase_key]
    sub = parcours_df[parcours_df["etape_parcours"].isin(phase["etapes"])]
    if sub.empty:
        return {"nb_clients": 0, "nb_produits": 0, "taux_friction": 0.0,
                "taux_abandon": 0.0, "level": "vert", "has_data": False}
    nb_clients = sub["client_id"].nunique()
    nb_produits = sub["produit"].nunique() if "produit" in sub.columns else 0
    taux_fric = pct((sub["friction"] == "Oui").sum(), len(sub)) \
        if "friction" in sub.columns else 0
    taux_abandon = pct((sub["issue_etape"] == "Abandon").sum(), len(sub))
    return {
        "nb_clients": nb_clients,
        "nb_produits": nb_produits,
        "taux_friction": taux_fric,
        "taux_abandon": taux_abandon,
        "level": _level_from_friction(taux_fric),
        "has_data": True,
    }


def _render_phase_selector(parcours_f, session_key):
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
            f'font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">Produits</div>'
            f'<div style="color:#FFFFFF;font-size:1.2rem;font-weight:800;'
            f'line-height:1.1;margin-top:3px;text-shadow:0 2px 4px rgba(0,0,0,0.25);">'
            f'{sante["nb_produits"]}</div></div>'
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

    top_produit = "—"
    if not sub.empty and "produit" in sub.columns:
        top_p = sub.groupby("produit")["client_id"].nunique().sort_values(ascending=False)
        if not top_p.empty:
            top_produit = f"{top_p.index[0]} ({top_p.iloc[0]} clients)"

    produit_risque = "—"
    taux_risque = 0
    if not sub.empty and "produit" in sub.columns:
        for p in sub["produit"].dropna().unique():
            sp = sub[sub["produit"] == p]
            tf = taux_friction(sp)
            if tf > taux_risque:
                taux_risque = tf
                produit_risque = f"{p} ({tf:.0f} % friction)"

    html = (
        f'<div style="background:linear-gradient(135deg,{light_color} 0%,rgba(0,0,0,0) 100%);'
        f'border-radius:16px;padding:20px 26px;margin:16px 0;'
        f'border-left:8px solid {main_color};border:1px solid {main_color}55;'
        f'box-shadow:0 4px 16px rgba(0,0,0,0.25);">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
        f'<div style="font-size:1.3rem;font-weight:800;color:#F4F7FB;">'
        f'{phase["emoji"]} PHASE {phase["label"].upper()} — {sante["nb_clients"]} clients · '
        f'{sante["nb_produits"]} produits</div>'
        f'<div style="background:{main_color}33;color:{main_color};'
        f'border-radius:30px;padding:8px 20px;font-weight:800;font-size:1rem;">'
        f'{icon} {label} · Friction {sante["taux_friction"]:.0f} %</div>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;'
        f'color:#F4F7FB;font-size:1rem;line-height:1.6;">'
        f'<div><b>🏆 Top produit :</b><br/>{top_produit}</div>'
        f'<div><b>⚠️ À surveiller :</b><br/>{produit_risque}</div>'
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
            f'Produit à risque : <b>{produit_risque}</b>.'
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
        f'<div style="font-size:1.6rem;font-weight:800;color:{color};'
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


def _bandeau_sante(parcours_f, contrats_f, reclamations_f):
    nb_produits = parcours_f["produit"].nunique() if not parcours_f.empty else 0
    nb_clients = parcours_f["client_id"].nunique() if not parcours_f.empty else 0
    ca = contrats_f.loc[
        contrats_f["statut_contrat"].isin(["Actif", "Arrivé à terme"]),
        "montant_cotisation_fcfa"
    ].sum() if not contrats_f.empty else 0

    taux_fric_global = taux_friction(parcours_f) if not parcours_f.empty else 0
    taux_abandon = pct(
        (parcours_f["issue_etape"] == "Abandon").sum(),
        len(parcours_f)
    ) if not parcours_f.empty else 0

    score = max(0, min(100, 100 - (taux_fric_global * 1.3 + taux_abandon * 0.8)))

    if score >= 75:
        level_color, level_label, level_icon = "#10B981", "PORTEFEUILLE SAIN", "🟢"
        bg_grad = "linear-gradient(135deg,rgba(16,185,129,0.2) 0%,rgba(0,0,0,0) 100%)"
    elif score >= 50:
        level_color, level_label, level_icon = "#F2B705", "À SURVEILLER", "🟠"
        bg_grad = "linear-gradient(135deg,rgba(242,183,5,0.2) 0%,rgba(0,0,0,0) 100%)"
    else:
        level_color, level_label, level_icon = "#DC2626", "PORTEFEUILLE À RISQUE", "🔴"
        bg_grad = "linear-gradient(135deg,rgba(220,38,38,0.2) 0%,rgba(0,0,0,0) 100%)"

    top_produit = "—"; top_produit_nb = 0
    if not parcours_f.empty:
        top_p = parcours_f.groupby("produit")["client_id"].nunique().sort_values(ascending=False)
        if not top_p.empty:
            top_produit = top_p.index[0]; top_produit_nb = top_p.iloc[0]

    produit_risque = "—"; taux_risque = 0
    if not parcours_f.empty:
        for p in parcours_f["produit"].dropna().unique():
            sp = parcours_f[parcours_f["produit"] == p]
            tf = taux_friction(sp)
            if tf > taux_risque:
                taux_risque = tf
                produit_risque = p

    html = (
        f'<div style="background:{bg_grad};border-radius:16px;padding:22px 28px;'
        f'margin-bottom:20px;border-left:8px solid {level_color};'
        f'border:1px solid {level_color}55;box-shadow:0 4px 16px rgba(0,0,0,0.25);">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">'
        f'<div style="font-size:1.25rem;font-weight:800;color:#F4F7FB;">'
        f'{level_icon} SANTÉ DU PORTEFEUILLE : {level_label}</div>'
        f'<div style="background:rgba(0,0,0,0.3);border-radius:30px;padding:8px 20px;'
        f'font-weight:800;color:#F4F7FB;font-size:1.05rem;">'
        f'Score : {score:.0f} / 100</div>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;'
        f'color:#F4F7FB;font-size:0.95rem;line-height:1.7;">'
        f'<div><b>🏆 Top produit :</b><br/>{top_produit} ({top_produit_nb} clients)</div>'
        f'<div><b>⚠️ À surveiller :</b><br/>{produit_risque} ({taux_risque} % friction)</div>'
        f'<div><b>💰 CA collecté :</b><br/>{_fmt_fcfa(ca)}</div>'
        f'</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ============================================================
# RENDU PRINCIPAL
# ============================================================

def render(data: dict, filters: dict):
    page_title(
        "📦", "Produits",
        "Analysez la performance de chaque produit : volume, conversion, "
        "abandons et principales tendances."
    )

    produits_ref = data["produits"]
    contrats_f = apply_filters(data["contrats"], filters, date_col="date_ref")
    parcours_f_global = apply_filters(data["parcours"], filters, date_col="date_ref")
    frictions_f = apply_filters(data["frictions"], filters, date_col="date_ref")
    reclamations_f = apply_filters(data["reclamations"], filters, date_col="date_ref")
    evenements_f = apply_filters(data["evenements"], filters, date_col="date_ref")

    if contrats_f.empty and parcours_f_global.empty:
        st.warning("⚠️ Aucune donnée pour la combinaison de filtres actuelle.")
        return

    # ============ SÉLECTEUR DE PHASE ============
    _render_phase_selector(parcours_f_global, "produits_phase_select")

    phase_active = st.session_state.get("produits_phase_select", None)

    # ============ FILTRAGE PAR PHASE ============
    if phase_active and phase_active in PHASES:
        etapes_phase = PHASES[phase_active]["etapes"]
        parcours_f = parcours_f_global[
            parcours_f_global["etape_parcours"].isin(etapes_phase)
        ].copy()
        _bandeau_phase_active(parcours_f_global, phase_active)
    else:
        parcours_f = parcours_f_global

    # ============ BANDEAU SANTÉ ============
    _bandeau_sante(parcours_f, contrats_f, reclamations_f)

    # ============ 5 KPI ============
    nb_clients = parcours_f["client_id"].nunique() if not parcours_f.empty else 0
    nb_produits = parcours_f["produit"].nunique() if not parcours_f.empty else 0
    ca = contrats_f.loc[
        contrats_f["statut_contrat"].isin(["Actif", "Arrivé à terme"]),
        "montant_cotisation_fcfa"
    ].sum() if not contrats_f.empty else 0
    tconv = taux_conversion(parcours_f, data["clients"])
    tabandon = pct(
        (parcours_f["issue_etape"] == "Abandon").sum(),
        len(parcours_f)
    ) if not parcours_f.empty else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(_kpi_card("Produits actifs", f"{nb_produits}",
                              f"{nb_clients:,} clients".replace(",", " "), "#F2B705", "📦"),
                    unsafe_allow_html=True)
    with k2:
        st.markdown(_kpi_card("Clients totaux", f"{nb_clients:,}".replace(",", " "),
                              "sur la période", "#3B82C4", "👥"), unsafe_allow_html=True)
    with k3:
        st.markdown(_kpi_card("Cotisations collectées", _fmt_fcfa(ca),
                              "contrats actifs", "#10B981", "💰"), unsafe_allow_html=True)
    with k4:
        color_conv = "#10B981" if tconv >= 60 else ("#F2B705" if tconv >= 40 else "#DC2626")
        st.markdown(_kpi_card("Taux de conversion", f"{tconv} %",
                              "objectif ≥ 60 %", color_conv, "🎯"), unsafe_allow_html=True)
    with k5:
        color_ab = "#DC2626" if tabandon > 15 else ("#F2B705" if tabandon > 7 else "#10B981")
        st.markdown(_kpi_card("Taux d'abandon", f"{tabandon} %",
                              "objectif < 7 %", color_ab, "❌"), unsafe_allow_html=True)

    st.write("")

    # ============ TOP 3 PRODUITS ============
    st.markdown(
        '<div style="font-size:1.15rem;font-weight:800;color:#F4F7FB;'
        'margin:12px 0 10px 0;">🎯 Top 3 des produits à surveiller</div>',
        unsafe_allow_html=True,
    )

    priorites = []
    if not parcours_f.empty:
        for p in parcours_f["produit"].dropna().unique():
            sp = parcours_f[parcours_f["produit"] == p]
            tf = taux_friction(sp)
            ta = pct((sp["issue_etape"] == "Abandon").sum(), len(sp)) if len(sp) > 0 else 0
            priorites.append({
                "produit": p, "clients": sp["client_id"].nunique(),
                "friction": tf, "abandon": ta, "score": tf * 0.5 + ta * 0.5,
            })
        priorites = sorted(priorites, key=lambda x: x["score"], reverse=True)[:3]

    if priorites:
        action_cols = st.columns(3)
        severities = ["rouge", "orange", "jaune"]
        for i, (col, p) in enumerate(zip(action_cols, priorites)):
            sev = severities[i]
            action_text = "Analyser la cause racine et mettre en place un plan de suivi."
            if p["friction"] > 30:
                action_text = "Audit produit recommandé — taux de friction critique."
            elif p["abandon"] > 15:
                action_text = "Revoir le parcours client — taux d'abandon élevé."
            elif p["friction"] > 20:
                action_text = "Renforcer la formation et clarifier la communication."
            with col:
                st.markdown(
                    _action_card(rank=i + 1, severity=sev, title=f"{p['produit']}",
                                 metric=f"{p['clients']} clients · {p['friction']} % friction · {p['abandon']} % abandon",
                                 owner="Marketing Produit", action=action_text),
                    unsafe_allow_html=True,
                )
    else:
        st.info("✅ Aucun produit à risque identifié.")

    st.write("")

    # ============ GRAPHIQUES ============
    c1, c2, c3 = st.columns([1, 1.3, 1.1])

    with c1:
        with card("📦 Répartition clients"):
            if not parcours_f.empty:
                rep = parcours_f.drop_duplicates("client_id")["produit"].value_counts().reset_index()
                rep.columns = ["produit", "n"]
                fig = px.pie(rep, names="produit", values="n", hole=0.55,
                             color_discrete_sequence=CHART_COLORS)
                fig.update_traces(textposition="inside", textinfo="percent",
                                  textfont=dict(size=11, color="white", family="Arial Black"))
                fig.add_annotation(text=f"<b>{nb_clients:,}</b><br>clients".replace(",", " "),
                                   showarrow=False, font=dict(size=12, color="#F2B705"))
                fig.update_layout(height=340, margin=dict(l=5, r=5, t=10, b=10),
                                  showlegend=True,
                                  legend=dict(font=dict(size=9, color="#F4F7FB"), orientation="v"))
                apply_dark_theme(fig)
                st.plotly_chart(fig, use_container_width=True)

    with c2:
        with card("📈 Évolution du volume clients par produit"):
            if not parcours_f.empty:
                tmp = parcours_f.dropna(subset=["date_entree_etape"]).copy()
                if not tmp.empty:
                    tmp["mois"] = tmp["date_entree_etape"].dt.to_period("M").dt.to_timestamp()
                    evo = tmp.groupby(["mois", "produit"])["client_id"].nunique().reset_index()
                    fig = px.line(evo, x="mois", y="client_id", color="produit",
                                  color_discrete_sequence=CHART_COLORS, markers=True)
                    fig.update_layout(
                        height=340, margin=dict(l=10, r=10, t=10, b=10),
                        legend=dict(orientation="h", y=-0.3, font=dict(size=10, color="#F4F7FB")),
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        hovermode="x unified",
                        yaxis=dict(title="", showgrid=True, gridcolor="#1E3A6B",
                                   tickfont=dict(color="#F4F7FB")),
                        xaxis=dict(title="", tickfont=dict(color="#F4F7FB")),
                    )
                    apply_dark_theme(fig)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption("Pas assez de données datées.")

    with c3:
        with card("🎯 Top 5 produits par conversion"):
            if not parcours_f.empty:
                rows = []
                for p in parcours_f["produit"].dropna().unique():
                    sub_p = parcours_f[parcours_f["produit"] == p]
                    rows.append({"produit": p, "conversion": taux_conversion(sub_p, data["clients"])})
                topdf = pd.DataFrame(rows).sort_values("conversion", ascending=True).tail(5)

                colors_conv = []
                for v in topdf["conversion"]:
                    if v >= 60: colors_conv.append("#10B981")
                    elif v >= 40: colors_conv.append("#F2B705")
                    else: colors_conv.append("#DC2626")

                fig = go.Figure(go.Bar(
                    x=topdf["conversion"], y=topdf["produit"], orientation="h",
                    text=[f"{v} %" for v in topdf["conversion"]],
                    textposition="outside",
                    textfont=dict(size=11, color="#F2B705", family="Arial Black"),
                    marker=dict(color=colors_conv),
                ))
                fig.update_layout(
                    height=340, margin=dict(l=10, r=60, t=10, b=10),
                    yaxis=dict(categoryorder="total ascending", title="",
                               tickfont=dict(size=10, color="#F4F7FB")),
                    xaxis=dict(title="", showgrid=False, ticksuffix="%",
                               range=[0, max(topdf["conversion"].max() * 1.25, 10)] if not topdf.empty else 10,
                               tickfont=dict(color="#F4F7FB")),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=False, font=dict(color="#F4F7FB"),
                )
                st.plotly_chart(fig, use_container_width=True)

    st.write("")

    # ============ MATRICE COMPARATIVE ============
    with card("📋 Matrice comparative de tous les produits"):
        produits_dispo = sorted(parcours_f["produit"].dropna().unique().tolist()) if not parcours_f.empty else []
        detail_rows = []
        for p in produits_dispo:
            sp = parcours_f[parcours_f["produit"] == p]
            sr = reclamations_f[reclamations_f["produit"] == p] if not reclamations_f.empty else pd.DataFrame()
            sf = frictions_f[frictions_f["produit"] == p] if not frictions_f.empty else pd.DataFrame()
            detail_rows.append({
                "Produit": p,
                "Clients": sp["client_id"].nunique(),
                "Conversion (%)": taux_conversion(sp, data["clients"]),
                "Friction (%)": taux_friction(sp),
                "Abandon (%)": pct((sp["issue_etape"] == "Abandon").sum(), len(sp)) if len(sp) > 0 else 0,
                "Réclamations": len(sr),
                "Frictions": len(sf),
            })
        df_detail = pd.DataFrame(detail_rows).sort_values("Clients", ascending=False)

        st.dataframe(
            df_detail, use_container_width=True, hide_index=True,
            column_config={
                "Clients": st.column_config.NumberColumn("Clients", format="%d"),
                "Conversion (%)": st.column_config.NumberColumn("Conversion (%)", format="%.1f %%"),
                "Friction (%)": st.column_config.NumberColumn("Friction (%)", format="%.1f %%"),
                "Abandon (%)": st.column_config.NumberColumn("Abandon (%)", format="%.1f %%"),
                "Réclamations": st.column_config.NumberColumn("Réclamations", format="%d"),
                "Frictions": st.column_config.NumberColumn("Frictions", format="%d"),
            },
        )

    st.write("")

    # ============ DÉTAIL PAR PRODUIT ============
    st.markdown(
        '<div style="font-size:1.15rem;font-weight:800;color:#F4F7FB;'
        'margin:12px 0 10px 0;">🔍 Analyse détaillée d\'un produit</div>',
        unsafe_allow_html=True,
    )

    produits_dispo = sorted(parcours_f["produit"].dropna().unique().tolist()) if not parcours_f.empty else []
    if not produits_dispo:
        st.info("Aucun produit disponible.")
        return

    produit_sel = st.selectbox("Sélectionner un produit", produits_dispo,
                               key="produit_select", label_visibility="collapsed")

    p_parcours = parcours_f[parcours_f["produit"] == produit_sel]
    p_contrats = contrats_f[contrats_f["produit"] == produit_sel] if "produit" in contrats_f.columns else pd.DataFrame()
    p_frictions = frictions_f[frictions_f["produit"] == produit_sel] if not frictions_f.empty else pd.DataFrame()
    p_reclam = reclamations_f[reclamations_f["produit"] == produit_sel] if not reclamations_f.empty else pd.DataFrame()
    p_evt = evenements_f[evenements_f["produit"] == produit_sel] if not evenements_f.empty else pd.DataFrame()

    # Fiche produit
    ref_row = produits_ref[produits_ref["produit"] == produit_sel]
    if not ref_row.empty:
        r = ref_row.iloc[0]
        st.markdown(
            f"""<div style="background:linear-gradient(135deg,#132B5C 0%,#0F2557 100%);border-radius:12px;padding:20px 24px;
            border-left:5px solid {NSIA_GOLD};box-shadow:0 4px 12px rgba(0,0,0,0.2);margin-bottom:16px;">
            <div style="font-size:1.1rem;font-weight:800;color:{NSIA_GOLD};margin-bottom:10px;">
            📦 Fiche produit — {produit_sel}</div>
            <div style="font-size:0.9rem;color:#F4F7FB;line-height:1.9;">
            <b>Catégorie :</b> {r.get('categorie','-')} &nbsp;|&nbsp;
            <b>Type de contrat :</b> {r.get('type_contrat','-')}<br/>
            <b>Objectif client :</b> {r.get('objectif_client','-')}<br/>
            <b>Éligibilité :</b> {r.get('eligibilite','-')} &nbsp;|&nbsp;
            <b>Mode de cotisation :</b> {r.get('mode_cotisation','-')}<br/>
            <b>Avance :</b> {r.get('avance','-')} &nbsp;|&nbsp;
            <b>Rachat partiel :</b> {r.get('rachat_partiel','-')} &nbsp;|&nbsp;
            <b>Prestation :</b> {r.get('prestation','-')}
            </div></div>""",
            unsafe_allow_html=True,
        )

    # 5 KPI produit
    d1, d2, d3, d4, d5 = st.columns(5)
    with d1:
        st.markdown(_kpi_card("Clients", f"{p_parcours['client_id'].nunique():,}".replace(",", " "),
                              "sur la période", "#F2B705", "👥"), unsafe_allow_html=True)
    with d2:
        st.markdown(_kpi_card("Contrats",
                              f"{p_contrats['contrat_id'].nunique() if not p_contrats.empty else 0:,}".replace(",", " "),
                              "actifs + clôturés", "#3B82C4", "📄"), unsafe_allow_html=True)
    with d3:
        conv_p = taux_conversion(p_parcours, data["clients"])
        color_conv = "#10B981" if conv_p >= 60 else ("#F2B705" if conv_p >= 40 else "#DC2626")
        st.markdown(_kpi_card("Conversion", f"{conv_p} %",
                              "taux du produit", color_conv, "🎯"), unsafe_allow_html=True)
    with d4:
        fric_p = taux_friction(p_parcours)
        color_fric = "#DC2626" if fric_p > 30 else ("#F2B705" if fric_p > 15 else "#10B981")
        st.markdown(_kpi_card("Friction", f"{fric_p} %",
                              "objectif < 15 %", color_fric, "⚠️"), unsafe_allow_html=True)
    with d5:
        st.markdown(_kpi_card("Réclamations", f"{len(p_reclam):,}".replace(",", " "),
                              "sur la période", "#DC2626" if len(p_reclam) > 10 else "#A9BDD1", "📣"),
                    unsafe_allow_html=True)

    st.write("")

    # Répartition + Canaux
    e1, e2 = st.columns(2)

    with e1:
        with card("📊 Répartition du parcours pour ce produit"):
            if not p_parcours.empty:
                rep = p_parcours["etape_parcours"].value_counts().reset_index()
                rep.columns = ["etape", "n"]
                rep = rep.sort_values("n", ascending=True)

                fig = go.Figure(go.Bar(
                    x=rep["n"], y=rep["etape"], orientation="h",
                    text=rep["n"], textposition="outside",
                    textfont=dict(size=11, color="#F2B705", family="Arial Black"),
                    marker=dict(color="#3B82C4"),
                ))
                fig.update_layout(
                    height=340, margin=dict(l=10, r=50, t=10, b=10),
                    yaxis=dict(categoryorder="total ascending", title="",
                               tickfont=dict(size=10, color="#F4F7FB")),
                    xaxis=dict(title="", showgrid=False,
                               range=[0, rep["n"].max() * 1.25] if not rep.empty else 10,
                               tickfont=dict(color="#F4F7FB")),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=False, font=dict(color="#F4F7FB"),
                )
                st.plotly_chart(fig, use_container_width=True)

    with e2:
        with card("🔀 Canaux & agences pour ce produit"):
            tab1, tab2 = st.tabs(["📞 Canaux", "🏢 Agences"])
            with tab1:
                if not p_parcours.empty:
                    can = p_parcours["canal"].value_counts().reset_index()
                    can.columns = ["canal", "n"]
                    can = can.sort_values("n", ascending=True)
                    fig = go.Figure(go.Bar(
                        x=can["n"], y=can["canal"], orientation="h",
                        text=can["n"], textposition="outside",
                        textfont=dict(size=11, color="#F2B705", family="Arial Black"),
                        marker=dict(color="#F2B705"),
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
            with tab2:
                if not p_parcours.empty and "agence" in p_parcours.columns:
                    ag = p_parcours["agence"].value_counts().reset_index().head(8)
                    ag.columns = ["agence", "n"]
                    ag = ag.sort_values("n", ascending=True)
                    fig = go.Figure(go.Bar(
                        x=ag["n"], y=ag["agence"], orientation="h",
                        text=ag["n"], textposition="outside",
                        textfont=dict(size=11, color="#F2B705", family="Arial Black"),
                        marker=dict(color="#3B82C4"),
                    ))
                    fig.update_layout(
                        height=300, margin=dict(l=10, r=50, t=10, b=10),
                        yaxis=dict(categoryorder="total ascending", title="",
                                   tickfont=dict(size=10, color="#F4F7FB")),
                        xaxis=dict(title="", showgrid=False,
                                   range=[0, ag["n"].max() * 1.25] if not ag.empty else 10,
                                   tickfont=dict(color="#F4F7FB")),
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                        showlegend=False, font=dict(color="#F4F7FB"),
                    )
                    st.plotly_chart(fig, use_container_width=True)

    st.write("")

    # 3 KPI événements
    f1, f2, f3 = st.columns(3)
    with f1:
        with card("💰 Rachats / Avances"):
            rachats = p_parcours[p_parcours["etape_parcours"] == "Avance / rachat"] if not p_parcours.empty else pd.DataFrame()
            nb_rachats = rachats["client_id"].nunique() if not rachats.empty else 0
            st.markdown(_kpi_card("Demandes", f"{nb_rachats}", "clients concernés", "#F2B705", "💰"),
                        unsafe_allow_html=True)
    with f2:
        with card("❌ Résiliations"):
            resil = p_parcours[p_parcours["etape_parcours"] == "Résiliation"] if not p_parcours.empty else pd.DataFrame()
            nb_resil = resil["client_id"].nunique() if not resil.empty else 0
            st.markdown(_kpi_card("Dossiers", f"{nb_resil}", "clients concernés", "#DC2626", "❌"),
                        unsafe_allow_html=True)
    with f3:
        with card("🛟 Sinistres"):
            sinistres = p_parcours[p_parcours["etape_parcours"] == "Sinistre"] if not p_parcours.empty else pd.DataFrame()
            nb_sin = sinistres["client_id"].nunique() if not sinistres.empty else 0
            st.markdown(_kpi_card("Déclarations", f"{nb_sin}", "clients concernés", "#F59E0B", "🛟"),
                        unsafe_allow_html=True)

    # ============ INSIGHT ============
    if not p_parcours.empty:
        conv_final = taux_conversion(p_parcours, data["clients"])
        fric_final = taux_friction(p_parcours)
        abandon_final = pct((p_parcours["issue_etape"] == "Abandon").sum(), len(p_parcours))

        insight_box(
            f"<b>À retenir sur « {produit_sel} » :</b> conversion de "
            f"<b>{conv_final} %</b>, friction de <b>{fric_final} %</b>, "
            f"abandon de <b>{abandon_final} %</b>. "
            f"{len(p_reclam)} réclamation(s) associée(s)."
        )