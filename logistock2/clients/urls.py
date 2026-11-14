from django.urls import path

from . import views

urlpatterns = [
    path("clients/", views.liste_clients, name="liste_clients"),
    path("clients/ajouter/", views.creer_client, name="creer_client"),
    path("clients/<int:pk>/", views.fiche_client, name="fiche_client"),
    path(
        "clients/<int:pk>/modifier/",
        views.modifier_client,
        name="modifier_client",
    ),
    path(
        "clients/<int:pk>/archiver/",
        views.archiver_client,
        name="archiver_client",
    ),
    path(
        "clients/<int:pk>/reactiver/",
        views.reactiver_client,
        name="reactiver_client",
    ),
    path(
        "clients/<int:pk>/paiement/",
        views.nouveau_paiement,
        name="nouveau_paiement",
    ),
]