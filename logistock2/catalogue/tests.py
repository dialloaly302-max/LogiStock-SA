from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from clients.models import Client
from comptes.models import Utilisateur
from stock.models import Stock
from ventes.models import Contenir, Vente

from .models import Categorie, Produit


class CatalogueTests(TestCase):
    def setUp(self):
        self.categorie = Categorie.objects.create(nom_categorie="Papeterie")
        self.produit = Produit.objects.create(
            code="P001", designation="Stylo", prix_achat=100,
            prix_vente=150, seuil_minimal=15, categorie=self.categorie,
        )

    # ---------- outils ----------
    def connecter(self, role):
        user = Utilisateur.objects.create(
            nom="Essai", identifiant=role, password=make_password("x"), role=role
        )
        self.client.force_login(user)
        return user

    def donnees_produit(self, **autres):
        donnees = {
            "code": "P002", "designation": "Cahier",
            "categorie": self.categorie.pk, "unite": "piece",
            "prix_achat": 200, "prix_vente": 9999, "seuil_minimal": 15,
        }
        donnees.update(autres)
        return donnees

    def mouvement(self, user, type_mouvement, quantite):
        return Stock.objects.create(
            produit=self.produit, utilisateur=user,
            date_mouvement=timezone.now(), type_mouvement=type_mouvement,
            quantite=quantite, quantite_restante=quantite,
        )

    # ---------- droits ----------
    def test_manager_consulte_sans_creer(self):
        self.connecter("manager")
        reponse = self.client.get(reverse("liste_produits"))
        self.assertEqual(reponse.status_code, 200)
        self.assertNotContains(reponse, "+ Ajouter un produit")
        reponse = self.client.get(reverse("creer_produit"))
        self.assertEqual(reponse.status_code, 403)

    def test_gestionnaire_ventes_refuse(self):
        self.connecter("gestionnaire_ventes")
        reponse = self.client.get(reverse("liste_produits"))
        self.assertEqual(reponse.status_code, 403)

    # ---------- prix de vente réservé à l'administrateur ----------
    def test_stock_cree_produit_prix_vente_zero(self):
        self.connecter("gestionnaire_stock")
        self.client.post(reverse("creer_produit"), self.donnees_produit())
        produit = Produit.objects.get(code="P002")
        self.assertEqual(produit.prix_vente, 0)

    def test_stock_ne_modifie_pas_prix_vente(self):
        self.connecter("gestionnaire_stock")
        donnees = self.donnees_produit(
            code="P001", designation="Stylo bleu", prix_vente=1
        )
        self.client.post(reverse("modifier_produit", args=[self.produit.pk]), donnees)
        self.produit.refresh_from_db()
        self.assertEqual(self.produit.designation, "Stylo bleu")
        self.assertEqual(self.produit.prix_vente, 150)

    def test_admin_modifie_prix_vente(self):
        self.connecter("administrateur")
        donnees = self.donnees_produit(code="P001", prix_vente=500)
        self.client.post(reverse("modifier_produit", args=[self.produit.pk]), donnees)
        self.produit.refresh_from_db()
        self.assertEqual(self.produit.prix_vente, 500)

    # ---------- règles des produits ----------
    def test_code_unique(self):
        self.connecter("administrateur")
        reponse = self.client.post(
            reverse("creer_produit"), self.donnees_produit(code="P001")
        )
        self.assertContains(reponse, "Ce code existe déjà")
        self.assertEqual(Produit.objects.filter(code="P001").count(), 1)

    def test_prix_negatif_refuse(self):
        self.connecter("administrateur")
        self.client.post(reverse("creer_produit"), self.donnees_produit(prix_achat=-5))
        self.assertFalse(Produit.objects.filter(code="P002").exists())

    def test_seuil_par_defaut(self):
        self.connecter("administrateur")
        reponse = self.client.get(reverse("creer_produit"))
        self.assertContains(reponse, 'value="15"')

    # ---------- suppression des produits ----------
    def test_produit_vendu_non_supprimable(self):
        admin = self.connecter("administrateur")
        client = Client.objects.create(nom="Client", plafond_credit=0, actif=1)
        vente = Vente.objects.create(
            reference="V001", date_vente=timezone.now(), mode_paiement="comptant",
            remise=0, montant_total=150, statut="validee",
            client=client, utilisateur=admin,
        )
        Contenir.objects.create(
            vente=vente, produit=self.produit, quantite=1, prix_unitaire=150
        )
        reponse = self.client.post(
            reverse("supprimer_produit", args=[self.produit.pk]), follow=True
        )
        self.assertContains(reponse, "déjà été vendu")
        self.assertTrue(Produit.objects.filter(pk=self.produit.pk).exists())

    def test_produit_avec_mouvements_non_supprimable(self):
        admin = self.connecter("administrateur")
        self.mouvement(admin, "entree", 5)
        reponse = self.client.post(
            reverse("supprimer_produit", args=[self.produit.pk]), follow=True
        )
        self.assertContains(reponse, "mouvements de stock")
        self.assertTrue(Produit.objects.filter(pk=self.produit.pk).exists())

    def test_produit_libre_supprimable(self):
        self.connecter("gestionnaire_stock")
        self.client.post(reverse("supprimer_produit", args=[self.produit.pk]))
        self.assertFalse(Produit.objects.filter(pk=self.produit.pk).exists())

    def test_suppression_par_get_refusee(self):
        self.connecter("administrateur")
        reponse = self.client.get(reverse("supprimer_produit", args=[self.produit.pk]))
        self.assertEqual(reponse.status_code, 405)
        self.assertTrue(Produit.objects.filter(pk=self.produit.pk).exists())

    # ---------- stock actuel, recherche, filtre ----------
    def test_stock_actuel_calcule(self):
        admin = self.connecter("administrateur")
        self.mouvement(admin, "entree", 20)
        self.mouvement(admin, "sortie", 6)
        self.assertEqual(self.produit.stock_actuel(), 14)
        reponse = self.client.get(reverse("liste_produits"))
        self.assertEqual(list(reponse.context["page"])[0].stock, 14)

    def test_recherche_et_filtre(self):
        self.connecter("administrateur")
        autre = Categorie.objects.create(nom_categorie="Informatique")
        Produit.objects.create(
            code="C001", designation="Clavier", prix_achat=1000,
            prix_vente=1500, seuil_minimal=15, categorie=autre,
        )
        url = reverse("liste_produits")
        nb = lambda r: r.context["page"].paginator.count
        self.assertEqual(nb(self.client.get(url)), 2)
        self.assertEqual(nb(self.client.get(url, {"q": "stylo"})), 1)
        self.assertEqual(nb(self.client.get(url, {"q": "c001"})), 1)
        self.assertEqual(nb(self.client.get(url, {"categorie": autre.pk})), 1)
        self.assertEqual(nb(self.client.get(url, {"q": "zzz"})), 0)

    # ---------- catégories ----------
    def test_categorie_doublon_refuse(self):
        self.connecter("gestionnaire_stock")
        reponse = self.client.post(
            reverse("creer_categorie"), {"nom_categorie": "papeterie"}
        )
        self.assertContains(reponse, "Cette catégorie existe déjà")
        self.assertEqual(Categorie.objects.count(), 1)

    def test_categorie_avec_produits_non_supprimable(self):
        self.connecter("administrateur")
        reponse = self.client.post(
            reverse("supprimer_categorie", args=[self.categorie.pk]), follow=True
        )
        self.assertContains(reponse, "elle contient 1 produit")
        self.assertTrue(Categorie.objects.filter(pk=self.categorie.pk).exists())

    def test_categorie_vide_supprimable(self):
        self.connecter("administrateur")
        vide = Categorie.objects.create(nom_categorie="Vide")
        self.client.post(reverse("supprimer_categorie", args=[vide.pk]))
        self.assertFalse(Categorie.objects.filter(pk=vide.pk).exists())