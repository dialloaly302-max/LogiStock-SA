import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "logistock.settings")
django.setup()

from clients.models import Paiement
from stock.models import Stock
from ventes.models import Vente

print("=== VENTES ANNULEES ===")
annulees = Vente.objects.exclude(statut="validee").select_related(
    "utilisateur_annulation"
)
for v in annulees:
    par = v.utilisateur_annulation.identifiant if v.utilisateur_annulation else None
    print(
        v.reference, v.statut,
        "| date_annulation:", v.date_annulation,
        "| par:", par,
        "| motif:", repr(v.motif_annulation),
    )
    for m in Stock.objects.filter(vente=v).order_by("date_mouvement", "id_stock"):
        print("     ", m.type_mouvement, m.quantite, "restante:", m.quantite_restante, "|", m.motif)

print("=== PAIEMENTS ===")
for p in Paiement.objects.select_related("client", "utilisateur").order_by("id_paiement"):
    print(p.id_paiement, p.date_paiement, p.client.nom, p.montant, "par", p.utilisateur.identifiant)