from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.shortcuts import render


def role_requis(*roles):
    """Autorise la vue seulement pour les rôles donnés."""

    def decorateur(vue):
        @wraps(vue)
        def enveloppe(request, *args, **kwargs):
            # 1. Pas connecté : on envoie vers la page de connexion
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            # 2. Connecté mais mauvais rôle : page « Accès refusé »
            if request.user.role not in roles:
                return render(request, "comptes/acces_refuse.html", status=403)
            # 3. Tout va bien : on exécute la vue
            return vue(request, *args, **kwargs)

        return enveloppe

    return decorateur