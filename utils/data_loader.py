"""
data_loader.py
----------------
Chargement, nettoyage et enrichissement des données NSIA Vie Assurances CI
depuis le fichier Excel source (données 100% fictives).

Toutes les feuilles sont chargées puis les tables "événementielles"
(Parcours, Interactions, Frictions, Réclamations, Événements) sont enrichies
avec les attributs clients (ville, agence, segment) afin de pouvoir appliquer
un filtre global cohérent sur toutes les pages de l'application.

NOTE SUR LES DONNÉES MANQUANTES
--------------------------------
Le fichier source ne contient pas de colonne "satisfaction client / CSAT".
Un indice de satisfaction est donc calculé (proxy) à partir du taux de
friction, du taux de réclamation et du taux de respect des SLA. Cet indice
est clairement identifié comme "estimé" partout où il est affiché
(cf. utils/calculations.py -> indice_satisfaction()).

Le fichier source ne contient pas non plus de colonne "échéance" pour les
actions managériales (feuille Pilotage). Une échéance indicative est donc
calculée = date du jour + délai moyen (jours) associé à l'action. Elle est
libellée "Échéance indicative" dans l'interface.
"""

from pathlib import Path
import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "NSIA_Vie_CI_Cartographie_Parcours_Client_Pilotage.xlsx"

CLIENT_ATTRS = ["client_id", "ville", "agence", "segment_client", "segment_anciennete", "valeur_client", "digitalite", "age", "sexe"]


def _read_sheet(xls, name, date_cols=None):
    df = pd.read_excel(xls, name)
    df.columns = [c.strip() for c in df.columns]
    if date_cols:
        for c in date_cols:
            if c in df.columns:
                df[c] = pd.to_datetime(df[c], errors="coerce")
    # Nettoyage des chaînes de caractères
    for c in df.select_dtypes(include="object").columns:
        df[c] = df[c].astype(str).str.strip().replace({"nan": pd.NA, "None": pd.NA})
    return df


@st.cache_data(show_spinner="Chargement des données NSIA Vie...")
def load_all_data(path: str = None) -> dict:
    """Charge toutes les feuilles du classeur et retourne un dict de DataFrames enrichis."""
    file_path = path or DATA_PATH
    xls = pd.ExcelFile(file_path)

    clients = _read_sheet(xls, "Clients")
    produits = _read_sheet(xls, "Produits")
    contrats = _read_sheet(xls, "Contrats", date_cols=["date_souscription"])
    parcours = _read_sheet(xls, "Parcours", date_cols=["date_entree_etape", "date_sortie_etape"])
    interactions = _read_sheet(xls, "Interactions", date_cols=["date_interaction"])
    frictions = _read_sheet(xls, "Frictions")
    reclamations = _read_sheet(xls, "Reclamations", date_cols=["date_reclamation"])
    evenements = _read_sheet(xls, "Evenements", date_cols=["date_evenement"])
    pilotage = _read_sheet(xls, "Pilotage")
    referentiels = _read_sheet(xls, "Referentiels")

    # Colonnes numériques -> forcer le type
    for col in ["age"]:
        if col in clients.columns:
            clients[col] = pd.to_numeric(clients[col], errors="coerce")
    for col in ["duree_contrat_ans", "montant_cotisation_fcfa"]:
        if col in contrats.columns:
            contrats[col] = pd.to_numeric(contrats[col], errors="coerce")
    for col in ["duree_etape_jours"]:
        if col in parcours.columns:
            parcours[col] = pd.to_numeric(parcours[col], errors="coerce")
    for col in ["duree_contact_min"]:
        if col in interactions.columns:
            interactions[col] = pd.to_numeric(interactions[col], errors="coerce")
    for col in ["delai_resolution_jours"]:
        if col in frictions.columns:
            frictions[col] = pd.to_numeric(frictions[col], errors="coerce")
    for col in ["delai_traitement_jours"]:
        if col in reclamations.columns:
            reclamations[col] = pd.to_numeric(reclamations[col], errors="coerce")
    for col in ["delai_traitement_jours"]:
        if col in evenements.columns:
            evenements[col] = pd.to_numeric(evenements[col], errors="coerce")
    for col in ["nb_incidents", "delai_moyen_jours"]:
        if col in pilotage.columns:
            pilotage[col] = pd.to_numeric(pilotage[col], errors="coerce")

    client_map = clients[CLIENT_ATTRS].drop_duplicates(subset="client_id")

    # --- Enrichissement (jointure des attributs client) ---
    parcours_e = parcours.merge(client_map, on="client_id", how="left")
    # Date de référence pour le filtre période sur Parcours
    parcours_e["date_ref"] = parcours_e["date_entree_etape"]

    interactions_e = interactions.merge(client_map, on="client_id", how="left")
    interactions_e["date_ref"] = interactions_e["date_interaction"]

    # Frictions n'a pas de date propre -> on récupère la date via le parcours_id
    parcours_dates = parcours[["parcours_id", "date_entree_etape"]].drop_duplicates("parcours_id")
    frictions_e = frictions.merge(client_map, on="client_id", how="left")
    frictions_e = frictions_e.merge(parcours_dates, on="parcours_id", how="left")
    frictions_e["date_ref"] = frictions_e["date_entree_etape"]

    reclamations_e = reclamations.merge(client_map, on="client_id", how="left")
    reclamations_e["date_ref"] = reclamations_e["date_reclamation"]

    evenements_e = evenements.merge(client_map, on="client_id", how="left")
    evenements_e["date_ref"] = evenements_e["date_evenement"]

    contrats_e = contrats.merge(
        client_map.drop(columns=["agence"]), on="client_id", how="left"
    )  # agence déjà présente dans Contrats
    contrats_e["date_ref"] = contrats_e["date_souscription"]

    return {
        "clients": clients,
        "produits": produits,
        "contrats": contrats_e,
        "parcours": parcours_e,
        "interactions": interactions_e,
        "frictions": frictions_e,
        "reclamations": reclamations_e,
        "evenements": evenements_e,
        "pilotage": pilotage,
        "referentiels": referentiels,
    }


def get_filter_options(data: dict) -> dict:
    """Calcule les listes d'options pour les filtres globaux à partir des données brutes."""
    clients = data["clients"]
    parcours = data["parcours"]
    contrats = data["contrats"]

    def _u(series):
        return sorted([v for v in series.dropna().unique().tolist() if str(v).strip() != ""])

    all_dates = pd.concat([
        data["parcours"]["date_entree_etape"],
        data["contrats"]["date_souscription"],
        data["reclamations"]["date_reclamation"],
        data["evenements"]["date_evenement"],
        data["interactions"]["date_interaction"],
    ], ignore_index=True).dropna()

    return {
        "date_min": all_dates.min().date() if not all_dates.empty else None,
        "date_max": all_dates.max().date() if not all_dates.empty else None,
        "produits": _u(pd.concat([contrats["produit"], parcours["produit"]])),
        "agences": _u(clients["agence"]),
        "villes": _u(clients["ville"]),
        "canaux": _u(pd.concat([parcours["canal"], contrats["canal_souscription"]])),
        "segments": _u(clients["segment_client"]),
        "etapes": _u(parcours["etape_parcours"]),
        "statuts_contrat": _u(contrats["statut_contrat"]),
        "niveaux_alerte": _u(data["evenements"]["niveau_alerte"]),
    }
