from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("comptes.urls")),
    path("", include("catalogue.urls")),
    path("", include("stock.urls")),
    path("", include("clients.urls")),
    path("", include("ventes.urls")),
    path("", include("tableau_bord.urls")),
]