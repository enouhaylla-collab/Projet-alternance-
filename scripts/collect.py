"""
Veille : interroge les API officielles et enregistre une extraction datée.

  data/AAAA-MM-JJ/offres.csv          une ligne par offre (France Travail + La Bonne Alternance)
  data/AAAA-MM-JJ/facettes_ft.csv     répartitions calculées par France Travail (contrats, expérience...)
  data/AAAA-MM-JJ/recruteurs_lba.csv  entreprises « qui recrutent » sans offre publiée (marché caché)
  data/extractions.csv                journal : date, canal, requête, total annoncé, offres récupérées, limites

Variables d'environnement : FT_CLIENT_ID, FT_CLIENT_SECRET, LBA_TOKEN (secrets GitHub).
Aucune donnée de LinkedIn, de l'APEC ni d'Indeed : uniquement des API publiques avec clé.
"""
import csv
import datetime as dt
import json
import os
import re
import sys
import time
import unicodedata

import requests

sys.path.insert(0, os.path.dirname(__file__))
import config  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(RACINE, "data")
FT_TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
FT_SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
LBA_SEARCH_URL = "https://api.apprentissage.beta.gouv.fr/api/job/v1/search"

OFFRES_COLS = ["date_extraction", "canal", "requetes", "id", "date_publication", "intitule", "variante_metier",
               "entreprise", "siret", "departement", "commune", "contrat", "alternance", "experience",
               "experience_exigee", "tranche_effectif", "secteur", "salaire_affiche", "competences_ft",
               "mots_cles", "url"]


