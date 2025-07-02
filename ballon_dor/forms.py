from django import forms
from .models import Player, Vote


class VoteForm(forms.ModelForm):
    CANDIDATE_NAMES_2025 = [
        "Ousmane Dembélé",
        "Lamine Yamal",
        "Raphinha",
        "Mohamed Salah",
        "Kylian Mbappé",
        "Vitinha",
        "Nuno Mendes",
        "Désiré Doué",
        "Khvicha Kvaratskhelia",
        "Achraf Hakimi",
        "Pedri",
        "Harry Kane",
        "Robert Lewandowski",
        "Gianluigi Donnarumma",
        "João Neves",
        "Viktor Gyökeres",
        "Vinícius Júnior",
        "Jude Bellingham",
        "Marquinhos",
        "Declan Rice",
        "Florian Wirtz",
        "Erling Haaland",
        "Rodri",
        "Jamal Musiala",
        "Lautaro Martínez",
        "Alessandro Bastoni",
        "Alisson Becker",
        "Virgil van Dijk",
        "Pau Cubarsí",
        "Willian Pacho",
    ]

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
        for field in ["player_1st", "player_2nd", "player_3rd"]:
            self.fields[field].queryset = Player.objects.filter(
                name__in=self.CANDIDATE_NAMES_2025
            ).order_by("name")

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
