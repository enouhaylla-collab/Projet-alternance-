/* Postul'IA · site d'enquête métier : rendu des pages à partir de data/stats.json */
const PAGES = [
  ["index.html", "Accueil"], ["metier.html", "1 · Le métier"], ["offres.html", "2 · Les offres"],
  ["competences.html", "3 · Compétences"], ["evolution.html", "4 · Évolution"], ["acteurs.html", "5 · Acteurs"],
  ["plan.html", "6 · Mon année"], ["methode.html", "7 · Méthode"]
];
const $ = (s, r = document) => r.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const fr = n => (n == null ? "—" : Number(n).toLocaleString("fr-FR"));
const dateFr = d => d ? new Date(d + "T12:00:00").toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" }) : "—";
let S = null;

function header() {
  const here = location.pathname.split("/").pop() || "index.html";
  const nav = PAGES.map(([h, l]) => `<a href="${h}" class="${h === here ? "on" : ""}">${l}</a>`).join("");
  document.body.insertAdjacentHTML("afterbegin",
    `<header class="site"><div class="in"><a class="brand" href="index.html">Enquête métier · <span>Chargé·e CRM</span></a><nav class="main">${nav}</nav></div></header>`);
  document.body.insertAdjacentHTML("beforeend",
    `<footer>Site généré à partir de données publiques datées (France Travail, La Bonne Alternance) · <a href="https://github.com/enouhaylla-collab/projet-alternance-">dépôt GitHub</a> · <span id="maj"></span></footer>`);
}

/* Encadré source : requête, date, canal, limites */
function src(reqId, extra = "") {
  const s = (S.sources || {})[reqId];
  if (!s) return `<div class="src">${extra}</div>`;
  return `<div class="src"><b>Requête :</b> ${esc(s.requete)} <span class="muted">(${esc(s.parametres)})</span><br>
  <b>Date :</b> extraction du ${dateFr(S.derniere)} · <b>Canal :</b> ${esc(s.canal)}<br>
  <b>Limites :</b> ${esc(s.limites)}${extra ? "<br>" + extra : ""}</div>`;
}
function srcMetier(extra = "") {
  return `<div class="src"><b>Requêtes :</b> union des requêtes détaillées France Travail (« CRM », « marketing automation », « marketing relationnel », « fidélisation client », « CRM » dans M1705) et des offres La Bonne Alternance M1705, puis filtre sur l'intitulé (variantes du métier, page 1).<br>
  <b>Date :</b> extraction du ${dateFr(S.derniere)} · <b>Canaux :</b> France Travail, La Bonne Alternance<br>
  <b>Limites :</b> France Travail renvoie au plus 1 150 offres par requête ; une offre absente de ces canaux (site carrière, réseau) n'est pas comptée ; le filtre par intitulé peut écarter des offres mal titrées.${extra ? "<br>" + extra : ""}</div>`;
}
function bars(items, total, max = 12) {
  if (!items || !items.length) return `<p class="muted">Pas encore de donnée.</p>`;
  const m = Math.max(...items.map(i => i.n));
  return items.slice(0, max).map(i => `<div class="bar"><div class="lab">${esc(i.label)}</div><div class="track"><div class="fill" style="width:${(100 * i.n / m).toFixed(1)}%"></div></div><div class="num">${fr(i.n)}${total ? ` · ${Math.round(100 * i.n / total)} %` : ""}</div></div>`).join("");
}
function kpi(v, l) { return `<div class="card kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`; }
function vide() { return `<div class="todo"><b>Pas encore d'extraction.</b> La veille n'a pas encore tourné : les chiffres apparaîtront après le premier passage du script (voir page 7).</div>`; }
function lineChart(el, datasets, labels) {
  if (!window.Chart) return;
  new Chart(el, { type: "line", data: { labels, datasets: datasets.map((d, i) => ({ label: d.label, data: d.data, tension: .25, borderWidth: 2, borderColor: ["#5b3df5", "#e8573a", "#0f8a5c", "#b7791f"][i % 4], backgroundColor: "transparent", pointRadius: 4 })) },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "bottom" } }, scales: { y: { beginAtZero: true } } } });
}

