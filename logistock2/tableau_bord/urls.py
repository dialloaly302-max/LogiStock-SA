from django.urls import path

from . import views

urlpatterns = [
    path("tableau-de-bord/", views.tableau_de_bord, name="tableau_bord"),
    path(
        "tableau-de-bord/export/excel/",
        views.export_excel,
        name="export_excel",
    ),
    path(
        "tableau-de-bord/export/pdf/",
        views.export_pdf,
        name="export_pdf",
    ),
]