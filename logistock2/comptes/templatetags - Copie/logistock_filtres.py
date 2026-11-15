from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()

NOMS_ROLES = {
    "administrateur": "Administrateur",
    "manager": "Manager",
    "gestionnaire_ventes": "Gestionnaire des ventes",
    "gestionnaire_stock": "Gestionnaire de stock",
}


@register.filter
def fcfa(valeur):
    """1250000 devient « 1 250 000 FCFA »."""
    if valeur in (None, ""):
        valeur = 0
    try:
        nombre = int(round(Decimal(str(valeur))))
    except (InvalidOperation, ValueError):
        return ""
    texte = f"{nombre:,}".replace(",", "\u00a0")
    return f"{texte}\u00a0FCFA"


@register.filter
def role_lisible(role):
    """gestionnaire_stock devient « Gestionnaire de stock »."""
    return NOMS_ROLES.get(role, role)

@register.filter
def multiplier(a, b):
    try:
        return int(a) * int(b)
    except (TypeError, ValueError):
        return 0