def norm(s):
    s = unicodedata.normalize("NFD", str(s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def variante(intitule):
    t = " " + norm(intitule) + " "
    if any(x in t for x in config.EXCLUSIONS):
        return ""
    for nom, motifs in config.VARIANTES:
        if any(m in t for m in motifs):
            return nom
    return ""


def mots_cles(texte):
    t = " " + norm(texte).replace("\n", " ") + " "
    return [lib for lib, _cat, motifs in config.COMPETENCES if any(m in t for m in motifs)]


def departement(libelle, code_postal=""):
    m = re.match(r"\s*(2A|2B|97\d|\d{2})\s*-", str(libelle or ""))
    if m:
        return m.group(1)
    cp = str(code_postal or "")
    if len(cp) == 5:
        return cp[:3] if cp.startswith("97") else cp[:2]
    return ""


def secret(nom):
    """Valeur d'un secret, sans espace ni retour à la ligne collés par erreur."""
    return (os.environ.get(nom) or "").strip()


def appel(methode, url, essais=5, **kw):
    for i in range(essais):
        r = requests.request(methode, url, timeout=40, **kw)
        if r.status_code == 429:
            time.sleep(1.5 * (i + 1))
            continue
        return r
    return r


# ---------------- France Travail ----------------
def token_ft():
    r = appel("POST", FT_TOKEN_URL, data={
        "grant_type": "client_credentials", "client_id": secret("FT_CLIENT_ID"),
        "client_secret": secret("FT_CLIENT_SECRET"), "scope": "api_offresdemploiv2 o2dsoffre"})
    if r.status_code != 200:
        raise RuntimeError(f"Connexion France Travail refusée (HTTP {r.status_code}) : {r.text[:300]}")
    return r.json()["access_token"]


def recherche_ft(token, params, detail):
    """Renvoie (total annoncé, offres récupérées, facettes)."""
    entetes = {"Authorization": "Bearer " + token, "Accept": "application/json"}
    offres, total, facettes, debut = [], 0, [], 0
    while debut < 1150:
        p = dict(params, range=f"{debut}-{min(debut + 149, 1149)}")
        r = appel("GET", FT_SEARCH_URL, headers=entetes, params=p)
        if r.status_code == 204:
            break
        if r.status_code not in (200, 206):
            raise RuntimeError(f"France Travail HTTP {r.status_code} : {r.text[:200]}")
        j = r.json()
        plage = r.headers.get("Content-Range", "")
        if "/" in plage:
            total = int(plage.split("/")[-1] or 0)
        if debut == 0:
            facettes = j.get("filtresPossibles", []) or []
        res = j.get("resultats", []) or []
        offres.extend(res)
        if not detail or len(res) < 150 or debut + 150 >= total:
            break
        debut += 150
        time.sleep(0.3)
    if not total:
        total = len(offres)
    return total, (offres if detail else []), facettes


def ligne_ft(o, date):
    lieu = o.get("lieuTravail") or {}
    ent = o.get("entreprise") or {}
    sal = o.get("salaire") or {}
    comp = [c.get("libelle", "") for c in (o.get("competences") or [])]
    texte = " ".join([o.get("intitule", ""), o.get("description", ""), " ".join(comp)])
    contrat = o.get("typeContratLibelle") or o.get("typeContrat") or ""
    alternance = bool(o.get("alternance")) or "apprenti" in norm(texte) or "alternance" in norm(o.get("intitule"))
    return {
        "date_extraction": date, "canal": "France Travail", "id": "FT-" + str(o.get("id")),
        "date_publication": (o.get("dateCreation") or "")[:10], "intitule": o.get("intitule", ""),
        "variante_metier": variante(o.get("intitule")), "entreprise": ent.get("nom", ""),
        "siret": ent.get("siret", ""), "departement": departement(lieu.get("libelle"), lieu.get("codePostal")),
        "commune": lieu.get("libelle", ""), "contrat": contrat, "alternance": "oui" if alternance else "non",
        "experience": o.get("experienceLibelle", ""), "experience_exigee": o.get("experienceExige", ""),
        "tranche_effectif": o.get("trancheEffectifEtab", ""), "secteur": o.get("secteurActiviteLibelle", ""),
        "salaire_affiche": sal.get("libelle", "") or sal.get("commentaire", ""),
        "competences_ft": " | ".join(comp), "mots_cles": " | ".join(mots_cles(texte)),
        "url": (o.get("origineOffre") or {}).get("urlOrigine")
        or f"https://candidat.francetravail.fr/offres/recherche/detail/{o.get('id')}",
    }


# ---------------- La Bonne Alternance ----------------
def appel_lba(lat, lon, rayon):
    r = appel("GET", LBA_SEARCH_URL,
              params={"romes": config.LBA_ROMES, "latitude": lat, "longitude": lon, "radius": rayon},
              headers={"Authorization": "Bearer " + secret("LBA_TOKEN"), "Accept": "application/json"})
    if r.status_code != 200:
        raise RuntimeError(f"La Bonne Alternance HTTP {r.status_code} : {r.text[:200]}")
    j = r.json()
    return j.get("jobs", []) or [], j.get("recruiters", []) or []


def recherche_lba():
    """Offres autour de 10 grandes villes ; recruteurs (marché caché) autour de Clermont-Ferrand."""
    jobs, vus = [], set()
    for _ville, lat, lon, rayon in config.LBA_POINTS_OFFRES:
        js, _ = appel_lba(lat, lon, rayon)
        for j in js:
            cle = (j.get("identifier") or {}).get("id") or json.dumps(j.get("offer", {}).get("title"))
            if cle not in vus:
                vus.add(cle)
                jobs.append(j)
        time.sleep(0.4)
    _v, lat, lon, rayon = config.LBA_POINT_RECRUTEURS
    _, recs = appel_lba(lat, lon, rayon)
    return jobs, recs


def lieu_lba(w):
    adr = ((w.get("location") or {}).get("address")) or ""
    m = re.search(r"(\d{5})\s+(.+)$", adr)
    cp, commune = (m.group(1), m.group(2)) if m else ("", adr)
    return departement("", cp), commune


def ligne_lba(j, date):
    off, w, ident = j.get("offer") or {}, j.get("workplace") or {}, j.get("identifier") or {}
    dep, commune = lieu_lba(w)
    texte = " ".join([off.get("title", ""), off.get("description", ""), " ".join(off.get("desired_skills") or [])])
    partenaire = ident.get("partner_label") or ""
    return {
        "date_extraction": date, "canal": "La Bonne Alternance" + (f" / {partenaire}" if partenaire else ""),
        "id": "LBA-" + str(ident.get("id") or ident.get("partner_job_id")),
        "date_publication": ((off.get("publication") or {}).get("creation") or "")[:10],
        "intitule": off.get("title", ""), "variante_metier": variante(off.get("title")),
        "entreprise": w.get("brand") or w.get("legal_name") or w.get("name") or "", "siret": w.get("siret") or "",
        "departement": dep, "commune": commune,
        "contrat": ", ".join((j.get("contract") or {}).get("type") or []) or "Alternance", "alternance": "oui",
        "experience": "", "experience_exigee": "", "tranche_effectif": w.get("size") or "",
        "secteur": ((w.get("domain") or {}).get("naf") or {}).get("label") or "", "salaire_affiche": "",
        "competences_ft": "", "mots_cles": " | ".join(mots_cles(texte)), "url": (j.get("apply") or {}).get("url", ""),
    }


def ligne_recruteur(rc, date):
    w = rc.get("workplace") or {}
    dep, commune = lieu_lba(w)
    naf = (w.get("domain") or {}).get("naf") or {}
    return {"date_extraction": date, "entreprise": w.get("brand") or w.get("legal_name") or w.get("name") or "",
            "siret": w.get("siret") or "", "departement": dep, "commune": commune,
            "naf": naf.get("code", ""), "secteur": naf.get("label", ""), "taille": w.get("size") or "",
            "url": (rc.get("apply") or {}).get("url", "")}


# ---------------- Écriture ----------------
def ecrire_csv(chemin, lignes, colonnes):
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colonnes, extrasaction="ignore")
        w.writeheader()
        w.writerows(lignes)


def journal(lignes):
    chemin = os.path.join(DATA, "extractions.csv")
    cols = ["date", "heure_utc", "canal", "requete_id", "requete", "parametres", "total_annonce",
            "recuperees", "limites"]
    neuf = not os.path.exists(chemin)
    with open(chemin, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        if neuf:
            w.writeheader()
        w.writerows(lignes)


def collecte_ft(date, heure, offres, facettes, log):
    tok = token_ft()
    for q in config.REQUETES_FT:
        total, res, fac = recherche_ft(tok, q["params"], q["detail"])
        for o in res:
            l = ligne_ft(o, date)
            if l["id"] in offres:
                offres[l["id"]]["requetes"] += " " + q["id"]
            else:
                l["requetes"] = q["id"]
                offres[l["id"]] = l
        for f in fac:
            for a in f.get("agregation", []) or []:
                facettes.append({"requete_id": q["id"], "filtre": f.get("filtre"),
                                 "valeur": a.get("valeurPossible"), "nb": a.get("nbResultats")})
        log.append({"date": date, "heure_utc": heure, "canal": "France Travail (API Offres d'emploi v2)",
                    "requete_id": q["id"], "requete": q["libelle"],
                    "parametres": json.dumps(q["params"], ensure_ascii=False), "total_annonce": total,
                    "recuperees": len(res), "limites": q["limites"]})
        print(f"{q['id']}: {total} annoncées, {len(res)} récupérées")
        time.sleep(0.5)


def collecte_lba(date, heure, offres, log):
    jobs, recs = recherche_lba()
    for j in jobs:
        if (j.get("offer") or {}).get("status", "Active") != "Active":
            continue
        l = ligne_lba(j, date)
        l["requetes"] = "lba_m1705"
        offres.setdefault(l["id"], l)
    villes = ", ".join(v for v, *_ in config.LBA_POINTS_OFFRES)
    params = json.dumps({"romes": config.LBA_ROMES, "rayon_km": 100, "villes": villes}, ensure_ascii=False)
    v, lat, lon, rayon = config.LBA_POINT_RECRUTEURS
    params_rec = json.dumps({"romes": config.LBA_ROMES, "autour_de": v, "rayon_km": rayon}, ensure_ascii=False)
    log.append({"date": date, "heure_utc": heure, "canal": "La Bonne Alternance (API offres)",
                "requete_id": "lba_m1705", "requete": "Offres en alternance, code ROME M1705, 10 grandes villes",
                "parametres": params, "total_annonce": len(jobs), "recuperees": len(jobs),
                "limites": config.LBA_LIMITES})
    log.append({"date": date, "heure_utc": heure, "canal": "La Bonne Alternance (API recruteurs)",
                "requete_id": "lba_recruteurs", "requete": f"Entreprises susceptibles de recruter, M1705, autour de {v}",
                "parametres": params_rec, "total_annonce": len(recs), "recuperees": len(recs),
                "limites": config.LBA_LIMITES})
    print(f"lba: {len(jobs)} offres, {len(recs)} recruteurs")
    return [ligne_recruteur(r, date) for r in recs]


def main():
    maintenant = dt.datetime.now(dt.timezone.utc)
    date, heure = maintenant.strftime("%Y-%m-%d"), maintenant.strftime("%H:%M")
    offres, facettes, recruteurs, log, erreurs = {}, [], [], [], []

    if secret("FT_CLIENT_ID"):
        try:
            collecte_ft(date, heure, offres, facettes, log)
        except Exception as e:   # une source en panne n'empêche pas l'autre
            erreurs.append(f"France Travail : {e}")
    else:
        print("FT_CLIENT_ID absent : France Travail ignoré")

    if secret("LBA_TOKEN"):
        try:
            recruteurs = collecte_lba(date, heure, offres, log)
        except Exception as e:
            erreurs.append(f"La Bonne Alternance : {e}")
    else:
        print("LBA_TOKEN absent : La Bonne Alternance ignorée")

    for err in erreurs:
        print("ERREUR", err)
    if not log:
        print("Aucune source n'a répondu : rien n'est enregistré.")
        sys.exit(1 if erreurs else 0)
    dossier = os.path.join(DATA, date)
    os.makedirs(dossier, exist_ok=True)
    ecrire_csv(os.path.join(dossier, "offres.csv"), list(offres.values()), OFFRES_COLS)
    ecrire_csv(os.path.join(dossier, "facettes_ft.csv"), facettes, ["requete_id", "filtre", "valeur", "nb"])
    ecrire_csv(os.path.join(dossier, "recruteurs_lba.csv"), recruteurs,
               ["date_extraction", "entreprise", "siret", "departement", "commune", "naf", "secteur", "taille", "url"])
    journal(log)
    print(f"Extraction du {date} : {len(offres)} offres uniques enregistrées dans {dossier}")
    if erreurs:
        print("::warning::Extraction partielle : " + " / ".join(erreurs))


if __name__ == "__main__":
    main()
