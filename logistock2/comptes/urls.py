from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("connexion/", views.connexion, name="connexion"),
    path("deconnexion/", LogoutView.as_view(), name="deconnexion"),
    path("utilisateurs/", views.liste_utilisateurs, name="liste_utilisateurs"),
    path("utilisateurs/creer/", views.creer_utilisateur, name="creer_utilisateur"),
    path(
        "utilisateurs/<int:pk>/modifier/",
        views.modifier_utilisateur,
        name="modifier_utilisateur",
    ),
    path(
        "utilisateurs/<int:pk>/actif/",
        views.basculer_actif,
        name="basculer_actif",
    ),
]