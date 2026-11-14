from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse

from catalogue.models import TYPE_ENTREE, TYPE_SORTIE
from comptes.decorators import role_requis
from comptes.menu import ADMIN, MANAGER, STOCK
from comptes.templatetags.logistock_filtres import fcfa

from .forms import EntreeStockForm, InventaireForm
from .models import Stock
from .services import (
    StockError,
    enregistrer_entree,
    enregistrer_inventaire,
    produits_avec_stock,
    valeur_stock_total,
)

LECTURE = (ADMIN, MANAGER, STOCK)   # peuvent consulter
GESTION = (ADMIN, STOCK)            # peuvent faire une entrée ou un inventaire


# ==================== LISTE DU STOCK EN TEMPS RÉEL ====================

@role_requis(*LECTURE)
def liste_stock(request):
    q = request.GET.get("q", "").strip()

    produits = produits_avec_stock()
    if q:
        produits = produits.filter(
            Q(code__icontains=q) | Q(designation__icontains=q)
        )
    page = Paginator(produits, 10).get_page(request.GET.get("page"))

    nb_critiques = sum(
        1 for p in produits_avec_stock() if p.stock <= p.seuil_minimal
    )
    return render(
        request,
        "stock/stock_liste.html",
        {
            "page": page,
            "q": q,
            "valeur_totale": valeur_stock_total(),
            "nb_critiques": nb_critiques,
            "peut_gerer": request.user.role in GESTION,
        },
    )


# ==================== ENTRÉE DE STOCK ====================

@role_requis(*GESTION)
def entree_stock(request):
    form = EntreeStockForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        produit = form.cleaned_data["produit"]
        quantite = form.cleaned_data["quantite"]
        try:
            mouvement, valeur = enregistrer_entree(produit, quantite, request.user)
        except StockError as erreur:
            form.add_error(None, str(erreur))
        else:
            messages.success(
                request,
                f"Entrée enregistrée : {quantite} × « {produit.designation} » "
                f"= {fcfa(valeur)}. "
                f"Valeur totale du stock : {fcfa(valeur_stock_total())}.",
            )
            return redirect("liste_stock")
    return render(
        request,
        "formulaire.html",
        {
            "form": form,
            "titre": "Entrée de stock (approvisionnement)",
            "aide": f"Valeur actuelle du stock : {fcfa(valeur_stock_total())}",
            "retour": reverse("liste_stock"),
        },
    )


# ==================== INVENTAIRE ====================

@role_requis(*GESTION)
def inventaire_stock(request):
    form = InventaireForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        produit = form.cleaned_data["produit"]
        comptee = form.cleaned_data["quantite_comptee"]
        try:
            mouvement, ecart = enregistrer_inventaire(produit, comptee, request.user)
        except StockError as erreur:
            form.add_error(None, str(erreur))
        else:
            if mouvement is None:
                messages.info(
                    request,
                    f"Inventaire de « {produit.designation} » : aucun écart, "
                    f"le stock est exact ({comptee}).",
                )
            else:
                sens = "en plus" if ecart > 0 else "en moins"
                messages.warning(
                    request,
                    f"Inventaire de « {produit.designation} » : écart de "
                    f"{abs(ecart)} unité(s) {sens}. Un mouvement "
                    f"« {mouvement.type_mouvement} » a été ajouté : "
                    f"le stock est maintenant de {comptee}.",
                )
            return redirect("liste_stock")
    return render(
        request,
        "formulaire.html",
        {
            "form": form,
            "titre": "Inventaire",
            "aide": (
                "Saisissez la quantité que vous avez réellement comptée. "
                "L'écart sera enregistré comme un mouvement « Inventaire » : "
                "rien n'est modifié ni supprimé."
            ),
            "retour": reverse("liste_stock"),
        },
    )


# ==================== NOTIFICATIONS ET HISTORIQUE ====================

@role_requis(*LECTURE)
def notifications_stock(request):
    base = Stock.objects.select_related("produit", "utilisateur").order_by(
        "-date_mouvement", "-id_stock"
    )
    dernieres_entrees = base.filter(type_mouvement=TYPE_ENTREE)[:5]
    dernieres_sorties = base.filter(type_mouvement=TYPE_SORTIE)[:5]

    q = request.GET.get("q", "").strip()
    type_choisi = request.GET.get("type", "").strip()

    historique = base
    if type_choisi in (TYPE_ENTREE, TYPE_SORTIE):
        historique = historique.filter(type_mouvement=type_choisi)
    else:
        type_choisi = ""
    if q:
        historique = historique.filter(
            Q(produit__code__icontains=q) | Q(produit__designation__icontains=q)
        )
    page = Paginator(historique, 15).get_page(request.GET.get("page"))

    return render(
        request,
        "stock/notifications.html",
        {
            "dernieres_entrees": dernieres_entrees,
            "dernieres_sorties": dernieres_sorties,
            "page": page,
            "q": q,
            "type_choisi": type_choisi,
        },
    )