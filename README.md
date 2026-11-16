# Enquête métier : Chargé·e CRM (ROME M1705)

**Site :** https://enouhaylla-collab.github.io/projet-alternance-/
**Auteure :** Nouhaylla El Achheb · Master 2 Marketing, Vente, parcours Marketing opérationnel et digital (IAE Clermont-Auvergne)

Ce dépôt est le compte rendu de mon enquête sur le métier de **chargé·e CRM / marketing automation**, présenté en pages web, et l'outil qui fait la veille à ma place : chaque jour, un script interroge des API publiques, enregistre une extraction datée, et le site affiche ce qu'elle trouve.

## Point de départ (v0 du 22/09)

Métier : Chargé·e de CRM (Customer Relationship Manager, spécialiste marketing automation, chargé·e d'inbound marketing), code ROME **M1705**.
Questions posées au marché :
1. Quelles compétences reviennent le plus dans les offres pour ce métier ?
2. Où sont localisées principalement les offres ?
3. Quelle taille d'entreprise recrute le plus ?
4. Quelle expérience est demandée ?

## Ce que dit le site (pages)

| Page | Contenu |
|---|---|
| 1 · Le métier | intitulés réels dans les offres, variantes, code ROME, mes questions |
| 2 · Les offres | volume dans le temps, géographie, contrats, expérience, taille, salaires **affichés** ; chaque chiffre avec requête, date, canal, limites |
| 3 · Compétences | compétences et outils comptés dans les annonces, confrontés à ma formation (`data/formation.csv`) |
| 4 · Évolution | mots qui montent entre deux extractions, source emploi citée (Apec), professionnels rencontrés |
| 5 · Acteurs | entreprises qui recrutent l'intitulé, marché caché (La Bonne Alternance), veille en direct |
| 6 · Mon année | ma position et trois actions datées, dont une qui produit une preuve |
| 7 · Méthode | canaux, scripts, automatisation, règle RGPD |

## Canaux branchés

| Canal | Accès | Ce qui est récupéré | Limites |
|---|---|---|---|
| France Travail, API Offres d'emploi v2 | OAuth2 (identifiant + secret) | offres, totaux annoncés, répartitions (`filtresPossibles`) | 150 offres par page, 1 150 au maximum par requête ; offres publiées sur France Travail et ses partenaires seulement |
| La Bonne Alternance, API offres | jeton | offres en alternance M1705 (LBA et partenaires) | alternance uniquement |
| La Bonne Alternance, API recruteurs | jeton | entreprises susceptibles de recruter (marché caché) | prédiction d'embauche, pas une offre |

**Pas de scraping** : aucune donnée de LinkedIn, de l'APEC ni d'Indeed.

## Scripts

- `scripts/config.py` : métier, requêtes envoyées, variantes d'intitulé, dictionnaire de compétences, régions.
- `scripts/collect.py` : appelle les API et écrit
  - `data/AAAA-MM-JJ/offres.csv` : une ligne par offre (canal, requêtes, intitulé, variante, entreprise, lieu, contrat, expérience, taille, salaire affiché, compétences détectées, lien) ;
  - `data/AAAA-MM-JJ/facettes_ft.csv` : répartitions calculées par France Travail ;
  - `data/AAAA-MM-JJ/recruteurs_lba.csv` : entreprises du marché caché ;
  - `data/extractions.csv` : **journal** (date, heure, canal, requête, paramètres, total annoncé, offres récupérées, limites).
- `scripts/analyse.py` : lit toutes les extractions et produit `docs/data/stats.json`, lu par le site.

Lancer à la main :
```bash
pip install -r requirements.txt
export FT_CLIENT_ID=... FT_CLIENT_SECRET=... LBA_TOKEN=...
python scripts/collect.py && python scripts/analyse.py
```

## Automatisation

`.github/workflows/veille.yml` lance la collecte puis l'analyse **chaque jour vers 7 h 17 (heure de Paris)** et enregistre les nouvelles données dans le dépôt (commit « Veille du AAAA-MM-JJ »). Le site est publié par GitHub Pages depuis le dossier `docs/`.
Les clés sont des **secrets du dépôt** (`FT_CLIENT_ID`, `FT_CLIENT_SECRET`, `LBA_TOKEN`), jamais dans le code.

## Règle RGPD pour les contacts

- Les scripts ne collectent **aucune donnée personnelle** : uniquement des offres et des entreprises (personnes morales).
- Les professionnels cités sur le site le sont par leur **fonction** et leur **entreprise**, pour la seule finalité de cette enquête ; leur nom n'apparaît qu'avec leur accord, et il est retiré sur simple demande.
- Aucun contact n'est réutilisé à d'autres fins.

## Lire un chiffre

Chaque chiffre du site affiche : **la requête** (paramètres exacts), **la date** de l'extraction, **le canal** et **ses limites**. Les salaires sont des salaires **affichés** dans les offres, pas des salaires réels.
