from django import forms

from catalogue.forms import habiller


class AnnulationForm(forms.Form):
    motif = forms.CharField(
        label="Motif d'annulation",
        max_length=255,
        widget=forms.Textarea(attrs={"rows": 3}),
        error_messages={"required": "Le motif d'annulation est obligatoire."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        habiller(self)