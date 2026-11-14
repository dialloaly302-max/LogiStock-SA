from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse

from catalogue.models import Categorie, Produit
from comptes.models import Utilisateur

from .models import Stock
from .services import (
    StockError,
    enregistrer_entree,
    enregistrer_inventaire,
    enregistrer_mouvement,
    produits_avec_stock,
    valeur_stock_total,
)


class StockTests(TestCase):
    def setUp(self):
        self.categorie = Categorie.objects.create(nom_categorie="Papeterie")
        self.produit = self.creer_produit("P001", "Stylo", 100)
        self.admin = self.creer_utilisateur("administrateur")

    # ---------- outils ----------
    def creer_produit(self, code, designation, prix_achat):
        return Produit.objects.create(
            code=code, designation=designation, prix_achat=prix_achat,
            prix_vente=prix_achat * 2, seuil_minimal=15, categorie=self.categorie,
        )

    def creer_utilisateur(self, role):
        return Utilisateur.objects.create(
            nom="Essai", identifiant=role,
            password=make_password("x"), role=role,
        )

    def connecter(self, role):
        user = (
            Utilisateur.objects.filter(identifiant=role).first()
            or self.creer_utilisateur(role)
        )
        self.client.force_login(user)
        return user

    def entree(self, quantite, produit=None):
        return enregistrer_entree(produit or self.produit, quantite, self.admin)

    def sortie(self, quantite):
        return enregistrer_mouvement(
            self.produit, "sortie", quantite, self.admin, "Vente"
        )

    # ---------- 1. ENTRÉE ----------
    def test_entree_cree_un_mouvement(self):
        mouvement, valeur = self.entree(20)
        self.assertEqual(mouvement.type_mouvement, "entree")
        self.assertEqual(mouvement.quantite, 20)
        self.assertEqual(mouvement.quantite_restante, 20)
        self.assertEqual(mouvement.utilisateur, self.admin)
        self.assertEqual(mouvement.motif, "Approvisionnement")
        self.assertIsNotNone(mouvement.date_mouvement)
        self.assertEqual(valeur, 20 * 100)   # quantité x prix d'achat

    def test_entree_quantite_zero_ou_negative_refusee(self):
        for quantite in (0, -3):
            with self.assertRaises(StockError):
                self.entree(quantite)
        self.assertEqual(Stock.objects.count(), 0)

    # ---------- 2. STOCK CALCULÉ ----------
    def test_stock_calcule_entrees_moins_sorties(self):
        self.entree(20)
        self.sortie(6)
        self.assertEqual(self.produit.stock_actuel(), 14)
        calcule = produits_avec_stock().get(pk=self.produit.pk)
        self.assertEqual(calcule.stock, 14)

    def test_quantite_restante_suit_les_mouvements(self):
        self.entree(10)
        self.entree(5)
        self.sortie(4)
        restantes = list(
            Stock.objects.order_by("id_stock")
            .values_list("quantite_restante", flat=True)
        )
        self.assertEqual(restantes, [10, 15, 11])

    def test_sortie_superieure_au_stock_refusee(self):
        self.entree(5)
        with self.assertRaises(StockError):
            self.sortie(6)
        self.assertEqual(self.produit.stock_actuel(), 5)

    def test_valeur_totale_du_stock(self):
        autre = self.creer_produit("C001", "Cahier", 500)
        self.assertEqual(valeur_stock_total(), 0)
        self.entree(10)                  # 10 x 100 = 1 000
        self.entree(2, produit=autre)    # 2 x 500 = 1 000
        self.assertEqual(valeur_stock_total(), 2000)

    # ---------- 3. INVENTAIRE ----------
    def test_inventaire_ecart_positif(self):
        self.entree(10)
        mouvement, ecart = enregistrer_inventaire(self.produit, 13, self.admin)
        self.assertEqual(ecart, 3)
        self.assertEqual(mouvement.type_mouvement, "entree")
        self.assertEqual(mouvement.quantite, 3)
        self.assertEqual(mouvement.motif, "Inventaire")
        self.assertEqual(self.produit.stock_actuel(), 13)

    def test_inventaire_ecart_negatif(self):
        self.entree(10)
        mouvement, ecart = enregistrer_inventaire(self.produit, 7, self.admin)
        self.assertEqual(ecart, -3)
        self.assertEqual(mouvement.type_mouvement, "sortie")
        self.assertEqual(mouvement.quantite, 3)
        self.assertEqual(mouvement.quantite_restante, 7)
        self.assertEqual(mouvement.motif, "Inventaire")
        self.assertEqual(self.produit.stock_actuel(), 7)

    def test_inventaire_sans_ecart_ne_cree_rien(self):
        self.entree(10)
        mouvement, ecart = enregistrer_inventaire(self.produit, 10, self.admin)
        self.assertIsNone(mouvement)
        self.assertEqual(ecart, 0)
        self.assertEqual(Stock.objects.count(), 1)

    def test_inventaire_quantite_negative_refusee(self):
        self.entree(10)
        with self.assertRaises(StockError):
            enregistrer_inventaire(self.produit, -1, self.admin)
        self.assertEqual(Stock.objects.count(), 1)

    def test_inventaire_ne_modifie_ni_supprime_rien(self):
        self.entree(10)
        premier = Stock.objects.get()
        enregistrer_inventaire(self.produit, 4, self.admin)
        premier.refresh_from_db()
        self.assertEqual(
            (premier.type_mouvement, premier.quantite, premier.quantite_restante),
            ("entree", 10, 10),
        )
        self.assertEqual(Stock.objects.count(), 2)

    # ---------- PAGES ----------
    def test_entree_via_la_page(self):
        self.connecter("administrateur")
        reponse = self.client.post(
            reverse("entree_stock"),
            {"produit": self.produit.pk, "quantite": 20},
            follow=True,
        )
        self.assertContains(reponse, "Entrée enregistrée")
        self.assertEqual(self.produit.stock_actuel(), 20)
        self.assertEqual(Stock.objects.count(), 1)

    def test_entree_quantite_zero_via_la_page(self):
        self.connecter("administrateur")
        reponse = self.client.post(
            reverse("entree_stock"), {"produit": self.produit.pk, "quantite": 0}
        )
        self.assertContains(reponse, "doit être supérieure à 0")
        self.assertEqual(Stock.objects.count(), 0)

    def test_inventaire_via_la_page(self):
        self.connecter("administrateur")
        self.entree(10)
        reponse = self.client.post(
            reverse("inventaire_stock"),
            {"produit": self.produit.pk, "quantite_comptee": 13},
            follow=True,
        )
        self.assertContains(reponse, "écart de 3")
        self.assertEqual(self.produit.stock_actuel(), 13)
        self.assertEqual(Stock.objects.order_by("id_stock").last().motif, "Inventaire")

    # ---------- DROITS ----------
    def test_gestionnaire_stock_peut_faire_une_entree(self):
        self.connecter("gestionnaire_stock")
        self.assertEqual(self.client.get(reverse("entree_stock")).status_code, 200)
        self.assertEqual(self.client.get(reverse("inventaire_stock")).status_code, 200)

    def test_manager_consulte_sans_gerer(self):
        self.connecter("manager")
        self.assertEqual(self.client.get(reverse("liste_stock")).status_code, 200)
        self.assertEqual(self.client.get(reverse("entree_stock")).status_code, 403)
        self.assertEqual(self.client.get(reverse("inventaire_stock")).status_code, 403)
        reponse = self.client.post(
            reverse("entree_stock"), {"produit": self.produit.pk, "quantite": 5}
        )
        self.assertEqual(reponse.status_code, 403)
        self.assertEqual(Stock.objects.count(), 0)

    def test_gestionnaire_ventes_refuse(self):
        self.connecter("gestionnaire_ventes")
        self.assertEqual(self.client.get(reverse("liste_stock")).status_code, 403)
        self.assertEqual(self.client.get(reverse("notifications_stock")).status_code, 403)

    # ---------- LISTE, RECHERCHE, NOTIFICATIONS ----------
    def test_liste_stock_critique_en_rouge(self):
        self.connecter("administrateur")
        self.entree(5)   # 5 <= seuil 15 : critique
        reponse = self.client.get(reverse("liste_stock"))
        self.assertEqual(reponse.context["nb_critiques"], 1)
        self.assertContains(reponse, "table-danger")
        self.entree(100)   # 105 > 15 : normal
        reponse = self.client.get(reverse("liste_stock"))
        self.assertEqual(reponse.context["nb_critiques"], 0)
        self.assertNotContains(reponse, "table-danger")

    def test_recherche_dans_la_liste_du_stock(self):
        self.connecter("administrateur")
        self.creer_produit("C001", "Cahier", 500)
        url = reverse("liste_stock")
        nb = lambda r: r.context["page"].paginator.count
        self.assertEqual(nb(self.client.get(url)), 2)
        self.assertEqual(nb(self.client.get(url, {"q": "cahier"})), 1)
        self.assertEqual(nb(self.client.get(url, {"q": "p001"})), 1)
        self.assertEqual(nb(self.client.get(url, {"q": "zzz"})), 0)

    def test_notifications_et_historique(self):
        self.connecter("gestionnaire_stock")
        self.entree(20)
        self.sortie(6)
        reponse = self.client.get(reverse("notifications_stock"))
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(len(list(reponse.context["dernieres_entrees"])), 1)
        self.assertEqual(len(list(reponse.context["dernieres_sorties"])), 1)
        self.assertContains(reponse, "Stylo")
        reponse = self.client.get(reverse("notifications_stock"), {"type": "sortie"})
        self.assertEqual(reponse.context["page"].paginator.count, 1)