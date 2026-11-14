from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Utilisateur

MESSAGE_ERREUR = (
    "Identifiant ou mot de passe incorrect, "
    "ou compte indisponible. Réessayez plus tard."
)


def connexion(request):
    # Déjà connecté : pas besoin de revoir la page
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    identifiant = ""

    if request.method == "POST":
        identifiant = request.POST.get("identifiant", "").strip()
        mot_de_passe = request.POST.get("mot_de_passe", "")
        maintenant = timezone.now()
        user = Utilisateur.objects.filter(identifiant=identifiant).first()

        if user and user.bloque_jusqua and user.bloque_jusqua > maintenant:
            # Compte bloqué : on refuse, même avec le bon mot de passe
            messages.error(request, MESSAGE_ERREUR)

        elif user and user.is_active and user.check_password(mot_de_passe):
            # Bon identifiant, bon mot de passe, compte actif
            user.tentatives_echec = 0
            user.bloque_jusqua = None
            user.save(update_fields=["tentatives_echec", "bloque_jusqua"])
            login(request, user)
            suite = request.POST.get("next") or request.GET.get("next")
            if suite and url_has_allowed_host_and_scheme(
                suite, allowed_hosts={request.get_host()}
            ):
                return redirect(suite)
            return redirect(settings.LOGIN_REDIRECT_URL)

        else:
            # Échec : on compte seulement pour un compte actif qui existe
            if user and user.is_active:
                user.tentatives_echec += 1
                if user.tentatives_echec >= settings.MAX_ECHECS:
                    user.bloque_jusqua = maintenant + timedelta(
                        minutes=settings.DUREE_BLOCAGE_MINUTES
                    )
                    user.tentatives_echec = 0
                user.save(update_fields=["tentatives_echec", "bloque_jusqua"])
            messages.error(request, MESSAGE_ERREUR)

    contexte = {
        "identifiant": identifiant,
        "next": request.GET.get("next", ""),
    }
    return render(request, "comptes/connexion.html", contexte)

from django.db.models import Sum
from django.urls import NoReverseMatch

from catalogue.models import Produit
from clients.models import STATUT_VALIDE, Client
from ventes.models import Vente

from .decorators import role_requis
from .menu import ADMIN, MANAGER, STOCK, TOUS, VENTES


def _lien(nom):
    """Adresse d'une page, ou « # » si la page n'existe pas encore."""
    try:
        return reverse(nom)
    except NoReverseMatch:
        return "#"


@role_requis(*TOUS)
def accueil(request):
    role = request.user.role
    cartes = []

    # Carte 1 : ventes du jour
    if role in (ADMIN, MANAGER, VENTES):
        debut = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
        ventes = Vente.objects.filter(
            statut=STATUT_VALIDE,
            date_vente__gte=debut,
            date_vente__lt=debut + timedelta(days=1),
        )
        total = ventes.aggregate(t=Sum("montant_total"))["t"] or 0
        cartes.append({
            "libelle": "Ventes du jour",
            "valeur": total,
            "montant": True,
            "detail": f"{ventes.count()} vente(s) validée(s) aujourd'hui",
            "classe": "succes",
            "url": _lien("liste_ventes"),
        })

    # Carte 2 : stock critique
    if role in (ADMIN, MANAGER, STOCK):
        nb_critiques = sum(
            1 for p in Produit.objects.all() if p.stock_actuel() <= p.seuil_minimal
        )
        cartes.append({
            "libelle": "Stock critique",
            "valeur": nb_critiques,
            "montant": False,
            "detail": "produit(s) au seuil minimal ou en dessous",
            "classe": "danger" if nb_critiques else "succes",
            "url": _lien("liste_stock"),
        })

    # Carte 3 : crédits à recouvrer
    if role in (ADMIN, MANAGER, VENTES):
        soldes = [c.solde() for c in Client.objects.all()]
        dettes = [s for s in soldes if s > 0]
        cartes.append({
            "libelle": "Crédits à recouvrer",
            "valeur": sum(dettes),
            "montant": True,
            "detail": f"{len(dettes)} client(s) avec une dette",
            "classe": "alerte" if dettes else "succes",
            "url": _lien("liste_clients"),
        })

    # Carte 4 : produits
    if role in (ADMIN, MANAGER, STOCK):
        cartes.append({
            "libelle": "Produits",
            "valeur": Produit.objects.count(),
            "montant": False,
            "detail": "produits au catalogue",
            "classe": "",
            "url": _lien("liste_produits"),
        })

    return render(request, "comptes/accueil.html", {"cartes": cartes})
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from .forms import UtilisateurForm


from django.core.paginator import Paginator
from django.db.models import Q


@role_requis("administrateur")
def liste_utilisateurs(request):
    q = request.GET.get("q", "").strip()
    utilisateurs = Utilisateur.objects.order_by("nom", "prenom")
    if q:
        utilisateurs = utilisateurs.filter(
            Q(nom__icontains=q)
            | Q(prenom__icontains=q)
            | Q(identifiant__icontains=q)
            | Q(role__icontains=q)
        )
    page = Paginator(utilisateurs, 5).get_page(request.GET.get("page"))
    return render(
        request,
        "comptes/utilisateurs_liste.html",
        {"page": page, "q": q},
    )

@role_requis("administrateur")
def creer_utilisateur(request):
    form = UtilisateurForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.is_active = True
        user.tentatives_echec = 0
        user.save()
        messages.success(request, "Utilisateur créé avec succès.")
        return redirect("liste_utilisateurs")
    return render(
        request,
        "comptes/utilisateur_form.html",
        {"form": form, "titre": "Créer un utilisateur"},
    )


@role_requis("administrateur")
def modifier_utilisateur(request, pk):
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    form = UtilisateurForm(request.POST or None, instance=utilisateur)
    if request.method == "POST" and form.is_valid():
        if (
            utilisateur == request.user
            and form.cleaned_data["role"] != "administrateur"
        ):
            form.add_error(
                "role",
                "Vous ne pouvez pas retirer votre propre rôle d'administrateur.",
            )
        else:
            form.save()
            messages.success(request, "Utilisateur modifié avec succès.")
            return redirect("liste_utilisateurs")
    return render(
        request,
        "comptes/utilisateur_form.html",
        {"form": form, "titre": "Modifier un utilisateur"},
    )


@role_requis("administrateur")
@require_POST
def basculer_actif(request, pk):
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    if utilisateur == request.user:
        messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
    else:
        utilisateur.is_active = not utilisateur.is_active
        utilisateur.save(update_fields=["is_active"])
        etat = "activé" if utilisateur.is_active else "désactivé"
        messages.success(request, f"Le compte de {utilisateur.identifiant} est {etat}.")
    return redirect("liste_utilisateurs")