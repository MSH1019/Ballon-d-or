from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from cloudinary.models import CloudinaryField


class Player(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=50, blank=True)
    profile_pic = CloudinaryField("image", folder="players/", blank=True)

    def __str__(self):
        return self.name


class Club(models.Model):
    name = models.CharField(max_length=100)
    logo = CloudinaryField("image", folder="logos/", blank=True)

    def __str__(self):
        return self.name


class NationalTeam(models.Model):
    name = models.CharField(max_length=100)
    flag = CloudinaryField("image", folder="flags/", blank=True)

    def __str__(self):
        return self.name


class Candidate(models.Model):
    POSITION_CHOICES = [
        ("FWD", "Forward"),
        ("CAM", "Attacking Midfielder"),
        ("MID", "Midfielder"),
        ("DEF", "Defender"),
    ]

    # Basic Information
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    image = CloudinaryField("image", folder="ballondor_2025/", blank=True)
    club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True)
    slug = models.SlugField(max_length=100, blank=True)

    # Essential Stats
    goals = models.PositiveIntegerField(default=0, help_text="Goals scored this season")
    assists = models.PositiveIntegerField(default=0, help_text="Assists this season")
    appearances = models.PositiveIntegerField(
        default=0, help_text="Games played this season"
    )
    avg_match_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        help_text="Average match rating (0.0-10.0)",
    )

    # Position decides which stat cards the profile page shows
    position = models.CharField(
        max_length=3,
        choices=POSITION_CHOICES,
        default="FWD",
        help_text="Controls which stats show on the profile page",
    )

    # Position-specific stats (leave at 0 when they do not apply)
    chances_created = models.PositiveIntegerField(
        default=0, help_text="Midfielders: chances created this season"
    )
    tackles_interceptions = models.PositiveIntegerField(
        default=0,
        help_text="Midfielders/defenders: tackles + interceptions combined",
    )
    clean_sheets = models.PositiveIntegerField(
        default=0, help_text="Defenders: clean sheets this season"
    )

    expected_goals = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=0,
        help_text="Attackers/attacking mids: expected goals (xG) this season",
    )

    # Optional highlight shown under "Show more stats"
    signature_label = models.CharField(
        max_length=60,
        blank=True,
        help_text="e.g. World Cup Golden Ball (optional, needs a value too)",
    )
    signature_value = models.CharField(
        max_length=60, blank=True, help_text="e.g. Winner (optional)"
    )

    # Trophies & Recognition
    trophies_won = models.TextField(
        blank=True,
        help_text="Trophies won, ONE PER LINE (e.g. Champions League, Premier League)",
    )
    awards = models.TextField(
        blank=True,
        help_text="Individual awards, ONE PER LINE (e.g. World Cup Golden Ball, Premier League Player of the Season)",
    )

    # Optional: Why they deserve it (brief)
    why_contender = models.TextField(
        blank=True, help_text="Brief explanation of why they deserve the Ballon d'Or"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["year", "slug"], name="unique_candidate_slug_per_year"
            ),
            models.UniqueConstraint(
                fields=["year", "player"], name="unique_candidate_player_per_year"
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.player.name)
            self.slug = base_slug

            # Handle duplicate slugs within the same year
            counter = 1
            while (
                Candidate.objects.filter(year=self.year, slug=self.slug)
                .exclude(pk=self.pk)
                .exists()
            ):
                self.slug = f"{base_slug}-{counter}"
                counter += 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.player.name} ({self.year})"

    # Helper properties
    @property
    def goal_contribution(self):
        """Total goals + assists"""
        return self.goals + self.assists

    @property
    def goals_per_game(self):
        """Goals per appearance"""
        if self.appearances > 0:
            return round(self.goals / self.appearances, 2)
        return 0.0

    @property
    def assists_per_game(self):
        """Assists per appearance"""
        if self.appearances > 0:
            return round(self.assists / self.appearances, 2)
        return 0.0

    @property
    def base_stats(self):
        """Stat cards that are always visible, chosen by position."""
        appearances = {"value": self.appearances, "label": "Appearances"}
        rating = {
            "value": self.avg_match_rating,
            "label": "Avg Rating",
            "highlight": True,
        }

        if self.position == "MID":
            middle = [
                {"value": self.chances_created, "label": "Chances Created"},
                {
                    "value": self.tackles_interceptions,
                    "label": "Tackles + Interceptions",
                },
            ]
        elif self.position == "DEF":
            middle = [
                {"value": self.clean_sheets, "label": "Clean Sheets"},
                {
                    "value": self.tackles_interceptions,
                    "label": "Tackles + Interceptions",
                },
            ]
        else:  # FWD and CAM lead with goals and assists
            middle = [
                {
                    "value": self.goals,
                    "label": "Goals",
                    "extra": f"{self.goals_per_game}/game",
                },
                {
                    "value": self.assists,
                    "label": "Assists",
                    "extra": f"{self.assists_per_game}/game",
                },
            ]

        return [appearances] + middle + [rating]

    @property
    def extra_stats(self):
        """Stat cards hidden behind the 'Show more stats' toggle.

        Optional stats (chances created, xG, tackles...) are skipped when they
        are 0, so older candidates without that data don't show empty cards.
        """
        cards = []

        def add(value, label, **kwargs):
            if value:
                cards.append({"value": value, "label": label, **kwargs})

        if self.position in ("FWD", "CAM"):
            cards.append(
                {
                    "value": self.goal_contribution,
                    "label": "G+A",
                    "extra": "Total contribution",
                    "highlight": True,
                }
            )
            add(self.chances_created, "Chances Created")
            add(self.expected_goals, "Expected Goals (xG)")
            if self.position == "CAM":
                add(self.tackles_interceptions, "Tackles + Interceptions")
        else:
            # Midfielders and defenders: attacking numbers are the secondary stats
            cards.append({"value": self.goals, "label": "Goals"})
            cards.append({"value": self.assists, "label": "Assists"})

        if self.signature_label and self.signature_value:
            cards.append(
                {
                    "value": self.signature_value,
                    "label": self.signature_label,
                    "highlight": True,
                    "text": True,
                }
            )

        return cards

    @staticmethod
    def _lines(text):
        return [line.strip() for line in (text or "").splitlines() if line.strip()]

    @property
    def trophy_list(self):
        return self._lines(self.trophies_won)

    @property
    def award_list(self):
        return self._lines(self.awards)


