from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from comptes.decorators import role_requis
from comptes.menu import ADMIN, MANAGER, STOCK

from .forms import CategorieForm, ProduitForm
from .models import TYPE_ENTREE, TYPE_SORTIE, Categorie, Produit

LECTURE = (ADMIN, MANAGER, STOCK)   # peuvent voir les listes
GESTION = (ADMIN, STOCK)            # peuvent créer, modifier, supprimer
PAR_PAGE = 10


# ==================== CATÉGORIES ====================

@role_requis(*LECTURE)
def liste_categories(request):
    q = request.GET.get("q", "").strip()
    categories = Categorie.objects.annotate(nb=Count("produits")).order_by(
        "nom_categorie"
    )
    if q:
        categories = categories.filter(nom_categorie__icontains=q)
    page = Paginator(categories, PAR_PAGE).get_page(request.GET.get("page"))
    return render(
        request,
        "catalogue/categories_liste.html",
        {"page": page, "q": q, "peut_gerer": request.user.role in GESTION},
    )


@role_requis(*GESTION)
def creer_categorie(request):
    form = CategorieForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        categorie = form.save()
        messages.success(
            request, f"Catégorie « {categorie.nom_categorie} » créée avec succès."
        )
        return redirect("liste_categories")
    return render(
        request,
        "formulaire.html",
        {
            "form": form,
            "titre": "Ajouter une catégorie",
            "retour": reverse("liste_categories"),
        },
    )


@role_requis(*GESTION)
def modifier_categorie(request, pk):
    categorie = get_object_or_404(Categorie, pk=pk)
    form = CategorieForm(request.POST or None, instance=categorie)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Catégorie modifiée avec succès.")
        return redirect("liste_categories")
    return render(
        request,
        "formulaire.html",
        {
            "form": form,
            "titre": "Modifier la catégorie",
            "retour": reverse("liste_categories"),
        },
    )


@role_requis(*GESTION)
@require_POST
def supprimer_categorie(request, pk):
    categorie = get_object_or_404(Categorie, pk=pk)
    nb = categorie.produits.count()
    if nb > 0:
        messages.error(
            request,
            f"Impossible de supprimer la catégorie « {categorie.nom_categorie} » : "
            f"elle contient {nb} produit(s). "
            "Déplacez ou supprimez d'abord ces produits.",
        )
    else:
        nom = categorie.nom_categorie
        categorie.delete()
        messages.success(request, f"La catégorie « {nom} » a été supprimée.")
    return redirect("liste_categories")


# ==================== PRODUITS ====================

@role_requis(*LECTURE)
def liste_produits(request):
    q = request.GET.get("q", "").strip()
    categorie_id = request.GET.get("categorie", "").strip()

    produits = (
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

    if q:
        produits = produits.filter(
            Q(code__icontains=q) | Q(designation__icontains=q)
        )
    if categorie_id.isdigit():
        produits = produits.filter(categorie_id=int(categorie_id))
    else:
        categorie_id = ""

    page = Paginator(produits, PAR_PAGE).get_page(request.GET.get("page"))
    return render(
        request,
        "catalogue/produits_liste.html",
        {
            "page": page,
            "q": q,
            "categorie_id": categorie_id,
            "categories": Categorie.objects.all(),
            "peut_gerer": request.user.role in GESTION,
        },
    )


@role_requis(*GESTION)
def creer_produit(request):
    form = ProduitForm(
        request.POST or None,
        peut_modifier_prix=(request.user.role == ADMIN),
    )
    if request.method == "POST" and form.is_valid():
        produit = form.save()
        messages.success(request, f"Produit « {produit.designation} » créé avec succès.")
        return redirect("liste_produits")
    return render(
        request,
        "formulaire.html",
        {
            "form": form,
            "titre": "Ajouter un produit",
            "retour": reverse("liste_produits"),
        },
    )


@role_requis(*GESTION)
def modifier_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    form = ProduitForm(
        request.POST or None,
        instance=produit,
        peut_modifier_prix=(request.user.role == ADMIN),
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Produit modifié avec succès.")
        return redirect("liste_produits")
    return render(
        request,
        "formulaire.html",
        {
            "form": form,
            "titre": "Modifier le produit",
            "retour": reverse("liste_produits"),
        },
    )


@role_requis(*GESTION)
@require_POST
def supprimer_produit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if produit.est_vendu():
        messages.error(
            request,
            f"Le produit « {produit.designation} » a déjà été vendu : "
            "il ne peut pas être supprimé.",
        )
    elif produit.a_des_mouvements():
        messages.error(
            request,
            f"Le produit « {produit.designation} » a des mouvements de stock : "
            "il ne peut pas être supprimé.",
        )
    else:
        nom = produit.designation
        produit.delete()
        messages.success(request, f"Le produit « {nom} » a été supprimé.")
    return redirect("liste_produits")