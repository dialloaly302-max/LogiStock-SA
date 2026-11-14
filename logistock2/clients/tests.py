from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from catalogue.models import Categorie, Produit
from comptes.models import Utilisateur
from ventes.models import Contenir, Vente

from .forms import ClientForm
from .models import Client, Paiement


class ClientTests(TestCase):
    def setUp(self):
        self.numero = 0
        self.vendeur = self.creer_utilisateur("gestionnaire_ventes")
        self.keita = self.creer_client("Keita", "Choupii", plafond=200000)

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

    def creer_client(self, nom, prenom="", plafond=0, actif=1, telephone=None):
        return Client.objects.create(
            nom=nom, prenom=prenom or None, telephone=telephone,
            plafond_credit=plafond, actif=actif,
        )

    def vente(self, client, montant, jours=0, mode="credit", statut="validee"):
        self.numero += 1
        return Vente.objects.create(
            reference=f"V-{self.numero:04d}",
            date_vente=timezone.now() - timedelta(days=jours),
            mode_paiement=mode, remise=0, montant_total=montant,
            statut=statut, client=client, utilisateur=self.vendeur,
        )

    def paiement(self, client, montant, jours=0):
        return Paiement.objects.create(
            date_paiement=timezone.now() - timedelta(days=jours),
            montant=montant, client=client, utilisateur=self.vendeur,
        )

    def fiche(self, client):
        return self.client.get(reverse("fiche_client", args=[client.pk]))

    # ---------- FORMULAIRE ----------
    def test_formulaire_nom_obligatoire(self):
        for nom in ("", "   "):
            form = ClientForm({"nom": nom, "plafond_credit": 0})
            self.assertFalse(form.is_valid())
            self.assertIn("nom", form.errors)

    def test_formulaire_plafond_negatif_refuse(self):
        form = ClientForm({"nom": "Essai", "plafond_credit": -5})
        self.assertFalse(form.is_valid())
        self.assertIn("plafond_credit", form.errors)

    def test_formulaire_valide(self):
        form = ClientForm({"nom": "Essai", "plafond_credit": 5000})
        self.assertTrue(form.is_valid())

    # ---------- AJOUT ET MODIFICATION ----------
    def test_ajout_via_la_page(self):
        self.connecter("gestionnaire_ventes")
        reponse = self.client.post(
            reverse("creer_client"),
            {"nom": "Essai", "prenom": "Client", "telephone": "70000000",
             "adresse": "", "plafond_credit": 20000},
            follow=True,
        )
        self.assertContains(reponse, "ajouté avec succès")
        nouveau = Client.objects.get(nom="Essai")
        self.assertEqual(nouveau.actif, 1)
        self.assertEqual(nouveau.plafond_credit, 20000)

    def test_ajout_nom_vide_refuse(self):
        self.connecter("gestionnaire_ventes")
        reponse = self.client.post(
            reverse("creer_client"), {"nom": "", "plafond_credit": 1000}
        )
        self.assertContains(reponse, "Le nom est obligatoire")
        self.assertEqual(Client.objects.count(), 1)

    def test_modification_via_la_page(self):
        self.connecter("gestionnaire_ventes")
        reponse = self.client.post(
            reverse("modifier_client", args=[self.keita.pk]),
            {"nom": "Keita", "prenom": "Choupii", "plafond_credit": 300000},
            follow=True,
        )
        self.assertContains(reponse, "modifié avec succès")
        self.keita.refresh_from_db()
        self.assertEqual(self.keita.plafond_credit, 300000)

    def test_page_ajout_plafond_par_defaut_zero(self):
        self.connecter("gestionnaire_ventes")
        reponse = self.client.get(reverse("creer_client"))
        self.assertContains(reponse, 'value="0"')

    # ---------- ARCHIVAGE (JAMAIS DE SUPPRESSION) ----------
    def test_archivage_ne_supprime_rien(self):
        self.connecter("gestionnaire_ventes")
        self.vente(self.keita, 105000)
        self.paiement(self.keita, 50000)
        self.client.post(reverse("archiver_client", args=[self.keita.pk]))
        self.keita.refresh_from_db()
        self.assertEqual(self.keita.actif, 0)
        self.assertEqual(Client.objects.count(), 1)
        self.assertEqual(Vente.objects.count(), 1)
        self.assertEqual(Paiement.objects.count(), 1)

    def test_archive_absent_du_choix_des_clients_actifs(self):
        archive = self.creer_client("Ancien", actif=0)
        self.assertIn(self.keita, Client.objects.actifs())
        self.assertNotIn(archive, Client.objects.actifs())

    def test_archive_garde_son_historique_dans_la_fiche(self):
        self.connecter("gestionnaire_ventes")
        categorie = Categorie.objects.create(nom_categorie="Papeterie")
        produit = Produit.objects.create(
            code="P001", designation="Stylo", prix_achat=100,
            prix_vente=150, seuil_minimal=15, categorie=categorie,
        )
        vente = self.vente(self.keita, 1500)
        Contenir.objects.create(
            vente=vente, produit=produit, quantite=10, prix_unitaire=150
        )
        self.paiement(self.keita, 500)
        self.keita.archiver()
        reponse = self.fiche(self.keita)
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, vente.reference)
        self.assertContains(reponse, "10 × Stylo")
        self.assertContains(reponse, "Archivé")

    def test_archivage_client_avec_dette_garde_la_dette(self):
        self.connecter("gestionnaire_ventes")
        self.vente(self.keita, 105000)
        reponse = self.client.post(
            reverse("archiver_client", args=[self.keita.pk]), follow=True
        )
        self.assertContains(reponse, "il doit encore")
        self.keita.refresh_from_db()
        self.assertEqual(self.keita.solde(), 105000)

    def test_reactivation(self):
        self.keita.archiver()
        self.connecter("gestionnaire_ventes")
        self.client.post(reverse("reactiver_client", args=[self.keita.pk]))
        self.keita.refresh_from_db()
        self.assertEqual(self.keita.actif, 1)

    def test_archivage_par_get_refuse(self):
        self.connecter("gestionnaire_ventes")
        reponse = self.client.get(reverse("archiver_client", args=[self.keita.pk]))
        self.assertEqual(reponse.status_code, 405)
        self.keita.refresh_from_db()
        self.assertEqual(self.keita.actif, 1)

    def test_aucune_suppression_possible(self):
        with self.assertRaises(NoReverseMatch):
            reverse("supprimer_client", args=[self.keita.pk])

    # ---------- SOLDE ET BADGES ----------
    def test_solde_credit_valide_moins_paiements(self):
        self.vente(self.keita, 105000)
        self.vente(self.keita, 50000, statut="annulee")
        self.vente(self.keita, 30000, mode="comptant")
        self.paiement(self.keita, 50000)
        self.assertEqual(self.keita.solde(), 55000)

    def test_statut_debiteur_puis_bon_payeur(self):
        self.assertEqual(self.keita.statut_paiement(), "bon_payeur")
        self.vente(self.keita, 10000)
        self.assertEqual(self.keita.statut_paiement(), "debiteur")
        self.paiement(self.keita, 10000)
        self.assertEqual(self.keita.statut_paiement(), "bon_payeur")

    def test_credit_disponible(self):
        self.connecter("gestionnaire_ventes")
        self.vente(self.keita, 105000)
        self.paiement(self.keita, 50000)
        reponse = self.fiche(self.keita)
        self.assertEqual(reponse.context["solde"], 55000)
        self.assertEqual(reponse.context["credit_disponible"], 145000)

    def test_credit_disponible_ne_depasse_pas_le_plafond(self):
        self.connecter("gestionnaire_ventes")
        avance = self.creer_client("Avance", plafond=20000)
        self.paiement(avance, 5000)
        reponse = self.fiche(avance)
        self.assertEqual(reponse.context["solde"], -5000)
        self.assertEqual(reponse.context["credit_disponible"], 20000)

    def test_fiche_bon_payeur(self):
        self.connecter("gestionnaire_ventes")
        reponse = self.fiche(self.keita)
        self.assertContains(reponse, "Bon payeur")
        self.assertNotContains(reponse, "Débiteur")
        self.assertNotContains(reponse, "En retard")

    def test_liste_badges(self):
        self.connecter("gestionnaire_ventes")
        self.creer_client("Bon")
        self.vente(self.keita, 10000)
        reponse = self.client.get(reverse("liste_clients"))
        self.assertContains(reponse, "Débiteur")
        self.assertContains(reponse, "Bon payeur")
        self.assertNotContains(reponse, "En retard")

    # ---------- RETARD (PLUS DE 30 JOURS) ----------
    def test_en_retard_vente_ancienne_non_reglee(self):
        vente = self.vente(self.keita, 10000, jours=40)
        self.assertTrue(self.keita.est_en_retard())
        self.assertEqual(self.keita.vente_en_retard(), vente)

    def test_pas_en_retard_si_vente_recente(self):
        self.vente(self.keita, 10000, jours=10)
        self.assertFalse(self.keita.est_en_retard())

    def test_pas_en_retard_si_vente_reglee(self):
        self.vente(self.keita, 10000, jours=40)
        self.paiement(self.keita, 10000)
        self.assertFalse(self.keita.est_en_retard())

    def test_en_retard_si_paiement_partiel(self):
        self.vente(self.keita, 10000, jours=40)
        self.paiement(self.keita, 4000)
        self.assertTrue(self.keita.est_en_retard())

    def test_paiements_couvrent_les_plus_anciennes_ventes(self):
        # Une vente ancienne et une récente : 10 000 payés couvrent l'ancienne.
        self.vente(self.keita, 10000, jours=40)
        self.vente(self.keita, 10000, jours=5)
        self.paiement(self.keita, 10000)
        self.assertFalse(self.keita.est_en_retard())
        # Si le paiement ne couvre pas toute l'ancienne vente : en retard.
        autre = self.creer_client("Autre", plafond=100000)
        self.vente(autre, 10000, jours=40)
        self.vente(autre, 10000, jours=5)
        self.paiement(autre, 4000)
        self.assertTrue(autre.est_en_retard())

    def test_comptant_et_annulee_ignorees_pour_le_retard(self):
        self.vente(self.keita, 10000, jours=40, mode="comptant")
        self.vente(self.keita, 10000, jours=40, statut="annulee")
        self.assertFalse(self.keita.est_en_retard())
        self.assertEqual(self.keita.solde(), 0)

    def test_fiche_badge_en_retard(self):
        self.connecter("gestionnaire_ventes")
        self.vente(self.keita, 10000, jours=40)
        reponse = self.fiche(self.keita)
        self.assertContains(reponse, "En retard")
        self.assertContains(reponse, "Débiteur")
        self.assertEqual(reponse.context["jours_retard"], 40)

    # ---------- LISTE, RECHERCHE, FILTRES ----------
    def test_recherche_nom_prenom_telephone(self):
        self.connecter("gestionnaire_ventes")
        self.creer_client("Barry", "Fanta", telephone="76157724")
        url = reverse("liste_clients")
        nb = lambda r: r.context["page"].paginator.count
        self.assertEqual(nb(self.client.get(url)), 2)
        for mot in ("barry", "fanta", "76157724"):
            self.assertEqual(nb(self.client.get(url, {"q": mot})), 1)
        self.assertEqual(nb(self.client.get(url, {"q": "zzz"})), 0)

    def test_filtre_actifs_archives_tous(self):
        self.connecter("gestionnaire_ventes")
        self.creer_client("Ancien", actif=0)
        url = reverse("liste_clients")
        nb = lambda r: r.context["page"].paginator.count
        self.assertEqual(nb(self.client.get(url)), 1)
        self.assertEqual(nb(self.client.get(url, {"etat": "archives"})), 1)
        self.assertEqual(nb(self.client.get(url, {"etat": "tous"})), 2)

    # ---------- DROITS ----------
    def test_manager_lecture_seule(self):
        self.connecter("manager")
        reponse = self.client.get(reverse("liste_clients"))
        self.assertEqual(reponse.status_code, 200)
        self.assertNotContains(reponse, "+ Ajouter un client")
        self.assertNotContains(reponse, "Modifier")
        reponse = self.fiche(self.keita)
        self.assertEqual(reponse.status_code, 200)
        self.assertNotContains(reponse, "Archiver")
        self.assertNotContains(reponse, "Modifier")

    def test_manager_ne_peut_rien_modifier(self):
        self.connecter("manager")
        pk = self.keita.pk
        self.assertEqual(self.client.get(reverse("creer_client")).status_code, 403)
        self.assertEqual(
            self.client.get(reverse("modifier_client", args=[pk])).status_code, 403
        )
        reponse = self.client.post(
            reverse("creer_client"), {"nom": "X", "plafond_credit": 0}
        )
        self.assertEqual(reponse.status_code, 403)
        self.assertEqual(Client.objects.count(), 1)
        reponse = self.client.post(reverse("archiver_client", args=[pk]))
        self.assertEqual(reponse.status_code, 403)
        self.keita.refresh_from_db()
        self.assertEqual(self.keita.actif, 1)

    def test_gestionnaire_stock_refuse(self):
        self.connecter("gestionnaire_stock")
        self.assertEqual(self.client.get(reverse("liste_clients")).status_code, 403)
        self.assertEqual(self.fiche(self.keita).status_code, 403)

    def test_gestionnaire_ventes_et_administrateur_gerent(self):
        for role in ("gestionnaire_ventes", "administrateur"):
            self.connecter(role)
            self.assertEqual(self.client.get(reverse("creer_client")).status_code, 200)
            self.assertEqual(
                self.client.get(
                    reverse("modifier_client", args=[self.keita.pk])
                ).status_code,
                200,
            )