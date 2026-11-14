from django import forms

from catalogue.forms import habiller
from catalogue.models import Produit

from .services import produits_avec_stock


class ProduitStockField(forms.ModelChoiceField):
    """Liste de produits qui montre aussi le stock actuel de chacun."""

    def label_from_instance(self, produit):
        return f"{produit.code} - {produit.designation} (stock : {produit.stock})"


class EntreeStockForm(forms.Form):
    produit = ProduitStockField(
        queryset=Produit.objects.none(),
        label="Produit",
        empty_label="Choisir un produit",
    )
    quantite = forms.IntegerField(
        label="Quantité reçue",
        min_value=1,
        error_messages={
            "min_value": "La quantité doit être supérieure à 0.",
            "invalid": "Entrez un nombre entier.",
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["produit"].queryset = produits_avec_stock()
        habiller(self)


class InventaireForm(forms.Form):
    produit = ProduitStockField(
        queryset=Produit.objects.none(),
        label="Produit",
        empty_label="Choisir un produit",
    )
    quantite_comptee = forms.IntegerField(
        label="Quantité comptée",
        min_value=0,
        error_messages={
            "min_value": "La quantité comptée ne peut pas être négative.",
            "invalid": "Entrez un nombre entier.",
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["produit"].queryset = produits_avec_stock()
        habiller(self)