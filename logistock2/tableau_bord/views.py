from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from comptes.decorators import role_requis
from comptes.menu import ADMIN, MANAGER

from .exports import construire_excel, construire_pdf
from .services import donnees_tableau_de_bord, lire_periode

ACCES = (ADMIN, MANAGER)   # seuls l'administrateur et le manager voient le tableau de bord


@role_requis(*ACCES)
def tableau_de_bord(request):
    debut, fin, erreur = lire_periode(
        request.GET.get("debut", ""), request.GET.get("fin", "")
    )
    if erreur:
        messages.warning(request, erreur)

    donnees = donnees_tableau_de_bord(debut, fin)
    # Les données du graphique : les noms et les quantités des 5 produits les plus vendus
    donnees["graphique"] = {
        "labels": [ligne["designation"] for ligne in donnees["top5"]],
        "quantites": [ligne["quantite"] for ligne in donnees["top5"]],
    }
    donnees["debut_texte"] = debut.isoformat()
    donnees["fin_texte"] = fin.isoformat()
    return render(request, "tableau_bord/tableau_bord.html", donnees)


@role_requis(*ACCES)
@require_GET
def export_excel(request):
    """Télécharge le tableau de bord de la période choisie, au format Excel."""
    debut, fin, _ = lire_periode(
        request.GET.get("debut", ""), request.GET.get("fin", "")
    )
    contenu = construire_excel(donnees_tableau_de_bord(debut, fin), request.user)
    reponse = HttpResponse(
        contenu,
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
    nom = f"logistock_tableau_de_bord_{debut.isoformat()}_{fin.isoformat()}.xlsx"
    reponse["Content-Disposition"] = f'attachment; filename="{nom}"'
    return reponse

@role_requis(*ACCES)
@require_GET
def export_pdf(request):
    """Télécharge le tableau de bord de la période choisie, au format PDF."""
    debut, fin, _ = lire_periode(
        request.GET.get("debut", ""), request.GET.get("fin", "")
    )
    contenu = construire_pdf(donnees_tableau_de_bord(debut, fin), request.user)
    reponse = HttpResponse(contenu, content_type="application/pdf")
    nom = f"logistock_tableau_de_bord_{debut.isoformat()}_{fin.isoformat()}.pdf"
    reponse["Content-Disposition"] = f'attachment; filename="{nom}"'
    return reponse