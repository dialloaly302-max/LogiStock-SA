from datetime import timedelta
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
from .services import VenteError, valider_vente


class VenteTests(TestCase):
    def setUp(self):
        self.categorie = Categorie.objects.create(nom_categorie="Papeterie")
        self.p1 = self.creer_produit("P001", "Stylo", 1500)
        self.p2 = self.creer_produit("P002", "Cahier", 2000)
        self.admin = self.creer_utilisateur("administrateur")
        self.vendeur = self.creer_utilisateur("gestionnaire_ventes")
        self.keita = Client.objects.create(nom="Keita", plafond_credit=5000, actif=1)
        enregistrer_entree(self.p1, 20, self.admin)   # stock P1 = 20
        enregistrer_entree(self.p2, 10, self.admin)   # stock P2 = 10

    # ---------- outils ----------
    def creer_produit(self, code, designation, prix_vente):
        return Produit.objects.create(
            code=code, designation=designation, prix_achat=prix_vente // 2,
            prix_vente=prix_vente, seuil_minimal=5, categorie=self.categorie,
        )

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

    def vendre(self, lignes, mode="comptant", remise=0, utilisateur=None,
               client=None, autoriser=False):
        return valider_vente(
            utilisateur=utilisateur or self.vendeur,
            client_id=(client or self.keita).pk,
            mode=mode, remise=remise, lignes=lignes,
            autoriser_depassement=autoriser,
        )

    def etat(self):
        """(ventes, lignes, mouvements) : pour vérifier que RIEN n'a changé."""
        return (Vente.objects.count(), Contenir.objects.count(), Stock.objects.count())

    def refuse(self, texte, **options):
        """La vente doit être refusée, avec ce message, sans rien enregistrer."""
        avant = self.etat()
        with self.assertRaises(VenteError) as contexte:
            self.vendre(**options)
        self.assertIn(texte, str(contexte.exception))
        self.assertEqual(self.etat(), avant)

    def vieille_vente(self, jours, montant=1000):
        return Vente.objects.create(
            reference="V-0001",
            date_vente=timezone.now() - timedelta(days=jours),
            mode_paiement="credit", remise=0, montant_total=montant,
            statut="validee", client=self.keita, utilisateur=self.vendeur,
        )

    def paiement(self, montant):
        return Paiement.objects.create(
            date_paiement=timezone.now(), montant=montant,
            client=self.keita, utilisateur=self.vendeur,
        )

    def donnees_vente(self, **autres):
        donnees = {
            "client": self.keita.pk, "mode": "comptant", "remise": "0",
            "produit": [self.p1.pk, self.p2.pk], "quantite": [2, 1],
        }
        donnees.update(autres)
        return donnees

    # ================= 1. CAS NORMAL =================
    def test_cas_normal(self):
        vente, alertes = self.vendre([(self.p1.pk, 2), (self.p2.pk, 1)])
        self.assertEqual(vente.reference, "V-0001")
        self.assertEqual(vente.statut, "validee")
        self.assertEqual(vente.remise, 0)
        self.assertEqual(vente.montant_total, 2 * 1500 + 2000)
        lignes = {l.produit_id: l for l in Contenir.objects.filter(vente=vente)}
        self.assertEqual(len(lignes), 2)
        self.assertEqual(lignes[self.p1.pk].quantite, 2)
        self.assertEqual(lignes[self.p1.pk].prix_unitaire, 1500)
        self.assertEqual(lignes[self.p2.pk].prix_unitaire, 2000)
        mouvements = Stock.objects.filter(vente=vente)
        self.assertEqual(mouvements.count(), 2)
        m1 = mouvements.get(produit=self.p1)
        self.assertEqual(
            (m1.type_mouvement, m1.quantite, m1.quantite_restante, m1.motif),
            ("sortie", 2, 18, "Vente V-0001"),
        )
        self.assertEqual(m1.utilisateur, self.vendeur)
        self.assertEqual(self.p1.stock_actuel(), 18)
        self.assertEqual(self.p2.stock_actuel(), 9)
        self.assertEqual(alertes, [])

    def test_references_se_suivent(self):
        premiere, _ = self.vendre([(self.p1.pk, 1)])
        seconde, _ = self.vendre([(self.p1.pk, 1)])
        self.assertEqual((premiere.reference, seconde.reference), ("V-0001", "V-0002"))

    def test_prix_du_moment_conserve(self):
        vente, _ = self.vendre([(self.p1.pk, 2)])
        Produit.objects.filter(pk=self.p1.pk).update(prix_vente=9999)
        self.assertEqual(Contenir.objects.get(vente=vente).prix_unitaire, 1500)
        self.assertEqual(vente.montant_total, 3000)

    # ================= 2. STOCK INSUFFISANT =================
    def test_stock_insuffisant(self):
        self.refuse("Stock insuffisant", lignes=[(self.p1.pk, 21)])
        self.assertEqual(self.p1.stock_actuel(), 20)

    def test_stock_insuffisant_sur_une_ligne_annule_tout(self):
        self.refuse("Stock insuffisant", lignes=[(self.p1.pk, 2), (self.p2.pk, 11)])
        self.assertEqual(self.p1.stock_actuel(), 20)
        self.assertEqual(self.p2.stock_actuel(), 10)

    # ================= TOUT OU RIEN =================
    def test_tout_ou_rien_si_une_etape_echoue(self):
        appels = []

        def mouvement_qui_echoue(*args, **kwargs):
            appels.append(1)
            if len(appels) == 2:        # la 2e sortie de stock « tombe en panne »
                raise StockError("Panne simulée")
            return vrai_mouvement(*args, **kwargs)

        avant = self.etat()
        with mock.patch(
            "ventes.services.enregistrer_mouvement", side_effect=mouvement_qui_echoue
        ):
            with self.assertRaises(VenteError):
                self.vendre([(self.p1.pk, 2), (self.p2.pk, 1)])
        self.assertEqual(self.etat(), avant)     # ni vente, ni lignes, ni sorties
        self.assertEqual(self.p1.stock_actuel(), 20)
        self.assertEqual(self.p2.stock_actuel(), 10)

    # ================= 3. REMISE TROP GRANDE =================
    def test_remise_trop_grande_gestionnaire_ventes(self):
        # Sous-total 3 000 : maximum 10 % = 300
        self.refuse("Remise refusée", lignes=[(self.p1.pk, 2)], remise=301)
        vente, _ = self.vendre([(self.p1.pk, 2)], remise=300)
        self.assertEqual(vente.remise, 300)
        self.assertEqual(vente.montant_total, 2700)

    def test_remise_administrateur_sans_limite(self):
        vente, _ = self.vendre([(self.p1.pk, 2)], remise=1500, utilisateur=self.admin)
        self.assertEqual(vente.montant_total, 1500)

    def test_remise_invalide(self):
        tout = [(self.p1.pk, 2)]
        self.refuse("ne peut pas dépasser le sous-total", lignes=tout,
                    remise=3001, utilisateur=self.admin)
        self.refuse("négative", lignes=tout, remise=-1)
        self.refuse("nombre entier", lignes=tout, remise="abc")

    # ================= 4. PLAFOND DÉPASSÉ =================
    def test_plafond_depasse(self):
        # 4 x 1 500 = 6 000 > plafond 5 000
        self.refuse("Crédit refusé", lignes=[(self.p1.pk, 4)], mode="credit")

    def test_plafond_tient_compte_du_solde_et_des_paiements(self):
        self.vendre([(self.p1.pk, 2)], mode="credit")                 # 3 000 : accepté
        self.refuse("Crédit refusé", lignes=[(self.p1.pk, 2)], mode="credit")
        self.paiement(2000)                                           # solde = 1 000
        self.vendre([(self.p1.pk, 2)], mode="credit")                 # 4 000 : accepté
        self.assertEqual(self.keita.solde(), 4000)

    def test_comptant_ignore_le_plafond(self):
        vente, _ = self.vendre([(self.p1.pk, 4)], mode="comptant")
        self.assertEqual(vente.montant_total, 6000)

    def test_administrateur_autorise_le_depassement(self):
        tout = [(self.p1.pk, 4)]
        # Sans la case : refusé, même pour l'administrateur
        self.refuse("Crédit refusé", lignes=tout, mode="credit", utilisateur=self.admin)
        # La case n'a AUCUN effet pour le gestionnaire des ventes
        self.refuse("Crédit refusé", lignes=tout, mode="credit", autoriser=True)
        # Administrateur + case : accepté
        vente, _ = self.vendre(tout, mode="credit", utilisateur=self.admin, autoriser=True)
        self.assertEqual(vente.montant_total, 6000)
        self.assertEqual(self.keita.solde(), 6000)

    # ================= 5. CLIENT EN RETARD =================
    def test_client_en_retard(self):
        self.vieille_vente(40)                    # 1 000 non réglés depuis 40 jours
        self.assertTrue(self.keita.est_en_retard())
        # Le plafond n'est pas dépassé (1 000 + 1 500 < 5 000) : c'est le retard qui refuse
        self.refuse("en retard", lignes=[(self.p1.pk, 1)], mode="credit")

    def test_client_en_retard_administrateur_autorise(self):
        self.vieille_vente(40)
        vente, _ = self.vendre(
            [(self.p1.pk, 1)], mode="credit", utilisateur=self.admin, autoriser=True
        )
        self.assertEqual(vente.montant_total, 1500)

    def test_client_en_retard_peut_acheter_comptant(self):
        self.vieille_vente(40)
        vente, _ = self.vendre([(self.p1.pk, 1)], mode="comptant")
        self.assertEqual(vente.montant_total, 1500)

    def test_pas_de_retard_si_vente_recente(self):
        self.vieille_vente(10)
        vente, _ = self.vendre([(self.p1.pk, 1)], mode="credit")
        self.assertEqual(vente.montant_total, 1500)

    def test_pas_de_retard_si_vente_reglee(self):
        self.vieille_vente(40, montant=1000)
        self.paiement(1000)
        self.assertFalse(self.keita.est_en_retard())
        vente, _ = self.vendre([(self.p1.pk, 1)], mode="credit")
        self.assertEqual(vente.montant_total, 1500)

    # ================= ALERTE DE STOCK BAS =================
    def test_alerte_stock_bas(self):
        _, alertes = self.vendre([(self.p1.pk, 14)])      # reste 6 > seuil 5
        self.assertEqual(alertes, [])
        _, alertes = self.vendre([(self.p1.pk, 1)])       # reste 5 <= seuil 5
        self.assertEqual(len(alertes), 1)
        self.assertEqual(alertes[0]["produit"].pk, self.p1.pk)
        self.assertEqual(alertes[0]["restante"], 5)

    # ================= AUTRES RÈGLES =================
    def test_produit_en_double_additionne(self):
        vente, _ = self.vendre([(self.p1.pk, 2), (self.p1.pk, 3)])
        self.assertEqual(Contenir.objects.get(vente=vente).quantite, 5)
        self.assertEqual(Stock.objects.filter(vente=vente).count(), 1)
        self.assertEqual(vente.montant_total, 7500)

    def test_lignes_invalides(self):
        self.refuse("au moins un produit", lignes=[])
        self.refuse("au moins un produit", lignes=[("", "")])
        self.refuse("supérieure à 0", lignes=[(self.p1.pk, 0)])
        self.refuse("supérieure à 0", lignes=[(self.p1.pk, -2)])
        self.refuse("quantité entière", lignes=[(self.p1.pk, "")])
        self.refuse("quantité entière", lignes=[("", 2)])

    def test_client_archive_refuse(self):
        self.keita.archiver()
        self.refuse("archivé", lignes=[(self.p1.pk, 1)])

    def test_mode_invalide_et_client_inconnu(self):
        self.refuse("mode de paiement", lignes=[(self.p1.pk, 1)], mode="autre")
        avant = self.etat()
        with self.assertRaises(VenteError):
            valider_vente(
                utilisateur=self.vendeur, client_id="", mode="comptant",
                remise=0, lignes=[(self.p1.pk, 1)],
            )
        self.assertEqual(self.etat(), avant)

    # ================= PAGES =================
    def test_page_vente_normale(self):
        self.connecter("gestionnaire_ventes")
        reponse = self.client.post(
            reverse("nouvelle_vente"), self.donnees_vente(), follow=True
        )
        self.assertContains(reponse, "Vente V-0001 enregistrée")
        self.assertEqual(Vente.objects.count(), 1)
        self.assertEqual(self.p1.stock_actuel(), 18)

    def test_page_refus_garde_la_saisie(self):
        self.connecter("gestionnaire_ventes")
        reponse = self.client.post(
            reverse("nouvelle_vente"), self.donnees_vente(quantite=[99, 1])
        )
        self.assertContains(reponse, "Stock insuffisant")
        self.assertContains(reponse, '"quantite": "99"')
        self.assertEqual(Vente.objects.count(), 0)

    def test_page_alerte_orange(self):
        self.connecter("gestionnaire_ventes")
        reponse = self.client.post(
            reverse("nouvelle_vente"),
            self.donnees_vente(produit=[self.p1.pk], quantite=[15]),
            follow=True,
        )
        self.assertContains(reponse, "Stock bas")

    def test_page_case_autoriser_ignoree_pour_vendeur(self):
        url = reverse("nouvelle_vente")
        donnees = self.donnees_vente(
            mode="credit", produit=[self.p1.pk], quantite=[4], autoriser="on"
        )
        self.connecter("gestionnaire_ventes")
        reponse = self.client.post(url, donnees)
        self.assertContains(reponse, "Crédit refusé")
        self.assertEqual(Vente.objects.count(), 0)
        self.connecter("administrateur")
        reponse = self.client.post(url, donnees, follow=True)
        self.assertContains(reponse, "Vente V-0001 enregistrée")
        self.assertEqual(Vente.objects.count(), 1)

    def test_droits(self):
        self.connecter("manager")
        self.assertEqual(self.client.get(reverse("nouvelle_vente")).status_code, 403)
        reponse = self.client.post(reverse("nouvelle_vente"), self.donnees_vente())
        self.assertEqual(reponse.status_code, 403)
        self.assertEqual(Vente.objects.count(), 0)
        reponse = self.client.get(reverse("liste_ventes"))
        self.assertEqual(reponse.status_code, 200)
        self.assertNotContains(reponse, "+ Nouvelle vente")

        self.connecter("gestionnaire_stock")
        self.assertEqual(self.client.get(reverse("liste_ventes")).status_code, 403)

        for role in ("administrateur", "gestionnaire_ventes"):
            self.connecter(role)
            self.assertEqual(self.client.get(reverse("nouvelle_vente")).status_code, 200)

    def test_archive_absent_du_choix(self):
        self.keita.archiver()
        Client.objects.create(nom="Actif", plafond_credit=0, actif=1)
        self.connecter("gestionnaire_ventes")
        reponse = self.client.get(reverse("nouvelle_vente"))
        self.assertEqual([c.nom for c in reponse.context["clients"]], ["Actif"])
        self.assertNotContains(reponse, "Keita")

    def test_liste_et_detail(self):
        vente, _ = self.vendre([(self.p1.pk, 2)], remise=100)
        self.connecter("manager")
        liste = self.client.get(reverse("liste_ventes"))
        self.assertContains(liste, vente.reference)
        self.assertContains(liste, "Keita")
        detail = self.client.get(reverse("detail_vente", args=[vente.pk]))
        self.assertContains(detail, "Stylo")
        self.assertEqual(detail.context["sous_total"], 3000)