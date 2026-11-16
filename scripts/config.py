"""
Configuration de la veille : métier étudié, requêtes envoyées aux API, dictionnaire de compétences.
Tout ce qui est compté sur le site part d'ici : modifier une requête ici change la donnée.
"""

METIER = "Chargé·e CRM / marketing automation"
ROME = "M1705"   # code ROME « Marketing » (France Travail)

# Intitulés qui désignent le métier dans les offres (recherche dans l'intitulé, sans accents, minuscules)
VARIANTES = [   # testées dans l'ordre : la première qui correspond donne la variante
    ("CRM manager / responsable CRM", ["crm manager", "responsable crm", "manager crm", "chef de projet crm",
                                       "head of crm", "directeur crm"]),
    ("Marketing automation", ["marketing automation", "automation marketing", "automatisation marketing"]),
    ("Inbound marketing", ["inbound"]),
    ("Marketing relationnel / fidélisation", ["marketing relationnel", "fidelisation", "customer relationship",
                                              "lifecycle", "retention", "loyalty", "relation client marketing"]),
    ("Emailing / marketing client", ["emailing", "e-mailing", "email marketing", "marketing client"]),
    ("Chargé·e CRM", ["crm"]),
]

# Requêtes France Travail : id stable, libellé lisible, paramètres envoyés, détail = récupérer les offres
REQUETES_FT = [
    {"id": "ft_rome_m1705", "libelle": "Code ROME M1705 (Marketing), France entière",
     "params": {"codeROME": ROME}, "detail": False,
     "limites": "Toutes les offres classées M1705 par France Travail, au-delà du seul CRM ; "
                "le classement ROME est fait par le recruteur ou le conseiller."},
    {"id": "ft_crm", "libelle": "Mot-clé « CRM », France entière",
     "params": {"motsCles": "CRM"}, "detail": True,
     "limites": "Le mot « CRM » apparaît aussi dans des offres commerciales qui demandent seulement "
                "d'utiliser un logiciel CRM : le site distingue les offres dont l'intitulé désigne le métier."},
    {"id": "ft_automation", "libelle": "Mots-clés « marketing automation », France entière",
     "params": {"motsCles": "marketing automation"}, "detail": True,
     "limites": "Mots recherchés dans tout le texte de l'offre ; volume faible, donc sensible aux variations."},
    {"id": "ft_crm_m1705", "libelle": "Mot-clé « CRM » dans le code ROME M1705",
     "params": {"codeROME": ROME, "motsCles": "CRM"}, "detail": True,
     "limites": "Croisement le plus proche du métier ; exclut les offres CRM classées dans un autre code ROME."},
]

# La Bonne Alternance : offres en alternance et entreprises qui recrutent (marché caché)
LBA_ROMES = ROME
LBA_LIMITES = ("Offres d'alternance de La Bonne Alternance et de ses partenaires, code ROME M1705 ; "
               "les « recruteurs » sont des entreprises identifiées comme susceptibles d'embaucher "
               "(candidature spontanée), pas des offres publiées.")

# Dictionnaire de compétences et d'outils : (libellé, catégorie, motifs recherchés sans accents)
COMPETENCES = [
    ("Segmentation / ciblage", "Compétence", ["segmentation", "segmenter", "ciblage"]),
    ("Emailing / campagnes e-mail", "Compétence", ["emailing", "e-mailing", "campagne email", "campagnes email",
                                                  "campagnes e-mail", "newsletter"]),
    ("Marketing automation / scénarios", "Compétence", ["marketing automation", "automatisation", "scenario",
                                                        "workflow", "nurturing"]),
    ("Fidélisation / rétention", "Compétence", ["fidelisation", "fideliser", "retention", "programme de fidelite"]),
    ("Parcours client", "Compétence", ["parcours client", "customer journey", "experience client"]),
    ("Analyse de données / KPI", "Compétence", ["kpi", "indicateur", "analyse de donnees", "analyser les donnees",
                                               "data", "dashboard", "tableau de bord", "reporting"]),
    ("A/B testing", "Compétence", ["a/b test", "ab test", "test a/b"]),
    ("RGPD / qualité de la base", "Compétence", ["rgpd", "gdpr", "qualite des donnees", "base de donnees",
                                                "nettoyage"]),
    ("Lead scoring / génération de leads", "Compétence", ["scoring", "lead", "generation de leads"]),
    ("Gestion de projet", "Compétence", ["gestion de projet", "chef de projet", "pilotage", "retroplanning"]),
    ("Rédaction / contenus", "Compétence", ["redaction", "rediger", "copywriting", "contenu"]),
    ("Anglais", "Compétence", ["anglais", "english"]),
    ("Intelligence artificielle", "Compétence", ["intelligence artificielle", " ia ", "ia generative", "chatgpt",
                                                 "gpt", " ai "]),
    ("Salesforce", "Outil", ["salesforce", "pardot", "marketing cloud"]),
    ("HubSpot", "Outil", ["hubspot"]),
    ("Brevo (Sendinblue)", "Outil", ["brevo", "sendinblue"]),
    ("Microsoft Dynamics", "Outil", ["dynamics"]),
    ("Selligent / Actito / Splio", "Outil", ["selligent", "actito", "splio"]),
    ("Adobe Campaign", "Outil", ["adobe campaign"]),
    ("Mailchimp / Klaviyo", "Outil", ["mailchimp", "klaviyo"]),
    ("Excel", "Outil", ["excel"]),
    ("SQL", "Outil", [" sql", "sql "]),
    ("Power BI / Looker / Tableau", "Outil", ["power bi", "powerbi", "looker", "tableau software"]),
    ("Google Analytics", "Outil", ["google analytics", "ga4"]),
    ("Canva / suite Adobe", "Outil", ["canva", "photoshop", "illustrator", "indesign"]),
]

# Correspondance département -> région (pour la géographie)
REGIONS = {
    "Auvergne-Rhône-Alpes": ["01", "03", "07", "15", "26", "38", "42", "43", "63", "69", "73", "74"],
    "Bourgogne-Franche-Comté": ["21", "25", "39", "58", "70", "71", "89", "90"],
    "Bretagne": ["22", "29", "35", "56"],
    "Centre-Val de Loire": ["18", "28", "36", "37", "41", "45"],
    "Corse": ["2A", "2B", "20"],
    "Grand Est": ["08", "10", "51", "52", "54", "55", "57", "67", "68", "88"],
    "Hauts-de-France": ["02", "59", "60", "62", "80"],
    "Île-de-France": ["75", "77", "78", "91", "92", "93", "94", "95"],
    "Normandie": ["14", "27", "50", "61", "76"],
    "Nouvelle-Aquitaine": ["16", "17", "19", "23", "24", "33", "40", "47", "64", "79", "86", "87"],
    "Occitanie": ["09", "11", "12", "30", "31", "32", "34", "46", "48", "65", "66", "81", "82"],
    "Pays de la Loire": ["44", "49", "53", "72", "85"],
    "Provence-Alpes-Côte d'Azur": ["04", "05", "06", "13", "83", "84"],
    "Outre-mer": ["971", "972", "973", "974", "976"],
}
