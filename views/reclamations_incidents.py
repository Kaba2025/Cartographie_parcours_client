"""views/reclamations_incidents.py - Réclamations & Incidents : phases colorées + analyse."""

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

STATUT_COULEURS = {
    "Ouverte": "#DC2626",
    "En traitement": "#F2B705",
    "Escaladée": "#991B1B",
    "Résolue": "#10B981",
}


# ============================================================
# HELPERS PHASES
# ============================================================

def _level_from_reclam(taux_non_resolu, sla_ko):
    """Niveau selon taux non résolu et SLA KO."""
    score = taux_non_resolu * 0.5 + sla_ko * 0.5
    if score >= 45:
        return "rouge"
    if score >= 25:
        return "orange"
    return "vert"


def _compute_phase_sante(reclamations_df, evenements_df, phase_key):
    """Calcule la santé d'une phase."""
    phase = PHASES[phase_key]
    sub_r = reclamations_df[reclamations_df["etape_parcours"].isin(phase["etapes"])] \
        if "etape_parcours" in reclamations_df.columns else pd.DataFrame()

    nb_reclam = len(sub_r)
    taux_non_resolu = pct(
        (sub_r["statut"] != "Résolue").sum(), nb_reclam
    ) if nb_reclam > 0 else 0
    sla_ko = pct(
        (sub_r["sla_respecte"] == "Non").sum(), nb_reclam
    ) if nb_reclam > 0 and "sla_respecte" in sub_r.columns else 0

    return {
        "nb_reclam": nb_reclam,
        "taux_non_resolu": taux_non_resolu,
        "sla_ko": sla_ko,
        "level": _level_from_reclam(taux_non_resolu, sla_ko),
        "has_data": nb_reclam > 0,
    }


def _render_phase_selector(reclamations_f, evenements_f, session_key):
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
        sante = _compute_phase_sante(reclamations_f, evenements_f, key)
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
            f'font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">Réclamations</div>'
            f'<div style="color:#FFFFFF;font-size:1.7rem;font-weight:800;'
            f'line-height:1.1;margin-top:3px;text-shadow:0 2px 4px rgba(0,0,0,0.25);">'
            f'{sante["nb_reclam"]}</div></div>'
            f'<div><div style="color:rgba(255,255,255,0.9);font-size:0.72rem;'
            f'font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">Non résolues</div>'
            f'<div style="color:#FFFFFF;font-size:1.7rem;font-weight:800;'
            f'line-height:1.1;margin-top:3px;text-shadow:0 2px 4px rgba(0,0,0,0.25);">'
            f'{sante["taux_non_resolu"]:.0f} %</div></div>'
            f'<div><div style="color:rgba(255,255,255,0.9);font-size:0.72rem;'
            f'font-weight:700;text-transform:uppercase;letter-spacing:0.04em;">SLA KO</div>'
            f'<div style="color:#FFFFFF;font-size:1.2rem;font-weight:800;'
            f'line-height:1.1;margin-top:3px;text-shadow:0 2px 4px rgba(0,0,0,0.25);">'
            f'{sante["sla_ko"]:.0f} %</div></div>'
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


