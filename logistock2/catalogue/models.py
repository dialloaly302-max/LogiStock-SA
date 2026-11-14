from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, Sum

TYPE_ENTREE = "entree"
TYPE_SORTIE = "sortie"


class Categorie(models.Model):
    id_categorie = models.AutoField(primary_key=True)
    nom_categorie = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = "categorie"
        ordering = ["nom_categorie"]

    def __str__(self):
        return self.nom_categorie

    def nb_produits(self):
        return self.produits.count()


class Produit(models.Model):
    id_produit = models.AutoField(primary_key=True)
    code = models.CharField(unique=True, max_length=30)
    designation = models.CharField(max_length=150)
    unite = models.CharField(max_length=20, blank=True, null=True)
    prix_achat = models.IntegerField(validators=[MinValueValidator(0)])
    prix_vente = models.IntegerField(validators=[MinValueValidator(0)])
    seuil_minimal = models.IntegerField(
        default=15, validators=[MinValueValidator(0)]
    )
    categorie = models.ForeignKey(
        Categorie, models.DO_NOTHING, db_column="id_categorie",
        related_name="produits",
    )

    class Meta:
        managed = False
        db_table = "produit"
        ordering = ["designation"]

    def __str__(self):
        return f"{self.code} - {self.designation}"

    def stock_actuel(self):
        r = self.mouvements.aggregate(
            e=Sum("quantite", filter=Q(type_mouvement=TYPE_ENTREE)),
            s=Sum("quantite", filter=Q(type_mouvement=TYPE_SORTIE)),
        )
        return (r["e"] or 0) - (r["s"] or 0)

    def est_vendu(self):
        """Vrai si le produit figure dans au moins une vente."""
        from ventes.models import Contenir

        return Contenir.objects.filter(produit=self).exists()

    def a_des_mouvements(self):
        """Vrai si le produit a déjà un mouvement de stock."""
        return self.mouvements.exists()