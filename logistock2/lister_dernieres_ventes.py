import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "logistock.settings")
django.setup()

from django.utils import timezone

from catalogue.models import Produit
from comptes.models import Utilisateur
from stock.models import Stock
from ventes.models import Contenir, Vente

print("=== 8 DERNIERES VENTES ===")
ventes = Vente.objects.select_related("client", "utilisateur").order_by("-id_vente")[:8]
for v in ventes:
    print(
        v.reference,
        timezone.localtime(v.date_vente).strftime("%d/%m %H:%M:%S"),
        "|", v.client.nom, "|", v.mode_paiement, v.statut,
        "| remise:", v.remise, "| total:", v.montant_total,
        "| vendeur:", v.utilisateur.identifiant, "(", v.utilisateur.role, ")",
    )
    for ligne in Contenir.objects.filter(vente=v).select_related("produit"):
        print("      ", ligne.produit.code, ligne.quantite, "x", ligne.prix_unitaire)

print("=== COMPTES D'ESSAI ===")
for u in Utilisateur.objects.filter(identifiant__in=["VTEST", "MTEST", "IS41"]):
    print(u.identifiant, "|", u.role, "|", "actif" if u.is_active else "desactive")

print("=== STOCK DE ESSAI2 ===")
print(Produit.objects.get(code="ESSAI2").stock_actuel())