from django.db import models


class Stock(models.Model):
    id_stock = models.AutoField(primary_key=True)
    date_mouvement = models.DateTimeField()
    type_mouvement = models.CharField(max_length=10)
    quantite = models.IntegerField()
    quantite_restante = models.IntegerField()
    motif = models.CharField(max_length=150, blank=True, null=True)
    produit = models.ForeignKey(
        "catalogue.Produit", models.DO_NOTHING, db_column="id_produit",
        related_name="mouvements",
    )
    utilisateur = models.ForeignKey(
        "comptes.Utilisateur", models.DO_NOTHING, db_column="id_utilisateur"
    )
    vente = models.ForeignKey(
        "ventes.Vente", models.DO_NOTHING, db_column="id_vente",
        blank=True, null=True,
    )

    class Meta:
        managed = False
        db_table = "stock"