from datetime import date, datetime, timedelta
from io import BytesIO

from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from openpyxl import load_workbook

from catalogue.models import Categorie, Produit
from clients.models import Client, Paiement
from comptes.models import Utilisateur
from comptes.templatetags.logistock_filtres import fcfa
from stock.services import enregistrer_entree
from ventes.models import Contenir, Vente
from ventes.services import valider_vente

from .services import (
    chiffre_affaires,
    classement_produits,
    credits_a_recouvrer,
    donnees_tableau_de_bord,
    lire_periode,
    produits_critiques,
)

TYPE_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MARS = {"debut": "2026-03-01", "fin": "2026-03-31"}


def moment(annee, mois, jour, heure=12, minute=0, seconde=0):
    """Un instant précis, avec le fuseau horaire du projet."""
    return timezone.make_aware(datetime(annee, mois, jour, heure, minute, seconde))


class TableauDeBordTests(TestCase):
    def setUp(self):
        self.numero = 0
        self.categorie = Categorie.objects.create(nom_categorie="Papeterie")
        self.admin = self.creer_utilisateur("administrateur")
        self.vendeur = self.creer_utilisateur("gestionnaire_ventes")
        self.keita = Client.objects.create(nom="Keita", plafond_credit=1000000, actif=1)

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

    def produit(self, code, designation=None, prix=1000, stock=100, seuil=5):
        produit = Produit.objects.create(
            code=code, designation=designation or f"Produit {code}",
            prix_achat=prix // 2, prix_vente=prix, seuil_minimal=seuil,
            categorie=self.categorie,
        )
        if stock > 0:
            enregistrer_entree(produit, stock, self.admin)
        return produit

    def vente(self, quand, lignes, client=None, mode="comptant",
              statut="validee", remise=0):
        """Une vente à une date précise : lignes = [(produit, quantité), ...]."""
        self.numero += 1
        total = sum(q * p.prix_vente for p, q in lignes) - remise
        vente = Vente.objects.create(
            reference=f"V-{self.numero:04d}", date_vente=quand,
            mode_paiement=mode, remise=remise, montant_total=total,
            statut=statut, client=client or self.keita, utilisateur=self.vendeur,
        )
        for produit, quantite in lignes:
            Contenir.objects.create(
                vente=vente, produit=produit, quantite=quantite,
                prix_unitaire=produit.prix_vente,
            )
        return vente

    def paiement(self, client, montant):
        return Paiement.objects.create(
            date_paiement=timezone.now(), montant=montant,
            client=client, utilisateur=self.vendeur,
        )

    def jeu_mars(self):
        """6 produits vendus en mars 2026, plus des ventes qui ne doivent PAS compter."""
        p = {n: self.produit(f"P{n}") for n in range(1, 7)}
        self.vente(moment(2026, 3, 2), [(p[1], 6), (p[2], 4)], remise=500)
        self.vente(moment(2026, 3, 10), [(p[1], 4), (p[3], 5)])
        self.vente(moment(2026, 3, 31, 23, 59, 59), [(p[2], 3), (p[4], 3), (p[5], 2)])
        self.vente(moment(2026, 3, 15), [(p[6], 1)])
        # À exclure : une vente annulée, une vente juste avant, une juste après.
        self.vente(moment(2026, 3, 20), [(p[6], 50)], statut="annulee")
        self.vente(moment(2026, 2, 28, 23, 59, 59), [(p[6], 100)])
        self.vente(moment(2026, 4, 1, 0, 0, 0), [(p[6], 100)])
        return p

    # ================= LES 4 CARTES =================
    def test_cartes_ventes_du_jour_et_du_mois(self):
        p = self.produit("P1", prix=1500)
        self.vente(timezone.now(), [(p, 2)])                            # 3 000 : compte
        self.vente(timezone.now(), [(p, 9)], statut="annulee")          # annulée : ignorée
        self.vente(timezone.now() - timedelta(days=40), [(p, 4)])       # trop ancienne
        debut, fin, _ = lire_periode("", "")
        donnees = donnees_tableau_de_bord(debut, fin)
        self.assertEqual(donnees["jour"], {"total": 3000, "nombre": 1})
        self.assertEqual(donnees["mois"], {"total": 3000, "nombre": 1})
        self.assertEqual(donnees["periode"], {"total": 3000, "nombre": 1})

    def test_produits_critiques(self):
        self.produit("A", stock=5, seuil=5)     # égal au seuil : critique
        self.produit("B", stock=6, seuil=5)     # au-dessus du seuil : normal
        self.produit("C", stock=0, seuil=5)     # rupture : critique
        self.produit("D", stock=3, seuil=0)     # au-dessus du seuil 0 : normal
        self.assertEqual([p.code for p in produits_critiques()], ["C", "A"])
        self.assertEqual([int(p.stock) for p in produits_critiques()], [0, 5])
        # Une vente fait baisser le stock : B devient critique (6 - 4 = 2).
        b = Produit.objects.get(code="B")
        valider_vente(
            utilisateur=self.vendeur, client_id=self.keita.pk, mode="comptant",
            remise=0, lignes=[(b.pk, 4)],
        )
        self.assertEqual([p.code for p in produits_critiques()], ["C", "B", "A"])
        debut, fin, _ = lire_periode("", "")
        self.assertEqual(donnees_tableau_de_bord(debut, fin)["nb_critiques"], 3)

    def test_credits_a_recouvrer(self):
        p = self.produit("P1", prix=1000)
        maintenant = timezone.now()
        clients = {
            nom: Client.objects.create(nom=nom, plafond_credit=100000, actif=1)
            for nom in ("K1", "K2", "K3", "K4", "K5", "K6")
        }
        archive = Client.objects.create(nom="K7", plafond_credit=100000, actif=0)

        self.vente(maintenant, [(p, 10)], client=clients["K1"], mode="credit")
        self.paiement(clients["K1"], 3000)                       # doit 7 000
        self.vente(maintenant, [(p, 5)], client=clients["K2"], mode="credit")
        self.paiement(clients["K2"], 5000)                       # tout payé : 0
        self.vente(maintenant, [(p, 8)], client=clients["K3"], mode="credit",
                   statut="annulee")                             # annulée : 0
        self.vente(maintenant, [(p, 9)], client=clients["K4"])   # comptant : 0
        self.vente(maintenant, [(p, 2)], client=clients["K5"], mode="credit")
        self.paiement(clients["K5"], 2500)                       # a trop payé : pas une dette
        self.vente(maintenant, [(p, 3)], client=clients["K6"], mode="credit")  # doit 3 000
        self.vente(maintenant, [(p, 1)], client=archive, mode="credit")        # archivé : 1 000

        resultat = credits_a_recouvrer()
        self.assertEqual(resultat, {"total": 11000, "nombre": 3})
        # Même résultat que le calcul client par client (méthode solde()).
        dettes = [c.solde() for c in Client.objects.all() if c.solde() > 0]
        self.assertEqual(sum(dettes), 11000)
        self.assertEqual(len(dettes), 3)

    # ================= LA PÉRIODE =================
    def test_periode_les_deux_dates_sont_incluses(self):
        p = self.produit("P1", prix=1500)
        for quand in (moment(2026, 3, 1, 0, 0, 0), moment(2026, 3, 10),
                      moment(2026, 3, 31, 23, 59, 59)):
            self.vente(quand, [(p, 1)])                          # 3 ventes : comptent
        for quand in (moment(2026, 2, 28, 23, 59, 59), moment(2026, 4, 1, 0, 0, 0)):
            self.vente(quand, [(p, 1)])                          # 2 ventes : hors période
        resultat = chiffre_affaires(date(2026, 3, 1), date(2026, 3, 31))
        self.assertEqual(resultat, {"total": 4500, "nombre": 3})

    def test_periode_d_un_seul_jour(self):
        p = self.produit("P1", prix=1500)
        self.vente(moment(2026, 3, 5, 8), [(p, 1)])
        self.vente(moment(2026, 3, 5, 18), [(p, 2)])
        self.vente(moment(2026, 3, 6, 8), [(p, 5)])
        resultat = chiffre_affaires(date(2026, 3, 5), date(2026, 3, 5))
        self.assertEqual(resultat, {"total": 4500, "nombre": 2})

    def test_ventes_annulees_exclues(self):
        p = self.produit("P1", prix=1000)
        self.vente(moment(2026, 3, 5), [(p, 2)])
        self.vente(moment(2026, 3, 6), [(p, 7)], statut="annulee")
        debut, fin = date(2026, 3, 1), date(2026, 3, 31)
        self.assertEqual(chiffre_affaires(debut, fin), {"total": 2000, "nombre": 1})
        classement = classement_produits(debut, fin)
        self.assertEqual(len(classement), 1)
        self.assertEqual(classement[0]["quantite"], 2)

    def test_lire_periode_par_defaut(self):
        aujourdhui = timezone.localdate()
        resultat = lire_periode("", "")
        self.assertEqual(resultat, (aujourdhui.replace(day=1), aujourdhui, None))

    def test_lire_periode_valide_et_invalide(self):
        self.assertEqual(
            lire_periode("2026-03-01", "2026-03-31"),
            (date(2026, 3, 1), date(2026, 3, 31), None),
        )
        self.assertEqual(                                        # un seul jour : permis
            lire_periode("2026-03-05", "2026-03-05"),
            (date(2026, 3, 5), date(2026, 3, 5), None),
        )
        par_defaut = (timezone.localdate().replace(day=1), timezone.localdate())
        mauvaises = (
            ("abc", "2026-03-31"),
            ("2026-03-01", "31/03/2026"),
            ("2026-03-10", "2026-03-01"),                        # début après la fin
        )
        for debut_texte, fin_texte in mauvaises:
            debut, fin, erreur = lire_periode(debut_texte, fin_texte)
            self.assertEqual((debut, fin), par_defaut)
            self.assertIsNotNone(erreur)

    # ================= LE CLASSEMENT =================
    def test_classement_des_produits(self):
        self.jeu_mars()
        debut, fin = date(2026, 3, 1), date(2026, 3, 31)
        classement = classement_produits(debut, fin)
        self.assertEqual(
            [l["code"] for l in classement], ["P1", "P2", "P3", "P4", "P5", "P6"]
        )
        self.assertEqual([l["quantite"] for l in classement], [10, 7, 5, 3, 2, 1])
        self.assertEqual(
            [l["ca"] for l in classement], [10000, 7000, 5000, 3000, 2000, 1000]
        )
        self.assertEqual([l["nombre_ventes"] for l in classement], [2, 2, 1, 1, 1, 1])
        donnees = donnees_tableau_de_bord(debut, fin)
        self.assertEqual(
            [l["code"] for l in donnees["top5"]], ["P1", "P2", "P3", "P4", "P5"]
        )
        # Le chiffre d'affaires de la période compte les remises (28 000 - 500).
        self.assertEqual(donnees["periode"], {"total": 27500, "nombre": 4})

    # ================= LA PAGE =================
    def test_page_tableau_de_bord(self):
        self.jeu_mars()
        self.connecter("manager")
        reponse = self.client.get(reverse("tableau_bord"), MARS)
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse.context["periode"], {"total": 27500, "nombre": 4})
        self.assertEqual(
            reponse.context["graphique"]["labels"],
            ["Produit P1", "Produit P2", "Produit P3", "Produit P4", "Produit P5"],
        )
        self.assertEqual(reponse.context["graphique"]["quantites"], [10, 7, 5, 3, 2])
        self.assertEqual(reponse.context["debut_texte"], "2026-03-01")
        self.assertContains(reponse, '<canvas id="graphique-top5">')
        self.assertContains(reponse, fcfa(27500))
        self.assertContains(reponse, "Ventes du jour")
        self.assertContains(reponse, "Crédits à recouvrer")

    def test_page_sans_ventes(self):
        self.connecter("administrateur")
        reponse = self.client.get(reverse("tableau_bord"), MARS)
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Aucune vente validée sur cette période.")
        self.assertNotContains(reponse, "<canvas")

    def test_page_dates_invalides(self):
        self.connecter("manager")
        par_defaut = timezone.localdate().replace(day=1).isoformat()
        url = reverse("tableau_bord")
        reponse = self.client.get(url, {"debut": "abc", "fin": "2026-03-31"})
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Date invalide")
        self.assertEqual(reponse.context["debut_texte"], par_defaut)
        reponse = self.client.get(url, {"debut": "2026-03-10", "fin": "2026-03-01"})
        self.assertContains(reponse, "date de début doit être avant la date de fin")
        self.assertEqual(reponse.context["debut_texte"], par_defaut)

    def test_page_stock_critique_en_rouge(self):
        self.connecter("administrateur")
        url = reverse("tableau_bord")
        reponse = self.client.get(url)
        self.assertEqual(reponse.context["nb_critiques"], 0)
        self.assertNotContains(reponse, "table-danger")
        self.assertContains(reponse, "Aucun produit en stock critique")
        self.produit("RUP", stock=2, seuil=5)
        reponse = self.client.get(url)
        self.assertEqual(reponse.context["nb_critiques"], 1)
        self.assertContains(reponse, "table-danger")
        self.assertContains(reponse, "RUP")

    # ================= LES EXPORTS =================
    def test_export_excel(self):
        self.jeu_mars()
        self.produit("CRI", stock=1, seuil=5)
        self.connecter("administrateur")
        reponse = self.client.get(reverse("export_excel"), MARS)
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse["Content-Type"], TYPE_XLSX)
        self.assertIn("attachment", reponse["Content-Disposition"])
        self.assertIn("2026-03-01_2026-03-31.xlsx", reponse["Content-Disposition"])

        classeur = load_workbook(BytesIO(reponse.content))
        self.assertEqual(
            classeur.sheetnames, ["Résumé", "Produits vendus", "Stock critique"]
        )
        resume = classeur["Résumé"]
        self.assertEqual(resume["B10"].value, 27500)       # chiffre d'affaires de la période
        self.assertEqual(resume["B8"].value, 1)            # un produit en stock critique
        produits = classeur["Produits vendus"]
        self.assertEqual(produits["B2"].value, "P1")
        self.assertEqual(produits["D2"].value, 10)
        self.assertEqual(produits["C8"].value, "TOTAL")
        self.assertEqual(produits["D8"].value, 28)
        self.assertEqual(produits["F8"].value, 28000)
        critiques = classeur["Stock critique"]
        self.assertEqual(critiques["A2"].value, "CRI")
        self.assertEqual(critiques["D2"].value, 1)

    def test_export_excel_sans_donnees(self):
        self.connecter("manager")
        reponse = self.client.get(reverse("export_excel"), MARS)
        self.assertEqual(reponse.status_code, 200)
        classeur = load_workbook(BytesIO(reponse.content))
        self.assertEqual(classeur["Résumé"]["B10"].value, 0)
        self.assertIn("Aucune vente", classeur["Produits vendus"]["A2"].value)
        self.assertIn("Aucun produit", classeur["Stock critique"]["A2"].value)

    def test_export_pdf(self):
        self.jeu_mars()
        self.connecter("manager")
        reponse = self.client.get(reverse("export_pdf"), MARS)
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse["Content-Type"], "application/pdf")
        self.assertIn("attachment", reponse["Content-Disposition"])
        self.assertIn("2026-03-01_2026-03-31.pdf", reponse["Content-Disposition"])
        self.assertTrue(reponse.content.startswith(b"%PDF"))
        self.assertGreater(len(reponse.content), 1000)

    def test_export_pdf_sans_donnees(self):
        self.connecter("administrateur")
        reponse = self.client.get(reverse("export_pdf"), MARS)
        self.assertEqual(reponse.status_code, 200)
        self.assertTrue(reponse.content.startswith(b"%PDF"))

    def test_exports_avec_caracteres_speciaux(self):
        p = self.produit("SPE", designation="Thé <noir> & café 'extra'", prix=1000)
        self.produit("CRI", designation="Crème <forte> & douce", stock=1, seuil=5)
        self.vente(moment(2026, 3, 5), [(p, 2)])
        self.connecter("administrateur")
        for nom in ("export_pdf", "export_excel"):
            reponse = self.client.get(reverse(nom), MARS)
            self.assertEqual(reponse.status_code, 200)

    # ================= LES DROITS =================
    def test_droits(self):
        adresses = [
            reverse("tableau_bord"), reverse("export_excel"), reverse("export_pdf"),
        ]
        for role in ("gestionnaire_ventes", "gestionnaire_stock"):
            self.connecter(role)
            for adresse in adresses:
                self.assertEqual(
                    self.client.get(adresse).status_code, 403, (role, adresse)
                )
        for role in ("administrateur", "manager"):
            self.connecter(role)
            for adresse in adresses:
                self.assertEqual(
                    self.client.get(adresse).status_code, 200, (role, adresse)
                )
        self.client.logout()
        for adresse in adresses:
            reponse = self.client.get(adresse)
            self.assertEqual(reponse.status_code, 302)
            self.assertTrue(reponse.url.startswith(reverse("connexion")))

    def test_exports_refusent_les_envois_de_formulaire(self):
        self.connecter("administrateur")
        for nom in ("export_excel", "export_pdf"):
            self.assertEqual(self.client.post(reverse(nom)).status_code, 405)

    def test_menu_selon_le_role(self):
        lien = reverse("tableau_bord")
        self.connecter("manager")
        self.assertContains(self.client.get(reverse("accueil")), lien)
        self.connecter("gestionnaire_ventes")
        self.assertNotContains(self.client.get(reverse("accueil")), lien)