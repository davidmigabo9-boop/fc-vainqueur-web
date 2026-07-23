ROLES = {
    "super_administrateur": "Super Administrateur",
    "administrateur": "Administrateur",
    "tresorier": "Tresorier",
    "entraineur": "Entraineur",
    "lecteur": "Lecteur",
}

ROLE_LABELS = list(ROLES.values())

PERMISSIONS = {
    "super_administrateur": {
        "joueurs_voir", "joueurs_ajouter", "joueurs_modifier", "joueurs_supprimer",
        "joueurs_exporter", "contributions_ajouter",
        "budget_voir", "budget_ajouter", "budget_supprimer", "budget_exporter",
        "equipements_voir", "equipements_ajouter", "equipements_modifier", "equipements_supprimer",
        "equipements_exporter",
        "feuilles_voir", "feuilles_ajouter", "feuilles_modifier", "feuilles_supprimer",
        "dashboard_voir",
        "parametres_voir", "parametres_modifier",
        "utilisateurs_voir", "utilisateurs_ajouter", "utilisateurs_supprimer",
        "sauvegarde_creer", "sauvegarde_restaurer",
        "audit_voir",
    },
    "administrateur": {
        "joueurs_voir", "joueurs_ajouter", "joueurs_modifier", "joueurs_supprimer",
        "joueurs_exporter", "contributions_ajouter",
        "budget_voir", "budget_ajouter", "budget_supprimer", "budget_exporter",
        "equipements_voir", "equipements_ajouter", "equipements_modifier", "equipements_supprimer",
        "equipements_exporter",
        "dashboard_voir",
    },
    "tresorier": {
        "joueurs_voir", "joueurs_exporter",
        "budget_voir", "budget_ajouter", "budget_supprimer", "budget_exporter",
        "dashboard_voir",
    },
    "entraineur": {
        "joueurs_voir", "joueurs_modifier", "joueurs_exporter",
        "feuilles_voir", "feuilles_ajouter", "feuilles_modifier",
        "dashboard_voir",
    },
    "lecteur": {
        "joueurs_voir", "joueurs_exporter",
    },
}


def get_role_key(role_label):
    for key, label in ROLES.items():
        if label == role_label:
            return key
    return role_label


def get_role_label(role_key):
    return ROLES.get(role_key, role_key)


def has_permission(role, permission):
    perms = PERMISSIONS.get(role, set())
    return permission in perms


def get_permissions(role):
    return PERMISSIONS.get(role, set())


CRITICAL_ACTIONS = {
    "supprimer_joueur": "Suppression d'un joueur",
    "supprimer_budget": "Suppression d'une operation budgetaire",
    "supprimer_equipement": "Suppression d'un equipement",
    "supprimer_utilisateur": "Suppression d'un utilisateur",
    "restaurer_sauvegarde": "Restauration d'une sauvegarde",
    "modifier_parametres": "Modification des parametres",
    "gerer_utilisateurs": "Gestion des utilisateurs",
}
