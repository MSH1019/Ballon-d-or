from django.contrib import admin
from .models import Player, Vote, BallonDorResult, Club, NationalTeam, Candidate


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "club")
    search_fields = ("name", "country", "club")


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("voter_name", "voter_country", "created_at", "ip_address")
    list_filter = ("voter_country", "created_at")


@admin.register(BallonDorResult)
class BallonDorResultAdmin(admin.ModelAdmin):
    list_display = (
        "year",
        "rank",
        "player",
        "club_at_award",
        "nationality_at_award",
        "points",
    )
    search_fields = (
        "player__name",
        "club_at_award__name",
        "nationality_at_award__name",
    )
    list_filter = ("year", "club_at_award", "nationality_at_award")


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(NationalTeam)
class NationalTeamAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("player", "year")
    list_filter = ("year",)
    search_fields = ("player__name",)
