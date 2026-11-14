from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from clients.models import MODE_CREDIT, STATUT_VALIDE, Client
from comptes.decorators import role_requis
from comptes.menu import ADMIN, MANAGER, VENTES
from comptes.templatetags.logistock_filtres import fcfa
from stock.services import produits_avec_stock

from .models import Vente
from .forms import AnnulationForm
from .services import MODE_COMPTANT, VenteError, annuler_vente, valider_vente

LECTURE = (ADMIN, MANAGER, VENTES)   # peuvent consulter les ventes
GESTION = (ADMIN, VENTES)            # peuvent saisir une vente


# ==================== NOUVELLE VENTE ====================

@role_requis(*GESTION)
def nouvelle_vente(request):
    est_admin = request.user.role == ADMIN
    saisie = {
        "client": "",
        "mode": MODE_COMPTANT,
        "remise": "0",
        "autoriser": False,
        "lignes": [],
    }

    if request.method == "POST":
        produits_post = request.POST.getlist("produit")
        quantites_post = request.POST.getlist("quantite")
        saisie.update(
            client=request.POST.get("client", ""),
            mode=request.POST.get("mode", MODE_COMPTANT),
            remise=request.POST.get("remise", "0"),
            autoriser=request.POST.get("autoriser") == "on",
            lignes=[
                {"produit": p, "quantite": q}
                for p, q in zip(produits_post, quantites_post)
            ],
        )
        try:
            vente, alertes = valider_vente(
                utilisateur=request.user,
                client_id=request.POST.get("client"),
                mode=request.POST.get("mode"),
                remise=request.POST.get("remise"),
                lignes=list(zip(produits_post, quantites_post)),
                autoriser_depassement=est_admin and saisie["autoriser"],
            )
        except VenteError as erreur:
            # Rien n'a été enregistré : on réaffiche ce que l'utilisateur a saisi.
            messages.error(request, str(erreur))
        else:
            messages.success(
                request,
                f"Vente {vente.reference} enregistrée : {fcfa(vente.montant_total)}.",
            )
            for alerte in alertes:
                produit = alerte["produit"]
                messages.warning(
                    request,
                    f"Stock bas : « {produit.designation} » - il ne reste que "
                    f"{alerte['restante']} (seuil minimal : {produit.seuil_minimal}).",
                )
            return redirect("detail_vente", pk=vente.pk)

    if not saisie["lignes"]:
        saisie["lignes"] = [{"produit": "", "quantite": "1"}]

    clients = list(Client.objects.actifs().order_by("nom", "prenom"))
    produits = list(produits_avec_stock())
    return render(
        request,
        "ventes/nouvelle_vente.html",
        {
            "clients": clients,
            "saisie": saisie,
            "est_admin": est_admin,
            "produits_js": [
                {
                    "id": p.pk,
                    "code": p.code,
                    "designation": p.designation,
                    "prix": p.prix_vente,
                    "stock": int(p.stock),
                }
                for p in produits
            ],
            "clients_js": {
                c.pk: {
                    "solde": c.solde(),
                    "plafond": c.plafond_credit,
                    "retard": c.est_en_retard(),
                }
                for c in clients
            },
        },
    )


# ==================== LISTE DES VENTES ====================

@role_requis(*LECTURE)
def liste_ventes(request):
    q = request.GET.get("q", "").strip()
    etat = request.GET.get("etat", "tous")

    ventes = Vente.objects.select_related("client", "utilisateur").order_by(
        "-date_vente", "-id_vente"
    )
    if etat == "comptant":
        ventes = ventes.filter(mode_paiement=MODE_COMPTANT, statut=STATUT_VALIDE)
    elif etat == "credit":
        ventes = ventes.filter(mode_paiement=MODE_CREDIT, statut=STATUT_VALIDE)
    elif etat == "annulees":
        ventes = ventes.exclude(statut=STATUT_VALIDE)
    else:
        etat = "tous"
    if q:
        ventes = ventes.filter(
            Q(reference__icontains=q)
            | Q(client__nom__icontains=q)
            | Q(client__prenom__icontains=q)
        )

    page = Paginator(ventes, 10).get_page(request.GET.get("page"))
    return render(
        request,
        "ventes/ventes_liste.html",
        {
            "page": page,
            "q": q,
            "etat": etat,
            "peut_gerer": request.user.role in GESTION,
        },
    )


