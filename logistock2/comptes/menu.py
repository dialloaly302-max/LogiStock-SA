from django.urls import NoReverseMatch, reverse

ADMIN = "administrateur"
MANAGER = "manager"
VENTES = "gestionnaire_ventes"
STOCK = "gestionnaire_stock"
TOUS = [ADMIN, MANAGER, VENTES, STOCK]

# (texte du menu, nom de l'adresse, rôles autorisés)
MENU = [
    ("Accueil", "accueil", TOUS),
    ("Tableau de bord", "tableau_bord", [ADMIN, MANAGER]),
    ("Clients", "liste_clients", [ADMIN, MANAGER, VENTES]),
    ("Ventes", "liste_ventes", [ADMIN, MANAGER, VENTES]),
    ("Nouvelle vente", "nouvelle_vente", [ADMIN, VENTES]),
    ("Catalogue", "liste_produits", [ADMIN, MANAGER, STOCK]),
    ("Catégories", "liste_categories", [ADMIN, MANAGER, STOCK]),
    ("Stock", "liste_stock", [ADMIN, MANAGER, STOCK]),
    ("Notifications", "notifications_stock", [ADMIN, MANAGER, STOCK]),
    ("Utilisateurs", "liste_utilisateurs", [ADMIN]),
]


def menu_pour(user):
    """Renvoie seulement les entrées du menu permises pour ce rôle."""
    if not user.is_authenticated:
        return []
    entrees = []
    for texte, nom_url, roles in MENU:
        if user.role not in roles:
            continue
        try:
                        entrees.append({"texte": texte, "url": reverse(nom_url), "nom": nom_url})
        except NoReverseMatch:
            continue  # la page n'existe pas encore : on ne l'affiche pas
    return entrees