from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models


class Utilisateur(AbstractBaseUser):
    id_utilisateur = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, blank=True, null=True)
    identifiant = models.CharField(unique=True, max_length=50)
    password = models.CharField(max_length=255, db_column="mot_de_passe")
    telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.CharField(max_length=150, blank=True, null=True)
    role = models.CharField(max_length=30)
    is_active = models.BooleanField(db_column="actif", default=True)
    tentatives_echec = models.IntegerField(default=0)
    bloque_jusqua = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = "identifiant"
    REQUIRED_FIELDS = []

    class Meta:
        managed = False
        db_table = "utilisateur"

    def __str__(self):
        return self.identifiant