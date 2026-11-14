from django import forms

from catalogue.forms import habiller

from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["nom", "prenom", "telephone", "adresse", "plafond_credit"]
        labels = {
            "nom": "Nom",
            "prenom": "Prénom",
            "telephone": "Téléphone",
            "adresse": "Adresse",
            "plafond_credit": "Plafond de crédit (FCFA)",
        }
        help_texts = {
            "plafond_credit": (
                "Montant maximum que le client peut devoir. "
                "Mettez 0 si le client n'a pas droit au crédit."
            ),
        }
        error_messages = {
            "nom": {"required": "Le nom est obligatoire."},
            "plafond_credit": {
                "required": "Indiquez le plafond (0 si pas de crédit).",
                "invalid": "Entrez un nombre entier, sans espace ni lettre.",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        habiller(self)

    def clean_nom(self):
        return self.cleaned_data["nom"].strip()


class PaiementForm(forms.Form):
    montant = forms.IntegerField(
        label="Montant payé (FCFA)",
        min_value=1,
        error_messages={
            "required": "Indiquez le montant payé.",
            "min_value": "Le montant doit être supérieur à 0.",
            "invalid": "Entrez un nombre entier, sans espace ni lettre.",
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        habiller(self)