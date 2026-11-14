from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from comptes.models import Utilisateur
from ventes.models import Vente

from .models import Client, Paiement
from .services import PaiementError, enregistrer_paiement


class PaiementTests(TestCase):
    def setUp(self):
        self.numero = 0
        self.vendeur = self.creer_utilisateur("gestionnaire_ventes")
        self.keita = Client.objects.create(nom="Keita", plafond_credit=100000, actif=1)
        self.vente(self.keita, 5000)          # Keita doit 5 000 FCFA

    # ---------- outils ----------
    def creer_utilisateur(self, role):
        return Utilisateur.objects.create(
            nom="Essai", identifiant=role, password=make_password("x"), role=role
        )

    def connecter(self, role):
        user = (
            Utilisateur.objects.filter(identifiant=role).first()
            or self.creer_utilisateur(role)
        )
        self.client.force_login(user)
        return user

    def vente(self, client, montant, mode="credit", statut="validee"):
        self.numero += 1
        return Vente.objects.create(
            reference=f"V-{self.numero:04d}", date_vente=timezone.now(),
            mode_paiement=mode, remise=0, montant_total=montant,
            statut=statut, client=client, utilisateur=self.vendeur,
        )

    def payer(self, montant, client=None):
        return enregistrer_paiement(
            client_id=(client or self.keita).pk,
            montant=montant, utilisateur=self.vendeur,
        )

    def refuse(self, montant, texte, client=None):
        avant = Paiement.objects.count()
        with self.assertRaises(PaiementError) as contexte:
            self.payer(montant, client=client)
        self.assertIn(texte, str(contexte.exception))
        self.assertEqual(Paiement.objects.count(), avant)

    def url(self, client=None):
        return reverse("nouveau_paiement", args=[(client or self.keita).pk])

    # ================= LA RÈGLE DU PAIEMENT =================
    def test_paiement_normal(self):
        paiement, solde = self.payer(2000)
        self.assertEqual(paiement.montant, 2000)
        self.assertEqual(paiement.client, self.keita)
        self.assertEqual(paiement.utilisateur, self.vendeur)
        self.assertIsNotNone(paiement.date_paiement)
        self.assertEqual(solde, 3000)
        self.assertEqual(self.keita.solde(), 3000)

    def test_paiement_du_solde_complet(self):
        _, solde = self.payer(5000)
        self.assertEqual(solde, 0)
        self.assertEqual(self.keita.solde(), 0)

    def test_montant_superieur_au_solde_refuse(self):
        self.refuse(5001, "dépasse")

    def test_montant_invalide(self):
        self.refuse(0, "supérieur à 0")
        self.refuse(-5, "supérieur à 0")
        self.refuse("abc", "nombre entier")
        self.refuse(None, "nombre entier")

    def test_client_sans_dette(self):
        zero = Client.objects.create(nom="Zero", plafond_credit=0, actif=1)
        self.refuse(100, "ne doit rien", client=zero)

    def test_paiements_cumules(self):
        self.payer(3000)                       # reste 2 000
        self.refuse(2500, "dépasse")
        _, solde = self.payer(2000)
        self.assertEqual(solde, 0)
        self.assertEqual(Paiement.objects.count(), 2)

    def test_client_archive_peut_payer(self):
        self.keita.archiver()
        _, solde = self.payer(1000)
        self.assertEqual(solde, 4000)

    def test_client_inexistant(self):
        with self.assertRaises(PaiementError):
            enregistrer_paiement(client_id=99999, montant=100, utilisateur=self.vendeur)

    def test_comptant_et_annulee_ne_comptent_pas_dans_la_dette(self):
        self.vente(self.keita, 10000, mode="comptant")
        self.vente(self.keita, 8000, statut="annulee")
        self.assertEqual(self.keita.solde(), 5000)
        self.refuse(5001, "dépasse")

    # ================= LES PAGES =================
    def test_page_formulaire(self):
        self.connecter("gestionnaire_ventes")
        reponse = self.client.get(self.url())
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Solde actuel à payer")

    def test_page_paiement_partiel(self):
        self.connecter("gestionnaire_ventes")
        reponse = self.client.post(self.url(), {"montant": 2000}, follow=True)
        self.assertContains(reponse, "Il reste à payer")
        self.assertEqual(reponse.context["solde"], 3000)
        self.assertEqual(reponse.context["total_paye"], 2000)

    def test_page_paiement_complet(self):
        self.connecter("gestionnaire_ventes")
        reponse = self.client.post(self.url(), {"montant": 5000}, follow=True)
        self.assertContains(reponse, "a tout payé")
        self.assertContains(reponse, "Bon payeur")
        self.assertNotContains(reponse, "Débiteur")

    def test_page_montant_trop_grand(self):
        self.connecter("gestionnaire_ventes")
        reponse = self.client.post(self.url(), {"montant": 9999})
        self.assertContains(reponse, "dépasse")
        self.assertEqual(Paiement.objects.count(), 0)

    def test_page_montant_nul_ou_texte(self):
        self.connecter("gestionnaire_ventes")
        reponse = self.client.post(self.url(), {"montant": 0})
        self.assertContains(reponse, "supérieur à 0")
        reponse = self.client.post(self.url(), {"montant": "abc"})
        self.assertContains(reponse, "nombre entier")
        self.assertEqual(Paiement.objects.count(), 0)

    def test_page_client_sans_dette(self):
        self.connecter("gestionnaire_ventes")
        zero = Client.objects.create(nom="Zero", plafond_credit=0, actif=1)
        reponse = self.client.get(self.url(zero), follow=True)
        self.assertContains(reponse, "ne doit rien")

    def test_bouton_paiement_dans_la_fiche(self):
        fiche = reverse("fiche_client", args=[self.keita.pk])
        self.connecter("gestionnaire_ventes")
        self.assertContains(self.client.get(fiche), "Enregistrer un paiement")
        self.connecter("manager")
        self.assertNotContains(self.client.get(fiche), "Enregistrer un paiement")
        self.payer(5000)
        self.connecter("gestionnaire_ventes")
        self.assertNotContains(self.client.get(fiche), "Enregistrer un paiement")

    def test_droits(self):
        self.connecter("manager")
        self.assertEqual(self.client.get(self.url()).status_code, 403)
        self.assertEqual(self.client.post(self.url(), {"montant": 100}).status_code, 403)
        self.assertEqual(Paiement.objects.count(), 0)
        self.connecter("gestionnaire_stock")
        self.assertEqual(self.client.get(self.url()).status_code, 403)
        self.connecter("administrateur")
        self.assertEqual(self.client.get(self.url()).status_code, 200)