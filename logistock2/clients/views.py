from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from comptes.decorators import role_requis
from comptes.menu import ADMIN, MANAGER, VENTES
from comptes.templatetags.logistock_filtres import fcfa
from ventes.models import Contenir, Vente

from .forms import ClientForm, PaiementForm
from .services import PaiementError, enregistrer_paiement
from .models import STATUT_VALIDE, Client

LECTURE = (ADMIN, MANAGER, VENTES)   # peuvent consulter
GESTION = (ADMIN, VENTES)            # peuvent ajouter, modifier, archiver


# ==================== LISTE ====================

@role_requis(*LECTURE)
def liste_clients(request):
    q = request.GET.get("q", "").strip()
    etat = request.GET.get("etat", "actifs")
    if etat not in ("actifs", "archives", "tous"):
        etat = "actifs"

    clients = Client.objects.order_by("nom", "prenom")
    if etat == "actifs":
        clients = clients.actifs()
    elif etat == "archives":
        clients = clients.filter(actif=0)
    if q:
        clients = clients.filter(
            Q(nom__icontains=q)
            | Q(prenom__icontains=q)
            | Q(telephone__icontains=q)
        )

    page = Paginator(clients, 10).get_page(request.GET.get("page"))
    lignes = [
        {
            "client": c,
            "solde": c.solde(),
            "statut": c.statut_paiement(),
            "retard": c.est_en_retard(),
        }
        for c in page
    ]
    return render(
        request,
        "clients/clients_liste.html",
        {
            "page": page,
            "lignes": lignes,
            "q": q,
            "etat": etat,
            "peut_gerer": request.user.role in GESTION,
        },
    )


# ==================== FICHE CLIENT ====================

@role_requis(*LECTURE)
def fiche_client(request, pk):
    client = get_object_or_404(Client, pk=pk)

    ventes = (
        Vente.objects.filter(client=client)
        .prefetch_related(
            Prefetch("lignes", queryset=Contenir.objects.select_related("produit"))
        )
        .order_by("-date_vente", "-id_vente")
    )
    paiements = client.paiements.select_related("utilisateur").order_by(
        "-date_paiement", "-id_paiement"
    )

    solde = client.solde()
    retard = client.vente_en_retard()
    total_achats = (
        ventes.filter(statut=STATUT_VALIDE).aggregate(t=Sum("montant_total"))["t"] or 0
    )
    return render(
        request,
        "clients/fiche_client.html",
        {
            "client": client,
            "ventes": ventes,
            "paiements": paiements,
            "solde": solde,
            "statut": "debiteur" if solde > 0 else "bon_payeur",
            "retard": retard,
            "jours_retard": (timezone.now() - retard.date_vente).days if retard else 0,
            "total_achats": total_achats,
            "total_paye": client.total_paye(),
                        "credit_disponible": max(client.plafond_credit - max(solde, 0), 0),
            "peut_gerer": request.user.role in GESTION,
        },
    )


# ==================== AJOUT, MODIFICATION ====================

@role_requis(*GESTION)
def creer_client(request):
    form = ClientForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        client = form.save(commit=False)
        client.actif = 1
        client.save()
        messages.success(request, f"Client « {client} » ajouté avec succès.")
        return redirect("fiche_client", pk=client.pk)
    return render(
        request,
        "formulaire.html",
        {
            "form": form,
            "titre": "Ajouter un client",
            "retour": reverse("liste_clients"),
        },
    )


@role_requis(*GESTION)
def modifier_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    form = ClientForm(request.POST or None, instance=client)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Client modifié avec succès.")
        return redirect("fiche_client", pk=client.pk)
    return render(
        request,
        "formulaire.html",
        {
            "form": form,
            "titre": "Modifier le client",
            "retour": reverse("fiche_client", args=[client.pk]),
        },
    )


# ==================== ARCHIVAGE (JAMAIS DE SUPPRESSION) ====================

@role_requis(*GESTION)
@require_POST
def archiver_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if not client.est_actif():
        messages.info(request, f"Le client « {client} » est déjà archivé.")
    else:
        client.archiver()
        solde = client.solde()
        if solde > 0:
            messages.warning(
                request,
                f"Client « {client} » archivé. Attention : il doit encore "
                f"{fcfa(solde)}. Sa dette reste suivie.",
            )
        else:
            messages.success(
                request,
                f"Client « {client} » archivé. Il n'apparaîtra plus dans le "
                "choix d'une vente. Son historique est conservé.",
            )
    return redirect("fiche_client", pk=client.pk)


@role_requis(*GESTION)
@require_POST
def reactiver_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if client.est_actif():
        messages.info(request, f"Le client « {client} » est déjà actif.")
    else:
        client.reactiver()
        messages.success(request, f"Client « {client} » réactivé.")
    return redirect("fiche_client", pk=client.pk)


# ==================== PAIEMENT D'UN CLIENT ====================

@role_requis(*GESTION)
def nouveau_paiement(request, pk):
    client = get_object_or_404(Client, pk=pk)
    solde = client.solde()
    if solde <= 0:
        messages.info(
            request, f"{client} ne doit rien : aucun paiement à enregistrer."
        )
        return redirect("fiche_client", pk=client.pk)

    form = PaiementForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            paiement, nouveau_solde = enregistrer_paiement(
                client_id=client.pk,
                montant=form.cleaned_data["montant"],
                utilisateur=request.user,
            )
        except PaiementError as erreur:
            form.add_error(None, str(erreur))
        else:
            if nouveau_solde == 0:
                messages.success(
                    request,
                    f"Paiement de {fcfa(paiement.montant)} enregistré. "
                    f"{client} a tout payé : son solde est de 0 FCFA.",
                )
            else:
                messages.success(
                    request,
                    f"Paiement de {fcfa(paiement.montant)} enregistré. "
                    f"Il reste à payer : {fcfa(nouveau_solde)}.",
                )
            return redirect("fiche_client", pk=client.pk)

    return render(
        request,
        "formulaire.html",
        {
            "form": form,
            "titre": f"Paiement de {client}",
            "aide": (
                f"Solde actuel à payer : {fcfa(solde)}. "
                "Le montant ne peut pas dépasser ce solde."
            ),
            "bouton": "Enregistrer le paiement",
            "classe_bouton": "btn-success",
            "retour": reverse("fiche_client", args=[client.pk]),
        },
    )