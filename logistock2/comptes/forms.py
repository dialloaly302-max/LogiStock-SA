from django import forms
from django.contrib.auth.password_validation import validate_password

from .models import Utilisateur

ROLES = [
    ("administrateur", "Administrateur"),
    ("manager", "Manager"),
    ("gestionnaire_ventes", "Gestionnaire des ventes"),
    ("gestionnaire_stock", "Gestionnaire de stock"),
]


class UtilisateurForm(forms.ModelForm):
    role = forms.ChoiceField(choices=ROLES)
    password1 = forms.CharField(
        label="Mot de passe", widget=forms.PasswordInput, required=False
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput,
        required=False,
    )

    class Meta:
        model = Utilisateur
        fields = ["nom", "prenom", "identifiant", "telephone", "adresse", "role"]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aspect Bootstrap pour tous les champs
        for champ in self.fields.values():
            if isinstance(champ.widget, forms.Select):
                champ.widget.attrs["class"] = "form-select"
            else:
                champ.widget.attrs["class"] = "form-control"
        # Libellés clairs, avec accents
        etiquettes = {
            "nom": "Nom",
            "prenom": "Prénom",
            "identifiant": "Identifiant",
            "telephone": "Téléphone",
            "adresse": "Adresse",
            "role": "Rôle",
        }
        for nom, texte in etiquettes.items():
            self.fields[nom].label = texte
        # Aide sous le mot de passe
        if self.instance.pk:
            self.fields["password1"].help_text = (
                "Laissez vide pour garder le mot de passe actuel."
            )
        else:
            self.fields["password1"].help_text = (
                "Au moins 8 caractères, avec des lettres et des chiffres."
            )


    def clean(self):
        data = super().clean()
        p1 = data.get("password1")
        p2 = data.get("password2")

        # Création : le mot de passe est obligatoire
        if self.instance.pk is None and not p1:
            self.add_error("password1", "Le mot de passe est obligatoire.")

        # Si un mot de passe est tapé : les deux doivent être identiques et solides
        if p1 or p2:
            if p1 != p2:
                self.add_error("password2", "Les deux mots de passe sont différents.")
            else:
                try:
                    validate_password(p1, self.instance)
                except forms.ValidationError as erreur:
                    self.add_error("password1", erreur)
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        p1 = self.cleaned_data.get("password1")
        if p1:
            user.set_password(p1)  # Django hache le mot de passe
        if commit:
            user.save()
        return user