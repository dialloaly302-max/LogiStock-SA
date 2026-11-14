from datetime import timedelta

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone

MODE_CREDIT = "credit"
STATUT_VALIDE = "validee"
JOURS_RETARD = 30


class ClientQuerySet(models.QuerySet):
    def actifs(self):
        """Les clients que l'on peut choisir pour une vente."""
        return self.filter(actif=1)


class Client(models.Model):
    id_client = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.CharField(max_length=150, blank=True, null=True)
    plafond_credit = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    actif = models.IntegerField(default=1)

    objects = ClientQuerySet.as_manager()

    class Meta:
        managed = False
        db_table = "client"

    def __str__(self):
        return f"{self.nom} {self.prenom or ''}".strip()

    # ---------- état du client ----------
    def est_actif(self):
        return self.actif == 1

    def archiver(self):
        """Archive le client (actif = 0). On ne supprime jamais."""
        self.actif = 0
        self.save(update_fields=["actif"])

    def reactiver(self):
        self.actif = 1
        self.save(update_fields=["actif"])

    # ---------- argent ----------
    def ventes_credit(self):
        return self.ventes.filter(
            mode_paiement=MODE_CREDIT, statut=STATUT_VALIDE
        )

    def total_paye(self):
        return self.paiements.aggregate(t=Sum("montant"))["t"] or 0

    def solde(self):
        du = self.ventes_credit().aggregate(t=Sum("montant_total"))["t"] or 0
        return du - self.total_paye()

    def vente_en_retard(self):
        """La plus ancienne vente à crédit pas réglée en entier,
        si elle date de plus de 30 jours. Sinon, None."""
        reste = self.total_paye()
        limite = timezone.now() - timedelta(days=JOURS_RETARD)
        for v in self.ventes_credit().order_by("date_vente"):
            if reste >= v.montant_total:
                reste -= v.montant_total
            else:
                return v if v.date_vente < limite else None
        return None

    def est_en_retard(self):
        return self.vente_en_retard() is not None

    def statut_paiement(self):
        """« debiteur » si le client doit de l'argent, sinon « bon_payeur »."""
        return "debiteur" if self.solde() > 0 else "bon_payeur"


class Paiement(models.Model):
    id_paiement = models.AutoField(primary_key=True)
    date_paiement = models.DateTimeField()
    montant = models.IntegerField()
    client = models.ForeignKey(
        Client, models.DO_NOTHING, db_column="id_client",
        related_name="paiements",
    )
    utilisateur = models.ForeignKey(
        "comptes.Utilisateur", models.DO_NOTHING, db_column="id_utilisateur"
    )

    class Meta:
        managed = False
        db_table = "paiement"