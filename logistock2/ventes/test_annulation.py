from unittest import mock

from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalogue.models import Categorie, Produit
from clients.models import Client, Paiement
from comptes.models import Utilisateur
from stock.models import Stock
from stock.services import StockError, enregistrer_entree
from stock.services import enregistrer_mouvement as vrai_mouvement

from .models import Contenir, Vente
from .services import VenteError, annuler_vente, valider_vente


class AnnulationTests(TestCase):
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
        self.keita = Client.objects.create(nom="Keita", plafond_credit=100000, actif=1)
        enregistrer_entree(self.p1, 20, self.admin)
        enregistrer_entree(self.p2, 10, self.admin)
        # Une vente de 2 stylos et 1 cahier : le stock devient 18 et 9.
        self.vente, _ = valider_vente(
            utilisateur=self.vendeur, client_id=self.keita.pk, mode="comptant",
            remise=0, lignes=[(self.p1.pk, 2), (self.p2.pk, 1)],
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

    def annuler(self, motif="Erreur de saisie", utilisateur=None, vente=None):
        return annuler_vente(
            vente_id=(vente or self.vente).pk,
            utilisateur=utilisateur or self.vendeur,
            motif=motif,
        )

    def etat(self):
        """(ventes, lignes, mouvements) : pour vérifier ce qui a changé."""
        return (Vente.objects.count(), Contenir.objects.count(), Stock.objects.count())

    # ================= LA RÈGLE D'ANNULATION =================
    def test_annulation_normale(self):
        self.annuler()
        self.vente.refresh_from_db()
        self.assertEqual(self.vente.statut, "annulee")
        self.assertEqual(self.vente.motif_annulation, "Erreur de saisie")
        self.assertIsNotNone(self.vente.date_annulation)
        self.assertEqual(self.vente.utilisateur_annulation, self.vendeur)
        self.assertEqual(self.p1.stock_actuel(), 20)
        self.assertEqual(self.p2.stock_actuel(), 10)

    def test_mouvements_de_correction(self):
        self.annuler()
        corrections = Stock.objects.filter(vente=self.vente, type_mouvement="entree")
        self.assertEqual(corrections.count(), 2)
        texte = f"Correction : annulation de {self.vente.reference}"
        for mouvement in corrections:
            self.assertEqual(mouvement.motif, texte)
            self.assertEqual(mouvement.utilisateur, self.vendeur)
        m1 = corrections.get(produit=self.p1)
        self.assertEqual((m1.quantite, m1.quantite_restante), (2, 20))
        m2 = corrections.get(produit=self.p2)
        self.assertEqual((m2.quantite, m2.quantite_restante), (1, 10))

    def test_motif_obligatoire(self):
        for motif in ("", "   ", None):
            avant = self.etat()
            with self.assertRaises(VenteError) as contexte:
                self.annuler(motif=motif)
            self.assertIn("obligatoire", str(contexte.exception))
            self.assertEqual(self.etat(), avant)
            self.vente.refresh_from_db()
            self.assertEqual(self.vente.statut, "validee")

    def test_deuxieme_annulation_refusee(self):
        self.annuler()
        avant = self.etat()
        with self.assertRaises(VenteError) as contexte:
            self.annuler()
        self.assertIn("déjà annulée", str(contexte.exception))
        self.assertEqual(self.etat(), avant)
        self.assertEqual(self.p1.stock_actuel(), 20)    # pas 22 !

    def test_rien_nest_supprime(self):
        ventes, lignes, mouvements = self.etat()
        self.annuler()
        apres = self.etat()
        self.assertEqual(apres[0], ventes)               # la vente existe toujours
        self.assertEqual(apres[1], lignes)               # ses lignes aussi
        self.assertEqual(apres[2], mouvements + 2)       # 2 corrections ajoutées
        sorties = Stock.objects.filter(vente=self.vente, type_mouvement="sortie")
        self.assertEqual(sorties.count(), 2)             # les sorties d'origine restent

    def test_annuler_une_vente_a_credit_corrige_le_solde(self):
        credit, _ = valider_vente(
            utilisateur=self.vendeur, client_id=self.keita.pk, mode="credit",
            remise=0, lignes=[(self.p1.pk, 2)],
        )
        self.assertEqual(self.keita.solde(), 3000)
        self.annuler(vente=credit, motif="Le client a renoncé", utilisateur=self.admin)
        self.assertEqual(self.keita.solde(), 0)

    def test_tout_ou_rien_si_une_correction_echoue(self):
        appels = []

        def mouvement_qui_echoue(*args, **kwargs):
            appels.append(1)
            if len(appels) == 2:          # la 2e correction « tombe en panne »
                raise StockError("Panne simulée")
            return vrai_mouvement(*args, **kwargs)

        avant = self.etat()
        with mock.patch(
            "ventes.services.enregistrer_mouvement", side_effect=mouvement_qui_echoue
        ):
            with self.assertRaises(VenteError):
                self.annuler()
        self.assertEqual(self.etat(), avant)     # aucune correction n'est restée
        self.vente.refresh_from_db()
        self.assertEqual(self.vente.statut, "validee")
        self.assertIsNone(self.vente.motif_annulation)
        self.assertEqual(self.p1.stock_actuel(), 18)
        self.assertEqual(self.p2.stock_actuel(), 9)

    def test_vente_inexistante(self):
        with self.assertRaises(VenteError):
            annuler_vente(vente_id=99999, utilisateur=self.vendeur, motif="Essai")

    # ================= LES PAGES =================
    def test_page_annulation_ouverte(self):
        self.connecter("gestionnaire_ventes")
        reponse = self.client.get(reverse("annuler_vente", args=[self.vente.pk]))
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, f"Annuler la vente {self.vente.reference}")

    def test_page_sans_motif(self):
        self.connecter("gestionnaire_ventes")
        reponse = self.client.post(
            reverse("annuler_vente", args=[self.vente.pk]), {"motif": ""}
        )
        self.assertContains(reponse, "est obligatoire")
        self.vente.refresh_from_db()
        self.assertEqual(self.vente.statut, "validee")

    def test_page_annulation_reussie(self):
        self.connecter("gestionnaire_ventes")
        reponse = self.client.post(
            reverse("annuler_vente", args=[self.vente.pk]),
            {"motif": "Erreur de saisie"},
            follow=True,
        )
        self.assertContains(reponse, "remis en stock")
        self.assertContains(reponse, "Annulée")
        self.vente.refresh_from_db()
        self.assertEqual(self.vente.statut, "annulee")
        self.assertEqual(self.p1.stock_actuel(), 20)

    def test_page_vente_deja_annulee(self):
        self.annuler()
        self.connecter("gestionnaire_ventes")
        avant = self.etat()
        url = reverse("annuler_vente", args=[self.vente.pk])
        reponse = self.client.get(url, follow=True)
        self.assertContains(reponse, "déjà annulée")
        self.client.post(url, {"motif": "Encore"})
        self.assertEqual(self.etat(), avant)

    def test_page_manager_refuse(self):
        self.connecter("manager")
        url = reverse("annuler_vente", args=[self.vente.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {"motif": "Essai"}).status_code, 403)
        self.vente.refresh_from_db()
        self.assertEqual(self.vente.statut, "validee")

    def test_bouton_annuler_selon_le_role(self):
        detail = reverse("detail_vente", args=[self.vente.pk])
        self.connecter("gestionnaire_ventes")
        self.assertContains(self.client.get(detail), "Annuler la vente")
        self.connecter("manager")
        self.assertNotContains(self.client.get(detail), "Annuler la vente")

    def test_page_avertissement_si_le_client_a_trop_paye(self):
        credit, _ = valider_vente(
            utilisateur=self.vendeur, client_id=self.keita.pk, mode="credit",
            remise=0, lignes=[(self.p1.pk, 2)],
        )
        Paiement.objects.create(
            date_paiement=timezone.now(), montant=3000,
            client=self.keita, utilisateur=self.vendeur,
        )
        self.connecter("administrateur")
        reponse = self.client.post(
            reverse("annuler_vente", args=[credit.pk]), {"motif": "Essai"}, follow=True
        )
        self.assertContains(reponse, "Cet argent lui revient")
        self.assertEqual(self.keita.solde(), -3000)