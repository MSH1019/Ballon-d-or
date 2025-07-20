from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from ballon_dor.models import  Candidate, Vote

# NEW: Candidate Detail View (year-specific)
class CandidateDetailView(DetailView):
    model = Candidate
    template_name = "ballon_dor/candidate_detail.html"
    context_object_name = "candidate"

    def get_object(self):
        return get_object_or_404(
            Candidate, year=self.kwargs["year"], slug=self.kwargs["slug"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        candidate = self.get_object()
        player = candidate.player
        year = candidate.year

        # Get voting stats for this player in this year
        first_votes = Vote.objects.filter(
            player_1st=player, year=year, is_verified=True
        ).count()
        second_votes = Vote.objects.filter(
            player_2nd=player, year=year, is_verified=True
        ).count()
        third_votes = Vote.objects.filter(
            player_3rd=player, year=year, is_verified=True
        ).count()

        total_points = (first_votes * 5) + (second_votes * 3) + (third_votes * 1)

        # Calculate current ranking
        points_map = {
            "player_1st": 5,
            "player_2nd": 3,
            "player_3rd": 1,
        }
        tally = {}

        # Get all verified votes for this year
        verified_votes = Vote.objects.filter(year=year, is_verified=True)

        for vote in verified_votes:
            for field, points in points_map.items():
                vote_player = getattr(vote, field)
                tally[vote_player] = tally.get(vote_player, 0) + points

        # Sort and find current player's rank
        sorted_results = sorted(tally.items(), key=lambda x: x[1], reverse=True)

        current_rank = None
        for i, (ranked_player, points) in enumerate(sorted_results):
            if ranked_player.id == player.id:
                current_rank = i + 1
                break

        # If player hasn't received votes yet, they're not ranked
        if current_rank is None:
            current_rank = "Unranked"

        context["voting_stats"] = {
            "first_votes": first_votes,
            "second_votes": second_votes,
            "third_votes": third_votes,
            "total_points": total_points,
            "current_rank": current_rank,
        }

        # Get other candidates from same year for comparison
        context["other_candidates"] = (
            Candidate.objects.filter(year=year)
            .exclude(pk=candidate.pk)
            .select_related("player", "club")
            .order_by("?")[:5]  # Add random ordering!
        )

        return context
