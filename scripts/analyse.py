"""
Analyse : lit toutes les extractions datées de data/ et produit docs/data/stats.json pour le site.
Chaque chiffre du JSON garde la trace de sa requête, de sa date et de son canal.
"""
import csv
import datetime as dt
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import config  # noqa: E402
from collect import norm, variante  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(RACINE, "data")
SORTIE = os.path.join(RACINE, "docs", "data", "stats.json")
EXPERIENCE = {"D": "Débutant accepté", "S": "Expérience souhaitée", "E": "Expérience exigée"}
DEP_REGION = {d: r for r, ds in config.REGIONS.items() for d in ds}


def lire(chemin):
    if not os.path.exists(chemin):
        return []
    with open(chemin, encoding="utf-8") as f:
        lignes = list(csv.DictReader(f))
    # la variante est recalculée avec la configuration actuelle (exclusions comprises)
    for l in lignes:
        if "intitule" in l and "variante_metier" in l:
            l["variante_metier"] = variante(l["intitule"])
    return lignes


def top(compteur, n=15):
    return [{"label": k, "n": v} for k, v in compteur.most_common(n) if k]


def part(n, total):
    return round(100 * n / total, 1) if total else 0


def salaire_mensuel(libelle):
    """Montant minimum affiché, ramené au mois. Ce n'est pas un salaire réel : c'est ce que l'offre affiche."""
    t = norm(libelle)
    nombres = [float(x.replace(",", ".")) for x in re.findall(r"(\d+(?:[.,]\d+)?)", t)]
    nombres = [x for x in nombres if x >= 5]
    if not nombres:
        return None
    m = nombres[0]
    if "annuel" in t:
        m = m / 12
    elif "horaire" in t:
        m = m * 151.67
    elif "mensuel" not in t:
        return None
    return round(m) if 300 <= m <= 15000 else None


def mediane(xs):
    xs = sorted(xs)
    if not xs:
        return None
    k = len(xs) // 2
    return xs[k] if len(xs) % 2 else round((xs[k - 1] + xs[k]) / 2)


