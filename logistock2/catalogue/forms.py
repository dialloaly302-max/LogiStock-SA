from django import forms

from .models import Categorie, Produit


def habiller(formulaire):
    """Donne l'aspect Bootstrap à tous les champs."""
    for champ in formulaire.fields.values():
        if isinstance(champ.widget, forms.Select):
            champ.widget.attrs["class"] = "form-select"
        else:
            champ.widget.attrs["class"] = "form-control"


class CategorieForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ["nom_categorie"]
        labels = {"nom_categorie": "Nom de la catégorie"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        habiller(self)

    def clean_nom_categorie(self):
        nom = self.cleaned_data["nom_categorie"].strip()
        doublons = Categorie.objects.filter(nom_categorie__iexact=nom)
        if self.instance.pk:
            doublons = doublons.exclude(pk=self.instance.pk)
        if doublons.exists():
            raise forms.ValidationError("Cette catégorie existe déjà.")
        return nom


class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = [
            "code", "designation", "categorie", "unite",
            "prix_achat", "prix_vente", "seuil_minimal",
        ]
        labels = {
            "code": "Code du produit",
            "designation": "Désignation",
            "categorie": "Catégorie",
            "unite": "Unité (ex. pièce, carton)",
            "prix_achat": "Prix d'achat (FCFA)",
            "prix_vente": "Prix de vente (FCFA)",
            "seuil_minimal": "Seuil minimal de stock",
        }

    def __init__(self, *args, peut_modifier_prix=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categorie"].queryset = Categorie.objects.order_by("nom_categorie")
        self.fields["categorie"].empty_label = "Choisir une catégorie"
        habiller(self)

        if not peut_modifier_prix:
            # Champ en lecture seule : Django ignore ce que le navigateur envoie
            # et garde la valeur d'origine (vérifié côté serveur).
            self.fields["prix_vente"].disabled = True
            if self.instance.pk:
                self.fields["prix_vente"].help_text = (
                    "Seul l'administrateur peut modifier le prix de vente."
                )
            else:
                self.initial["prix_vente"] = 0
                self.fields["prix_vente"].help_text = (
                    "Le prix de vente est fixé à 0 : l'administrateur le renseignera."
                )

    def clean_code(self):
        code = self.cleaned_data["code"].strip()
        doublons = Produit.objects.filter(code__iexact=code)
        if self.instance.pk:
            doublons = doublons.exclude(pk=self.instance.pk)
        if doublons.exists():
            raise forms.ValidationError("Ce code existe déjà. Choisissez un autre code.")
        return code