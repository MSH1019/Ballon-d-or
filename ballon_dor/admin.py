from django.contrib import admin
from .models import Player, Vote, BallonDorResult, Club, NationalTeam, Candidate


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("name", "country")
    search_fields = ("name", "country")


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
    list_display = (
        "player",
        "year",
        "club",
        "goals",
        "assists",
        "appearances",
        "avg_match_rating",
    )
    list_filter = ("year", "club")
    search_fields = ("player__name", "slug")
    prepopulated_fields = {"slug": ("player",)}

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": ("player", "year", "club", "slug", "image"),
                "classes": ("wide",),
            },
        ),
        (
            "Season Statistics",
            {
                "fields": ("appearances", "goals", "assists", "avg_match_rating"),
                "classes": ("wide",),
            },
        ),
        (
            "Additional Information",
            {
                "fields": ("trophies_won", "why_contender"),
                "classes": ("collapse",),
            },
        ),
    )

    # Show calculated stats in admin
    readonly_fields = []

    def get_readonly_fields(self, request, obj=None):
        # You could add calculated fields here if needed
        return self.readonly_fields
