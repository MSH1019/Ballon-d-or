from django import forms
from .models import Player, Vote


class VoteForm(forms.ModelForm):
    class Meta:
        model = Vote
        fields = [
            "player_1st",
            "player_2nd",
            "player_3rd",
            "voter_name",
            "voter_country",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: make dropdowns prettier or add classes for Select2
        for field in ["player_1st", "player_2nd", "player_3rd"]:
            self.fields[field].queryset = Player.objects.all().order_by("name")

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("player_1st")
        p2 = cleaned_data.get("player_2nd")
        p3 = cleaned_data.get("player_3rd")

        if p1 == p2 or p1 == p3 or p2 == p3:
            raise forms.ValidationError(
                "Each player must be unique in your top 3 picks."
            )

        return cleaned_data
