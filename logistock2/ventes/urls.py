from django.urls import path

from . import views

urlpatterns = [
    path("ventes/", views.liste_ventes, name="liste_ventes"),
    path("ventes/nouvelle/", views.nouvelle_vente, name="nouvelle_vente"),
    path("ventes/<int:pk>/", views.detail_vente, name="detail_vente"),
    path("ventes/<int:pk>/annuler/", views.annulation_vente, name="annuler_vente"),
    path("ventes/<int:pk>/facture/", views.facture_vente, name="facture_vente"),
    path("ventes/<int:pk>/ticket/", views.ticket_vente, name="ticket_vente"),
]