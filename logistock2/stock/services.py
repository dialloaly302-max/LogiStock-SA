from django.db import transaction
from django.db.models import F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from catalogue.models import TYPE_ENTREE, TYPE_SORTIE, Produit

from .models import Stock

MOTIF_APPROVISIONNEMENT = "Approvisionnement"
MOTIF_INVENTAIRE = "Inventaire"


class StockError(ValueError):
    """Erreur de règle du stock, avec un message lisible par l'utilisateur."""


def produits_avec_stock():
    """Tous les produits, avec leur stock calculé à partir des mouvements."""
    return (
        Produit.objects.select_related("categorie")
        .annotate(
            entrees=Coalesce(
                Sum("mouvements__quantite",
                    filter=Q(mouvements__type_mouvement=TYPE_ENTREE)),
                Value(0),
            ),
            sorties=Coalesce(
                Sum("mouvements__quantite",
                    filter=Q(mouvements__type_mouvement=TYPE_SORTIE)),
                Value(0),
            ),
        )
        .annotate(stock=F("entrees") - F("sorties"))
        .order_by("designation")
    )


def valeur_stock_total():
    """Valeur de tout le stock : somme de (stock x prix d'achat)."""
    return int(sum(int(p.stock) * p.prix_achat for p in produits_avec_stock()))


def enregistrer_mouvement(produit, type_mouvement, quantite, utilisateur,
                          motif, vente=None):
    """Ajoute un mouvement. C'est la SEULE façon de changer le stock."""
    if quantite is None or quantite <= 0:
        raise StockError("La quantité doit être supérieure à 0.")

    with transaction.atomic():
        # Verrou : deux mouvements du même produit ne se mélangent pas.
        Produit.objects.select_for_update().get(pk=produit.pk)
        actuel = produit.stock_actuel()

        if type_mouvement == TYPE_ENTREE:
            restante = actuel + quantite
        else:
            if quantite > actuel:
                raise StockError(
                    f"Stock insuffisant : il reste {actuel} unité(s) de "
                    f"« {produit.designation} »."
                )
            restante = actuel - quantite

        return Stock.objects.create(
            produit=produit,
            utilisateur=utilisateur,
            vente=vente,
            date_mouvement=timezone.now(),
            type_mouvement=type_mouvement,
            quantite=quantite,
            quantite_restante=restante,
            motif=motif,
        )


def enregistrer_entree(produit, quantite, utilisateur):
    """Approvisionnement. Renvoie (mouvement, valeur de l'entrée)."""
    mouvement = enregistrer_mouvement(
        produit, TYPE_ENTREE, quantite, utilisateur, MOTIF_APPROVISIONNEMENT
    )
    return mouvement, quantite * produit.prix_achat


def enregistrer_inventaire(produit, quantite_comptee, utilisateur):
    """L'écart entre le compté et le calculé devient un mouvement.

    Renvoie (mouvement, écart). Si l'écart est 0, il n'y a pas de mouvement.
    """
    if quantite_comptee is None or quantite_comptee < 0:
        raise StockError("La quantité comptée ne peut pas être négative.")

    ecart = quantite_comptee - produit.stock_actuel()
    if ecart == 0:
        return None, 0

    type_mouvement = TYPE_ENTREE if ecart > 0 else TYPE_SORTIE
    mouvement = enregistrer_mouvement(
        produit, type_mouvement, abs(ecart), utilisateur, MOTIF_INVENTAIRE
    )
    return mouvement, ecart