from django.db import transaction, models
from ballon_dor.models import Player, Club, NationalTeam, BallonDorResult
import pandas as pd

df = pd.read_csv(
    "/Users/mohamedsohail/Desktop/Personal/ballon_dor_project/ballon-d'or-top3.csv"
)
print(df.head())

with transaction.atomic():
    for _, row in df.iterrows():
        year = int(row["year"])
        rank = int(
            row["rank"]
            .replace("st", "")
            .replace("nd", "")
            .replace("rd", "")
            .replace("th", "")
        )
        player_name = row["player"].strip()
        club_name = row["team"].strip()

        points_raw = row["points"]
        if pd.isnull(points_raw):
            points = 0  # or choose what you want for missing points
        else:
            points = int(float(points_raw))

        player, _ = Player.objects.get_or_create(name=player_name)
        club, _ = Club.objects.get_or_create(name=club_name)
        nation, _ = NationalTeam.objects.get_or_create(name=player.country or "Unknown")

        existing = (
            BallonDorResult.objects.filter(year=year)
            .filter(models.Q(rank=rank) | models.Q(player=player))
            .first()
        )

        if existing:
            existing.rank = rank
            existing.player = player
            existing.club_at_award = club
            existing.nationality_at_award = nation
            existing.points = points
            existing.save()
            print(f"Updated: {player_name} {year} rank {rank}")
        else:
            BallonDorResult.objects.create(
                year=year,
                rank=rank,
                player=player,
                club_at_award=club,
                nationality_at_award=nation,
                points=points,
            )
            print(f"Created: {player_name} {year} rank {rank}")

print("✅ Import done successfully!")
