from datetime import date, datetime, time, timedelta

from django.db.models import Count, F, IntegerField, OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from clients.models import MODE_CREDIT, STATUT_VALIDE, Client, Paiement
from stock.services import produits_avec_stock
from ventes.models import Contenir, Vente


# ---------- Outils pour les dates ----------

def _debut_du_jour(jour):
    """Minuit du jour donné, avec le fuseau horaire du projet."""
    return timezone.make_aware(datetime.combine(jour, time.min))


def lire_periode(debut_texte, fin_texte):
    """Lit les dates choisies. Renvoie (début, fin, message d'erreur ou None).

    Par défaut : du premier jour du mois jusqu'à aujourd'hui.
    """
    aujourdhui = timezone.localdate()
    debut_defaut = aujourdhui.replace(day=1)
    erreur = None
    try:
        debut = date.fromisoformat(debut_texte) if debut_texte else debut_defaut
        fin = date.fromisoformat(fin_texte) if fin_texte else aujourdhui
    except ValueError:
        return debut_defaut, aujourdhui, "Date invalide : la période par défaut est affichée."
    if debut > fin:
        return debut_defaut, aujourdhui, (
            "La date de début doit être avant la date de fin : "
            "la période par défaut est affichée."
        )
    return debut, fin, erreur


# ---------- Les requêtes ----------

def ventes_validees(debut, fin):
    """Requête 1 : garde seulement les ventes validées (les annulées sont exclues)
    dont la date est entre le début et la fin, fin incluse."""
    return Vente.objects.filter(
        statut=STATUT_VALIDE,
        date_vente__gte=_debut_du_jour(debut),
        date_vente__lt=_debut_du_jour(fin + timedelta(days=1)),
    )


def chiffre_affaires(debut, fin):
    """Requête 2 (aggregate) : additionne les montants et compte les ventes
    validées de la période, en une seule requête."""
    resultat = ventes_validees(debut, fin).aggregate(
        total=Sum("montant_total"), nombre=Count("pk")
    )
    return {"total": int(resultat["total"] or 0), "nombre": resultat["nombre"]}


def classement_produits(debut, fin):
    """Requête 3 (annotate) : pour chaque produit, additionne les quantités et
    les montants des lignes des ventes validées, puis les trie du plus vendu
    au moins vendu."""
    lignes = (
        Contenir.objects.filter(
            vente__statut=STATUT_VALIDE,
            vente__date_vente__gte=_debut_du_jour(debut),
            vente__date_vente__lt=_debut_du_jour(fin + timedelta(days=1)),
        )
        .values("produit__code", "produit__designation")
        .annotate(
            total_quantite=Sum("quantite"),
            total_ca=Sum(F("quantite") * F("prix_unitaire")),
            nombre_ventes=Count("vente", distinct=True),
        )
        .order_by("-total_quantite", "produit__designation")
    )
    return [
        {
            "code": ligne["produit__code"],
            "designation": ligne["produit__designation"],
            "quantite": int(ligne["total_quantite"]),
            "ca": int(ligne["total_ca"]),
            "nombre_ventes": ligne["nombre_ventes"],
        }
        for ligne in lignes
    ]


def produits_critiques():
    """Requête 4 (annotate + filter) : calcule le stock de chaque produit
    (entrées moins sorties) et garde ceux dont le stock est inférieur ou égal
    à leur seuil minimal, les plus bas d'abord."""
    return (
        produits_avec_stock()
        .filter(stock__lte=F("seuil_minimal"))
        .order_by("stock", "designation")
    )


def credits_a_recouvrer():
    """Requête 5 (annotate + aggregate) : pour chaque client, calcule ce qu'il
    doit (ventes à crédit validées moins paiements), garde ceux qui doivent
    quelque chose, puis additionne leurs dettes."""
    du = (
        Vente.objects.filter(
            client=OuterRef("pk"), mode_paiement=MODE_CREDIT, statut=STATUT_VALIDE
        )
        .order_by()
        .values("client")
        .annotate(t=Sum("montant_total"))
        .values("t")
    )
    paye = (
        Paiement.objects.filter(client=OuterRef("pk"))
        .order_by()
        .values("client")
        .annotate(t=Sum("montant"))
        .values("t")
    )
    debiteurs = (
        Client.objects.annotate(
            du=Coalesce(Subquery(du, output_field=IntegerField()), 0),
            paye=Coalesce(Subquery(paye, output_field=IntegerField()), 0),
        )
        .annotate(solde_calcule=F("du") - F("paye"))
        .filter(solde_calcule__gt=0)
    )
    resultat = debiteurs.aggregate(total=Sum("solde_calcule"), nombre=Count("pk"))
    return {"total": int(resultat["total"] or 0), "nombre": resultat["nombre"]}


def donnees_tableau_de_bord(debut, fin):
    """Toutes les données du tableau de bord, pour la page et pour les exports."""
    aujourdhui = timezone.localdate()
    critiques = list(produits_critiques())
    classement = classement_produits(debut, fin)
    return {
        "debut": debut,
        "fin": fin,
        "jour": chiffre_affaires(aujourdhui, aujourdhui),
        "mois": chiffre_affaires(aujourdhui.replace(day=1), aujourdhui),
        "credits": credits_a_recouvrer(),
        "critiques": critiques,
        "nb_critiques": len(critiques),
        "periode": chiffre_affaires(debut, fin),
        "classement": classement,
        "top5": classement[:5],
    }