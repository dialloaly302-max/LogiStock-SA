from django.db import IntegrityError, transaction
from django.utils import timezone

from catalogue.models import TYPE_ENTREE, TYPE_SORTIE, Produit
from clients.models import MODE_CREDIT, STATUT_VALIDE, Client
from comptes.menu import ADMIN
from comptes.templatetags.logistock_filtres import fcfa
from stock.services import StockError, enregistrer_mouvement

from .models import Contenir, Vente

MODE_COMPTANT = "comptant"
REMISE_MAX_POURCENT = 10


class VenteError(ValueError):
    """Une règle de la vente n'est pas respectée : rien n'est enregistré."""


def _normaliser_lignes(lignes):
    """[(produit, quantité), ...] devient {produit_id: quantité}.

    Les lignes vides sont ignorées, un même produit saisi deux fois est additionné.
    """
    regroupees = {}
    for produit_id, quantite in lignes or []:
        if str(produit_id or "").strip() == "" and str(quantite or "").strip() == "":
            continue
        try:
            produit_id = int(produit_id)
            quantite = int(quantite)
        except (TypeError, ValueError):
            raise VenteError(
                "Chaque ligne doit avoir un produit et une quantité entière."
            )
        if quantite <= 0:
            raise VenteError("Chaque quantité doit être supérieure à 0.")
        regroupees[produit_id] = regroupees.get(produit_id, 0) + quantite
    if not regroupees:
        raise VenteError("Ajoutez au moins un produit à la vente.")
    return regroupees


def _prochain_numero():
    """Numéro de la prochaine vente (verrou sur la dernière : pas de doublon)."""
    derniere = Vente.objects.select_for_update().order_by("-id_vente").first()
    if derniere is None:
        return 1
    try:
        return int(derniere.reference.split("-")[-1]) + 1
    except ValueError:
        return derniere.id_vente + 1


def valider_vente(*, utilisateur, client_id, mode, remise, lignes,
                  autoriser_depassement=False):
    """Valide une vente dans UNE SEULE transaction.

    Renvoie (vente, alertes). Si une règle échoue, une VenteError est levée
    et RIEN n'est enregistré (ni vente, ni lignes, ni mouvements de stock).
    """
    est_admin = utilisateur.role == ADMIN
    depassement_ok = est_admin and bool(autoriser_depassement)

    if mode not in (MODE_COMPTANT, MODE_CREDIT):
        raise VenteError("Choisissez le mode de paiement : comptant ou crédit.")
    try:
        remise = int(remise or 0)
    except (TypeError, ValueError):
        raise VenteError("La remise doit être un nombre entier en FCFA.")
    if remise < 0:
        raise VenteError("La remise ne peut pas être négative.")
    demandees = _normaliser_lignes(lignes)

    try:
        with transaction.atomic():
            # --- Le client (verrouillé : deux ventes à crédit ne se croisent pas)
            try:
                client = Client.objects.select_for_update().get(pk=client_id)
            except (Client.DoesNotExist, ValueError, TypeError):
                raise VenteError("Choisissez un client.")
            if not client.est_actif():
                raise VenteError(
                    "Ce client est archivé : il ne peut plus faire d'achat."
                )

            # --- Les produits (verrouillés, toujours dans le même ordre)
            produits = {
                p.pk: p
                for p in Produit.objects.select_for_update()
                .filter(pk__in=list(demandees))
                .order_by("pk")
            }
            if len(produits) != len(demandees):
                raise VenteError("Un des produits choisis n'existe plus.")

            # --- 1. Stock disponible
            for pk, quantite in demandees.items():
                produit = produits[pk]
                disponible = produit.stock_actuel()
                if quantite > disponible:
                    raise VenteError(
                        f"Stock insuffisant pour « {produit.designation} » : "
                        f"demandé {quantite}, disponible {disponible}."
                    )

            sous_total = sum(
                quantite * produits[pk].prix_vente
                for pk, quantite in demandees.items()
            )

            # --- 2. Remise
            if remise > sous_total:
                raise VenteError("La remise ne peut pas dépasser le sous-total.")
            if not est_admin and remise * 100 > sous_total * REMISE_MAX_POURCENT:
                maximum = sous_total * REMISE_MAX_POURCENT // 100
                raise VenteError(
                    f"Remise refusée : elle dépasse {REMISE_MAX_POURCENT} % du "
                    f"total. Maximum autorisé : {fcfa(maximum)}."
                )
            total = sous_total - remise

            # --- 3. Crédit
            if mode == MODE_CREDIT and not depassement_ok:
                solde = client.solde()
                if solde + total > client.plafond_credit:
                    raise VenteError(
                        f"Crédit refusé : le solde actuel ({fcfa(solde)}) plus "
                        f"cette vente ({fcfa(total)}) dépasse le plafond de "
                        f"{fcfa(client.plafond_credit)}."
                    )
                if client.est_en_retard():
                    raise VenteError(
                        f"Crédit refusé : {client} est en retard de plus de "
                        "30 jours sur une vente à crédit."
                    )

            # --- 4. Création : vente, lignes, mouvements de stock
            reference = f"V-{_prochain_numero():04d}"
            vente = Vente.objects.create(
                reference=reference,
                date_vente=timezone.now(),
                mode_paiement=mode,
                remise=remise,
                montant_total=total,
                statut=STATUT_VALIDE,
                client=client,
                utilisateur=utilisateur,
            )
            alertes = []
            for pk, quantite in demandees.items():
                produit = produits[pk]
                Contenir.objects.create(
                    vente=vente, produit=produit, quantite=quantite,
                    prix_unitaire=produit.prix_vente,
                )
                try:
                    mouvement = enregistrer_mouvement(
                        produit, TYPE_SORTIE, quantite, utilisateur,
                        f"Vente {reference}", vente=vente,
                    )
                except StockError as erreur:
                    raise VenteError(str(erreur))
                # --- 5. Alerte de stock bas
                if mouvement.quantite_restante <= produit.seuil_minimal:
                    alertes.append(
                        {"produit": produit, "restante": mouvement.quantite_restante}
                    )
    except IntegrityError:
        raise VenteError(
            "Une autre vente vient d'être enregistrée en même temps. "
            "Votre vente n'a pas été enregistrée : recommencez."
        )

    return vente, alertes


