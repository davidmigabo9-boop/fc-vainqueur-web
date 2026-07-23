from datetime import date, datetime


def parse_date(d):
    if isinstance(d, date):
        return d
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, str) and d.strip():
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(d.strip(), fmt).date()
            except ValueError:
                continue
    return None


def calculer_age_exact(date_naissance_str):
    dob = parse_date(date_naissance_str)
    if not dob:
        return None
    today = date.today()
    years = today.year - dob.year
    months = today.month - dob.month
    days = today.day - dob.day
    if days < 0:
        months -= 1
        prev_month = today.month - 1 if today.month > 1 else 12
        prev_year = today.year if today.month > 1 else today.year - 1
        import calendar
        days += calendar.monthrange(prev_year, prev_month)[1]
    if months < 0:
        years -= 1
        months += 12
    return {"annees": years, "mois": months, "jours": days}


def format_age(date_naissance_str):
    age = calculer_age_exact(date_naissance_str)
    if not age:
        return "Inconnu"
    return f"{age['annees']} ans, {age['mois']} mois, {age['jours']} jours"


def jours_avant_anniversaire(date_naissance_str):
    dob = parse_date(date_naissance_str)
    if not dob:
        return None
    today = date.today()
    this_year_birthday = date(today.year, dob.month, dob.day)
    if this_year_birthday < today:
        next_birthday = date(today.year + 1, dob.month, dob.day)
    elif this_year_birthday == today:
        return 0
    else:
        next_birthday = this_year_birthday
    return (next_birthday - today).days


def anniversaire_info(date_naissance_str):
    jours = jours_avant_anniversaire(date_naissance_str)
    if jours is None:
        return None
    dob = parse_date(date_naissance_str)
    today = date.today()
    age_actuel = calculer_age_exact(date_naissance_str)
    if age_actuel is None:
        return None
    age_suivant = age_actuel["annees"] + 1
    if jours == 0:
        return {"message": f"Joyeux anniversaire! {age_suivant} ans aujourd'hui!", "niveau": "aujourd'hui", "jours": 0, "age_suivant": age_suivant}
    elif jours <= 7:
        return {"message": f"Dans {jours} jour(s), {age_suivant} ans!", "niveau": "bientot", "jours": jours, "age_suivant": age_suivant}
    elif jours <= 30:
        return {"message": f"Anniversaire dans {jours} jours ({age_suivant} ans)", "niveau": "proche", "jours": jours, "age_suivant": age_suivant}
    else:
        return {"message": f"Prochain anniversaire dans {jours} jours", "niveau": "loin", "jours": jours, "age_suivant": age_suivant}


def categorie_automatique(date_naissance_str):
    age = calculer_age_exact(date_naissance_str)
    if not age:
        return "Inconnu"
    a = age["annees"]
    if a <= 8:
        return "U9"
    elif a <= 10:
        return "U11"
    elif a <= 12:
        return "U13"
    elif a <= 14:
        return "U15"
    elif a <= 16:
        return "U17"
    elif a <= 19:
        return "U20"
    elif a <= 34:
        return "Senior"
    else:
        return "Veteran"


CATEGORIES_LIMITES = {
    "U9": 9, "U11": 11, "U13": 13, "U15": 15,
    "U17": 17, "U20": 20, "Senior": 35, "Veteran": 99,
}


def alerte_changement_categorie(date_naissance_str):
    age = calculer_age_exact(date_naissance_str)
    if not age:
        return None
    cat_actuelle = categorie_automatique(date_naissance_str)
    limites = list(CATEGORIES_LIMITES.items())
    for i, (nom, limite) in enumerate(limites):
        if nom == cat_actuelle and i < len(limites) - 1:
            nom_suivant, limite_suivante = limites[i + 1]
            age_en_secondes = age["annees"] * 365.25 + age["mois"] * 30.44 + age["jours"]
            limite_en_secondes = limite * 365.25
            reste_jours = int((limite_en_secondes - age_en_secondes) / 1)
            if reste_jours <= 0:
                return None
            if reste_jours <= 365:
                mois_restants = reste_jours // 30
                if mois_restants <= 0:
                    mois_restants = 1
                return {
                    "message": f"Dans {mois_restants} mois, ce joueur passera en {nom_suivant}.",
                    "niveau": "critique" if mois_restants <= 3 else "attention",
                    "jours": reste_jours,
                    "categorie_suivante": nom_suivant,
                }
    return None


def potentiel_joueur(date_naissance_str):
    age = calculer_age_exact(date_naissance_str)
    if not age:
        return {"label": "Inconnu", "couleur": "secondary", "icone": "fa-question"}
    a = age["annees"]
    if a <= 16:
        return {"label": "Jeune talent", "couleur": "success", "icone": "fa-star"}
    elif a <= 22:
        return {"label": "En developpement", "couleur": "primary", "icone": "fa-chart-line"}
    elif a <= 29:
        return {"label": "A maturite", "couleur": "warning", "icone": "fa-fire"}
    else:
        return {"label": "Fin de carriere sportive", "couleur": "danger", "icone": "fa-heart"}


def recommandation_joueur(date_naissance_str):
    age = calculer_age_exact(date_naissance_str)
    if not age:
        return "Pas de recommandation disponible."
    a = age["annees"]
    if a <= 12:
        return "Accent sur la formation technique et le plaisir de jouer. Developper la creativite et le fair-play."
    elif a <= 16:
        return "Developpement tactique et physique progressif. Participer a des matchs pour gagner en experience."
    elif a <= 20:
        return "Preparation physique renforcee. Tactique avancee et competition reguliere."
    elif a <= 29:
        return "Condition physique au top. Strategie de match et leadership. Pique de carriere."
    elif a <= 34:
        return "Recuperation et prevention des blessures. Transmettre l'experience aux jeunes joueurs."
    else:
        return "Role de mentor. Gestion de la charge physique. Prevention des blessures et recuperation soignee."


def annees_au_club(date_inscription_str):
    d = parse_date(date_inscription_str)
    if not d:
        return None
    today = date.today()
    years = today.year - d.year
    if (today.month, today.day) < (d.month, d.day):
        years -= 1
    return max(years, 0)


def repartition_ages(joueurs_list):
    categories = {"Moins de 15 ans": 0, "15-18 ans": 0, "19-25 ans": 0, "Plus de 25 ans": 0}
    for j in joueurs_list:
        age = calculer_age_exact(j.date_naissance)
        if not age:
            continue
        a = age["annees"]
        if a < 15:
            categories["Moins de 15 ans"] += 1
        elif a <= 18:
            categories["15-18 ans"] += 1
        elif a <= 25:
            categories["19-25 ans"] += 1
        else:
            categories["Plus de 25 ans"] += 1
    return categories
