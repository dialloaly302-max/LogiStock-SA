import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "logistock.settings")
django.setup()

from comptes.models import Utilisateur

identifiant = "IS41"
u = Utilisateur.objects.get(identifiant=identifiant)

if len(sys.argv) > 1 and sys.argv[1] == "debloquer":
    u.tentatives_echec = 0
    u.bloque_jusqua = None
    u.save(update_fields=["tentatives_echec", "bloque_jusqua"])
    print("Compte débloqué.")

print("Identifiant :", u.identifiant)
print("Actif :", u.is_active)
print("Échecs :", u.tentatives_echec)
print("Bloqué jusqu'à :", u.bloque_jusqua)