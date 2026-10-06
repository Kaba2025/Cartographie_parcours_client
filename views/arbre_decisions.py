"""views/arbre_decisions.py - Arbre des décisions interactif (Graphviz + fallback Sankey)."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.calculations import apply_dark_theme
from components.style import (
    page_title, insight_box, card, badge,
    NSIA_NAVY, NSIA_GOLD, CHART_COLORS,
)
from utils.calculations import apply_filters, pct, safe_mean


# ============================================================
# RÉFÉRENTIELS
# ============================================================

ETAPES_ICONES = {
    "Découverte": "🔎", "Information / conseil": "ℹ️", "Simulation": "🧮",
    "Souscription": "📝", "Validation du contrat": "✅", "Paiement / cotisation": "💳",
    "Suivi du contrat": "📊", "Avance / rachat": "💰", "Sinistre": "🛟",
    "Réclamation": "💬", "Demande de service": "🛎️", "Suspension": "⏸️",
    "Résiliation": "❌", "Terme": "🏁", "Renouvellement": "🔄",
}
ETAPES_ORDRE = list(ETAPES_ICONES.keys())

# Regroupement des 5 issues en 3 catégories
ISSUE_GROUPES = {
    "✅ Positif": {
        "issues": ["Poursuite", "Résolution"],
        "bg": "#2E9E6C",
        "border": "#1E6F4A",
    },
    "⚠️ Neutre": {
        "issues": ["Blocage", "Modification"],
        "bg": "#F2B705",
        "border": "#B8860B",
    },
    "❌ Négatif": {
        "issues": ["Abandon", "Escalade"],
        "bg": "#DC2626",
        "border": "#991B1B",
    },
}

# Couleurs individuelles (pour le panneau droit)
ISSUE_COLORS = {
    "Poursuite": "#2E9E6C", "Résolution": "#2E9E6C",
    "Blocage": "#F2B705", "Modification": "#F2B705",
    "Abandon": "#DC2626", "Escalade": "#991B1B",
}


# ============================================================
# HELPERS
# ============================================================

def _safe_id(text: str) -> str:
    return (
        str(text)
        .replace(" ", "_").replace("/", "_").replace("'", "")
        .replace("(", "").replace(")", "").replace(",", "").replace(".", "")
        .replace("é", "e").replace("è", "e").replace("ê", "e")
        .replace("à", "a").replace("â", "a")
        .replace("ô", "o").replace("î", "i").replace("û", "u")
        .replace("ç", "c")
    )


def _build_graphviz(etape_sel: str, sub: pd.DataFrame) -> str:
    """Arbre Graphviz compact : étape → sous-étapes → 3 groupes d'issues."""
    sous_etapes = sub["sous_etape"].dropna().unique().tolist()
    total = sub["client_id"].nunique()

    # Calcul : pour chaque sous-étape et chaque groupe, le nb de clients
    def _count_groupe(se_df, groupe_key):
        issues = ISSUE_GROUPES[groupe_key]["issues"]
        return se_df[se_df["issue_etape"].isin(issues)]["client_id"].nunique()

    # --- Entête Graphviz ---
    dot = [
        "digraph ArbreDecisions {",
        '    rankdir=TB;',
        '    bgcolor="transparent";',
        '    splines=ortho;',  # flèches orthogonales, plus propres
        '    nodesep=0.4;',
        '    ranksep=0.55;',
        '    node [shape=box, style="rounded,filled", fontname="Arial", fontsize=10, margin="0.12,0.07"];',
        '    edge [color="#94A3B8", penwidth=1.5, arrowsize=0.6, fontsize=9, fontcolor="#475569"];',
        '',
        # Racine
        f'    root [label="👤 Client\\n{total} clients\\n100%", '
        f'fillcolor="#0B1F4D", fontcolor="white", color="#081736", penwidth=2];'.replace(",", " "),
        # Étape
        f'    etape [label="{ETAPES_ICONES.get(etape_sel, "•")} {etape_sel}\\n{total} clients", '
        f'fillcolor="#1E88E5", fontcolor="white", color="#1565C0", penwidth=2];',
        '    root -> etape [penwidth=2.5, color="#1E88E5", arrowsize=0.8];',
        '',
    ]

    # Sous-étapes
    for se in sous_etapes:
        se_df = sub[sub["sous_etape"] == se]
        n = se_df["client_id"].nunique()
        pct_val = pct(n, total)
        se_id = f"se_{_safe_id(se)}"
        dot.append(
            f'    {se_id} [label="{se}\\n{n} clients\\n({pct_val}%)", '
            f'fillcolor="#E8F0F8", color="#3B82C4", fontcolor="#0B1F4D"];'
        )
        dot.append(f'    etape -> {se_id} [color="#3B82C4"];')

    dot.append('')

    # Groupes d'issues
    for grp_key, grp in ISSUE_GROUPES.items():
        grp_id = f"grp_{_safe_id(grp_key)}"
        # Total sur toute l'étape
        total_grp = sub[sub["issue_etape"].isin(grp["issues"])]["client_id"].nunique()
        pct_grp = pct(total_grp, total)
        dot.append(
            f'    {grp_id} [label="{grp_key}\\n{total_grp} clients\\n({pct_grp}%)", '
            f'fillcolor="{grp["bg"]}", color="{grp["border"]}", fontcolor="white", penwidth=2];'
        )

    dot.append('')

    # Flèches sous-étapes → groupes
    for se in sous_etapes:
        se_df = sub[sub["sous_etape"] == se]
        se_id = f"se_{_safe_id(se)}"
        for grp_key, grp in ISSUE_GROUPES.items():
            n = _count_groupe(se_df, grp_key)
            if n > 0:
                grp_id = f"grp_{_safe_id(grp_key)}"
                # Épaisseur selon le volume
                penwidth = max(1.0, min(3.5, n / 8))
                dot.append(
                    f'    {se_id} -> {grp_id} [label="{n}", color="{grp["bg"]}", '
                    f'penwidth={penwidth:.1f}];'
                )

    dot.append('}')
    return "\n".join(dot)