class BallonDorResult(models.Model):
    RANK_CHOICES = [
        ("1", "First"),
        ("2", "Second"),
        ("3", "Third"),
    ]

    year = models.PositiveIntegerField()
    rank = models.CharField(max_length=2, choices=RANK_CHOICES, default="")
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    club_at_award = models.ForeignKey(Club, on_delete=models.CASCADE)
    nationality_at_award = models.ForeignKey(NationalTeam, on_delete=models.CASCADE)
    points = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["year", "rank"], name="unique_rank_per_year"
            ),
            models.UniqueConstraint(
                fields=["year", "player"], name="unique_player_per_year"
            ),
        ]

    def __str__(self):
        return f"{self.player.name} - {self.year} - Rank {self.rank}"


class Vote(models.Model):
    player_1st = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="first_votes"
    )
    player_2nd = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="second_votes"
    )
    player_3rd = models.ForeignKey(
        Player, on_delete=models.CASCADE, related_name="third_votes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    voter_country = models.CharField(max_length=2, blank=True)
    year = models.PositiveIntegerField()
    email = models.EmailField(blank=True)
    is_verified = models.BooleanField(default=False)
    token = models.CharField(max_length=36, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["year", "email"], name="unique_email_per_year"
            )
        ]

    def __str__(self):
        return f"Vote: 1st-{self.player_1st.name}, 2nd-{self.player_2nd.name}, 3rd-{self.player_3rd.name}"
