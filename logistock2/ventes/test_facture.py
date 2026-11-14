from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalogue.models import Categorie, Produit
from clients.models import Client
from comptes.models import Utilisateur
from comptes.templatetags.logistock_filtres import fcfa
from stock.services import enregistrer_entree

from .services import annuler_vente, valider_vente


class FactureTests(TestCase):
    def setUp(self):
        categorie = Categorie.objects.create(nom_categorie="Papeterie")
        self.p1 = Produit.objects.create(
            code="P001", designation="Stylo", prix_achat=700,
            prix_vente=1500, seuil_minimal=5, categorie=categorie,
        )
        self.p2 = Produit.objects.create(
            code="P002", designation="Cahier", prix_achat=1000,
            prix_vente=2000, seuil_minimal=5, categorie=categorie,
        )
        self.admin = self.creer_utilisateur("administrateur")
        self.vendeur = self.creer_utilisateur("gestionnaire_ventes")
        self.keita = Client.objects.create(
            nom="Keita", telephone="64056795", plafond_credit=100000, actif=1
        )
        enregistrer_entree(self.p1, 20, self.admin)
        enregistrer_entree(self.p2, 10, self.admin)
        # 2 stylos + 1 cahier = 5 000, remise 100, total 4 900.
        self.vente, _ = valider_vente(
            utilisateur=self.vendeur, client_id=self.keita.pk, mode="comptant",
            remise=100, lignes=[(self.p1.pk, 2), (self.p2.pk, 1)],
        )

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

    def url_facture(self, vente=None):
        return reverse("facture_vente", args=[(vente or self.vente).pk])

    def url_ticket(self, vente=None):
        return reverse("ticket_vente", args=[(vente or self.vente).pk])

    # ================= CONTENU =================
    def test_facture_a4(self):
        self.connecter("manager")
        reponse = self.client.get(self.url_facture())
        self.assertEqual(reponse.status_code, 200)
        for texte in (
            "LogiStock SA", "FACTURE", self.vente.reference, "Keita",
            "Stylo", "Cahier", "Au comptant", "Vendeur", "Imprimer",
            "size: A4", "@media print",
            fcfa(1500), fcfa(2000), fcfa(100), fcfa(4900),
            timezone.localtime(self.vente.date_vente).strftime("%d/%m/%Y"),
        ):
            self.assertContains(reponse, texte)
        self.assertEqual(reponse.context["sous_total"], 5000)

    def test_ticket_80mm(self):
        self.connecter("manager")
        reponse = self.client.get(self.url_ticket())
        self.assertEqual(reponse.status_code, 200)
        for texte in (
            "LogiStock SA", "Ticket", self.vente.reference, "Keita", "Stylo",
            "Imprimer", "80mm", "@media print", fcfa(4900),
        ):
            self.assertContains(reponse, texte)

    def test_mode_a_credit(self):
        credit, _ = valider_vente(
            utilisateur=self.vendeur, client_id=self.keita.pk, mode="credit",
            remise=0, lignes=[(self.p1.pk, 1)],
        )
        self.connecter("manager")
        reponse = self.client.get(self.url_facture(credit))
        self.assertContains(reponse, "À crédit")

    def test_prix_du_moment_sur_la_facture(self):
        Produit.objects.filter(pk=self.p1.pk).update(prix_vente=9999)
        self.connecter("manager")
        reponse = self.client.get(self.url_facture())
        self.assertContains(reponse, fcfa(1500))
        self.assertNotContains(reponse, fcfa(9999))

    # ================= UNE VENTE ANNULÉE NE S'IMPRIME PAS =================
    def test_vente_annulee_non_imprimable(self):
        annuler_vente(vente_id=self.vente.pk, utilisateur=self.admin, motif="Erreur")
        self.connecter("administrateur")
        detail = reverse("detail_vente", args=[self.vente.pk])
        for url in (self.url_facture(), self.url_ticket()):
            reponse = self.client.get(url)
            self.assertRedirects(reponse, detail, fetch_redirect_response=False)
        reponse = self.client.get(self.url_facture(), follow=True)
        self.assertContains(reponse, "ne peut pas être imprimée")
        self.assertNotContains(reponse, "FACTURE")

    def test_boutons_dans_le_detail(self):
        self.connecter("manager")
        detail = reverse("detail_vente", args=[self.vente.pk])
        reponse = self.client.get(detail)
        self.assertContains(reponse, self.url_facture())
        self.assertContains(reponse, self.url_ticket())
        annuler_vente(vente_id=self.vente.pk, utilisateur=self.admin, motif="Erreur")
        reponse = self.client.get(detail)
        self.assertNotContains(reponse, self.url_facture())
        self.assertNotContains(reponse, self.url_ticket())

    # ================= DROITS =================
    def test_droits(self):
        self.connecter("gestionnaire_stock")
        self.assertEqual(self.client.get(self.url_facture()).status_code, 403)
        self.assertEqual(self.client.get(self.url_ticket()).status_code, 403)
        for role in ("administrateur", "gestionnaire_ventes", "manager"):
            self.connecter(role)
            self.assertEqual(self.client.get(self.url_facture()).status_code, 200)
            self.assertEqual(self.client.get(self.url_ticket()).status_code, 200)

    def test_vente_inexistante_et_non_connecte(self):
        self.connecter("administrateur")
        reponse = self.client.get(reverse("facture_vente", args=[99999]))
        self.assertEqual(reponse.status_code, 404)
        self.client.logout()
        reponse = self.client.get(self.url_facture())
        self.assertEqual(reponse.status_code, 302)
        self.assertTrue(reponse.url.startswith(reverse("connexion")))