def _fallback_sankey(etape_sel: str, sub: pd.DataFrame):
    """Sankey compact : étape → sous-étapes → 3 groupes."""
    sous_etapes = sub["sous_etape"].dropna().unique().tolist()

    labels = [etape_sel] + sous_etapes + list(ISSUE_GROUPES.keys())
    idx = {lab: i for i, lab in enumerate(labels)}

    sources, targets, values, colors = [], [], [], []
    for se in sous_etapes:
        se_df = sub[sub["sous_etape"] == se]
        sources.append(idx[etape_sel])
        targets.append(idx[se])
        values.append(se_df["client_id"].nunique())
        colors.append("rgba(11,31,77,0.35)")

        for grp_key, grp in ISSUE_GROUPES.items():
            n = se_df[se_df["issue_etape"].isin(grp["issues"])]["client_id"].nunique()
            if n > 0:
                sources.append(idx[se])
                targets.append(idx[grp_key])
                values.append(int(n))
                colors.append(grp["bg"] + "AA")

    node_colors = (
        [NSIA_NAVY]
        + [CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(sous_etapes))]
        + [g["bg"] for g in ISSUE_GROUPES.values()]
    )

    fig = go.Figure(data=[go.Sankey(
        node=dict(pad=20, thickness=20, line=dict(color="white", width=1),
                  label=labels, color=node_colors),
        link=dict(source=sources, target=targets, value=values, color=colors),
    )])
    fig.update_layout(
        height=420, margin=dict(l=10, r=10, t=10, b=10),
        font=dict(size=12, color=NSIA_NAVY),
    )
    apply_dark_theme(fig)
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# RENDU PRINCIPAL
# ============================================================