def main():
    dates = sorted(os.path.basename(d) for d in glob.glob(os.path.join(DATA, "20??-??-??")) if os.path.isdir(d))
    journal = lire(os.path.join(DATA, "extractions.csv"))
    # une seule ligne par (date, requête) : la dernière de la journée
    derniers = {}
    for l in journal:
        derniers[(l["date"], l["requete_id"])] = l
    journal = sorted(derniers.values(), key=lambda l: (l["date"], l["requete_id"]))
    sources = {}
    for l in journal:
        sources[l["requete_id"]] = {k: l[k] for k in ("requete", "canal", "parametres", "limites")}

    stats = {"metier": config.METIER, "rome": config.ROME,
             "genere_le": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
             "dates": dates, "extractions": journal, "sources": sources}
    if not dates:
        stats["vide"] = True
        os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
        json.dump(stats, open(SORTIE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("Aucune extraction : stats.json vide écrit.")
        return

    # Séries temporelles (le marché qui bouge)
    series = defaultdict(list)
    for l in journal:
        series[l["requete_id"]].append({"date": l["date"], "total": int(l["total_annonce"] or 0)})
    stats["series"] = series

    derniere = dates[-1]
    offres = lire(os.path.join(DATA, derniere, "offres.csv"))
    metier = [o for o in offres if o["variante_metier"]]
    n = len(metier)
    stats["derniere"] = derniere
    stats["comptes"] = {"offres_uniques": len(offres), "offres_metier": n,
                        "offres_metier_ft": sum(1 for o in metier if o["canal"].startswith("France Travail")),
                        "offres_metier_lba": sum(1 for o in metier if o["canal"].startswith("La Bonne")),
                        "alternance": sum(1 for o in metier if o["alternance"] == "oui")}

    # 1. Le métier tel que le marché le nomme
    stats["variantes"] = top(Counter(o["variante_metier"] for o in metier), 10)
    intit = Counter(re.sub(r"\s+", " ", re.sub(r"\(.*?\)|[hH]\s*/\s*[fF]|[fF]\s*/\s*[hH]", "", o["intitule"])).strip(" -–")
                    for o in metier)
    stats["intitules"] = top(intit, 15)

    # 2. Ce que disent les offres
    regions = Counter(DEP_REGION.get(o["departement"], "Non renseignée") for o in metier)
    stats["regions"] = top(regions, 15)
    stats["departements"] = top(Counter(o["departement"] or "?" for o in metier), 12)
    stats["contrats"] = top(Counter(o["contrat"] or "Non renseigné" for o in metier), 10)
    stats["experience"] = top(Counter(EXPERIENCE.get(o["experience_exigee"], "") for o in metier
                                      if o["canal"].startswith("France Travail")), 5)
    stats["tailles"] = top(Counter(o["tranche_effectif"] or "Non renseignée" for o in metier), 12)
    avec_sal = [o for o in metier if o["salaire_affiche"].strip()]
    mensuels = [m for m in (salaire_mensuel(o["salaire_affiche"]) for o in avec_sal if o["alternance"] != "oui") if m]
    stats["salaires"] = {
        "n_ft": stats["comptes"]["offres_metier_ft"], "n_affiche": len(avec_sal),
        "part_affiche": part(len(avec_sal), stats["comptes"]["offres_metier_ft"]),
        "n_montants": len(mensuels), "mediane_min_mensuel": mediane(mensuels),
        "min": min(mensuels) if mensuels else None, "max": max(mensuels) if mensuels else None,
        "exemples": top(Counter(o["salaire_affiche"] for o in avec_sal), 6)}
    fac = lire(os.path.join(DATA, derniere, "facettes_ft.csv"))
    stats["facettes"] = defaultdict(list)
    for f in fac:
        if f["requete_id"] == "ft_crm_m1705":
            stats["facettes"][f["filtre"]].append({"label": f["valeur"], "n": int(f["nb"] or 0)})

    # 3. Compétences et outils comptés dans les annonces, confrontés à la formation
    formation = {l["competence"]: l for l in lire(os.path.join(DATA, "formation.csv"))}
    cpt = Counter(k for o in metier for k in o["mots_cles"].split(" | ") if k)
    comp = []
    for lib, cat, _m in config.COMPETENCES:
        f = formation.get(lib, {})
        comp.append({"label": lib, "categorie": cat, "n": cpt.get(lib, 0), "part": part(cpt.get(lib, 0), n),
                     "formation": f.get("couverte", "À compléter"), "justification": f.get("justification", "")})
    comp.sort(key=lambda c: -c["n"])
    stats["competences"] = comp
    stats["competences_ft"] = top(Counter(c.strip() for o in metier for c in o["competences_ft"].split("|")
                                          if c.strip()), 12)

    # 4. Comment le métier bouge : comparaison de la première et de la dernière extraction
    if len(dates) >= 2:
        premiere = [o for o in lire(os.path.join(DATA, dates[0], "offres.csv")) if o["variante_metier"]]
        c0 = Counter(k for o in premiere for k in o["mots_cles"].split(" | ") if k)
        evo = []
        for lib, _cat, _m in config.COMPETENCES:
            p0, p1 = part(c0.get(lib, 0), len(premiere)), part(cpt.get(lib, 0), n)
            evo.append({"label": lib, "avant": p0, "apres": p1, "delta": round(p1 - p0, 1)})
        evo.sort(key=lambda e: -e["delta"])
        stats["evolution"] = {"de": dates[0], "a": derniere, "n_avant": len(premiere), "n_apres": n, "mots": evo}

    # 5. Les acteurs
    ent = Counter(o["entreprise"].strip() for o in metier if o["entreprise"].strip())
    stats["entreprises"] = top(ent, 20)
    noms_offres = {norm(o["entreprise"]) for o in offres if o["entreprise"]}
    recs = lire(os.path.join(DATA, derniere, "recruteurs_lba.csv"))
    cache = [r for r in recs if r["entreprise"] and norm(r["entreprise"]) not in noms_offres]
    stats["marche_cache"] = {"n_recruteurs": len(recs), "n_sans_offre": len(cache),
                             "liste": [{k: r[k] for k in ("entreprise", "commune", "secteur", "taille", "url")}
                                       for r in cache[:30]],
                             "secteurs": top(Counter(r["secteur"] for r in cache if r["secteur"]), 8)}

    # Profondeur dans le temps : offres encore en ligne, par semaine de publication
    def lundi(d):
        try:
            j = dt.date.fromisoformat(d[:10])
        except ValueError:
            return None
        return j - dt.timedelta(days=j.weekday())
    ref = dt.date.fromisoformat(derniere)
    debut = lundi(derniere) - dt.timedelta(weeks=7)
    semaines = [debut + dt.timedelta(weeks=k) for k in range(8)]
    toutes = Counter(lundi(o["date_publication"]) for o in offres if o["date_publication"])
    met = Counter(lundi(o["date_publication"]) for o in metier if o["date_publication"])
    par_var = defaultdict(Counter)
    for o in metier:
        if o["date_publication"]:
            par_var[o["variante_metier"]][lundi(o["date_publication"])] += 1
    anciennes = sum(1 for o in metier if o["date_publication"] and lundi(o["date_publication"]) < debut)
    stats["publication"] = {
        "reference": derniere,
        "semaines": [{"debut": s.isoformat(), "fin": min(s + dt.timedelta(days=6), ref).isoformat(),
                      "n_metier": met.get(s, 0), "n_collectees": toutes.get(s, 0)} for s in semaines],
        "variantes": {v: [c.get(s, 0) for s in semaines] for v, c in par_var.items()},
        "avant": anciennes, "sans_date": sum(1 for o in metier if not o["date_publication"])}

    # La veille : dernières offres du métier
    metier.sort(key=lambda o: o["date_publication"], reverse=True)
    stats["veille"] = [{k: o[k] for k in ("date_publication", "intitule", "entreprise", "commune", "contrat",
                                          "alternance", "canal", "url")} for o in metier[:60]]

    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    with open(SORTIE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)
    print(f"stats.json écrit : {n} offres du métier au {derniere}, {len(dates)} extraction(s).")


if __name__ == "__main__":
    main()
