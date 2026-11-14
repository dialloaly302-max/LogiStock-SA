import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "logistock.settings")
django.setup()

from catalogue.models import Produit
from ventes.models import Contenir, Vente

print("=== VENTES ET LIGNES ===")
for v in Vente.objects.select_related("client").order_by("id_vente"):
    lignes = Contenir.objects.filter(vente=v).select_related("produit")
    sous_total = sum(l.quantite * l.prix_unitaire for l in lignes)
    print(
        v.id_vente, v.reference, v.mode_paiement, v.statut,
        "| remise:", v.remise, "| total:", v.montant_total,
        "| sous-total calculé:", sous_total,
    )
    for l in lignes:
        print("      ", l.produit.code, l.quantite, "x", l.prix_unitaire)

print("=== PRODUITS ===")
for p in Produit.objects.order_by("code"):
    print(p.code, "| vente:", p.prix_vente, "| seuil:", p.seuil_minimal, "| stock:", p.stock_actuel())