def render(data: dict, filters: dict):
    page_title(
        "🔀", "Arbre des décisions",
        "Explorez les différentes possibilités après chaque étape du parcours client."
    )

    parcours_f = apply_filters(data["parcours"], filters, date_col="date_ref")
    if parcours_f.empty:
        st.warning("⚠️ Aucune donnée pour la combinaison de filtres actuelle.")
        return

    etapes_dispo = [e for e in ETAPES_ORDRE if e in parcours_f["etape_parcours"].unique()]
    if not etapes_dispo:
        st.info("Aucune étape disponible.")
        return

    # ============ SÉLECTION D'ÉTAPE ============
    st.markdown(
        f'<div style="font-size:0.9rem;font-weight:700;color:{NSIA_NAVY};'
        f'text-transform:uppercase;letter-spacing:0.04em;margin:8px 0 8px 0;">'
        f'🎯 Sélectionner une étape du parcours</div>',
        unsafe_allow_html=True,
    )

    if "arbre_etape_select" not in st.session_state or \
            st.session_state["arbre_etape_select"] not in etapes_dispo:
        st.session_state["arbre_etape_select"] = etapes_dispo[0]

    n_cols = 6
    for i in range(0, len(etapes_dispo), n_cols):
        row = etapes_dispo[i:i + n_cols]
        cols = st.columns(n_cols)
        for c, etape in zip(cols, row):
            with c:
                is_active = st.session_state["arbre_etape_select"] == etape
                if st.button(
                    f"{ETAPES_ICONES.get(etape, '•')} {etape}",
                    key=f"arbre_btn_{etape}",
                    type="primary" if is_active else "secondary",
                    use_container_width=True,
                ):
                    st.session_state["arbre_etape_select"] = etape
                    st.rerun()

    etape_sel = st.session_state["arbre_etape_select"]
    sub = parcours_f[parcours_f["etape_parcours"] == etape_sel]
    total_clients = sub["client_id"].nunique()

    st.write("")

    # ============ LAYOUT : arbre (gauche) + panneau (droite) ============
    left, right = st.columns([2.1, 1])

    with left:
        with card(f"🌳 Arbre des décisions — Étape « {etape_sel} »"):
            st.caption(
                "Cliquez sur une sous-étape dans le panneau droit pour voir ses statistiques. "
                "Les issues sont regroupées en 3 catégories pour une lecture claire."
            )

            sous_etapes = sub["sous_etape"].dropna().unique().tolist()
            if not sous_etapes:
                st.info("Aucune sous-étape disponible pour cette étape.")
            else:
                # Légende
                legende_html = " ".join([
                    f'<span style="display:inline-block;background:{grp["bg"]};'
                    f'color:white;padding:3px 10px;border-radius:12px;'
                    f'font-size:0.78rem;font-weight:700;margin-right:8px;">'
                    f'{key}</span>'
                    for key, grp in ISSUE_GROUPES.items()
                ])
                st.markdown(
                    f'<div style="margin-bottom:8px;">{legende_html}</div>',
                    unsafe_allow_html=True,
                )

                try:
                    dot = _build_graphviz(etape_sel, sub)
                    st.graphviz_chart(dot, use_container_width=True)
                except Exception:
                    st.info(
                        "ℹ️ Graphviz n'est pas installé — affichage Sankey par défaut. "
                        "Pour l'arbre complet : `pip install graphviz` + binaire Graphviz."
                    )
                    _fallback_sankey(etape_sel, sub)

        # Détail chiffré dans un expandeur (replié par défaut)
        with st.expander("📋 Détail chiffré par sous-étape (cliquer pour ouvrir)"):
            if sous_etapes:
                rows = []
                for se in sous_etapes:
                    se_df = sub[sub["sous_etape"] == se]
                    n = se_df["client_id"].nunique()
                    row = {
                        "Sous-étape": se,
                        "Clients": n,
                        "% total": f"{pct(n, total_clients)}%",
                    }
                    # Détail par issue
                    for iss in ["Poursuite", "Résolution", "Blocage", "Modification", "Abandon", "Escalade"]:
                        cnt = (se_df["issue_etape"] == iss).sum()
                        if cnt > 0:
                            row[iss] = f"{cnt} ({pct(cnt, len(se_df))}%)"
                    rows.append(row)
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with right:
        # ============ KPI COMPACTS (dans le panneau droit) ============
        with card("📊 Indicateurs clés de l'étape"):
            total_lignes = len(sub)

            def _taux(issue):
                if total_lignes == 0:
                    return 0
                return pct((sub["issue_etape"] == issue).sum(), total_lignes)

            m1, m2 = st.columns(2)
            m1.metric("Clients", f"{total_clients:,}".replace(",", " "))
            m2.metric("Sous-étapes", f"{len(sous_etapes) if sous_etapes else 0}")

            m3, m4 = st.columns(2)
            m3.metric("Poursuite", f"{_taux('Poursuite')} %")
            m4.metric("Abandon", f"{_taux('Abandon')} %")

            m5, m6 = st.columns(2)
            m5.metric("Blocage", f"{_taux('Blocage')} %")
            m6.metric("Escalade", f"{_taux('Escalade')} %")

        # ============ DÉTAIL SOUS-ÉTAPE ============
        with card("🔍 Détail d'une sous-étape"):
            if sous_etapes:
                se_choice = st.selectbox(
                    "Choisir une sous-étape", sous_etapes, key="arbre_se_select"
                )
                se_df = sub[sub["sous_etape"] == se_choice]
                n = se_df["client_id"].nunique()

                m1, m2 = st.columns(2)
                m1.metric("Clients", f"{n:,}".replace(",", " "))
                m2.metric("Délai moyen", f"{safe_mean(se_df['duree_etape_jours'])} j")

                st.markdown("**Répartition des issues**")
                issues_rep = se_df["issue_etape"].value_counts()
                for iss, cnt in issues_rep.items():
                    pct_val = pct(cnt, len(se_df))
                    color = ISSUE_COLORS.get(iss, "#9CA3AF")
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;'
                        f'padding:4px 0;font-size:0.85rem;">'
                        f'<span style="color:{color};font-weight:700;">• {iss}</span>'
                        f'<span style="color:#6B7280;">{cnt} ({pct_val}%)</span></div>',
                        unsafe_allow_html=True,
                    )

                st.markdown("**Causes de friction**")
                frictions = apply_filters(data["frictions"], filters, date_col="date_ref")
                frictions = frictions[frictions["etape_parcours"] == etape_sel]
                if not frictions.empty:
                    causes = frictions["cause_racine"].value_counts().head(5)
                    total_causes = causes.sum()
                    for cause, cnt in causes.items():
                        pct_val = pct(cnt, total_causes)
                        st.markdown(
                            f'<div style="margin-bottom:5px;">'
                            f'<div style="display:flex;justify-content:space-between;'
                            f'font-size:0.82rem;color:{NSIA_NAVY};font-weight:700;">'
                            f'<span>{cause}</span><span>{pct_val:.0f}%</span></div>'
                            f'<div style="background:#EEF1F8;border-radius:4px;height:5px;'
                            f'margin-top:3px;">'
                            f'<div style="background:{NSIA_GOLD};width:{pct_val}%;'
                            f'height:100%;border-radius:4px;"></div></div></div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.caption("Aucune friction pour cette étape.")
            else:
                st.caption("Aucune sous-étape disponible.")

    # ============ EXPORT ============
    st.write("")
    col_export, _ = st.columns([1, 3])
    with col_export:
        export_rows = []
        if sous_etapes:
            for se in sous_etapes:
                se_df = sub[sub["sous_etape"] == se]
                for iss in se_df["issue_etape"].dropna().unique():
                    export_rows.append({
                        "Etape": etape_sel,
                        "Sous_etape": se,
                        "Issue": iss,
                        "Clients": se_df[se_df["issue_etape"] == iss]["client_id"].nunique(),
                    })
        if export_rows:
            df_export = pd.DataFrame(export_rows)
            st.download_button(
                "📄 Exporter le rapport (CSV)",
                df_export.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"arbre_decisions_{etape_sel}.csv",
                mime="text/csv",
            )

    # ============ INSIGHT ============
    if sous_etapes:
        worst = max(
            sous_etapes,
            key=lambda se: pct(
                (sub[sub["sous_etape"] == se]["issue_etape"] == "Abandon").sum(),
                len(sub[sub["sous_etape"] == se]),
            ) if len(sub[sub["sous_etape"] == se]) > 0 else 0,
        )
        worst_pct = pct(
            (sub[sub["sous_etape"] == worst]["issue_etape"] == "Abandon").sum(),
            len(sub[sub["sous_etape"] == worst]),
        ) if len(sub[sub["sous_etape"] == worst]) > 0 else 0
        insight_box(
            f"<b>À retenir :</b> sur l'étape « {etape_sel} », la sous-étape "
            f"« {worst} » présente le taux d'abandon le plus élevé ({worst_pct} %)."
        )