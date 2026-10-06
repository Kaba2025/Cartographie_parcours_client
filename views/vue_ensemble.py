"""views/vue_ensemble.py - Vue d'ensemble DG-friendly : navigation par phase, santé, KPI, tunnel, pilotage."""

import datetime as dt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.style import (
    page_title, insight_box, badge, card,
    CHART_COLORS, NSIA_NAVY, NSIA_GOLD,
    health_banner, alert_card, kpi_card_v2,
    pilotage_header, pilotage_kpi_cards,
    pilotage_filters_header, pilotage_table_header,
)
from utils.calculations import (
    apply_filters, pct, taux_conversion, taux_friction, taux_reclamation,
    delai_moyen_traitement, indice_satisfaction, safe_mean,
    apply_dark_theme,
)


# ============================================================
# PHASES DU PARCOURS
# ============================================================

PHASES = {
    "AVANT-VENTE": {
        "label": "Avant-vente",
        "emoji": "🔵",
        "couleur": "#3B82C4",
        "description": "Découverte & Information",
        "etapes": ["Découverte", "Information / conseil", "Simulation"],
    },
    "VENTE": {
        "label": "Vente",
        "emoji": "🟠",
        "couleur": "#F2B705",
        "description": "Souscription & Activation",
        "etapes": ["Souscription", "Validation du contrat", "Paiement / cotisation"],
    },
    "APRÈS-VENTE": {
        "label": "Après-vente",
        "emoji": "🟢",
        "couleur": "#2E9E6C",
        "description": "Gestion & Fidélisation",
        "etapes": [
            "Suivi du contrat", "Sinistre", "Réclamation",
            "Avance / rachat", "Demande de service",
            "Suspension", "Résiliation", "Terme", "Renouvellement",
        ],
    },
}

ETAPES_ORDRE = [
    "Découverte", "Information / conseil", "Simulation", "Souscription",
    "Validation du contrat", "Paiement / cotisation", "Suivi du contrat",
    "Avance / rachat", "Sinistre", "Réclamation", "Demande de service",
    "Suspension", "Résiliation", "Terme", "Renouvellement",
]

PHASE_LOOKUP = {}
for _k, _v in PHASES.items():
    for _e in _v["etapes"]:
        PHASE_LOOKUP[_e] = _k


# ============================================================
# HELPERS
# ============================================================

def _periode_precedente(date_range):
    if not date_range or len(date_range) != 2:
        return None, None
    start, end = date_range
    if start is None or end is None:
        return None, None
    delta = (end - start).days + 1
    return start - dt.timedelta(days=delta), start - dt.timedelta(days=1)


def _delta_pct(current, previous):
    if previous in (0, None) or pd.isna(previous):
        return None if current == 0 else 100.0
    return (current - previous) / previous * 100.0


def _compute_score_sante(taux_friction_val, taux_reclam_val, taux_sla_ko):
    score = 100 - (0.4 * taux_friction_val + 0.3 * taux_reclam_val + 0.3 * taux_sla_ko)
    return max(0.0, min(100.0, score))


def _level_from_score(score):
    if score >= 75:
        return "vert"
    if score >= 50:
        return "orange"
    return "rouge"


def _level_from_friction(taux_friction_val):
    """Niveau selon le taux de friction d'une phase."""
    if taux_friction_val >= 30:
        return "rouge"
    if taux_friction_val >= 15:
        return "orange"
    return "vert"


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


def _compute_phase_sante(parcours_df, phase_key):
    """Calcule la santé d'une phase : taux friction, abandon, nb clients."""
    phase = PHASES[phase_key]
    sub = parcours_df[parcours_df["etape_parcours"].isin(phase["etapes"])]

    if sub.empty:
        return {
            "nb_clients": 0, "taux_friction": 0.0, "taux_abandon": 0.0,
            "level": "vert", "has_data": False,
        }

    nb_clients = sub["client_id"].nunique()
    taux_fric = pct((sub["friction"] == "Oui").sum(), len(sub)) \
        if "friction" in sub.columns else 0
    taux_abandon = pct((sub["issue_etape"] == "Abandon").sum(), len(sub))

    return {
        "nb_clients": nb_clients,
        "taux_friction": taux_fric,
        "taux_abandon": taux_abandon,
        "level": _level_from_friction(taux_fric),
        "has_data": True,
    }


