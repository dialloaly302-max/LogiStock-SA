from django.db import transaction
from django.utils import timezone

from comptes.templatetags.logistock_filtres import fcfa

from .models import Client, Paiement


class PaiementError(ValueError):
    """Une règle du paiement n'est pas respectée : rien n'est enregistré."""


def enregistrer_paiement(*, client_id, montant, utilisateur):
    """Enregistre un paiement dans UNE SEULE transaction.

    Renvoie (paiement, nouveau_solde). Le solde est recalculé à partir des
    ventes à crédit validées et des paiements : on ne le modifie jamais à la main.
    """
    try:
        montant = int(montant)
    except (TypeError, ValueError):
        raise PaiementError("Le montant doit être un nombre entier en FCFA.")
    if montant <= 0:
        raise PaiementError("Le montant doit être supérieur à 0.")

    with transaction.atomic():
        # Le client est verrouillé : deux paiements en même temps ne se croisent pas.
        try:
            client = Client.objects.select_for_update().get(pk=client_id)
        except (Client.DoesNotExist, ValueError, TypeError):
            raise PaiementError("Ce client n'existe pas.")

        solde = client.solde()
        if solde <= 0:
            raise PaiementError(
                "Ce client ne doit rien : aucun paiement n'est à enregistrer."
            )
        if montant > solde:
            raise PaiementError(
                f"Le montant dépasse ce que le client doit ({fcfa(solde)})."
            )

        paiement = Paiement.objects.create(
            date_paiement=timezone.now(),
            montant=montant,
            client=client,
            utilisateur=utilisateur,
        )
        nouveau_solde = client.solde()
    return paiement, nouveau_solde