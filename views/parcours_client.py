"""views/parcours_client.py - Parcours client : phases colorées + sous-étapes + graphiques dark."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.style import (
    page_title, insight_box, card,
    CHART_COLORS, NSIA_NAVY, NSIA_GOLD,
    kpi_card_v2,
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

ETAPES_COULEURS = {
    "Découverte": "#0B1F4D",
    "Information / conseil": "#3B82C4",
    "Simulation": "#4FA8A0",
    "Souscription": "#2E9E6C",
    "Validation du contrat": "#5CB85C",
    "Paiement / cotisation": "#F2B705",
    "Suivi du contrat": "#1E88E5",
    "Sinistre": "#DC2626",
    "Réclamation": "#7C5CBF",
    "Avance / rachat": "#F59E0B",
    "Demande de service": "#0EA5E9",
    "Suspension": "#94A3B8",
    "Résiliation": "#94A3B8",
    "Terme": "#94A3B8",
    "Renouvellement": "#3730A3",
}

ETAPES_ICONES = {
    "Découverte": "🔎", "Information / conseil": "ℹ️", "Simulation": "🧮",
    "Souscription": "📝", "Validation du contrat": "✅", "Paiement / cotisation": "💳",
    "Suivi du contrat": "📊", "Avance / rachat": "💰", "Sinistre": "🛟",
    "Réclamation": "💬", "Demande de service": "🛎️", "Suspension": "⏸️",
    "Résiliation": "❌", "Terme": "🏁", "Renouvellement": "🔄",
}


# ============================================================
# HELPERS
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
        return {"nb_clients": 0, "taux_friction": 0.0, "taux_abandon": 0.0,
                "level": "vert", "has_data": False}
    nb_clients = sub["client_id"].nunique()
    taux_fric = pct((sub["friction"] == "Oui").sum(), len(sub)) \
        if "friction" in sub.columns else 0
    taux_abandon = pct((sub["issue_etape"] == "Abandon").sum(), len(sub))
    return {"nb_clients": nb_clients, "taux_friction": taux_fric,
            "taux_abandon": taux_abandon,
            "level": _level_from_friction(taux_fric), "has_data": True}


def _render_phase_selector(parcours_f, session_key):
    """Affiche les 3 cartes phases — fond plein coloré selon niveau."""
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

    # HTML en 1 SEUL bloc (pas de wrappers Streamlit)
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
            f'font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">Abandon</div>'
            f'<div style="color:#FFFFFF;font-size:1.2rem;font-weight:800;'
            f'line-height:1.1;margin-top:3px;text-shadow:0 2px 4px rgba(0,0,0,0.25);">'
            f'{sante["taux_abandon"]:.0f} %</div></div>'
            f'<div><div style="color:rgba(255,255,255,0.9);font-size:0.72rem;'
            f'font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">Étapes</div>'
            f'<div style="color:#FFFFFF;font-size:1.2rem;font-weight:800;'
            f'line-height:1.1;margin-top:3px;text-shadow:0 2px 4px rgba(0,0,0,0.25);">'
            f'{len(phase["etapes"])}</div></div>'
            f'</div></div>'
        )
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    # Boutons Streamlit natifs
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
    """Bandeau récapitulatif de la phase sélectionnée."""
    phase = PHASES[phase_key]
    sante = _compute_phase_sante(parcours_f, phase_key)

    level_styles = {
        "vert":   ("#10B981", "rgba(16,185,129,0.15)", "🟢", "SAIN"),
        "orange": ("#F2B705", "rgba(242,183,5,0.15)", "🟠", "À SURVEILLER"),
        "rouge":  ("#DC2626", "rgba(220,38,38,0.15)", "🔴", "CRITIQUE"),
    }
    main_color, light_color, icon, label = level_styles[sante["level"]]

    sub = parcours_f[parcours_f["etape_parcours"].isin(phase["etapes"])]

    cause_txt = "Aucune friction significative"
    if not sub.empty and "friction" in sub.columns:
        sub_fric = sub[sub["friction"] == "Oui"]
        if not sub_fric.empty:
            etape_top = sub_fric.groupby("etape_parcours").size()
            if not etape_top.empty:
                cause_txt = f"Frictions à l'étape « {etape_top.idxmax()} » ({etape_top.max()} cas)"

    etape_critique = "—"
    if not sub.empty:
        ab = sub.groupby("etape_parcours").apply(
            lambda g: pct((g["issue_etape"] == "Abandon").sum(), len(g))
        )
        if not ab.empty and ab.max() > 0:
            etape_critique = ab.idxmax()

    html = (
        f'<div style="background:linear-gradient(135deg,{light_color} 0%,rgba(0,0,0,0) 100%);'
        f'border-radius:16px;padding:20px 26px;margin:16px 0;'
        f'border-left:8px solid {main_color};border:1px solid {main_color}55;'
        f'box-shadow:0 4px 16px rgba(0,0,0,0.25);">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
        f'<div style="font-size:1.3rem;font-weight:800;color:#F4F7FB;">'
        f'{phase["emoji"]} PHASE {phase["label"].upper()} — {sante["nb_clients"]} clients</div>'
        f'<div style="background:{main_color}33;color:{main_color};'
        f'border-radius:30px;padding:8px 20px;font-weight:800;font-size:1rem;">'
        f'{icon} {label} · Friction {sante["taux_friction"]:.0f} %</div>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;'
        f'color:#F4F7FB;font-size:1rem;line-height:1.6;">'
        f'<div><b>🎯 Cause n°1 :</b><br/>{cause_txt}</div>'
        f'<div><b>⚠️ Étape critique :</b><br/>{etape_critique} '
        f'({sante["taux_abandon"]:.0f} % abandon)</div>'
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
            f'taux de friction > 30 %. Priorité : « <b>{etape_critique}</b> ». '
            f'Cause : <b>{cause_txt}</b>.'
            f'</div>',
            unsafe_allow_html=True,
        )


# ============================================================
# RENDU PRINCIPAL
# ============================================================

def render(data: dict, filters: dict):
    page_title(
        "🗺️", "Parcours client",
        "Visualisez le parcours complet de vos clients, de la découverte à la fidélisation."
    )

    parcours_f_global = apply_filters(data["parcours"], filters, date_col="date_ref")
    frictions_f_global = apply_filters(data["frictions"], filters, date_col="date_ref")
    clients_df = data["clients"]

    if parcours_f_global.empty:
        st.warning("⚠️ Aucune donnée de parcours pour la combinaison de filtres actuelle.")
        return

    # ============ SÉLECTEUR DE PHASE ============
    _render_phase_selector(parcours_f_global, "parcours_phase_select")

    phase_active = st.session_state.get("parcours_phase_select", None)

    # ============ FILTRAGE PAR PHASE ============
    if phase_active and phase_active in PHASES:
        etapes_phase = PHASES[phase_active]["etapes"]
        parcours_f = parcours_f_global[
            parcours_f_global["etape_parcours"].isin(etapes_phase)
        ].copy()
        frictions_f = frictions_f_global[
            frictions_f_global["etape_parcours"].isin(etapes_phase)
        ].copy()
        _bandeau_phase_active(parcours_f_global, phase_active)
    else:
        parcours_f = parcours_f_global
        frictions_f = frictions_f_global

    # ============ 4 KPI ============
    nb_clients = parcours_f["client_id"].nunique()
    nb_etapes = parcours_f["etape_parcours"].nunique()
    taux_abandon = pct((parcours_f["issue_etape"] == "Abandon").sum(), len(parcours_f))
    taux_fric = pct((parcours_f["friction"] == "Oui").sum(), len(parcours_f)) \
        if "friction" in parcours_f.columns else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card_v2("Clients concernés", f"{nb_clients:,}".replace(",", " "), None)
    with k2:
        kpi_card_v2("Étapes actives", f"{nb_etapes} / 15", None)
    with k3:
        kpi_card_v2("Taux d'abandon", f"{taux_abandon} %", None, invert=True)
    with k4:
        kpi_card_v2("Taux de friction", f"{taux_fric} %", None, invert=True)

    st.write("")

    # ============ SÉLECTION D'ÉTAPE ============
    etapes_dispo = [e for e in (PHASES[phase_active]["etapes"] if phase_active and phase_active in PHASES
                                else list(ETAPES_ICONES.keys()))
                    if e in parcours_f["etape_parcours"].unique()]

    if not etapes_dispo:
        st.info("Aucune étape disponible dans cette phase.")
        return

    st.markdown(
        f'<div style="font-size:1.15rem;font-weight:800;color:#F4F7FB;'
        f'margin:14px 0 10px 0;">👉 Explorer une étape en détail</div>',
        unsafe_allow_html=True,
    )

    etape_state_key = f"etape_phase_{phase_active}"
    if etape_state_key not in st.session_state or \
            st.session_state[etape_state_key] not in etapes_dispo:
        st.session_state[etape_state_key] = etapes_dispo[0]

    cols_etapes = st.columns(min(len(etapes_dispo), 6))
    for i, etape in enumerate(etapes_dispo):
        with cols_etapes[i % len(cols_etapes)]:
            is_active = st.session_state[etape_state_key] == etape
            if st.button(
                f"{ETAPES_ICONES.get(etape, '•')} {etape}",
                key=f"btn_etape_{phase_active}_{etape}",
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                st.session_state[etape_state_key] = etape
                st.rerun()

    etape_sel = st.session_state[etape_state_key]
    sub = parcours_f[parcours_f["etape_parcours"] == etape_sel]
    total_clients_etape = sub["client_id"].nunique()

    st.write("")

    # ============ DÉTAIL SOUS-ÉTAPES ============
    st.markdown(
        f'<div style="font-size:1.15rem;font-weight:800;color:#F4F7FB;'
        f'margin:12px 0 12px 0;">🔬 Étape « {etape_sel} » — '
        f'<span style="font-weight:500;color:#A9BDD1;font-size:0.9rem;">'
        f'{total_clients_etape:,} clients concernés</span></div>'.replace(",", " "),
        unsafe_allow_html=True,
    )

    sous_etapes = sub["sous_etape"].dropna().unique().tolist()
    if not sous_etapes:
        st.info("Aucune sous-étape enregistrée pour cette étape.")
        return

    # ===== Cartes sous-étapes =====
    with card("📋 Sous-étapes"):
        n_cols_sub = min(len(sous_etapes), 4)
        cols_sub = st.columns(n_cols_sub)

        stats = {}
        for i, se in enumerate(sous_etapes):
            se_df = sub[sub["sous_etape"] == se]
            n = se_df["client_id"].nunique()
            duree = safe_mean(se_df["duree_etape_jours"])
            friction_pct = pct((se_df["friction"] == "Oui").sum(), len(se_df))
            abandon_pct = pct((se_df["issue_etape"] == "Abandon").sum(), len(se_df))
            stats[se] = dict(n=n, duree=duree, friction=friction_pct,
                             abandon=abandon_pct,
                             pct_total=pct(n, total_clients_etape))

            border = "#DC2626" if abandon_pct >= 15 else (
                "#F2B705" if abandon_pct >= 5 else "#10B981"
            )
            with cols_sub[i % n_cols_sub]:
                st.markdown(
                    f'<div style="background:linear-gradient(135deg,#132B5C 0%,#0F2557 100%);'
                    f'border-radius:12px;padding:16px;border-left:5px solid {border};'
                    f'border-top:1px solid #1E3A6B;border-right:1px solid #1E3A6B;'
                    f'border-bottom:1px solid #1E3A6B;margin-bottom:10px;'
                    f'min-height:140px;">'
                    f'<div style="font-weight:800;color:#F4F7FB;'
                    f'font-size:0.9rem;min-height:2.4em;line-height:1.25;">{se}</div>'
                    f'<div style="font-size:1.5rem;font-weight:800;'
                    f'color:#F2B705;margin:6px 0 2px 0;">{n}</div>'
                    f'<div style="color:#A9BDD1;font-size:0.78rem;">'
                    f'clients · {stats[se]["pct_total"]} %</div>'
                    f'<div style="color:#A9BDD1;font-size:0.75rem;'
                    f'margin-top:4px;">⏱ {duree:.1f} j</div>'
                    f'<div style="background:{border};color:white;'
                    f'border-radius:6px;padding:3px 10px;font-weight:700;'
                    f'font-size:0.72rem;margin-top:8px;display:inline-block;">'
                    f'{abandon_pct} % abandon</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ===== Détail sous-étape =====
    with card("🔬 Détail par sous-étape"):
        se_choice = st.radio(
            "Choisir une sous-étape", sous_etapes,
            horizontal=True, key=f"se_radio_{etape_sel}",
        )
        d = stats[se_choice]
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Clients", f"{d['n']:,}".replace(",", " "))
        m2.metric("% total", f"{d['pct_total']} %")
        m3.metric("Délai moyen", f"{d['duree']} j")
        m4.metric("Friction", f"{d['friction']} %")
        m5.metric("Abandon", f"{d['abandon']} %")

    st.write("")

    # ===== 3 graphiques dark =====
    se_df = sub[sub["sous_etape"] == se_choice]
    c1, c2, c3 = st.columns(3)

    with c1:
        with card("📞 Canaux utilisés"):
            can = se_df["canal"].value_counts().reset_index()
            can.columns = ["canal", "n"]
            can = can.sort_values("n", ascending=True).head(6)
            if not can.empty:
                fig = go.Figure(go.Bar(
                    x=can["n"], y=can["canal"], orientation="h",
                    text=can["n"], textposition="outside",
                    textfont=dict(size=12, color="#F2B705", family="Arial Black"),
                    marker=dict(color="#3B82C4"),
                    hovertemplate="<b>%{y}</b><br>%{x} interactions<extra></extra>",
                ))
                fig.update_layout(
                    height=300, margin=dict(l=5, r=50, t=10, b=10),
                    yaxis=dict(categoryorder="total ascending", title="",
                               tickfont=dict(size=11, color="#F4F7FB")),
                    xaxis=dict(title="", showgrid=False,
                               range=[0, can["n"].max() * 1.3] if not can.empty else 10,
                               tickfont=dict(color="#F4F7FB")),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#F4F7FB"),
                )
                apply_dark_theme(fig)
                st.plotly_chart(fig, use_container_width=True)

    with c2:
        with card("📦 Produits concernés"):
            pr = se_df["produit"].value_counts().reset_index()
            pr.columns = ["produit", "n"]
            pr = pr.sort_values("n", ascending=True).head(6)
            if not pr.empty:
                fig = go.Figure(go.Bar(
                    x=pr["n"], y=pr["produit"], orientation="h",
                    text=pr["n"], textposition="outside",
                    textfont=dict(size=12, color="#F2B705", family="Arial Black"),
                    marker=dict(color="#F2B705"),
                    hovertemplate="<b>%{y}</b><br>%{x} interactions<extra></extra>",
                ))
                fig.update_layout(
                    height=300, margin=dict(l=5, r=50, t=10, b=10),
                    yaxis=dict(categoryorder="total ascending", title="",
                               tickfont=dict(size=11, color="#F4F7FB")),
                    xaxis=dict(title="", showgrid=False,
                               range=[0, pr["n"].max() * 1.3] if not pr.empty else 10,
                               tickfont=dict(color="#F4F7FB")),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#F4F7FB"),
                )
                apply_dark_theme(fig)
                st.plotly_chart(fig, use_container_width=True)

    with c3:
        with card("⚠️ Niveau de friction"):
            fr = se_df["niveau_friction"].value_counts().reset_index()
            fr.columns = ["niveau", "n"]
            if not fr.empty:
                fig = px.pie(
                    fr, names="niveau", values="n", hole=0.55,
                    color_discrete_sequence=CHART_COLORS,
                )
                fig.update_traces(
                    textposition="inside", textinfo="percent",
                    textfont=dict(size=13, color="white", family="Arial Black"),
                )
                fig.update_layout(
                    height=300, margin=dict(l=5, r=5, t=10, b=10),
                    showlegend=True,
                    legend=dict(font=dict(size=11, color="#F4F7FB"), orientation="v"),
                )
                apply_dark_theme(fig)
                st.plotly_chart(fig, use_container_width=True)

    # ============ INSIGHT ============
    st.write("")
    if stats:
        worst_se = max(stats, key=lambda k: stats[k]["abandon"])
        top_cause = None
        fric_etape_all = frictions_f[frictions_f["etape_parcours"] == etape_sel]
        if not fric_etape_all.empty:
            top_cause = fric_etape_all["cause_racine"].mode().iloc[0]

        texte = (
            f"<b>À retenir :</b> la sous-étape « {worst_se} » enregistre "
            f"le taux d'abandon le plus élevé ({stats[worst_se]['abandon']} %)."
        )
        if top_cause:
            texte += f" Cause principale : <b>{top_cause}</b>."
        insight_box(texte)