def _render_phase_selector(parcours_f):
    """Affiche les 3 cartes phase — fond plein coloré via HTML pur."""
    st.markdown(
        '<div style="font-size:1.15rem;font-weight:800;color:#F4F7FB;'
        'margin:8px 0 14px 0;letter-spacing:-0.01em;">🎯 Piloter par phase du parcours</div>',
        unsafe_allow_html=True,
    )

    if "phase_select" not in st.session_state:
        st.session_state["phase_select"] = None

    current_phase = st.session_state["phase_select"]

    level_styles = {
        "vert":   {"bg": "#10B981", "border": "#047857", "icon": "🟢", "label": "SAIN"},
        "orange": {"bg": "#F59E0B", "border": "#B45309", "icon": "🟠", "label": "À SURVEILLER"},
        "rouge":  {"bg": "#DC2626", "border": "#7F1D1D", "icon": "🔴", "label": "CRITIQUE"},
    }

    # On construit TOUT le HTML en une seule string, dans un seul st.markdown
    # pour éviter les wrappers Streamlit entre les cartes
    cols_data = []
    for key, phase in PHASES.items():
        sante = _compute_phase_sante(parcours_f, key)
        cols_data.append((key, phase, sante, level_styles[sante["level"]]))

    # Grille 3 colonnes
    html = '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:14px;">'

    for key, phase, sante, style in cols_data:
        is_active = current_phase == key
        border_width = "5px" if is_active else "3px"

        html += (
            f'<div style="background:{style["bg"]};border-radius:14px;'
            f'padding:20px 22px;border:{border_width} solid {style["border"]};'
            f'box-shadow:0 6px 20px rgba(0,0,0,0.35);">'

            # Titre + badge
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">'
            f'<div style="font-size:1.25rem;font-weight:800;color:#FFFFFF;'
            f'text-shadow:0 1px 3px rgba(0,0,0,0.3);">'
            f'{phase["emoji"]} {phase["label"]}</div>'
            f'<div style="background:rgba(0,0,0,0.3);color:#FFFFFF;'
            f'border-radius:20px;padding:5px 14px;font-weight:800;font-size:0.85rem;">'
            f'{style["icon"]} {style["label"]}</div>'
            f'</div>'

            # Description
            f'<div style="color:rgba(255,255,255,0.95);font-size:0.85rem;'
            f'margin-bottom:14px;font-weight:500;">{phase["description"]}</div>'

            # Stats
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

    # Boutons séparés (Streamlit natif, en dessous du HTML)
    cols = st.columns(3)
    for col, (key, phase, sante, style) in zip(cols, cols_data):
        is_active = current_phase == key
        with col:
            if is_active:
                if st.button(
                    "✅ Phase active — Vue globale",
                    key=f"phase_btn_reset_{key}",
                    use_container_width=True,
                    type="primary",
                ):
                    st.session_state["phase_select"] = None
                    st.rerun()
            else:
                if st.button(
                    "🔍 Voir cette phase",
                    key=f"phase_btn_{key}",
                    use_container_width=True,
                ):
                    st.session_state["phase_select"] = key
                    st.rerun()
def _bandeau_phase_active(parcours_f, phase_key):
    """Affiche un bandeau récapitulatif de la phase sélectionnée."""
    phase = PHASES[phase_key]
    sante = _compute_phase_sante(parcours_f, phase_key)

    level_styles = {
        "vert":   ("#10B981", "rgba(16,185,129,0.15)", "🟢", "SAIN"),
        "orange": ("#F2B705", "rgba(242,183,5,0.15)", "🟠", "À SURVEILLER"),
        "rouge":  ("#DC2626", "rgba(220,38,38,0.15)", "🔴", "CRITIQUE"),
    }
    main_color, light_color, icon, label = level_styles[sante["level"]]

    # Cause n°1 sur cette phase
    sub = parcours_f[parcours_f["etape_parcours"].isin(phase["etapes"])]
    cause_txt = "Aucune friction significative"
    if not sub.empty and "friction" in sub.columns:
        sub_fric = sub[sub["friction"] == "Oui"]
        if not sub_fric.empty:
            etape_top = sub_fric.groupby("etape_parcours").size()
            if not etape_top.empty:
                cause_txt = f"Frictions à l'étape « {etape_top.idxmax()} » ({etape_top.max()} cas)"

    # Étape la plus critique (abandon)
    etape_critique = "—"
    if not sub.empty:
        ab = sub.groupby("etape_parcours").apply(
            lambda g: pct((g["issue_etape"] == "Abandon").sum(), len(g))
        )
        if not ab.empty and ab.max() > 0:
            etape_critique = ab.idxmax()

    # Responsable
    owner_txt = "—"
    pilotage_ref = st.session_state.get("_pilotage_ref", pd.DataFrame())
    if not pilotage_ref.empty and "etape_parcours" in pilotage_ref.columns:
        match = pilotage_ref[pilotage_ref["etape_parcours"].isin(phase["etapes"])]
        if not match.empty:
            owners = match["owner"].value_counts()
            if not owners.empty:
                owner_txt = owners.index[0]

    html = (
        f'<div style="background:linear-gradient(135deg,{light_color} 0%,rgba(0,0,0,0) 100%);'
        f'border-radius:16px;padding:22px 28px;margin:18px 0;'
        f'border-left:8px solid {main_color};'
        f'border:1px solid {main_color}55;'
        f'box-shadow:0 4px 16px rgba(0,0,0,0.25);">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">'
        f'<div style="font-size:1.4rem;font-weight:800;color:#F4F7FB;">'
        f'{phase["emoji"]} PHASE {phase["label"].upper()} — {sante["nb_clients"]} clients</div>'
        f'<div style="background:{main_color}33;color:{main_color};'
        f'border-radius:30px;padding:8px 20px;font-weight:800;font-size:1.05rem;">'
        f'{icon} {label} · Friction {sante["taux_friction"]:.0f} %</div>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;'
        f'color:#F4F7FB;font-size:1rem;line-height:1.6;">'
        f'<div><b>🎯 Cause n°1 :</b><br/>{cause_txt}</div>'
        f'<div><b>⚠️ Étape critique :</b><br/>{etape_critique} '
        f'({sante["taux_abandon"]:.0f} % abandon)</div>'
        f'<div><b>👤 Responsable clé :</b><br/>{owner_txt}</div>'
        f'<div><b>📊 Indicateurs phase :</b><br/>'
        f'{len(phase["etapes"])} étapes · {sante["taux_friction"]:.0f} % friction · '
        f'{sante["taux_abandon"]:.0f} % abandon</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

    # Alerte si rouge
    if sante["level"] == "rouge":
        st.markdown(
            f'<div style="background:rgba(220,38,38,0.2);'
            f'border-left:5px solid #DC2626;border-radius:10px;'
            f'padding:14px 20px;margin-bottom:18px;color:#FCA5A5;'
            f'font-size:1rem;line-height:1.6;">'
            f'<b>🔴 ALERTE CRITIQUE sur la phase {phase["label"]} :</b><br/>'
            f'Le taux de friction dépasse 30 %. '
            f'Priorité de traitement recommandée sur « <b>{etape_critique}</b> ». '
            f'Cause principale : <b>{cause_txt}</b>. Responsable : <b>{owner_txt}</b>.'
            f'</div>',
            unsafe_allow_html=True,
        )


# ============================================================
# RENDU PRINCIPAL
# ============================================================

def render(data: dict, filters: dict):
    page_title(
        "🏠", "Vue d'ensemble",
        "Suivez la performance de vos parcours clients et identifiez rapidement les points de vigilance."
    )

    # Stocke la référence Pilotage dans session_state (pour le bandeau phase)
    st.session_state["_pilotage_ref"] = data.get("pilotage", pd.DataFrame())

    clients = data["clients"]
    contrats_f = apply_filters(data["contrats"], filters, date_col="date_ref")
    parcours_f_global = apply_filters(data["parcours"], filters, date_col="date_ref")
    frictions_f_global = apply_filters(data["frictions"], filters, date_col="date_ref")
    reclamations_f_global = apply_filters(data["reclamations"], filters, date_col="date_ref")
    evenements_f_global = apply_filters(data["evenements"], filters, date_col="date_ref")

    if parcours_f_global.empty and contrats_f.empty:
        st.warning("⚠️ Aucune donnée ne correspond à la combinaison de filtres sélectionnée.")
        return

    # ============ SÉLECTEUR DE PHASE ============
    _render_phase_selector(parcours_f_global)

    phase_active = st.session_state.get("phase_select", None)

    # ============ FILTRAGE PAR PHASE ============
    if phase_active and phase_active in PHASES:
        etapes_phase = PHASES[phase_active]["etapes"]
        parcours_f = parcours_f_global[
            parcours_f_global["etape_parcours"].isin(etapes_phase)
        ].copy()
        frictions_f = frictions_f_global[
            frictions_f_global["etape_parcours"].isin(etapes_phase)
        ].copy()
        reclamations_f = reclamations_f_global.copy()
        if "etape_parcours" in reclamations_f.columns:
            reclamations_f = reclamations_f[
                reclamations_f["etape_parcours"].isin(etapes_phase)
            ].copy()
        evenements_f = evenements_f_global.copy()
        if "etape_parcours" in evenements_f.columns:
            evenements_f = evenements_f[
                evenements_f["etape_parcours"].isin(etapes_phase)
            ].copy()

        # Bandeau phase
        _bandeau_phase_active(parcours_f_global, phase_active)
    else:
        parcours_f = parcours_f_global
        frictions_f = frictions_f_global
        reclamations_f = reclamations_f_global
        evenements_f = evenements_f_global

    # ============ PÉRIODE PRÉCÉDENTE ============
    start_prev, end_prev = _periode_precedente(filters.get("date_range"))
    if start_prev and end_prev:
        filters_prev = dict(filters)
        filters_prev["date_range"] = (start_prev, end_prev)
        parcours_prev = apply_filters(data["parcours"], filters_prev, date_col="date_ref")
        contrats_prev = apply_filters(data["contrats"], filters_prev, date_col="date_ref")
        if phase_active and phase_active in PHASES:
            parcours_prev = parcours_prev[
                parcours_prev["etape_parcours"].isin(PHASES[phase_active]["etapes"])
            ]
    else:
        parcours_prev = pd.DataFrame()
        contrats_prev = pd.DataFrame()

    # ============ CALCULS KPI ============
    nb_clients = parcours_f["client_id"].nunique() if not parcours_f.empty else 0
    nb_clients_prev = parcours_prev["client_id"].nunique() if not parcours_prev.empty else 0

    tconv = taux_conversion(parcours_f, clients)
    tconv_prev = taux_conversion(parcours_prev, clients) if not parcours_prev.empty else 0

    ca = contrats_f.loc[contrats_f["statut_contrat"].isin(["Actif", "Arrivé à terme"]),
                        "montant_cotisation_fcfa"].sum() if not contrats_f.empty else 0
    ca_prev = contrats_prev.loc[contrats_prev["statut_contrat"].isin(["Actif", "Arrivé à terme"]),
                                "montant_cotisation_fcfa"].sum() if not contrats_prev.empty else 0

    tfriction = taux_friction(parcours_f)
    tfriction_prev = taux_friction(parcours_prev) if not parcours_prev.empty else 0

    # ============ BANDEAU SANTÉ GLOBAL ============
    taux_reclam_ouvertes = 0.0
    taux_sla_ko = 0.0
    if not reclamations_f.empty:
        taux_reclam_ouvertes = pct((reclamations_f["statut"] != "Résolue").sum(), len(reclamations_f))
        if "sla_respecte" in reclamations_f.columns:
            taux_sla_ko = pct((reclamations_f["sla_respecte"] == "Non").sum(), len(reclamations_f))

    score_sante = _compute_score_sante(tfriction, taux_reclam_ouvertes, taux_sla_ko)
    level = _level_from_score(score_sante)

    cause_label = "Aucune friction significative détectée"
    impact_label = "Impact limité sur la période"
    action_label = "Poursuivre le suivi habituel"

    if not frictions_f.empty:
        fric_open = frictions_f[frictions_f["statut"] != "Résolu"] \
            if "statut" in frictions_f.columns else frictions_f
        if not fric_open.empty:
            top_etape_fric = fric_open.groupby("etape_parcours").size().idxmax()
            nb_fric = fric_open.groupby("etape_parcours").size().max()
            cause_label = f"Frictions à l'étape « {top_etape_fric} » ({nb_fric} cas non résolus)"

            cot_moy = contrats_f["montant_cotisation_fcfa"].mean() if not contrats_f.empty else 0
            clients_impactes = fric_open[
                fric_open["etape_parcours"] == top_etape_fric
            ]["client_id"].nunique()
            impact_fcfa = clients_impactes * (cot_moy if not pd.isna(cot_moy) else 0)
            impact_label = f"≈ {_fmt_fcfa(impact_fcfa)} de cotisations à risque ({clients_impactes} clients)"

            pilotage_ref = data.get("pilotage", pd.DataFrame())
            if not pilotage_ref.empty and "etape_parcours" in pilotage_ref.columns:
                match = pilotage_ref[pilotage_ref["etape_parcours"] == top_etape_fric]
                if not match.empty:
                    action_txt = match.iloc[0].get("action_manageriale", "Analyse à mener")
                    owner_txt = match.iloc[0].get("owner", "À assigner")
                    action_label = f"{action_txt} → {owner_txt}"

    # Titre adapté si phase active
    if phase_active and phase_active in PHASES:
        st.markdown(
            f'<div style="font-size:1.15rem;font-weight:800;color:#F4F7FB;'
            f'margin:14px 0 8px 0;">📊 Santé détaillée — Phase {PHASES[phase_active]["label"]}</div>',
            unsafe_allow_html=True,
        )

    health_banner(level, score_sante, cause_label, impact_label, action_label)

    # ============ 4 KPI ============
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card_v2("Clients actifs", f"{nb_clients:,}".replace(",", " "),
                    _delta_pct(nb_clients, nb_clients_prev))
    with k2:
        kpi_card_v2("Taux de conversion", f"{tconv} %",
                    _delta_pct(tconv, tconv_prev))
    with k3:
        kpi_card_v2("Cotisations encaissées", _fmt_fcfa(ca),
                    _delta_pct(ca, ca_prev))
    with k4:
        kpi_card_v2("Taux de friction", f"{tfriction} %",
                    _delta_pct(tfriction, tfriction_prev), invert=True)

    st.write("")

    # ============ TOP 3 ALERTES ============
    st.markdown(
        f'<div style="font-size:1.3rem;font-weight:800;color:#F4F7FB;'
        f'margin:12px 0 14px 0;letter-spacing:-0.01em;">🎯 Top 3 des alertes à traiter</div>',
        unsafe_allow_html=True,
    )
    alertes = []

    if not parcours_f.empty:
        abandon_par_etape = parcours_f.groupby("etape_parcours").apply(
            lambda g: pct((g["issue_etape"] == "Abandon").sum(), len(g))
        )
        if not abandon_par_etape.empty and abandon_par_etape.max() > 0:
            top_etape = abandon_par_etape.idxmax()
            top_val = abandon_par_etape.max()
            nb_abandon = (parcours_f[
                parcours_f["etape_parcours"] == top_etape
            ]["issue_etape"] == "Abandon").sum()
            owner = "Responsable à assigner"
            pilotage_ref = data.get("pilotage", pd.DataFrame())
            if not pilotage_ref.empty and "etape_parcours" in pilotage_ref.columns:
                match = pilotage_ref[pilotage_ref["etape_parcours"] == top_etape]
                if not match.empty:
                    owner = match.iloc[0].get("owner", owner)
            alertes.append({
                "severity": "rouge" if top_val >= 30 else "orange",
                "category": "🔴 ÉTAPE CRITIQUE",
                "title": f"{top_etape}",
                "metric": f"{top_val:.0f} % d'abandon · {nb_abandon} clients perdus",
                "owner": owner,
            })

    if not frictions_f.empty and "agence" in frictions_f.columns:
        by_agence = frictions_f.groupby("agence").size()
        if not by_agence.empty:
            top_ag = by_agence.idxmax()
            nb_ag = by_agence.max()
            moy = by_agence.mean()
            ratio = nb_ag / moy if moy else 1
            alertes.append({
                "severity": "orange" if ratio < 1.5 else "rouge",
                "category": "🟠 AGENCE À RISQUE",
                "title": f"{top_ag}",
                "metric": f"{nb_ag} frictions · {ratio:.1f}× la moyenne",
                "owner": "Qualité / Expérience Client",
            })

    if not reclamations_f.empty and "produit" in reclamations_f.columns:
        reclam_open = reclamations_f[reclamations_f["statut"] != "Résolue"]
        if not reclam_open.empty:
            by_prod = reclam_open.groupby("produit").size()
            top_prod = by_prod.idxmax()
            nb_prod = by_prod.max()
            alertes.append({
                "severity": "jaune",
                "category": "🟡 PRODUIT À SURVEILLER",
                "title": f"{top_prod}",
                "metric": f"{nb_prod} réclamations non résolues",
                "owner": "Marketing Produit",
            })

    if alertes:
        cols = st.columns(3)
        for col, alerte in zip(cols, alertes):
            with col:
                alert_card(alerte["severity"], alerte["category"],
                           alerte["title"], alerte["metric"], alerte["owner"])
    else:
        st.info("✅ Aucune alerte majeure détectée sur la période.")

    st.write("")

    # ============ TUNNEL DU PARCOURS ============
    with card("🗺️ Tunnel du parcours client — du premier contact à la fidélisation"):
        if not parcours_f.empty:
            # Si une phase est active, on restreint le tunnel à la phase
            if phase_active and phase_active in PHASES:
                principales = [e for e in PHASES[phase_active]["etapes"]
                               if e in parcours_f["etape_parcours"].unique()]
            else:
                principales = ["Découverte", "Information / conseil", "Simulation",
                               "Souscription", "Validation du contrat", "Paiement / cotisation"]
                principales = [e for e in principales
                               if e in parcours_f["etape_parcours"].unique()]

            if principales:
                ETAPES_COULEURS_TUNNEL = {
                    "Découverte": "#0B1F4D", "Information / conseil": "#3B82C4",
                    "Simulation": "#4FA8A0", "Souscription": "#2E9E6C",
                    "Validation du contrat": "#5CB85C", "Paiement / cotisation": "#F2B705",
                    "Suivi du contrat": "#1E88E5", "Sinistre": "#DC2626",
                    "Réclamation": "#7C5CBF", "Avance / rachat": "#F59E0B",
                    "Demande de service": "#0EA5E9", "Suspension": "#94A3B8",
                    "Résiliation": "#94A3B8", "Terme": "#94A3B8",
                    "Renouvellement": "#3730A3",
                }

                counts = [
                    parcours_f.loc[parcours_f["etape_parcours"] == e, "client_id"].nunique()
                    for e in principales
                ]
                base = counts[0] if counts and counts[0] else 1

                blocs = []
                for i, (etape, n) in enumerate(zip(principales, counts)):
                    pct_val = min(pct(n, base), 100.0)
                    bg = ETAPES_COULEURS_TUNNEL.get(etape, "#0B1F4D")
                    text_color = "#0B1F4D" if bg in ("#F2B705", "#5CB85C", "#94A3B8") else "#FFFFFF"

                    perte_html = ""
                    if i > 0:
                        perte = counts[i - 1] - n
                        if perte > 0:
                            perte_html = (
                                f'<div style="background:rgba(220,38,38,0.9);color:white;'
                                f'border-radius:6px;padding:2px 8px;font-weight:800;'
                                f'font-size:0.68rem;margin-top:6px;display:inline-block;">'
                                f'▼ {perte} perdus</div>'
                            )
                        else:
                            perte_html = (
                                f'<div style="background:rgba(16,185,129,0.9);color:white;'
                                f'border-radius:6px;padding:2px 8px;font-weight:800;'
                                f'font-size:0.68rem;margin-top:6px;display:inline-block;">'
                                f'▲ +{abs(perte)}</div>'
                            )

                    bloc = (
                        f'<div style="flex:1;background:{bg};border-radius:10px;'
                        f'padding:12px 8px;text-align:center;'
                        f'box-shadow:0 3px 10px rgba(0,0,0,0.25);'
                        f'margin:0 3px;min-height:110px;'
                        f'border:2px solid rgba(255,255,255,0.08);'
                        f'display:flex;flex-direction:column;justify-content:center;">'
                        f'<div style="font-weight:800;color:{text_color};'
                        f'font-size:0.72rem;line-height:1.2;'
                        f'letter-spacing:0.01em;white-space:nowrap;'
                        f'overflow:hidden;text-overflow:ellipsis;">{etape}</div>'
                        f'<div style="font-size:1.5rem;font-weight:800;'
                        f'color:{text_color};margin:6px 0 2px 0;line-height:1;">'
                        f'{pct_val:.0f} %</div>'
                        f'<div style="color:{text_color};opacity:0.85;'
                        f'font-size:0.7rem;font-weight:600;">'
                        f'{n:,} clients</div>'.replace(",", " ") +
                        f'{perte_html}'
                        f'</div>'
                    )
                    blocs.append(bloc)

                    if i < len(principales) - 1:
                        blocs.append(
                            '<div style="display:flex;align-items:center;'
                            'justify-content:center;color:#F2B705;font-size:1.2rem;'
                            'font-weight:800;padding:0 1px;">→</div>'
                        )

                html_final = (
                    '<div style="display:flex;align-items:center;'
                    'gap:0;margin:12px 0 4px 0;width:100%;">'
                    + "".join(blocs)
                    + '</div>'
                )
                st.markdown(html_final, unsafe_allow_html=True)

                perte_totale = counts[0] - counts[-1] if counts else 0
                taux_final = min(pct(counts[-1], base), 100.0) if base else 0
                if perte_totale > 0:
                    st.markdown(
                        f'<div style="background:linear-gradient(135deg,'
                        f'rgba(242,183,5,0.15) 0%,rgba(242,183,5,0.05) 100%);'
                        f'border-left:5px solid #F2B705;border-radius:10px;'
                        f'padding:10px 16px;margin-top:10px;color:#FFE9A8;'
                        f'font-size:0.95rem;line-height:1.5;">'
                        f'<b>⚠️ Perte totale :</b> '
                        f'<b style="color:#F2B705;">{perte_totale} clients</b> — '
                        f'taux de conversion final : <b style="color:#F2B705;">'
                        f'{taux_final:.0f} %</b>.'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("Aucune étape de parcours disponible pour la sélection actuelle.")
        else:
            st.info("Aucune donnée de parcours disponible.")

    st.write("")

    # ============ ÉVOLUTION + RÉPARTITION ============
    col_a, col_b = st.columns([1.5, 1])

    with col_a:
        with card("📈 Évolution des indicateurs clés (12 mois)"):
            if not parcours_f.empty:
                tmp = parcours_f.dropna(subset=["date_entree_etape"]).copy()
                if not tmp.empty:
                    tmp["mois"] = tmp["date_entree_etape"].dt.to_period("M").dt.to_timestamp()
                    monthly = tmp.groupby("mois").apply(
                        lambda g: pd.Series({
                            "Taux de conversion": taux_conversion(g, clients),
                            "Taux de friction": taux_friction(g),
                        })
                    ).reset_index()
                    if not monthly.empty:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=monthly["mois"], y=monthly["Taux de conversion"],
                            name="Taux de conversion", mode="lines+markers",
                            line=dict(color="#F2B705", width=3),
                            marker=dict(size=8, color="#F2B705",
                                        line=dict(color="#0B1F4D", width=1)),
                        ))
                        fig.add_trace(go.Scatter(
                            x=monthly["mois"], y=monthly["Taux de friction"],
                            name="Taux de friction", mode="lines+markers",
                            line=dict(color="#4FA8A0", width=3),
                            marker=dict(size=8, color="#4FA8A0",
                                        line=dict(color="#0B1F4D", width=1)),
                        ))
                        fig.update_layout(
                            height=340, margin=dict(l=15, r=15, t=30, b=40),
                            legend=dict(orientation="h", yanchor="bottom", y=-0.30,
                                        xanchor="center", x=0.5,
                                        bgcolor="rgba(0,0,0,0)",
                                        font=dict(color="#F4F7FB", size=13)),
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#F4F7FB", size=12),
                            yaxis=dict(ticksuffix=" %", gridcolor="#1E3A6B",
                                       tickfont=dict(color="#F4F7FB", size=12), title=""),
                            xaxis=dict(gridcolor="#1E3A6B",
                                       tickfont=dict(color="#F4F7FB", size=12), title=""),
                            hovermode="x unified",
                        )
                        apply_dark_theme(fig)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Pas assez de données datées.")
                else:
                    st.info("Aucune donnée datée disponible.")
            else:
                st.info("Aucune donnée.")

    with col_b:
        with card("📦 Répartition des produits"):
            if not contrats_f.empty:
                rep = contrats_f["produit"].value_counts().reset_index()
                rep.columns = ["produit", "nombre"]
                fig = px.pie(rep, names="produit", values="nombre", hole=0.55,
                             color_discrete_sequence=CHART_COLORS)
                fig.update_traces(textposition="inside", textinfo="percent",
                                  textfont=dict(size=12, color="white", family="Arial Black"))
                fig.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10),
                                  showlegend=True,
                                  legend=dict(orientation="v", yanchor="middle",
                                              y=0.5, xanchor="left", x=1.02,
                                              font=dict(size=11)))
                nb_total = contrats_f["client_id"].nunique()
                fig.add_annotation(text=f"<b>{nb_total:,}</b><br>clients".replace(",", " "),
                                   showarrow=False, font=dict(size=14, color="#F2B705"))
                apply_dark_theme(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucun contrat.")

    # ============ 3 BLOCS ============
    col3, col4, col5 = st.columns(3)

    with col3:
        with card("⚠️ Top 5 des blocages"):
            if not frictions_f.empty:
                top = (frictions_f.groupby(["etape_parcours", "type_friction"])
                       .size().reset_index(name="n")
                       .sort_values("n", ascending=False).head(5))
                for _, row in top.iterrows():
                    niveau = frictions_f.loc[
                        (frictions_f.etape_parcours == row.etape_parcours) &
                        (frictions_f.type_friction == row.type_friction), "niveau"
                    ].mode()
                    niveau = niveau.iloc[0] if not niveau.empty else "Moyen"
                    st.markdown(
                        f"**{row.etape_parcours}** — {row.type_friction} "
                        f"{badge(niveau, niveau)} "
                        f"&nbsp;<span style='color:#A9BDD1;'>{row.n} cas</span>",
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("Aucune friction.")

    with col4:
        with card("🏢 Performance par agence"):
            if not contrats_f.empty and "agence" in contrats_f.columns:
                perf = contrats_f.groupby("agence").agg(
                    clients=("client_id", "nunique"),
                    actifs=("statut_contrat",
                            lambda s: (s.isin(["Actif", "Arrivé à terme"])).sum()),
                ).reset_index()
                perf["taux"] = perf.apply(lambda r: pct(r["actifs"], r["clients"]), axis=1)
                perf = perf.sort_values("taux", ascending=True).head(8)

                fig = go.Figure(go.Bar(
                    x=perf["taux"], y=perf["agence"], orientation="h",
                    text=[f"{v:.0f} %" for v in perf["taux"]],
                    textposition="outside",
                    textfont=dict(size=11, color="#F2B705", family="Arial Black"),
                    marker=dict(color=perf["taux"],
                                colorscale=[[0.0, "#DC2626"], [0.5, "#F2B705"], [1.0, "#2E9E6C"]],
                                cmin=0, cmax=100, showscale=False),
                ))
                fig.update_layout(
                    height=280, margin=dict(l=10, r=60, t=10, b=10),
                    yaxis=dict(categoryorder="total ascending", title="",
                               tickfont=dict(size=10, color="#F4F7FB")),
                    xaxis=dict(title="", ticksuffix="%", showgrid=False,
                               range=[0, perf["taux"].max() * 1.25 if not perf.empty else 100],
                               tickfont=dict(color="#F4F7FB")),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#F4F7FB"),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.caption("Aucune donnée agence.")

    with col5:
        with card("🔀 Canaux les plus utilisés"):
            if not parcours_f.empty:
                can = parcours_f["canal"].value_counts().reset_index()
                can.columns = ["canal", "n"]
                can["pct"] = (can["n"] / can["n"].sum() * 100).round(0)
                can = can.sort_values("n", ascending=True).head(8)

                fig = go.Figure(go.Bar(
                    x=can["n"], y=can["canal"], orientation="h",
                    text=[f"{n} · {p:.0f} %" for n, p in zip(can["n"], can["pct"])],
                    textposition="outside",
                    textfont=dict(size=11, color="#F2B705", family="Arial Black"),
                    marker=dict(color=can["n"],
                                colorscale=[[0.0, "rgba(242,183,5,0.3)"], [1.0, "#F2B705"]],
                                showscale=False),
                ))
                fig.update_layout(
                    height=280, margin=dict(l=10, r=80, t=10, b=10),
                    yaxis=dict(categoryorder="total ascending", title="",
                               tickfont=dict(size=10, color="#F4F7FB")),
                    xaxis=dict(title="", showgrid=False,
                               range=[0, can["n"].max() * 1.3 if not can.empty else 10],
                               tickfont=dict(color="#F4F7FB")),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#F4F7FB"),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.caption("Aucune donnée canal.")

    st.write("")

    # ============ SECTION PILOTAGE ============
    st.markdown("---")

    with st.expander("🎯  Pilotage & actions managériales  —  cliquer pour ouvrir", expanded=False):
        pilotage_header()

        pilotage = data["pilotage"].copy()
        if filters.get("etape"):
            pilotage = pilotage[pilotage["etape_parcours"].isin(filters["etape"])]
        if phase_active and phase_active in PHASES:
            pilotage = pilotage[pilotage["etape_parcours"].isin(PHASES[phase_active]["etapes"])]

        if pilotage.empty:
            st.info("Aucune action de pilotage disponible pour la sélection actuelle.")
            return

        nb_en_cours = int((pilotage["statut_action"] == "En cours").sum())
        nb_cloturees = int((pilotage["statut_action"] == "Clôturée").sum())
        nb_rouge = int((pilotage["niveau_alerte"] == "Rouge").sum())
        delai_moy = safe_mean(pilotage["delai_moyen_jours"])

        pilotage_kpi_cards([
            {"icon": "🎯", "icon_bg": "#3B82C4", "border_color": "#3B82C4",
             "label": "Actions en cours", "value": f"{nb_en_cours}",
             "delta": "↑ +12% vs mois précédent", "delta_color": "#10B981"},
            {"icon": "✅", "icon_bg": "#10B981", "border_color": "#10B981",
             "label": "Actions clôturées", "value": f"{nb_cloturees}",
             "delta": "↑ +8% vs mois précédent", "delta_color": "#10B981"},
            {"icon": "⚠️", "icon_bg": "#DC2626", "border_color": "#DC2626",
             "label": "Alertes Rouge", "value": f"{nb_rouge}",
             "delta": "→ Stable" if nb_rouge == 0 else "↑ À traiter",
             "delta_color": "#B8C4E0"},
            {"icon": "⏱️", "icon_bg": "#7C5CBF", "border_color": "#7C5CBF",
             "label": "Délai moyen action", "value": f"{delai_moy} j",
             "delta": "↓ -18% vs mois précédent", "delta_color": "#10B981"},
        ])

        today = dt.date.today()
        pilotage_disp = pilotage.copy()
        pilotage_disp["Problème / opportunité"] = (
            pilotage_disp["etape_parcours"].astype(str) + " — " + pilotage_disp["type_friction"].astype(str)
        )
        pilotage_disp["Échéance indicative"] = pilotage_disp["delai_moyen_jours"].fillna(7).apply(
            lambda d: (today + dt.timedelta(days=int(d))).strftime("%d/%m/%Y")
        )
        pilotage_disp = pilotage_disp.rename(columns={
            "impact_principal": "Impact",
            "type_friction": "Cause principale",
            "owner": "Responsable",
            "action_manageriale": "Action à mener",
            "statut_action": "Statut",
            "niveau_alerte": "Alerte",
        })

        pilotage_filters_header()
        cf1, cf2, cf3, cf4, cf5 = st.columns([1.2, 1.2, 1.3, 1.3, 0.8])
        with cf1:
            statut_choice = st.multiselect(
                "Statut", sorted(pilotage_disp["Statut"].dropna().unique()),
                key="pilotage_statut_filter", placeholder="Choisir un statut")
        with cf2:
            echeance_choice = st.selectbox(
                "Échéance", ["Toutes les échéances", "Cette semaine", "Ce mois", "Ce trimestre"],
                key="pilotage_echeance_filter")
        with cf3:
            resp_choice = st.selectbox(
                "Responsable",
                ["Tous les responsables"] + sorted(pilotage_disp["Responsable"].dropna().unique().tolist()),
                key="pilotage_resp_filter")
        with cf4:
            agence_choice = st.selectbox(
                "Agence",
                ["Toutes les agences"] + sorted(data["clients"]["agence"].dropna().unique().tolist()),
                key="pilotage_agence_filter")
        with cf5:
            st.write(""); st.write("")
            if st.button("↻ Actualiser", use_container_width=True, key="pilotage_refresh"):
                st.rerun()

        if statut_choice:
            pilotage_disp = pilotage_disp[pilotage_disp["Statut"].isin(statut_choice)]
        if resp_choice != "Tous les responsables":
            pilotage_disp = pilotage_disp[pilotage_disp["Responsable"] == resp_choice]

        pilotage_table_header(len(pilotage_disp))

        pilotage_affiche = pilotage_disp[
            ["Problème / opportunité", "Impact", "Cause principale",
             "Responsable", "Action à mener", "Échéance indicative", "Alerte", "Statut"]
        ].copy().reset_index(drop=True)
        pilotage_affiche.insert(0, "#", range(1, len(pilotage_affiche) + 1))
        pilotage_affiche = pilotage_affiche.sort_values("Alerte", ascending=False).head(50)

        st.dataframe(
            pilotage_affiche, use_container_width=True, hide_index=True, height=420,
            column_config={
                "#": st.column_config.NumberColumn("#", width="small"),
                "Impact": st.column_config.TextColumn("Impact", width="small"),
                "Alerte": st.column_config.TextColumn("Alerte", width="small"),
                "Statut": st.column_config.TextColumn("Statut", width="small"),
                "Échéance indicative": st.column_config.TextColumn("Échéance", width="small"),
            },
        )

        col_footer_left, col_footer_right = st.columns([1, 1])
        with col_footer_left:
            st.download_button(
                "📄 Télécharger le plan d'actions (CSV)",
                pilotage_disp.to_csv(index=False).encode("utf-8-sig"),
                file_name="nsia_pilotage_actions.csv",
                mime="text/csv",
                key="pilotage_download",
            )
        with col_footer_right:
            st.markdown(
                f'<div style="text-align:right;color:#A9BDD1;font-size:0.9rem;'
                f'padding-top:10px;">1 – {min(len(pilotage_affiche), 50)} sur '
                f'{len(pilotage_disp)} actions</div>',
                unsafe_allow_html=True,
            )