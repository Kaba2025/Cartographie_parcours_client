"""views/guide.py - Guide d'utilisation du cockpit NSIA Vie."""

import streamlit as st

from components.style import (
    page_title, card, NSIA_NAVY, NSIA_GOLD, NSIA_BORDER,
)


# ============================================================
# HELPERS
# ============================================================

def _section(emoji, title, content_html):
    """Encadré de section avec titre doré."""
    st.markdown(
        f'<div style="background:linear-gradient(135deg, #132B5C 0%, #0F2557 100%);'
        f'border-radius:14px;padding:22px 26px;margin-bottom:16px;'
        f'border:1px solid {NSIA_BORDER};box-shadow:0 4px 16px rgba(0,0,0,0.2);">'
        f'<div style="font-size:1.3rem;font-weight:800;color:{NSIA_GOLD};'
        f'margin-bottom:14px;letter-spacing:-0.01em;">{emoji} {title}</div>'
        f'{content_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _carte_couleur(color, icon, label, regle, action):
    """Carte de code couleur."""
    return (
        f'<div style="background:rgba(0,0,0,0.2);border-radius:12px;'
        f'padding:18px;border-left:5px solid {color};'
        f'border:1px solid {color}55;height:100%;">'
        f'<div style="font-size:2rem;text-align:center;margin-bottom:8px;">{icon}</div>'
        f'<div style="font-size:1.1rem;font-weight:800;color:{color};'
        f'text-align:center;margin-bottom:12px;">{label}</div>'
        f'<div style="color:#F4F7FB;font-size:0.9rem;line-height:1.6;'
        f'text-align:center;"><b>Règle :</b> {regle}</div>'
        f'<div style="color:#A9BDD1;font-size:0.85rem;line-height:1.5;'
        f'text-align:center;margin-top:8px;padding-top:8px;'
        f'border-top:1px dashed {color}55;"><b>Action :</b> {action}</div>'
        f'</div>'
    )


def _onglet_card(emoji, title, description, use_case):
    """Carte descriptive d'un onglet."""
    return (
        f'<div style="background:rgba(255,255,255,0.05);border-radius:10px;'
        f'padding:14px 18px;margin-bottom:10px;'
        f'border-left:4px solid {NSIA_GOLD};">'
        f'<div style="font-size:1.05rem;font-weight:800;color:#F4F7FB;'
        f'margin-bottom:6px;">{emoji} {title}</div>'
        f'<div style="color:#A9BDD1;font-size:0.9rem;line-height:1.5;">'
        f'{description}</div>'
        f'<div style="color:{NSIA_GOLD};font-size:0.82rem;margin-top:8px;'
        f'font-weight:700;">💡 {use_case}</div>'
        f'</div>'
    )


# ============================================================
# RENDU PRINCIPAL
# ============================================================

def render(data: dict = None, filters: dict = None):
    page_title(
        "📖", "Guide d'utilisation",
        "Tout ce qu'il faut savoir pour piloter le cockpit NSIA Vie."
    )

    # ============================================================
    # SECTION 1 — À QUOI SERT CETTE APPLICATION
    # ============================================================
    _section(
        "🎯", "À quoi sert cette application ?",
        f'<div style="color:#F4F7FB;font-size:1rem;line-height:1.8;">'
        f'Le <b style="color:{NSIA_GOLD};">Cockpit de pilotage du parcours client NSIA Vie</b> '
        f'permet de suivre la performance de bout en bout, de la découverte jusqu\'à la fidélisation :'
        f'<ul style="margin-top:10px;margin-left:20px;">'
        f'<li>📊 <b>Suivre la performance</b> globale du parcours client en temps réel</li>'
        f'<li>⚠️ <b>Identifier les frictions</b> et blocages sur chaque étape</li>'
        f'<li>💰 <b>Mesurer l\'impact financier</b> des problèmes détectés</li>'
        f'<li>🎯 <b>Prioriser les actions managériales</b> avec responsables nommés</li>'
        f'<li>🚦 <b>Piloter par phase</b> : Avant-vente / Vente / Après-vente</li>'
        f'</ul>'
        f'</div>',
    )

    # ============================================================
    # SECTION 2 — BARRE DE FILTRES
    # ============================================================
    _section(
        "🎛️", "La barre de filtres globale",
        f'<div style="color:#F4F7FB;font-size:1rem;line-height:1.8;">'
        f'La barre de filtres <b>en haut de chaque page</b> filtre <b style="color:{NSIA_GOLD};">'
        f'toutes les données</b> de l\'application. Tout changement recalcule <b>instantanément</b> '
        f'les KPI, graphiques et tableaux.'
        f'<div style="background:rgba(242,183,5,0.1);border-left:4px solid {NSIA_GOLD};'
        f'border-radius:8px;padding:12px 16px;margin-top:14px;">'
        f'<b style="color:{NSIA_GOLD};">📋 Filtres disponibles :</b><br/>'
        f'<span style="color:#F4F7FB;">'
        f'📅 Période · 📦 Produit · 🏢 Agence · 📍 Ville · 🔀 Canal · 👥 Segment'
        f'</span>'
        f'</div>'
        f'<div style="background:rgba(59,130,196,0.1);border-left:4px solid #3B82C4;'
        f'border-radius:8px;padding:12px 16px;margin-top:10px;">'
        f'<b style="color:#3B82C4;">⚙️ Filtres avancés (dans le tiroir dépliable) :</b><br/>'
        f'<span style="color:#F4F7FB;">'
        f'🧭 Étape du parcours · ⚠️ Niveau de friction · 📌 Statut · 🚨 Niveau d\'alerte'
        f'</span>'
        f'</div>'
        f'<div style="background:rgba(16,185,129,0.1);border-left:4px solid #10B981;'
        f'border-radius:8px;padding:12px 16px;margin-top:10px;">'
        f'<b style="color:#10B981;">💡 Astuces :</b><br/>'
        f'<span style="color:#F4F7FB;">'
        f'• <b>Un filtre vide = tous les résultats</b> (aucune restriction)<br/>'
        f'• <b>Trop de filtres = 0 résultat</b> → élargissez la période ou retirez un filtre<br/>'
        f'• Cliquez sur <b>↺ Réinit.</b> pour revenir à la vue par défaut'
        f'</span>'
        f'</div>'
        f'</div>',
    )

    # ============================================================
    # SECTION 3 — CODES COULEUR
    # ============================================================
    _section(
        "🚦", "Les codes couleur (santé)",
        f'<div style="color:#F4F7FB;font-size:1rem;line-height:1.8;margin-bottom:18px;">'
        f'Chaque <b>phase</b> et chaque <b>étape</b> est évaluée selon son <b>taux de friction</b>. '
        f'La couleur vous dit immédiatement s\'il faut agir.'
        f'</div>'
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;">'
        + _carte_couleur(
            "#10B981", "🟢", "SAIN",
            "Friction &lt; 15 %",
            "Poursuivre le suivi habituel"
        )
        + _carte_couleur(
            "#F2B705", "🟠", "À SURVEILLER",
            "Friction entre 15 % et 30 %",
            "Suivi régulier — plan d'action à prévoir"
        )
        + _carte_couleur(
            "#DC2626", "🔴", "CRITIQUE",
            "Friction &gt; 30 %",
            "Action urgente — escalade responsable"
        )
        + '</div>'
        + f'<div style="background:rgba(242,183,5,0.1);border-left:4px solid {NSIA_GOLD};'
        f'border-radius:8px;padding:14px 18px;margin-top:18px;">'
        f'<b style="color:{NSIA_GOLD};">💡 Autres couleurs dans l\'application :</b><br/>'
        f'<span style="color:#F4F7FB;font-size:0.9rem;line-height:1.7;">'
        f'• <b style="color:#F2B705;">Doré</b> : éléments NSIA, valeurs clés<br/>'
        f'• <b style="color:#F4F7FB;">Blanc</b> : textes et données neutres<br/>'
        f'• <b style="color:#A9BDD1;">Gris clair</b> : informations secondaires<br/>'
        f'• <b style="color:#DC2626;">Rouge dans un graphique</b> : valeur négative ou en baisse'
        f'</span>'
        f'</div>',
    )

    # ============================================================
    # SECTION 4 — LES 7 ONGLETS
    # ============================================================
    _section(
        "🗂️", "Les 7 onglets de l'application",
        f'<div style="color:#F4F7FB;font-size:1rem;line-height:1.8;margin-bottom:16px;">'
        f'Chaque onglet a un rôle précis. Utilisez-les dans l\'ordre pour une lecture stratégique.'
        f'</div>'
        + _onglet_card(
            "🏠", "Vue d'ensemble",
            "Tableau de bord principal. Affiche le score de santé global, les 3 phases cliquables, "
            "4 KPI principaux, les Top 3 alertes, le tunnel du parcours et le pilotage managérial.",
            "Point d'entrée — commencez toujours ici."
        )
        + _onglet_card(
            "👥", "Parcours Client",
            "Schéma interactif du parcours : 3 phases (Avant-vente, Vente, Après-vente). "
            "Cliquez sur une étape pour explorer ses sous-étapes et statistiques.",
            "Comprendre le parcours de bout en bout."
        )
        + _onglet_card(
            "🔀", "Arbre des décisions",
            "Diagramme des branches possibles après chaque étape (Poursuite, Abandon, "
            "Blocage, Escalade, Résolution).",
            "Comprendre pourquoi les clients partent ou restent."
        )
        + _onglet_card(
            "⚠️", "Frictions & Blocages",
            "Analyse des points de blocage : causes, étapes, agences, responsables, délais. "
            "Top 3 des actions prioritaires.",
            "Identifier où ça bloque et qui doit agir."
        )
        + _onglet_card(
            "💬", "Réclamations & Incidents",
            "Suivi des réclamations clients et des incidents (impayés, sinistres, rachats, "
            "résiliations). SLA et délais de traitement.",
            "Piloter la satisfaction client."
        )
        + _onglet_card(
            "🏢", "Agences & Canaux",
            "Performance du réseau d'agences et des canaux de distribution. "
            "Classement, carte géographique, taux de conversion.",
            "Comparer les agences et les canaux."
        )
        + _onglet_card(
            "📦", "Produits",
            "Vue à 360° de chaque produit : clients, contrats, conversion, friction, "
            "réclamations, canaux. Fiche produit détaillée.",
            "Analyser la performance par produit."
        ),
    )

    # ============================================================
    # SECTION 5 — DÉMARRER EN 3 ÉTAPES
    # ============================================================
    _section(
        "🚀", "Comment démarrer en 3 étapes",
        f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;">'
        # Étape 1
        f'<div style="background:rgba(59,130,196,0.1);border-radius:12px;'
        f'padding:20px;border:1px solid #3B82C455;">'
        f'<div style="background:#3B82C4;color:white;border-radius:50%;'
        f'width:38px;height:38px;display:flex;align-items:center;justify-content:center;'
        f'font-weight:800;font-size:1.2rem;margin-bottom:12px;">1</div>'
        f'<div style="color:#F4F7FB;font-weight:800;font-size:1.05rem;'
        f'margin-bottom:8px;">📅 Choisir la période</div>'
        f'<div style="color:#A9BDD1;font-size:0.88rem;line-height:1.5;">'
        f'Dans la barre en haut, sélectionnez la période (mois, trimestre ou personnalisée).'
        f'</div></div>'
        # Étape 2
        f'<div style="background:rgba(242,183,5,0.1);border-radius:12px;'
        f'padding:20px;border:1px solid #F2B70555;">'
        f'<div style="background:#F2B705;color:#0B1F4D;border-radius:50%;'
        f'width:38px;height:38px;display:flex;align-items:center;justify-content:center;'
        f'font-weight:800;font-size:1.2rem;margin-bottom:12px;">2</div>'
        f'<div style="color:#F4F7FB;font-weight:800;font-size:1.05rem;'
        f'margin-bottom:8px;">🎯 Cliquer sur une phase</div>'
        f'<div style="color:#A9BDD1;font-size:0.88rem;line-height:1.5;">'
        f'Sur la Vue d\'ensemble, cliquez sur Avant-vente, Vente ou Après-vente pour filtrer '
        f'tout le dashboard sur cette phase.'
        f'</div></div>'
        # Étape 3
        f'<div style="background:rgba(16,185,129,0.1);border-radius:12px;'
        f'padding:20px;border:1px solid #10B98155;">'
        f'<div style="background:#10B981;color:white;border-radius:50%;'
        f'width:38px;height:38px;display:flex;align-items:center;justify-content:center;'
        f'font-weight:800;font-size:1.2rem;margin-bottom:12px;">3</div>'
        f'<div style="color:#F4F7FB;font-weight:800;font-size:1.05rem;'
        f'margin-bottom:8px;">🔍 Explorer les onglets</div>'
        f'<div style="color:#A9BDD1;font-size:0.88rem;line-height:1.5;">'
        f'Naviguez dans les 7 onglets de la sidebar pour analyser en détail.'
        f'</div></div>'
        f'</div>',
    )

    # ============================================================
    # SECTION 6 — QUESTIONS FRÉQUENTES
    # ============================================================
    faq_items = [
        ("Pourquoi les chiffres changent quand je clique sur une phase ?",
         "Le cockpit recalcule tout en temps réel. Cliquer sur une phase filtre les données sur les "
         "étapes de cette phase uniquement (ex : « Vente » = Souscription + Validation + Paiement)."),
        ("Que faire si une case est rouge ?",
         "Cliquez dessus. Le bandeau d'alerte s'affiche avec la cause n°1, l'étape critique et le "
         "responsable. Puis allez dans « Frictions & Blocages » pour voir les actions à mener."),
        ("Comment revenir à la vue globale après avoir cliqué sur une phase ?",
         "Cliquez sur le bouton jaune « ✅ Phase active — Vue globale » sous la carte de la phase."),
        ("Pourquoi certains filtres donnent-ils 0 résultat ?",
         "Trop de filtres combinés. Retirez le filtre le plus restrictif ou élargissez la période. "
         "Un filtre vide = tous les résultats."),
        ("À quoi correspond le « Score de santé » ?",
         "Score sur 100 calculé à partir du taux de friction, du taux de réclamation ouverte et du "
         "respect des SLA. Plus le score est haut, meilleure est la santé."),
        ("Qui contacter en cas de problème ?",
         "Le responsable indiqué sur chaque alerte (IT / Digital, Qualité, Direction Réseau, etc.)."),
    ]

    faq_html = ""
    for i, (question, answer) in enumerate(faq_items):
        faq_html += (
            f'<div style="background:rgba(255,255,255,0.05);border-radius:10px;'
            f'padding:14px 18px;margin-bottom:10px;border-left:4px solid {NSIA_GOLD};">'
            f'<div style="color:{NSIA_GOLD};font-weight:800;font-size:0.98rem;'
            f'margin-bottom:6px;">❓ {question}</div>'
            f'<div style="color:#F4F7FB;font-size:0.9rem;line-height:1.6;">{answer}</div>'
            f'</div>'
        )

    _section("❓", "Questions fréquentes", faq_html)

    # ============================================================
    # FOOTER
    # ============================================================
    st.markdown(
        f'<div style="text-align:center;padding:24px;color:#A9BDD1;'
        f'font-size:0.9rem;margin-top:20px;border-top:1px solid {NSIA_BORDER};">'
        f'🎯 <b style="color:{NSIA_GOLD};">Cockpit NSIA Vie Assurances</b> — '
        f'Guide d\'utilisation v1.0<br/>'
        f'<span style="font-size:0.8rem;">Pour toute question : contactez l\'équipe Qualité / Expérience Client</span>'
        f'</div>',
        unsafe_allow_html=True,
    )