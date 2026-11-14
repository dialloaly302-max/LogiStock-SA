from django.urls import path

from . import views

urlpatterns = [
    path("stock/", views.liste_stock, name="liste_stock"),
    path("stock/entree/", views.entree_stock, name="entree_stock"),
    path("stock/inventaire/", views.inventaire_stock, name="inventaire_stock"),
    path(
        "stock/notifications/",
        views.notifications_stock,
        name="notifications_stock",
    ),
]