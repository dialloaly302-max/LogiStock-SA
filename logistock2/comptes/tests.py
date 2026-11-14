from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Utilisateur

MOT_DE_PASSE = "BonMotDePasse1"
MESSAGE = "Identifiant ou mot de passe incorrect"


class ConnexionTests(TestCase):
    def creer(self, identifiant="USER1", role="gestionnaire_stock", actif=True):
        return Utilisateur.objects.create(
            nom="Essai",
            identifiant=identifiant,
            password=make_password(MOT_DE_PASSE),
            role=role,
            is_active=actif,
        )

    def connexion(self, identifiant, mot_de_passe):
        return self.client.post(
            reverse("connexion"),
            {"identifiant": identifiant, "mot_de_passe": mot_de_passe},
        )

    def est_connecte(self):
        return "_auth_user_id" in self.client.session

    # 1. Bon mot de passe
    def test_bon_mot_de_passe(self):
        self.creer()
        reponse = self.connexion("USER1", MOT_DE_PASSE)
        self.assertRedirects(
            reponse, reverse("accueil"), fetch_redirect_response=False
        )
        self.assertTrue(self.est_connecte())

    # 2. Mauvais mot de passe
    def test_mauvais_mot_de_passe(self):
        user = self.creer()
        reponse = self.connexion("USER1", "faux")
        self.assertContains(reponse, MESSAGE)
        self.assertFalse(self.est_connecte())
        user.refresh_from_db()
        self.assertEqual(user.tentatives_echec, 1)

    # 3. Cinq échecs : blocage de 15 minutes
    def test_cinq_echecs_bloquent_le_compte(self):
        user = self.creer()
        for _ in range(settings.MAX_ECHECS):
            self.connexion("USER1", "faux")
        user.refresh_from_db()
        self.assertIsNotNone(user.bloque_jusqua)
        self.assertGreater(user.bloque_jusqua, timezone.now())

        # Même avec le bon mot de passe, le compte reste fermé
        reponse = self.connexion("USER1", MOT_DE_PASSE)
        self.assertContains(reponse, MESSAGE)
        self.assertFalse(self.est_connecte())

    # 4. Compte désactivé
    def test_compte_desactive(self):
        self.creer(actif=False)
        reponse = self.connexion("USER1", MOT_DE_PASSE)
        self.assertContains(reponse, MESSAGE)
        self.assertFalse(self.est_connecte())

    # 5. Même message si l'identifiant n'existe pas
    def test_identifiant_inconnu_meme_message(self):
        reponse = self.connexion("INCONNU", "faux")
        self.assertContains(reponse, MESSAGE)
        self.assertFalse(self.est_connecte())

    # 6. Un rôle non autorisé reçoit « Accès refusé »
    def test_acces_refuse_pour_mauvais_role(self):
        user = self.creer(role="gestionnaire_stock")
        self.client.force_login(user)
        reponse = self.client.get(reverse("liste_utilisateurs"))
        self.assertEqual(reponse.status_code, 403)
        self.assertContains(reponse, "Accès refusé", status_code=403)

    # 7. L'administrateur a accès à l'écran des utilisateurs
    def test_administrateur_voit_les_utilisateurs(self):
        admin = self.creer(identifiant="ADMIN1", role="administrateur")
        self.client.force_login(admin)
        reponse = self.client.get(reverse("liste_utilisateurs"))
        self.assertEqual(reponse.status_code, 200)