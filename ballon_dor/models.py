from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator


class Player(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=50, blank=True)
    profile_pic = models.ImageField(upload_to="players/", blank=True)

    def __str__(self):
        return self.name


class Club(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to="logos/", blank=True)

    def __str__(self):
        return self.name


class NationalTeam(models.Model):
    name = models.CharField(max_length=100)
    flag = models.ImageField(upload_to="flags/", blank=True)

    def __str__(self):
        return self.name


class Candidate(models.Model):
    # Basic Information
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    image = models.ImageField(upload_to="candidate/", blank=True)
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

    # Trophies & Recognition
    trophies_won = models.TextField(
        blank=True,
        help_text="Major trophies won this season (e.g., Champions League, Premier League)",
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
    voter_name = models.CharField(max_length=100, blank=True)
    voter_country = models.CharField(max_length=2, blank=True)
    # TODO: remove the ip_address
    ip_address = models.GenericIPAddressField(blank=True, null=True)
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
