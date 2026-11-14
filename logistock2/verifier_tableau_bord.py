import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "logistock.settings")
django.setup()

from tableau_bord.services import donnees_tableau_de_bord, lire_periode

debut, fin, erreur = lire_periode("", "")
d = donnees_tableau_de_bord(debut, fin)

print("Periode :", debut, "au", fin, "| erreur :", erreur)
print("Ventes du jour  :", d["jour"])
print("Ventes du mois  :", d["mois"])
print("Credits         :", d["credits"])
print("Stock critique  :", d["nb_critiques"])
for p in d["critiques"]:
    print("    ", p.code, "stock", p.stock, "seuil", p.seuil_minimal)
print("CA de la periode:", d["periode"])
print("Classement :")
for ligne in d["classement"]:
    print("    ", ligne)