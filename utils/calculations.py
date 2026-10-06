"""
calculations.py
-----------------
Fonctions utilitaires de filtrage et de calcul des indicateurs (KPI) utilisés
dans l'ensemble de l'application. Centraliser ces calculs garantit que tous
les onglets utilisent la même définition d'un indicateur donné.
"""

import pandas as pd
import numpy as np

# Colonnes candidates pour chaque type de filtre, testées dans l'ordre pour
# chaque DataFrame (toutes les tables n'ont pas les mêmes noms de colonnes).
COL_CANDIDATES = {
    "produit": ["produit"],
    "agence": ["agence"],
    "ville": ["ville"],
    "canal": ["canal", "canal_souscription"],
    "segment": ["segment_client"],
    "etape": ["etape_parcours"],
    "statut": ["statut_contrat"],
    "alerte": ["niveau_alerte"],
    "friction": ["friction"],
    "niveau_friction": ["niveau_friction"],
}

def apply_filters(df: pd.DataFrame, filters: dict, date_col: str = "date_ref") -> pd.DataFrame:
    """Applique le dictionnaire de filtres globaux à un DataFrame, en ne
    filtrant que sur les colonnes réellement présentes dans ce DataFrame."""
    if df is None or df.empty:
        return df

    out = df.copy()

    # Période
    if date_col in out.columns and filters.get("date_range"):
        start, end = filters["date_range"]
        if start and end:
            mask = out[date_col].isna() | (
                (out[date_col].dt.date >= start) & (out[date_col].dt.date <= end)
            )
            # On ne perd pas les lignes sans date exploitable (ex : friction sans date liée)
            has_date = out[date_col].notna()
            keep = (~has_date) | ((out[date_col].dt.date >= start) & (out[date_col].dt.date <= end))
            out = out[keep]

    def _filter_multiselect(key, values):
        nonlocal out
        if not values:
            return
        for col in COL_CANDIDATES[key]:
            if col in out.columns:
                out = out[out[col].isin(values)]
                break

    _filter_multiselect("produit", filters.get("produit"))
    _filter_multiselect("agence", filters.get("agence"))
    _filter_multiselect("ville", filters.get("ville"))
    _filter_multiselect("canal", filters.get("canal"))
    _filter_multiselect("segment", filters.get("segment"))
    _filter_multiselect("etape", filters.get("etape"))
    _filter_multiselect("statut", filters.get("statut"))
    _filter_multiselect("alerte", filters.get("alerte"))
    _filter_multiselect("friction", filters.get("friction"))
    _filter_multiselect("niveau_friction", filters.get("niveau_friction"))

    return out


def pct(numerator, denominator, decimals=1):
    """Pourcentage sûr (évite la division par zéro)."""
    if not denominator:
        return 0.0
    return round(100 * numerator / denominator, decimals)


def safe_mean(series, decimals=1):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return 0.0
    return round(s.mean(), decimals)


def taux_conversion(parcours: pd.DataFrame, clients: pd.DataFrame) -> float:
    """Taux de conversion = part des clients du périmètre filtré dont le
    parcours a atteint au moins l'étape 'Souscription' ou au-delà, parmi les
    clients ayant démarré un parcours (étape 'Découverte')."""
    if parcours.empty:
        return 0.0
    etapes_avancees = [
        "Souscription", "Validation du contrat", "Paiement / cotisation",
        "Sinistre", "Renouvellement", "Terme",
    ]
    clients_avances = parcours.loc[parcours["etape_parcours"].isin(etapes_avancees), "client_id"].nunique()
    clients_total = parcours["client_id"].nunique()
    return pct(clients_avances, clients_total)


def taux_friction(parcours: pd.DataFrame) -> float:
    """Taux de friction = part des étapes de parcours marquées en friction."""
    if parcours.empty or "friction" not in parcours.columns:
        return 0.0
    total = len(parcours)
    n_friction = (parcours["friction"] == "Oui").sum()
    return pct(n_friction, total)


def taux_reclamation(reclamations: pd.DataFrame, clients: pd.DataFrame) -> float:
    """Taux de réclamation = clients ayant au moins une réclamation / total clients du périmètre."""
    total = clients["client_id"].nunique() if not clients.empty else 0
    if total == 0:
        return 0.0
    n = reclamations["client_id"].nunique() if not reclamations.empty else 0
    return pct(n, total)


def delai_moyen_traitement(reclamations: pd.DataFrame, evenements: pd.DataFrame) -> float:
    """Délai moyen de traitement (jours), combinant réclamations et événements."""
    parts = []
    if not reclamations.empty and "delai_traitement_jours" in reclamations.columns:
        parts.append(pd.to_numeric(reclamations["delai_traitement_jours"], errors="coerce").dropna())
    if not evenements.empty and "delai_traitement_jours" in evenements.columns:
        parts.append(pd.to_numeric(evenements["delai_traitement_jours"], errors="coerce").dropna())
    if not parts:
        return 0.0
    combined = pd.concat(parts)
    if combined.empty:
        return 0.0
    return round(combined.mean(), 1)


def indice_satisfaction(parcours: pd.DataFrame, reclamations: pd.DataFrame, sur_5: bool = False) -> float:
    """Indice de satisfaction ESTIMÉ (proxy), calculé car le fichier source ne
    contient pas de colonne de satisfaction client / CSAT.

    Méthode : on part de 100% et on retranche le taux de friction et le taux
    de réclamation (pondérés), avec un plancher à 0. C'est un indicateur
    directionnel destiné à la démonstration, pas une mesure réelle de CSAT.
    """
    tf = taux_friction(parcours)
    if not reclamations.empty and "sla_respecte" in reclamations.columns:
        sla_ko = pct((reclamations["sla_respecte"] == "Non").sum(), len(reclamations))
    else:
        sla_ko = 0
    score = 100 - (0.5 * tf) - (0.5 * sla_ko)
    score = max(0.0, min(100.0, score))
    if sur_5:
        return round(score / 20, 1)
    return round(score, 1)


def evolution_mensuelle(df: pd.DataFrame, date_col: str, value_cols_agg: dict) -> pd.DataFrame:
    """Regroupe un DataFrame par mois (YYYY-MM) et calcule les agrégations demandées.
    value_cols_agg: dict {nom_colonne_sortie: (colonne_source, fonction_agg)}"""
    if df.empty or date_col not in df.columns:
        return pd.DataFrame()
    tmp = df.dropna(subset=[date_col]).copy()
    if tmp.empty:
        return pd.DataFrame()
    tmp["mois"] = tmp[date_col].dt.to_period("M").dt.to_timestamp()
    out = tmp.groupby("mois").size().reset_index(name="volume")
    return out.sort_values("mois")


def top_n_value_counts(series: pd.Series, n=5):
    s = series.dropna()
    if s.empty:
        return pd.DataFrame(columns=["valeur", "nombre"])
    vc = s.value_counts().head(n).reset_index()
    vc.columns = ["valeur", "nombre"]
    return vc
# Dans utils/calculations.py (à la fin)

PLOTLY_DARK_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#F4F7FB", size=12),
    xaxis=dict(gridcolor="#1E3A6B", zerolinecolor="#1E3A6B", color="#F4F7FB"),
    yaxis=dict(gridcolor="#1E3A6B", zerolinecolor="#1E3A6B", color="#F4F7FB"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#F4F7FB")),
)


def apply_dark_theme(fig, height=None):
    """Applique le thème dark NSIA à un graphique Plotly."""
    fig.update_layout(**PLOTLY_DARK_LAYOUT)
    if height:
        fig.update_layout(height=height)
    return fig