"""filters.py - Barre de filtres globale NSIA Vie, tout sur une seule ligne."""

import calendar
import datetime as dt
from typing import Any, Iterable, List, Optional, Tuple

import streamlit as st


# Personnalisé en 1ère position, puis toutes les périodicités classiques
PERIODICITES = (
    "Personnalisé",
    "Journalier",
    "Hebdomadaire",
    "Mensuel",
    "Bimestriel",
    "Trimestriel",
    "Semestriel",
    "Annuel",
)

COMPARAISONS = (
    "Aucune", "Période précédente", "Même période N-1",
)

MOIS_FR = (
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
)


# ---------------------------------------------------------------------------
# Utilitaires dates
# ---------------------------------------------------------------------------

def _as_date(value: Any, fallback: Optional[dt.date] = None) -> Optional[dt.date]:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if value is None:
        return fallback
    if hasattr(value, "to_pydatetime"):
        try:
            return value.to_pydatetime().date()
        except Exception:
            pass
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return dt.datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return fallback


def _normalize_bounds(date_min, date_max) -> Tuple[dt.date, dt.date]:
    start = _as_date(date_min, None)
    end = _as_date(date_max, None)

    if start is None and end is None:
        start = dt.date(2024, 1, 1)
        end = dt.date(2026, 12, 31)
    elif start is None:
        start = end
    elif end is None:
        end = start

    if start > end:
        start, end = end, start

    return start, end


def _month_start(d): return d.replace(day=1)
def _month_end(d): return d.replace(day=calendar.monthrange(d.year, d.month)[1])


def _add_months(d: dt.date, months: int) -> dt.date:
    index = d.year * 12 + (d.month - 1) + months
    year, month0 = divmod(index, 12)
    return dt.date(year, month0 + 1, 1)


