from django.db import models


class Vente(models.Model):
    id_vente = models.AutoField(primary_key=True)
    reference = models.CharField(unique=True, max_length=30)
    date_vente = models.DateTimeField()
    mode_paiement = models.CharField(max_length=10)
    remise = models.IntegerField()
    montant_total = models.IntegerField()
    statut = models.CharField(max_length=20)
    motif_annulation = models.CharField(max_length=255, blank=True, null=True)
    date_annulation = models.DateTimeField(blank=True, null=True)
    client = models.ForeignKey(
        "clients.Client", models.DO_NOTHING, db_column="id_client",
        related_name="ventes",
    )
    utilisateur = models.ForeignKey(
        "comptes.Utilisateur", models.DO_NOTHING, db_column="id_utilisateur",
        related_name="ventes_faites",
    )
    utilisateur_annulation = models.ForeignKey(
        "comptes.Utilisateur", models.DO_NOTHING,
        db_column="id_utilisateur_annulation",
        related_name="ventes_annulees", blank=True, null=True,
    )

    class Meta:
        managed = False
        db_table = "vente"

    def __str__(self):
        return self.reference


class Contenir(models.Model):
    pk = models.CompositePrimaryKey("vente", "produit")
    vente = models.ForeignKey(
        Vente, models.DO_NOTHING, db_column="id_vente", related_name="lignes"
    )
    produit = models.ForeignKey(
        "catalogue.Produit", models.DO_NOTHING, db_column="id_produit"
    )
    quantite = models.IntegerField()
    prix_unitaire = models.IntegerField()

    class Meta:
        managed = False
        db_table = "contenir"