from django.apps import apps
from django.conf import settings
from django.test.runner import DiscoverRunner


class TestRunnerTablesExistantes(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        # Pour les tests seulement : Django crée aussi les tables
        # « non gérées » dans la base temporaire.
        self.modeles_non_geres = [
            m for m in apps.get_models() if not m._meta.managed
        ]
        for m in self.modeles_non_geres:
            m._meta.managed = True
        # Toutes les applications concernées (comptes, catalogue, clients,
        # ventes, stock) : on crée leurs tables directement depuis les modèles.
        settings.MIGRATION_MODULES = {
            m._meta.app_label: None for m in self.modeles_non_geres
        }
        super().setup_test_environment(**kwargs)

    def teardown_test_environment(self, **kwargs):
        super().teardown_test_environment(**kwargs)
        for m in self.modeles_non_geres:
            m._meta.managed = False