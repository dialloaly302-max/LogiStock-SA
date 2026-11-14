import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "logistock.settings")
django.setup()

from comptes.models import Utilisateur

for u in Utilisateur.objects.order_by("id_utilisateur"):
    print(
        u.id_utilisateur,
        repr(u.identifiant),
        u.role,
        "actif" if u.is_active else "désactivé",
        "échecs:", u.tentatives_echec,
        "bloqué jusqu'à:", u.bloque_jusqua,
    )