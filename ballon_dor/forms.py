from django import forms
from .models import Player, Vote
from .utils import get_active_year
from django_countries.fields import CountryField


class VoteForm(forms.ModelForm):
    voter_country = CountryField(blank_label="").formfield(required=False)

    class Meta:
        model = Vote
        fields = [
            "player_1st",
            "player_2nd",
            "player_3rd",
            "voter_name",
            "voter_country",
            "email",
        ]

    def __init__(self, *args, year=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        if year is None:
            year = get_active_year()  # helper
        allowed_qs = Player.objects.filter(candidate__year=year).order_by("name")
        for field in ["player_1st", "player_2nd", "player_3rd"]:
            self.fields[field].queryset = allowed_qs
            self.fields[field].label = field.replace("_", " ").capitalize()

        # to Update all the labels to be more user-friendly
        self.fields["player_1st"].label = "1st Place"
        self.fields["player_2nd"].label = "2nd Place"
        self.fields["player_3rd"].label = "3rd Place"

        # to add (optional) to the labels
        self.fields["voter_name"].label = "Your Name (optional)"
        self.fields["voter_country"].label = "Your Country (optional)"
        self.fields["email"].label = "Your Email"

        # remove the empty choice (dotted lines):
        self.fields["player_1st"].empty_label = ""
        self.fields["player_2nd"].empty_label = ""
        self.fields["player_3rd"].empty_label = ""

        # CUSTOM ERROR MESSAGES:
        self.fields["player_1st"].error_messages = {
            "required": "Please select your 1st place player."
        }
        self.fields["player_2nd"].error_messages = {
            "required": "Please select your 2nd place player."
        }
        self.fields["player_3rd"].error_messages = {
            "required": "Please select your 3rd place player."
        }

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
