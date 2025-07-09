from django.db import models

# TODO: Add media field to the db
class Player(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=50, blank=True)
    # FIXME: Make a relationship with the club
    club = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class Candidate(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    # FIXME: Change this to DateField
    year = models.IntegerField()

    def __str__(self):
        return f"{self.player.name} ({self.year})"


class Club(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class NationalTeam(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class BallonDorResult(models.Model):
    RANK_CHOICES = [
        ("1", "First"),
        ("2", "Second"),
        ("3", "Third"),
    ]

    # FIXME: Change this to DateField
    year = models.IntegerField()
    rank = models.CharField(max_length=2, choices=RANK_CHOICES, default="")
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    club_at_award = models.ForeignKey(Club, on_delete=models.CASCADE)
    nationality_at_award = models.ForeignKey(NationalTeam, on_delete=models.CASCADE)
    points = models.IntegerField()

    # COMMENT: Rethink about this concept
    class Meta:
        unique_together = (("year", "rank"), ("year", "player"))

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
    voter_country = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    # FIXME: Change this to DateField
    year = models.IntegerField(default=2025)

    def __str__(self):
        return f"Vote: 1st-{self.player_1st.name}, 2nd-{self.player_2nd.name}, 3rd-{self.player_3rd.name}"
