from django.views.generic import TemplateView, ListView

from django.utils import timezone

from ballon_dor.models import BallonDorResult, Vote
from ballon_dor.utils import get_active_year, get_voting_deadline


class LiveResultsView(TemplateView):
    template_name = "ballon_dor/live_results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_year = get_active_year()
        deadline = get_voting_deadline(active_year)
        points_map = {
            "player_1st": 5,
            "player_2nd": 3,
            "player_3rd": 1,
        }
        tally = {}

        # Get all verified votes for this year
        verified_votes = Vote.objects.filter(year=active_year, is_verified=True)

        for vote in verified_votes:
            for field, points in points_map.items():
                player = getattr(vote, field)
                tally[player] = tally.get(player, 0) + points

        # Sort and get top 30
        sorted_results = sorted(tally.items(), key=lambda x: x[1], reverse=True)[:30]

        # Handle ties - assign proper ranks
        ranked_results = []
        current_rank = 1

        for i, (player, points) in enumerate(sorted_results):
            if i > 0 and points < sorted_results[i - 1][1]:
                current_rank = i + 1
            ranked_results.append((current_rank, player, points))

        context["results"] = ranked_results
        context["total_votes"] = verified_votes.count()
        context["last_updated"] = timezone.now()
        context["active_year"] = active_year
        context["deadline"] = deadline

        return context


class HistoryView(ListView):
    model = BallonDorResult
    template_name = "ballon_dor/history.html"
    context_object_name = "results"
    ordering = ["-year"]
