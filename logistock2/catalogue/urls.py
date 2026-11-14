from django.urls import path

from . import views

urlpatterns = [
    # Catégories
    path("categories/", views.liste_categories, name="liste_categories"),
    path("categories/ajouter/", views.creer_categorie, name="creer_categorie"),
    path(
        "categories/<int:pk>/modifier/",
        views.modifier_categorie,
        name="modifier_categorie",
    ),
    path(
        "categories/<int:pk>/supprimer/",
        views.supprimer_categorie,
        name="supprimer_categorie",
    ),
    # Produits
    path("produits/", views.liste_produits, name="liste_produits"),
    path("produits/ajouter/", views.creer_produit, name="creer_produit"),
    path(
        "produits/<int:pk>/modifier/",
        views.modifier_produit,
        name="modifier_produit",
    ),
    path(
        "produits/<int:pk>/supprimer/",
        views.supprimer_produit,
        name="supprimer_produit",
    ),
]