def _bandeau_phase_active(reclamations_f, evenements_f, phase_key):
    """Bandeau récapitulatif de la phase sélectionnée."""
    phase = PHASES[phase_key]
    sante = _compute_phase_sante(reclamations_f, evenements_f, phase_key)

    level_styles = {
        "vert":   ("#10B981", "rgba(16,185,129,0.15)", "🟢", "SAIN"),
        "orange": ("#F2B705", "rgba(242,183,5,0.15)", "🟠", "À SURVEILLER"),
        "rouge":  ("#DC2626", "rgba(220,38,38,0.15)", "🔴", "CRITIQUE"),
    }
    main_color, light_color, icon, label = level_styles[sante["level"]]

    sub_r = reclamations_f[reclamations_f["etape_parcours"].isin(phase["etapes"])] \
        if "etape_parcours" in reclamations_f.columns else pd.DataFrame()

    # Motif n°1
    motif_top = "Aucun"
    motif_nb = 0
    if not sub_r.empty:
        motif_s = sub_r["motif"].value_counts()
        if not motif_s.empty:
            motif_top = motif_s.index[0]
            motif_nb = motif_s.iloc[0]

    # Responsable
    resp_top = "—"
    if "responsable" in sub_r.columns and not sub_r.empty:
        resp_s = sub_r["responsable"].value_counts()
        if not resp_s.empty:
            resp_top = resp_s.index[0]

    html = (
        f'<div style="background:linear-gradient(135deg,{light_color} 0%,rgba(0,0,0,0) 100%);'
        f'border-radius:16px;padding:20px 26px;margin:16px 0;'
        f'border-left:8px solid {main_color};border:1px solid {main_color}55;'
        f'box-shadow:0 4px 16px rgba(0,0,0,0.25);">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
        f'<div style="font-size:1.3rem;font-weight:800;color:#F4F7FB;">'
        f'{phase["emoji"]} PHASE {phase["label"].upper()} — {sante["nb_reclam"]} réclamations</div>'
        f'<div style="background:{main_color}33;color:{main_color};'
        f'border-radius:30px;padding:8px 20px;font-weight:800;font-size:1rem;">'
        f'{icon} {label} · {sante["taux_non_resolu"]:.0f} % non résolues</div>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;'
        f'color:#F4F7FB;font-size:1rem;line-height:1.6;">'
        f'<div><b>🎯 Motif n°1 :</b><br/>{motif_top} ({motif_nb} cas)</div>'
        f'<div><b>📊 SLA KO :</b><br/>{sante["sla_ko"]:.0f} %</div>'
        f'<div><b>👤 Responsable clé :</b><br/>{resp_top}</div>'
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
            f'{sante["taux_non_resolu"]:.0f} % de réclamations non résolues, '
            f'SLA KO {sante["sla_ko"]:.0f} %. '
            f'Motif prioritaire : <b>{motif_top}</b>. Responsable : <b>{resp_top}</b>.'
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


def _bandeau_sante(reclamations_f, evenements_f):
    total_reclam = len(reclamations_f)
    total_evt = len(evenements_f)

    sla_ko = 0
    if total_reclam > 0 and "sla_respecte" in reclamations_f.columns:
        sla_ko = pct((reclamations_f["sla_respecte"] == "Non").sum(), total_reclam)

    taux_non_resolu = 0
    if total_reclam > 0:
        taux_non_resolu = pct(
            (reclamations_f["statut"] != "Résolue").sum(), total_reclam
        )

    delai_moy = safe_mean(reclamations_f["delai_traitement_jours"]) if total_reclam > 0 else 0
    score_risque = min(100, sla_ko * 0.4 + taux_non_resolu * 0.4 + min(delai_moy * 2, 20))

    if score_risque >= 60:
        level_color = "#DC2626"; level_label = "CRITIQUE"; level_icon = "🔴"
        bg_grad = "linear-gradient(135deg,rgba(220,38,38,0.2) 0%,rgba(0,0,0,0) 100%)"
    elif score_risque >= 35:
        level_color = "#F2B705"; level_label = "À SURVEILLER"; level_icon = "🟠"
        bg_grad = "linear-gradient(135deg,rgba(242,183,5,0.2) 0%,rgba(0,0,0,0) 100%)"
    else:
        level_color = "#10B981"; level_label = "MAÎTRISÉ"; level_icon = "🟢"
        bg_grad = "linear-gradient(135deg,rgba(16,185,129,0.2) 0%,rgba(0,0,0,0) 100%)"

    motif_top = "Aucun"; motif_nb = 0
    if total_reclam > 0:
        motif_s = reclamations_f["motif"].value_counts()
        if not motif_s.empty:
            motif_top = motif_s.index[0]; motif_nb = motif_s.iloc[0]

    resp_top = "—"
    if "responsable" in reclamations_f.columns and total_reclam > 0:
        resp_s = reclamations_f["responsable"].value_counts()
        if not resp_s.empty:
            resp_top = resp_s.index[0]

    evt_top = "—"
    if total_evt > 0:
        evt_s = evenements_f["type_evenement"].value_counts()
        if not evt_s.empty:
            evt_top = evt_s.index[0]

    html = (
        f'<div style="background:{bg_grad};border-radius:16px;padding:22px 28px;'
        f'margin-bottom:20px;border-left:8px solid {level_color};'
        f'border:1px solid {level_color}55;box-shadow:0 4px 16px rgba(0,0,0,0.25);">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">'
        f'<div style="font-size:1.25rem;font-weight:800;color:#F4F7FB;">'
        f'{level_icon} SITUATION GLOBALE : {level_label}</div>'
        f'<div style="background:rgba(0,0,0,0.3);border-radius:30px;padding:8px 20px;'
        f'font-weight:800;color:#F4F7FB;font-size:1.05rem;">'
        f'Score risque : {score_risque:.0f} / 100</div>'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;'
        f'color:#F4F7FB;font-size:0.95rem;line-height:1.7;">'
        f'<div><b>🎯 Motif n°1 :</b><br/>{motif_top} ({motif_nb} cas)</div>'
        f'<div><b>📌 Événement majeur :</b><br/>{evt_top}</div>'
        f'<div><b>👤 Responsable clé :</b><br/>{resp_top}</div>'
        f'</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ============================================================
# RENDU PRINCIPAL
# ============================================================

def render(data: dict, filters: dict):
    page_title(
        "📣", "Réclamations & Incidents",
        "Suivez les réclamations et incidents clients, analysez les causes, les délais "
        "de traitement et identifiez les points d'amélioration."
    )

    reclamations_f_global = apply_filters(data["reclamations"], filters, date_col="date_ref")
    evenements_f_global = apply_filters(data["evenements"], filters, date_col="date_ref")

    if reclamations_f_global.empty and evenements_f_global.empty:
        st.warning("⚠️ Aucune réclamation ni événement pour la combinaison de filtres actuelle.")
        return

    # ============ SÉLECTEUR DE PHASE ============
    _render_phase_selector(reclamations_f_global, evenements_f_global, "reclam_phase_select")

    phase_active = st.session_state.get("reclam_phase_select", None)

    # ============ FILTRAGE PAR PHASE ============
    if phase_active and phase_active in PHASES:
        etapes_phase = PHASES[phase_active]["etapes"]

        # Réclamations filtrées
        if "etape_parcours" in reclamations_f_global.columns:
            reclamations_f = reclamations_f_global[
                reclamations_f_global["etape_parcours"].isin(etapes_phase)
            ].copy()
        else:
            reclamations_f = reclamations_f_global.copy()

        # Événements filtrés
        if "etape_parcours" in evenements_f_global.columns:
            evenements_f = evenements_f_global[
                evenements_f_global["etape_parcours"].isin(etapes_phase)
            ].copy()
        else:
            evenements_f = evenements_f_global.copy()

        _bandeau_phase_active(reclamations_f_global, evenements_f_global, phase_active)
    else:
        reclamations_f = reclamations_f_global
        evenements_f = evenements_f_global

    # ============ BANDEAU SANTÉ ============
    _bandeau_sante(reclamations_f, evenements_f)

    # ============ 5 KPI ============
    total_reclam = len(reclamations_f)
    total_evt = len(evenements_f)
    delai_moy = safe_mean(reclamations_f["delai_traitement_jours"]) if total_reclam else 0
    taux_resolution = pct(
        (reclamations_f["statut"] == "Résolue").sum(), total_reclam
    ) if total_reclam else 0
    sla_ok = pct(
        (reclamations_f["sla_respecte"] == "Oui").sum(), total_reclam
    ) if total_reclam else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(_kpi_card("Réclamations", f"{total_reclam:,}".replace(",", " "),
                              "sur la période", "#F2B705", "📣"), unsafe_allow_html=True)
    with k2:
        st.markdown(_kpi_card("Événements / incidents", f"{total_evt:,}".replace(",", " "),
                              "impayés, sinistres, rachats…", "#3B82C4", "🚨"), unsafe_allow_html=True)
    with k3:
        color_delai = "#DC2626" if delai_moy > 20 else ("#F2B705" if delai_moy > 10 else "#10B981")
        st.markdown(_kpi_card("Délai moyen traitement", f"{delai_moy} j",
                              "objectif < 10 j", color_delai, "⏱"), unsafe_allow_html=True)
    with k4:
        color_res = "#10B981" if taux_resolution >= 70 else ("#F2B705" if taux_resolution >= 40 else "#DC2626")
        st.markdown(_kpi_card("Taux de résolution", f"{taux_resolution} %",
                              f"{100 - taux_resolution:.0f} % ouverts", color_res, "✅"), unsafe_allow_html=True)
    with k5:
        color_sla = "#10B981" if sla_ok >= 80 else ("#F2B705" if sla_ok >= 50 else "#DC2626")
        st.markdown(_kpi_card("SLA respecté", f"{sla_ok} %",
                              "objectif ≥ 80 %", color_sla, "🎯"), unsafe_allow_html=True)

    st.write("")

    # ============ TOP 3 ACTIONS ============
    st.markdown(
        '<div style="font-size:1.15rem;font-weight:800;color:#F4F7FB;'
        'margin:12px 0 10px 0;">🎯 Top 3 des actions prioritaires</div>',
        unsafe_allow_html=True,
    )

    priorités = pd.DataFrame()
    if not reclamations_f.empty:
        reclam_ouvertes = reclamations_f[
            reclamations_f["statut"] != "Résolue"
        ] if "statut" in reclamations_f.columns else reclamations_f

        if not reclam_ouvertes.empty:
            priorités = (
                reclam_ouvertes.groupby(["motif", "responsable"])
                .agg(
                    cas=("reclamation_id", "count"),
                    delai=("delai_traitement_jours", "mean"),
                    sla_ko=("sla_respecte", lambda s: (s == "Non").sum()),
                )
                .reset_index()
                .sort_values(["cas", "sla_ko"], ascending=False)
                .head(3)
            )

    if not priorités.empty:
        action_cols = st.columns(3)
        severities = ["rouge", "orange", "jaune"]
        for i, (col, (_, p)) in enumerate(zip(action_cols, priorités.iterrows())):
            sev = severities[i]
            action_text = "Analyser la cause racine et mettre en place un plan de suivi."
            if p["sla_ko"] > 3:
                action_text = "SLA non respecté — escalade au responsable + revue du process."
            elif p["delai"] > 15:
                action_text = "Revoir les délais de traitement — renforcer les effectifs."
            elif p["cas"] > 10:
                action_text = "Prioriser la résolution — impact client important."
            with col:
                st.markdown(
                    _action_card(
                        rank=i + 1, severity=sev,
                        title=f"{p['motif']}",
                        metric=f"{p['cas']} cas · délai {p['delai']:.0f} j · {p['sla_ko']} SLA KO",
                        owner=p["responsable"], action=action_text,
                    ),
                    unsafe_allow_html=True,
                )
    else:
        st.info("✅ Aucune réclamation non résolue sur la période.")

    st.write("")

    # ============ GRAPHIQUES ============
    c1, c2, c3 = st.columns([1, 1.4, 1])

    with c1:
        with card("🎯 Répartition par motif"):
            if not reclamations_f.empty:
                rep = reclamations_f["motif"].value_counts().reset_index()
                rep.columns = ["motif", "n"]
                fig = px.pie(rep, names="motif", values="n", hole=0.55,
                             color_discrete_sequence=CHART_COLORS)
                fig.update_traces(textposition="inside", textinfo="percent",
                                  textfont=dict(size=11, color="white", family="Arial Black"))
                fig.add_annotation(text=f"<b>{total_reclam}</b><br>réclamations",
                                   showarrow=False, font=dict(size=12, color="#F2B705"))
                fig.update_layout(height=300, margin=dict(l=5, r=5, t=10, b=10),
                                  showlegend=True,
                                  legend=dict(font=dict(size=10, color="#F4F7FB"), orientation="v"))
                apply_dark_theme(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.caption("Aucune réclamation.")

    with c2:
        with card("📈 Évolution des réclamations et incidents"):
            frames = []
            if not reclamations_f.empty:
                t = reclamations_f.dropna(subset=["date_reclamation"]).copy()
                t["mois"] = t["date_reclamation"].dt.to_period("M").dt.to_timestamp()
                frames.append(t.groupby("mois").size().reset_index(name="Réclamations"))
            if not evenements_f.empty:
                t2 = evenements_f.dropna(subset=["date_evenement"]).copy()
                t2["mois"] = t2["date_evenement"].dt.to_period("M").dt.to_timestamp()
                frames.append(t2.groupby("mois").size().reset_index(name="Incidents"))

            if frames:
                merged = frames[0]
                for f in frames[1:]:
                    merged = merged.merge(f, on="mois", how="outer")
                merged = merged.sort_values("mois").fillna(0)

                fig = go.Figure()
                if "Réclamations" in merged:
                    fig.add_trace(go.Scatter(
                        x=merged["mois"], y=merged["Réclamations"],
                        name="Réclamations", mode="lines+markers",
                        line=dict(color="#F2B705", width=3),
                        marker=dict(size=8, color="#F2B705"),
                    ))
                if "Incidents" in merged:
                    fig.add_trace(go.Scatter(
                        x=merged["mois"], y=merged["Incidents"],
                        name="Incidents", mode="lines+markers",
                        line=dict(color="#4FA8A0", width=3),
                        marker=dict(size=8, color="#4FA8A0"),
                    ))
                fig.update_layout(
                    height=300, margin=dict(l=10, r=10, t=10, b=10),
                    legend=dict(orientation="h", y=-0.2,
                                bgcolor="rgba(0,0,0,0)",
                                font=dict(color="#F4F7FB")),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    hovermode="x unified",
                )
                apply_dark_theme(fig)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.caption("Aucune donnée temporelle.")

    with c3:
        with card("🕐 Réclamations récentes"):
            if not reclamations_f.empty:
                recent = reclamations_f.sort_values(
                    "date_reclamation", ascending=False
                ).head(5)
                for _, r in recent.iterrows():
                    d = r["date_reclamation"].strftime("%d/%m/%Y") \
                        if not str(r["date_reclamation"]) == "NaT" else "-"
                    statut = r.get("statut", "-")
                    color = STATUT_COULEURS.get(statut, "#6B7280")
                    st.markdown(
                        f'<div style="padding:8px 0;border-bottom:1px solid #1E3A6B;">'
                        f'<div style="font-weight:700;color:#F4F7FB;'
                        f'font-size:0.85rem;">{r["motif"]}</div>'
                        f'<div style="font-size:0.75rem;color:#A9BDD1;margin-top:2px;">'
                        f'{r.get("canal","-")} · {d} · '
                        f'<span style="background:{color};color:white;'
                        f'padding:1px 8px;border-radius:10px;font-weight:700;'
                        f'font-size:0.68rem;">{statut}</span></div></div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("Aucune réclamation récente.")

    st.write("")

    # ============ TOP 10 + FOCUS ============
    left, right = st.columns([1.3, 1])

    with left:
        with card("🔝 Top 10 dossiers à traiter en priorité"):
            if not reclamations_f.empty:
                problematiques = reclamations_f[
                    (reclamations_f["statut"] != "Résolue") & (
                        (reclamations_f["sla_respecte"] == "Non") |
                        (reclamations_f["delai_traitement_jours"] > delai_moy)
                    )
                ].sort_values("delai_traitement_jours", ascending=False).head(10)

                disp = problematiques[[
                    "reclamation_id", "produit", "motif", "canal",
                    "statut", "delai_traitement_jours", "sla_respecte", "responsable"
                ]].rename(columns={
                    "reclamation_id": "ID", "produit": "Produit",
                    "motif": "Motif", "canal": "Canal", "statut": "Statut",
                    "delai_traitement_jours": "Délai (j)",
                    "sla_respecte": "SLA", "responsable": "Responsable",
                })
                st.dataframe(
                    disp, use_container_width=True, hide_index=True, height=420,
                    column_config={
                        "Délai (j)": st.column_config.NumberColumn("Délai (j)", format="%.0f j"),
                    },
                )
            else:
                st.caption("Aucun dossier à afficher.")

    with right:
        with card("🔍 Focus par dimension"):
            if not reclamations_f.empty:
                dim_choice = st.radio(
                    "Analyser par :",
                    ["Produit", "Canal", "Responsable", "Niveau"],
                    horizontal=True, key="reclam_dim_focus",
                )
                col_map = {"Produit": "produit", "Canal": "canal",
                           "Responsable": "responsable", "Niveau": "niveau"}
                col = col_map[dim_choice]

                if col in reclamations_f.columns:
                    rep4 = reclamations_f[col].value_counts().reset_index().head(10)
                    rep4.columns = [dim_choice, "n"]
                    rep4 = rep4.sort_values("n", ascending=True)

                    if dim_choice == "Niveau":
                        colors_dim = [NIVEAU_COULEURS.get(v, "#F2B705") for v in rep4[dim_choice]]
                    else:
                        colors_dim = ["#F2B705"] * len(rep4)

                    fig = go.Figure(go.Bar(
                        x=rep4["n"], y=rep4[dim_choice], orientation="h",
                        text=rep4["n"], textposition="outside",
                        textfont=dict(size=11, color="#F2B705", family="Arial Black"),
                        marker=dict(color=colors_dim),
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
            else:
                st.caption("Aucune réclamation.")

    st.write("")

    # ============ ÉVÉNEMENTS PAR TYPE ============
    if not evenements_f.empty:
        with card("🚨 Événements par type (impayés, sinistres, rachats, résiliations…)"):
            rep5 = evenements_f["type_evenement"].value_counts().reset_index()
            rep5.columns = ["type", "n"]
            rep5 = rep5.sort_values("n", ascending=True)

            fig = go.Figure(go.Bar(
                x=rep5["n"], y=rep5["type"], orientation="h",
                text=rep5["n"], textposition="outside",
                textfont=dict(size=12, color="#F2B705", family="Arial Black"),
                marker=dict(color="#3B82C4"),
            ))
            fig.update_layout(
                height=320, margin=dict(l=10, r=60, t=10, b=10),
                yaxis=dict(categoryorder="total ascending", title="",
                           tickfont=dict(size=11, color="#F4F7FB")),
                xaxis=dict(title="", showgrid=False,
                           range=[0, rep5["n"].max() * 1.25] if not rep5.empty else 10,
                           tickfont=dict(color="#F4F7FB")),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False, font=dict(color="#F4F7FB"),
            )
            st.plotly_chart(fig, use_container_width=True)

    # ============ INSIGHT ============
    if not reclamations_f.empty:
        top_motif = reclamations_f["motif"].mode().iloc[0]
        resp_top = "—"
        if "responsable" in reclamations_f.columns:
            resp_s = reclamations_f["responsable"].value_counts()
            if not resp_s.empty:
                resp_top = resp_s.index[0]

        insight_box(
            f"<b>À retenir :</b> le motif « <b>{top_motif}</b> » est le plus fréquent. "
            f"{taux_resolution} % des réclamations sont résolues, avec un SLA respecté "
            f"dans {sla_ok} % des cas. Responsable principal : <b>{resp_top}</b>."
        )