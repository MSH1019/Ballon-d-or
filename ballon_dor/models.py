from django.db import models


class Player(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=50, blank=True)
    club = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class BallonDorResult(models.Model):
    year = models.IntegerField()
    rank = models.IntegerField()  # 1, 2, 3, etc.
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    club_at_award = models.CharField(max_length=100, blank=True)
    nationality_at_award = models.CharField(max_length=100, blank=True)
    points = models.IntegerField()

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

    def __str__(self):
        return f"Vote: 1st-{self.player_1st.name}, 2nd-{self.player_2nd.name}, 3rd-{self.player_3rd.name}"
