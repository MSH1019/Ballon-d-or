from django.db import models


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
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    image = models.ImageField(upload_to="players/", blank=True)
    club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.player.name} ({self.year})"


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

    # COMMENT: Better way of implementing it in django
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
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    year = models.PositiveIntegerField()
    email = models.EmailField(blank=True)
    is_verified = models.BooleanField(default=False)
    token = models.CharField(max_length=36, blank=True)

    def __str__(self):
        return f"Vote: 1st-{self.player_1st.name}, 2nd-{self.player_2nd.name}, 3rd-{self.player_3rd.name}"