const RENDU = {
  index() {
    if (S.vide) { $("#chiffres").innerHTML = vide(); return; }
    const c = S.comptes;
    $("#chiffres").innerHTML = `<div class="grid g4">${kpi(fr(c.offres_metier), "offres du métier dans la dernière extraction")}
      ${kpi(fr(c.alternance), "dont en alternance")}${kpi(fr(S.marche_cache.n_sans_offre), "entreprises du marché caché (sans offre publiée)")}
      ${kpi(fr(S.dates.length), "extractions datées depuis le début")}</div>${srcMetier()}`;
  },
  metier() {
    if (S.vide) { $("#donnees").innerHTML = vide(); return; }
    $("#variantes").innerHTML = bars(S.variantes, S.comptes.offres_metier) + srcMetier("Chaque offre est rattachée à la première variante dont un motif apparaît dans son intitulé (liste dans scripts/config.py). Sont exclus les intitulés techniques ou commerciaux qui citent le CRM sans être le métier (développeur, testeur, consultant Dynamics, commercial, missions freelance…).");
    $("#intitules").innerHTML = bars(S.intitules, null, 15) + srcMetier("Intitulés nettoyés des mentions (H/F) et des parenthèses.");
  },
  offres() {
    if (S.vide) { $("#donnees").innerHTML = vide(); return; }
    const labels = S.dates;
    const ds = Object.entries(S.series).filter(([k]) => k !== "lba_recruteurs").map(([k, v]) => ({ label: (S.sources[k] || {}).requete || k, data: labels.map(d => (v.find(x => x.date === d) || {}).total ?? null) }));
    lineChart($("#serie"), ds, labels.map(dateFr));
    $("#serie-src").innerHTML = `<div class="src"><b>Requêtes :</b> une courbe par requête (détail dans le tableau ci-dessous).<br><b>Dates :</b> ${S.dates.map(dateFr).join(", ")} · <b>Canaux :</b> France Travail, La Bonne Alternance<br><b>Limites :</b> « total annoncé » = nombre renvoyé par l'API le jour de l'extraction (offres en ligne ce jour-là), pas un flux de nouvelles offres.</div>`;
    $("#journal").innerHTML = `<table><tr><th>Date</th><th>Canal</th><th>Requête</th><th>Total annoncé</th><th>Récupérées</th></tr>${S.extractions.slice().reverse().map(e => `<tr><td>${dateFr(e.date)}</td><td>${esc(e.canal)}</td><td>${esc(e.requete)}<br><span class="muted">${esc(e.parametres)}</span></td><td>${fr(e.total_annonce)}</td><td>${Number(e.recuperees) === 0 && Number(e.total_annonce) > 0 ? "comptage seul" : fr(e.recuperees)}</td></tr>`).join("")}</table>`;
    const n = S.comptes.offres_metier;
    $("#geo").innerHTML = bars(S.regions, n) + srcMetier();
    $("#deps").innerHTML = bars(S.departements, n) + srcMetier("Département lu dans le lieu de travail de l'offre.");
    $("#contrats").innerHTML = bars(S.contrats, n) + srcMetier() +
      (S.facettes && S.facettes.typeContrat ? `<h3 style="margin-top:16px">Répartition calculée par France Travail (toutes les offres de la requête)</h3>${bars(S.facettes.typeContrat)}${src("ft_crm_m1705", "Répartition fournie par l'API (filtresPossibles), sur toutes les offres de la requête et pas seulement celles récupérées.")}` : "");
    $("#experience").innerHTML = bars(S.experience, S.comptes.offres_metier_ft) + srcMetier("Champ « expérience exigée » de France Travail uniquement (D, S, E).");
    $("#tailles").innerHTML = bars(S.tailles, n) + srcMetier("Tranche d'effectif de l'établissement déclarée dans l'offre ; souvent non renseignée.");
    const s = S.salaires;
    $("#salaires").innerHTML = `<div class="grid g3">${kpi(s.part_affiche + " %", "des offres France Travail du métier affichent un salaire")}${kpi(s.mediane_min_mensuel ? fr(s.mediane_min_mensuel) + " €" : "—", "médiane du <b>minimum affiché</b>, ramené au mois (hors alternance)")}${kpi(fr(s.n_montants), "montants exploitables")}</div>
      <h3 style="margin-top:16px">Libellés de salaire les plus fréquents</h3>${bars(s.exemples, null, 6)}
      ${srcMetier("<b>Salaire affiché ≠ salaire réel :</b> c'est ce que le recruteur a écrit dans l'offre (souvent une fourchette basse, parfois absente). Les offres en alternance sont exclues du calcul : leur rémunération dépend de l'âge et de l'année de contrat (pourcentage du SMIC).")}`;
  },
  competences() {
    if (S.vide) { $("#donnees").innerHTML = vide(); return; }
    const n = S.comptes.offres_metier;
    const ligne = c => { const f = c.formation || ""; const cls = /^non/i.test(f) ? "no" : /^oui/i.test(f) ? "ok" : "mid"; return `<tr><td>${esc(c.label)}</td><td>${esc(c.categorie)}</td><td>${fr(c.n)}</td><td>${c.part} %</td><td><span class="pill ${cls}">${esc(f)}</span><br><span class="muted">${esc(c.justification)}</span></td></tr>`; };
    $("#table").innerHTML = `<table><tr><th>Compétence / outil</th><th>Type</th><th>Offres</th><th>Part</th><th>Ma formation</th></tr>${S.competences.filter(c => c.n > 0).map(ligne).join("")}</table>` + srcMetier("Comptage : une offre compte une fois par compétence si un des motifs du dictionnaire (scripts/config.py) apparaît dans son intitulé, sa description ou ses compétences. Colonne « Ma formation » : data/formation.csv.");
    const manque = S.competences.filter(c => c.n > 0 && !/^oui/i.test(c.formation || "")).slice(0, 8);
    $("#manque").innerHTML = manque.length ? `<ol>${manque.map(c => `<li><b>${esc(c.label)}</b> : demandé dans ${c.part} % des offres · ${esc(c.formation)}</li>`).join("")}</ol>` : "<p>Toutes les compétences comptées sont couvertes.</p>";
    $("#ft").innerHTML = bars(S.competences_ft, n, 12) + srcMetier("Compétences saisies par le recruteur dans le référentiel France Travail (offres France Travail uniquement).");
  },
  evolution() {
    if (S.vide) { $("#donnees").innerHTML = vide(); return; }
    if (!S.evolution) { $("#mots").innerHTML = `<div class="todo">Une seule extraction pour l'instant : la comparaison apparaîtra dès la deuxième (la veille tourne chaque jour).</div>`; return; }
    const e = S.evolution;
    const ligne = m => `<tr><td>${esc(m.label)}</td><td>${m.avant} %</td><td>${m.apres} %</td><td><b style="color:${m.delta > 0 ? "var(--green)" : m.delta < 0 ? "var(--coral)" : "inherit"}">${m.delta > 0 ? "+" : ""}${m.delta} pt</b></td></tr>`;
    $("#mots").innerHTML = `<table><tr><th>Compétence / outil</th><th>${dateFr(e.de)} (${e.n_avant} offres)</th><th>${dateFr(e.a)} (${e.n_apres} offres)</th><th>Évolution</th></tr>${e.mots.filter(m => m.avant || m.apres).map(ligne).join("")}</table>` +
      `<div class="src"><b>Méthode :</b> part des offres du métier qui citent chaque compétence, première extraction comparée à la dernière.<br><b>Dates :</b> ${dateFr(e.de)} et ${dateFr(e.a)} · <b>Canaux :</b> France Travail, La Bonne Alternance<br><b>Limites :</b> écart de quelques points = bruit tant que les volumes restent faibles ; une tendance se lit sur plusieurs semaines d'extraction.</div>`;
  },
  acteurs() {
    if (S.vide) { $("#donnees").innerHTML = vide(); return; }
    $("#entreprises").innerHTML = bars(S.entreprises, null, 20) + srcMetier("Nom de l'entreprise tel que publié ; les offres anonymes ou de cabinets de recrutement ne sont pas attribuées.");
    const m = S.marche_cache;
    $("#cache").innerHTML = `<p><b>${fr(m.n_sans_offre)}</b> entreprises identifiées par La Bonne Alternance comme susceptibles de recruter sur le code M1705, sans offre publiée dans les canaux suivis (sur ${fr(m.n_recruteurs)} recruteurs renvoyés).</p>
      <table><tr><th>Entreprise</th><th>Commune</th><th>Secteur</th><th>Taille</th></tr>${m.liste.map(r => `<tr><td>${r.url ? `<a href="${esc(r.url)}">${esc(r.entreprise)}</a>` : esc(r.entreprise)}</td><td>${esc(r.commune)}</td><td>${esc(r.secteur)}</td><td>${esc(r.taille)}</td></tr>`).join("")}</table>` + src("lba_recruteurs", "Une entreprise « qui recrute » est une prédiction d'embauche (personne morale), pas une offre : à contacter par candidature spontanée.");
    $("#veille").innerHTML = `<table><tr><th>Publiée</th><th>Intitulé</th><th>Entreprise</th><th>Lieu</th><th>Contrat</th><th>Canal</th></tr>${S.veille.slice(0, 40).map(o => `<tr><td>${dateFr(o.date_publication)}</td><td><a href="${esc(o.url)}">${esc(o.intitule)}</a></td><td>${esc(o.entreprise)}</td><td>${esc(o.commune)}</td><td>${esc(o.contrat)}${o.alternance === "oui" ? ' <span class="pill">alternance</span>' : ""}</td><td>${esc(o.canal)}</td></tr>`).join("")}</table>` + srcMetier("Liste mise à jour à chaque passage de la veille.");
  },
  plan() {
    if (S.vide) return;
    const top = S.competences.filter(c => c.n > 0 && !/^oui/i.test(c.formation || ""))[0];
    const reg = (S.regions || [])[0];
    const el = $("#chiffres-position");
    if (el) el.innerHTML = `Dans la dernière extraction (${dateFr(S.derniere)}), j'ai compté <b>${fr(S.comptes.offres_metier)}</b> offres du métier, dont <b>${fr(S.comptes.alternance)}</b> en alternance${reg ? `, d'abord en <b>${esc(reg.label)}</b>` : ""}. ${top ? `La compétence la plus demandée que ma formation ne couvre pas encore est <b>${esc(top.label)}</b> (${top.part} % des offres).` : ""}`;
  },
  methode() {
    if (S.vide) { $("#journal").innerHTML = vide(); return; }
    $("#journal").innerHTML = `<p>${fr(S.extractions.length)} requêtes journalisées sur ${fr(S.dates.length)} extraction(s), de ${dateFr(S.dates[0])} à ${dateFr(S.derniere)}.</p>`;
  }
};

header();
fetch("data/stats.json", { cache: "no-store" }).then(r => r.json()).then(j => {
  S = j;
  const m = $("#maj"); if (m) m.textContent = "Données mises à jour : " + (j.genere_le || "—");
  const page = document.body.dataset.page;
  if (RENDU[page]) RENDU[page]();
}).catch(() => {
  const z = document.querySelector("main");
  if (z) z.insertAdjacentHTML("afterbegin", `<div class="todo">Impossible de charger data/stats.json.</div>`);
});