def _period_bounds(periodicite: str, anchor: dt.date) -> Tuple[dt.date, dt.date]:
    if periodicite == "Journalier":
        return anchor, anchor

    if periodicite == "Hebdomadaire":
        # Semaine ISO : lundi → dimanche
        start = anchor - dt.timedelta(days=anchor.weekday())
        return start, start + dt.timedelta(days=6)

    if periodicite == "Mensuel":
        start = _month_start(anchor)
        return start, _month_end(start)

    if periodicite == "Bimestriel":
        start_month = ((anchor.month - 1) // 2) * 2 + 1
        start = dt.date(anchor.year, start_month, 1)
        return start, _month_end(_add_months(start, 1))

    if periodicite == "Trimestriel":
        sm = ((anchor.month - 1) // 3) * 3 + 1
        start = dt.date(anchor.year, sm, 1)
        return start, _month_end(_add_months(start, 2))

    if periodicite == "Semestriel":
        sm = 1 if anchor.month <= 6 else 7
        start = dt.date(anchor.year, sm, 1)
        return start, _month_end(_add_months(start, 5))

    if periodicite == "Annuel":
        return dt.date(anchor.year, 1, 1), dt.date(anchor.year, 12, 31)

    return anchor, anchor


def _clamp_period(start, end, data_min, data_max) -> Tuple[dt.date, dt.date]:
    start = max(start, data_min)
    end = min(end, data_max)
    if start > end:
        if end < data_min:
            return data_min, data_min
        return data_max, data_max
    return start, end


def _period_key(start, end) -> str:
    return f"{start.isoformat()}|{end.isoformat()}"


def _period_label(periodicite: str, start: dt.date, end: dt.date) -> str:
    if periodicite == "Journalier":
        return start.strftime("%d/%m/%Y")
    if periodicite == "Hebdomadaire":
        return (
            f"S{start.isocalendar().week:02d} "
            f"{start.strftime('%d/%m')} → {end.strftime('%d/%m/%Y')}"
        )
    if periodicite == "Mensuel":
        return f"{MOIS_FR[start.month - 1]} {start.year}"
    if periodicite == "Bimestriel":
        rang = (start.month - 1) // 2 + 1
        return f"B{rang} {start.year}"
    if periodicite == "Trimestriel":
        return f"T{(start.month - 1) // 3 + 1} {start.year}"
    if periodicite == "Semestriel":
        return f"S{1 if start.month == 1 else 2} {start.year}"
    if periodicite == "Annuel":
        return str(start.year)
    return f"{start.strftime('%d/%m/%Y')} → {end.strftime('%d/%m/%Y')}"


def _available_periods(periodicite, data_min, data_max) -> List[Tuple[str, dt.date, dt.date]]:
    if periodicite == "Personnalisé":
        return []

    periods = []
    cursor = data_min

    # Journalier : on itère jour par jour
    if periodicite == "Journalier":
        while cursor <= data_max:
            periods.append((_period_key(cursor, cursor), cursor, cursor))
            cursor += dt.timedelta(days=1)
        return periods

    # Autres périodicités : on démarre au début de la période contenant data_min
    anchor_start, _ = _period_bounds(periodicite, data_min)
    cursor = anchor_start

    increments = {
        "Hebdomadaire": 7,
        "Mensuel": 1,
        "Bimestriel": 2,
        "Trimestriel": 3,
        "Semestriel": 6,
        "Annuel": 12,
    }

    while cursor <= data_max:
        ns, ne = _period_bounds(periodicite, cursor)
        s, e = _clamp_period(ns, ne, data_min, data_max)
        if s <= e:
            periods.append((_period_key(s, e), s, e))

        if periodicite == "Hebdomadaire":
            cursor += dt.timedelta(days=increments[periodicite])
        else:
            cursor = _add_months(cursor, increments[periodicite])

    return periods


# ---------------------------------------------------------------------------
# Helpers UI
# ---------------------------------------------------------------------------

def _opts(options, key):
    v = options.get(key, [])
    return list(v) if v else []


def _safe_multi(label, values, key, placeholder):
    values = list(values)
    previous = st.session_state.get(key, [])
    if not isinstance(previous, list):
        previous = list(previous) if previous else []
    default = [v for v in previous if v in values]
    return st.multiselect(label, options=values, default=default, key=key, placeholder=placeholder)


def _clear_state(prefix):
    for s in ["periodicite", "periode_selection", "date_start", "date_end",
              "comparaison", "produit", "agence", "ville", "canal", "segment",
              "etape", "friction", "niveau_friction", "statut", "alerte"]:
        st.session_state.pop(f"{prefix}_{s}", None)


def _inject_filter_css():
    st.markdown(
        """
        <style>
        .nsia-filter-shell {
            background: linear-gradient(135deg, #081736 0%, #0B1F4D 100%);
            border: 1px solid rgba(242,183,5,.25);
            border-radius: 12px;
            padding: 12px 18px 10px 18px;
            margin: 0 0 14px 0;
            box-shadow: 0 4px 16px rgba(0,0,0,.25);
        }
        .nsia-filter-title {
            color: #F2B705;
            font-size: 1.15rem;
            font-weight: 800;
            margin-bottom: 3px;
        }
        .nsia-filter-subtitle {
            color: rgba(255,255,255,.75);
            font-size: 0.85rem;
            margin-bottom: 10px;
        }
        .nsia-filter-period {
            color: #FFFFFF;
            font-size: 1rem;
            padding: 10px 14px;
            border-radius: 10px;
            background: rgba(242,183,5,.12);
            border: 1px solid rgba(242,183,5,.3);
            line-height: 1.5;
        }
        .nsia-filter-chip {
            display: inline-block;
            border: 1px solid rgba(242,183,5,.4);
            background: rgba(242,183,5,.15);
            color: #F2B705;
            border-radius: 999px;
            padding: 5px 12px;
            margin: 4px 5px 4px 0;
            font-size: 0.85rem;
            font-weight: 700;
        }
        .nsia-filter-active-label {
            color: rgba(255,255,255,.75);
            font-size: 0.9rem;
            margin-right: 6px;
            font-weight: 700;
        }
        .nsia-filter-shell label,
        .nsia-filter-shell .stSelectbox label,
        .nsia-filter-shell .stMultiSelect label,
        .nsia-filter-shell .stDateInput label {
            color: #FFFFFF !important;
            font-weight: 700 !important;
            font-size: 1rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
# ---------------------------------------------------------------------------
# Barre principale
# ---------------------------------------------------------------------------

def render_filter_bar(options: dict, key_prefix: str = "global") -> dict:
    _inject_filter_css()
    prefix = key_prefix

    data_min, data_max = _normalize_bounds(
        options.get("date_min"),
        options.get("date_max"),
    )
    date_label = options.get("date_label", "Date d'analyse")

    # Périodicité par défaut = Personnalisé (1er de la liste)
    current_periodicity = st.session_state.get(f"{prefix}_periodicite", "Personnalisé")
    if current_periodicity not in PERIODICITES:
        current_periodicity = "Personnalisé"

    st.markdown(
        '<div class="nsia-filter-shell">'
        '<div class="nsia-filter-title">🎛️ Filtres de pilotage</div>'
        '<div class="nsia-filter-subtitle">'
        'Toutes les données sont recalculées instantanément selon vos filtres.'
        '</div>',
        unsafe_allow_html=True,
    )

    # On connaît la périodicité actuelle depuis le session_state
    periodicite = current_periodicity

    # ===== Ligne dynamique =====
    if periodicite == "Personnalisé":
        # 9 colonnes : Périodicité | Date début | Date fin | Produit | Agence | Canal | Segment | Ville | Reset
        c1, c2, c3, c4, c5, c6, c7, c8, c9 = st.columns(
            [1.0, 1.05, 1.05, 1.15, 1.15, 1.1, 1.1, 1.1, 0.65],
            gap="small",
        )
    else:
        # 8 colonnes : Périodicité | Date | Produit | Agence | Canal | Segment | Ville | Reset
        c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(
            [1.0, 1.15, 1.25, 1.25, 1.15, 1.15, 1.15, 0.65],
            gap="small",
        )

    # --- Périodicité (colonne 1, toujours) ---
    with c1:
        periodicite = st.selectbox(
            "Périodicité",
            PERIODICITES,
            index=PERIODICITES.index(current_periodicity),
            key=f"{prefix}_periodicite",
        )

    periods = _available_periods(periodicite, data_min, data_max)

    # ===== Mode Personnalisé : Date début + Date fin =====
    if periodicite == "Personnalisé":
        default_start = _as_date(st.session_state.get(f"{prefix}_date_start"), data_min)
        default_end = _as_date(st.session_state.get(f"{prefix}_date_end"), data_max)

        with c2:
            start = st.date_input(
                "Date début", value=max(default_start, data_min),
                min_value=data_min, max_value=data_max,
                format="DD/MM/YYYY", key=f"{prefix}_date_start",
            )
        with c3:
            end = st.date_input(
                "Date fin", value=min(default_end, data_max),
                min_value=data_min, max_value=data_max,
                format="DD/MM/YYYY", key=f"{prefix}_date_end",
            )
        if start > end:
            start, end = end, start

        col_produit = c4
        col_agence = c5
        col_canal = c6
        col_segment = c7
        col_ville = c8
        col_reset = c9

    # ===== Autres modes : 1 seule colonne date =====
    else:
        labels = [_period_label(periodicite, s, e) for _, s, e in periods]
        previous_label = st.session_state.get(f"{prefix}_periode_selection")

        if previous_label in labels:
            selected_index = labels.index(previous_label)
        else:
            selected_index = max(len(labels) - 1, 0) if labels else 0

        with c2:
            selected_label = st.selectbox(
                date_label,
                labels if labels else ["—"],
                index=selected_index,
                key=f"{prefix}_periode_selection",
            )

        if periods and selected_label in labels:
            selected_index = labels.index(selected_label)
            _, start, end = periods[selected_index]
        else:
            start, end = data_min, data_max

        col_produit = c3
        col_agence = c4
        col_canal = c5
        col_segment = c6
        col_ville = c7
        col_reset = c8

    # ===== Filtres communs =====
    with col_produit:
        produit = _safe_multi("Produit", _opts(options, "produits"),
                              f"{prefix}_produit", "Tous")

    with col_agence:
        agence = _safe_multi("Agence", _opts(options, "agences"),
                             f"{prefix}_agence", "Toutes")

    with col_canal:
        canal = _safe_multi("Canal", _opts(options, "canaux"),
                            f"{prefix}_canal", "Tous")

    with col_segment:
        segment = _safe_multi("Segment", _opts(options, "segments"),
                              f"{prefix}_segment", "Tous")

    with col_ville:
        ville = _safe_multi("Ville", _opts(options, "villes"),
                            f"{prefix}_ville", "Toutes")

    with col_reset:
        st.write("")
        st.write("")
        if st.button("↺ Réinit.", key=f"{prefix}_reset", use_container_width=True):
            _clear_state(prefix)
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # ===== Filtres avancés =====
    with st.expander("⚙️ Filtres avancés — étape, friction, statut, alerte, comparaison"):
        a1, a2, a3, a4, a5 = st.columns(5)
        with a1:
            etape = _safe_multi("🧭 Étape", _opts(options, "etapes"),
                                f"{prefix}_etape", "Toutes")
        with a2:
            niveau_friction = _safe_multi("⚠️ Niveau friction",
                                          _opts(options, "niveaux_friction"),
                                          f"{prefix}_niveau_friction", "Tous")
        with a3:
            friction = _safe_multi("Friction", _opts(options, "frictions"),
                                   f"{prefix}_friction", "Toutes")
        with a4:
            statut = _safe_multi("📌 Statut", _opts(options, "statuts_contrat"),
                                 f"{prefix}_statut", "Tous")
        with a5:
            alerte = _safe_multi("🚨 Alerte", _opts(options, "niveaux_alerte"),
                                 f"{prefix}_alerte", "Tous")

        comparison_default = st.session_state.get(f"{prefix}_comparaison", "Aucune")
        if comparison_default not in COMPARAISONS:
            comparison_default = "Aucune"
        comparaison = st.selectbox(
            "Comparer à", COMPARAISONS,
            index=COMPARAISONS.index(comparison_default),
            key=f"{prefix}_comparaison",
        )

    # ===== Période de comparaison =====
    comparaison_range = None
    if comparaison == "Période précédente":
        duration = (end - start).days + 1
        ce = start - dt.timedelta(days=1)
        cs = ce - dt.timedelta(days=duration - 1)
        comparaison_range = _clamp_period(cs, ce, data_min, data_max)
    elif comparaison == "Même période N-1":
        try:
            cs = start.replace(year=start.year - 1)
            ce = end.replace(year=end.year - 1)
        except ValueError:
            cs = start.replace(year=start.year - 1, day=min(start.day, 28))
            ce = end.replace(year=end.year - 1, day=min(end.day, 28))
        comparaison_range = _clamp_period(cs, ce, data_min, data_max)

   

    # ===== Chips filtres actifs =====
    chips = []
    if periodicite != "Personnalisé":
        chips.append(f"Périodicité : {periodicite}")
    if (start, end) != (data_min, data_max):
        chips.append(f"Période : {start.strftime('%d/%m/%Y')} → {end.strftime('%d/%m/%Y')}")
    if comparaison != "Aucune":
        chips.append(f"Comparaison : {comparaison}")

    labels_map = {
        "produit": "Produit", "agence": "Agence", "ville": "Ville",
        "canal": "Canal", "segment": "Segment", "etape": "Étape",
        "friction": "Friction", "niveau_friction": "Niveau friction",
        "statut": "Statut", "alerte": "Alerte",
    }
    local_result = {
        "produit": produit, "agence": agence, "ville": ville, "canal": canal,
        "segment": segment, "etape": etape, "friction": friction,
        "niveau_friction": niveau_friction, "statut": statut, "alerte": alerte,
    }
    for key, label in labels_map.items():
        values = local_result.get(key) or []
        if values:
            txt = str(values[0]) if len(values) == 1 else f"{len(values)} sélection(s)"
            chips.append(f"{label} : {txt}")

    if chips:
        html = "".join(f'<span class="nsia-filter-chip">{c}</span>' for c in chips)
        st.markdown(
            f'<div style="margin:10px 0 4px 0;">'
            f'<span class="nsia-filter-active-label">Filtres actifs :</span>'
            f'{html}</div>',
            unsafe_allow_html=True,
        )

    return {
        "date_range": (start, end),
        "produit": produit,
        "agence": agence,
        "ville": ville,
        "canal": canal,
        "segment": segment,
        "etape": etape,
        "statut": statut,
        "alerte": alerte,
        "friction": friction,
        "niveau_friction": niveau_friction,
        "periodicite": periodicite,
        "comparaison": comparaison,
        "comparaison_range": comparaison_range,
        "date_min_source": data_min,
        "date_max_source": data_max,
        "date_reference": end,
        "date_label": date_label,
        "filtres_actifs": chips,
    }


def build_filter_options(
    *,
    date_min, date_max,
    produits=(), agences=(), villes=(), canaux=(), segments=(),
    etapes=(), frictions=(), niveaux_friction=(),
    statuts_contrat=(), niveaux_alerte=(),
    date_label="Date d'analyse",
) -> dict:
    return {
        "date_min": _as_date(date_min),
        "date_max": _as_date(date_max),
        "date_label": date_label,
        "produits": sorted(set(produits)),
        "agences": sorted(set(agences)),
        "villes": sorted(set(villes)),
        "canaux": sorted(set(canaux)),
        "segments": sorted(set(segments)),
        "etapes": sorted(set(etapes)),
        "frictions": sorted(set(frictions)),
        "niveaux_friction": sorted(set(niveaux_friction)),
        "statuts_contrat": sorted(set(statuts_contrat)),
        "niveaux_alerte": sorted(set(niveaux_alerte)),
    }