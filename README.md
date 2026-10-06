# NSIA Vie Assurances CI — Cockpit de pilotage du parcours client

Application **Streamlit** de pilotage managérial du parcours client, construite à partir du
classeur `NSIA_Vie_CI_Cartographie_Parcours_Client_Pilotage.xlsx` (données 100 % fictives).

## 🚀 Lancer l'application

```bash
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre sur `http://localhost:8501`. Le fichier Excel est déjà présent dans
`data/` ; vous pouvez le remplacer par une version plus récente tant que la structure des
feuilles (noms de colonnes) reste identique.

## 🗂️ Structure du projet

```
nsia_streamlit/
├── app.py                     # Point d'entrée : navigation, en-tête, filtres globaux
├── requirements.txt
├── README.md
├── data/
│   └── NSIA_Vie_CI_Cartographie_Parcours_Client_Pilotage.xlsx
├── utils/
│   ├── data_loader.py          # Lecture Excel, nettoyage, enrichissement, cache
│   └── calculations.py         # apply_filters() + tous les calculs de KPI centralisés
├── components/
│   ├── style.py                 # CSS (charte NSIA), en-tête, cartes, badges
│   ├── filters.py                # Barre de filtres globale
│   └── kpis.py                   # Composant carte KPI réutilisable
└── views/                      # Les 7 modules fonctionnels (1 fichier = 1 onglet)
    ├── vue_ensemble.py           # 🏠 Vue d'ensemble + Pilotage & actions managériales
    ├── parcours_client.py        # 🗺️ Parcours interactif étape → sous-étapes → stats
    ├── arbre_decisions.py        # 🔀 Arbre des décisions (diagramme de flux Sankey)
    ├── frictions_blocages.py     # ⚠️ Frictions & blocages
    ├── reclamations_incidents.py # 📣 Réclamations & incidents
    ├── agences_canaux.py         # 🏢 Agences & canaux (+ carte)
    └── produits.py               # 📦 Produits (fiche + comparatif)
```

## 🧭 Onglets

Conformément au cahier des charges, l'application compte **7 onglets** (l'ancien onglet
« Pilotage Manager » des maquettes visuelles a été **fusionné dans « Vue d'ensemble »**, comme
demandé explicitement dans les instructions : section *« Pilotage & actions managériales »*
en bas de la page d'accueil).

## 🔎 Filtres

- **Barre principale** (identique sur toutes les pages, cohérente entre onglets) : Période,
  Produit, Agence, Ville, Canal, Segment client, + bouton **Réinitialiser**. C'est la barre
  visible sur les maquettes fournies.
- **Filtres avancés** (tiroir dépliable `⚙️ Filtres avancés`, sous la barre principale) :
  Étape du parcours, Statut du contrat, Niveau d'alerte. Ces 3 dimensions sont demandées dans
  le cahier des charges (§9) mais n'apparaissent pas dans les maquettes visuelles (qui
  n'affichent que 6 filtres) : elles sont donc disponibles, sans surcharger l'en-tête.
- Sur les pages **Parcours Client** et **Arbre des décisions**, l'étape se sélectionne aussi
  directement via les boutons dédiés (logique demandée au §3/§4 : un seul composant dynamique,
  pas une page par étape).
- Chaque page applique les filtres **uniquement sur les colonnes qu'elle possède réellement**
  (`utils/calculations.py::apply_filters`), donc un filtre "impossible" (ex. produit + agence
  qui ne se croisent jamais) affiche un message clair plutôt qu'une erreur.

## 🧮 Données : hypothèses et choix documentés

Le fichier source ne contient pas nativement certaines colonnes demandées dans le cahier des
charges. Plutôt que d'inventer des données, les choix suivants ont été faits et sont indiqués
dans l'interface (tooltip / légende) à chaque fois :

| Besoin exprimé | Donnée source disponible | Traitement retenu |
|---|---|---|
| Satisfaction client (CSAT) | Absente | **Indice estimé** = 100 − (taux de friction + taux de non-respect SLA), affiché avec la mention « estimée » |
| Échéance d'une action managériale | Absente (feuille `Pilotage`) | **Échéance indicative** = date du jour + délai moyen (jours) de l'action, libellée comme telle |
| Date d'une friction | Absente (feuille `Frictions`) | Héritée de la date d'entrée d'étape du parcours associé (jointure sur `parcours_id`) |
| Coordonnées géographiques des agences | Absentes | Coordonnées réelles des **villes** de Côte d'Ivoire (donnée publique), utilisées pour la carte |

Toutes les autres données affichées proviennent directement du classeur Excel fourni, sans
donnée inventée, via les clés de liaison `client_id`, `contrat_id`, `produit_id`,
`parcours_id`, `friction_id`, `reclamation_id`, `evenement_id`.

## ✅ Tests effectués avant livraison

Le réseau n'étant pas disponible dans l'environnement de build, l'application n'a pas pu être
testée dans un vrai navigateur. Un **harnais de test hors-ligne** (`test_harness/`) simule
l'API Streamlit/Plotly utilisée par le code et exécute réellement toute la logique
pandas/plotly de chaque page :

- Chargement des 11 feuilles du classeur et vérification des volumes.
- 7 scénarios de filtres (aucun filtre, tous les filtres, période sans données, combinaison
  impossible, produit seul, agence + canal seuls, segment seul) × 7 pages = 49 rendus complets
  sans exception.
- Couverture exhaustive : chaque étape du parcours, chaque sous-étape, chaque produit, chaque
  agence, chaque ville, chaque dimension du bloc Frictions, chaque valeur de statut et de
  niveau d'alerte — testés individuellement et en combinaison.
- Vérification explicite des cas « aucun résultat » (message d'avertissement propre, aucune
  exception, aucun graphique cassé).

➡️ Avant toute mise en production, il est fortement recommandé de lancer `streamlit run app.py`
en local et de parcourir visuellement les 7 onglets, en particulier pour valider le rendu
CSS/HTML (couleurs, alignements) qui n'est pas vérifiable par un test automatisé hors-ligne.

## 🎨 Identité visuelle

Bleu marine (`#0B1F4D`), or (`#F2B705`), fond clair (`#F4F6FB`), cartes blanches à coins
arrondis avec ombre légère, navigation latérale sombre avec état actif doré — cohérent avec
les maquettes fournies.