# ==================== DÉTAIL D'UNE VENTE ====================

@role_requis(*LECTURE)
def detail_vente(request, pk):
    vente = get_object_or_404(
        Vente.objects.select_related("client", "utilisateur"), pk=pk
    )
    lignes = [
        {
            "produit": ligne.produit,
            "quantite": ligne.quantite,
            "prix": ligne.prix_unitaire,
            "sous_total": ligne.quantite * ligne.prix_unitaire,
        }
        for ligne in vente.lignes.select_related("produit")
    ]
    return render(
        request,
        "ventes/detail_vente.html",
        {
            "vente": vente,
            "lignes": lignes,
            "sous_total": sum(l["sous_total"] for l in lignes),
            "peut_gerer": request.user.role in GESTION,
        },
    )


# ==================== ANNULATION D'UNE VENTE ====================

@role_requis(*GESTION)
def annulation_vente(request, pk):
    vente = get_object_or_404(Vente.objects.select_related("client"), pk=pk)
    if vente.statut != STATUT_VALIDE:
        messages.info(request, f"La vente {vente.reference} est déjà annulée.")
        return redirect("detail_vente", pk=vente.pk)

    form = AnnulationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            annuler_vente(
                vente_id=vente.pk,
                utilisateur=request.user,
                motif=form.cleaned_data["motif"],
            )
        except VenteError as erreur:
            form.add_error(None, str(erreur))
        else:
            messages.success(
                request,
                f"Vente {vente.reference} annulée. Les produits sont remis en stock.",
            )
            solde = vente.client.solde()
            if solde < 0:
                messages.warning(
                    request,
                    f"Attention : {vente.client} a payé {fcfa(-solde)} de plus que "
                    "ce qu'il doit. Cet argent lui revient.",
                )
            return redirect("detail_vente", pk=vente.pk)

    return render(
        request,
        "formulaire.html",
        {
            "form": form,
            "titre": f"Annuler la vente {vente.reference}",
            "aide": (
                "L'annulation remet les produits en stock par des mouvements "
                "d'entrée et corrige la dette du client. Rien n'est supprimé, "
                "mais l'annulation ne peut pas être défaite."
            ),
            "bouton": "Confirmer l'annulation",
            "classe_bouton": "btn-danger",
            "retour": reverse("detail_vente", args=[vente.pk]),
        },
    )


# ==================== FACTURE ET TICKET (IMPRESSION) ====================

def _donnees_impression(request, pk):
    """Les données à imprimer, ou None si la vente n'est pas validée."""
    vente = get_object_or_404(
        Vente.objects.select_related("client", "utilisateur"), pk=pk
    )
    if vente.statut != STATUT_VALIDE:
        messages.error(
            request,
            f"La vente {vente.reference} n'est pas validée : "
            "elle ne peut pas être imprimée.",
        )
        return None
    lignes = [
        {
            "produit": ligne.produit,
            "quantite": ligne.quantite,
            "prix": ligne.prix_unitaire,
            "sous_total": ligne.quantite * ligne.prix_unitaire,
        }
        for ligne in vente.lignes.select_related("produit")
    ]
    return {
        "vente": vente,
        "lignes": lignes,
        "sous_total": sum(l["sous_total"] for l in lignes),
    }


@role_requis(*LECTURE)
def facture_vente(request, pk):
    donnees = _donnees_impression(request, pk)
    if donnees is None:
        return redirect("detail_vente", pk=pk)
    return render(request, "ventes/facture.html", donnees)


@role_requis(*LECTURE)
def ticket_vente(request, pk):
    donnees = _donnees_impression(request, pk)
    if donnees is None:
        return redirect("detail_vente", pk=pk)
    return render(request, "ventes/ticket.html", donnees)