STATUT_ANNULE = "annulee"
MOTIF_CORRECTION = "Correction : annulation de {reference}"


def annuler_vente(*, vente_id, utilisateur, motif):
    """Annule une vente dans UNE SEULE transaction. Rien n'est supprimé.

    - le motif est obligatoire ;
    - une vente déjà annulée ne peut pas l'être une deuxième fois ;
    - chaque ligne de la vente remet son stock par un mouvement d'entrée.
    Si une étape échoue, une VenteError est levée et RIEN n'est modifié.
    """
    motif = (motif or "").strip()
    if not motif:
        raise VenteError("Le motif d'annulation est obligatoire.")
    if len(motif) > 255:
        raise VenteError("Le motif est trop long (255 caractères au maximum).")

    with transaction.atomic():
        # La vente est verrouillée : deux annulations en même temps sont impossibles.
        try:
            vente = Vente.objects.select_for_update().get(pk=vente_id)
        except (Vente.DoesNotExist, ValueError, TypeError):
            raise VenteError("Cette vente n'existe pas.")
        if vente.statut != STATUT_VALIDE:
            raise VenteError(
                f"La vente {vente.reference} est déjà annulée : "
                "elle ne peut pas l'être une deuxième fois."
            )

        lignes = list(
            Contenir.objects.filter(vente=vente)
            .select_related("produit")
            .order_by("produit_id")
        )
        # Les produits sont verrouillés dans le même ordre que pour une vente.
        list(
            Produit.objects.select_for_update()
            .filter(pk__in=[l.produit_id for l in lignes])
            .order_by("pk")
        )

        texte_correction = MOTIF_CORRECTION.format(reference=vente.reference)
        for ligne in lignes:
            try:
                enregistrer_mouvement(
                    ligne.produit, TYPE_ENTREE, ligne.quantite, utilisateur,
                    texte_correction, vente=vente,
                )
            except StockError as erreur:
                raise VenteError(str(erreur))

        vente.statut = STATUT_ANNULE
        vente.motif_annulation = motif
        vente.date_annulation = timezone.now()
        vente.utilisateur_annulation = utilisateur
        vente.save(
            update_fields=[
                "statut", "motif_annulation", "date_annulation",
                "utilisateur_annulation",
            ]
        )
    return vente