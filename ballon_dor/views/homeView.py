from django.views.generic import TemplateView
from ballon_dor.models import Candidate, Vote
from ballon_dor.utils import get_active_year, get_voting_deadline
from django.core.paginator import Paginator
from django.utils import timezone
from collections import defaultdict


class HomePageView(TemplateView):
    """
    Display the homepage with a list of candidates for the active voting year.

    This view fetches all candidates for the currently active year, optimizing
    database queries by selecting related player and club data in advance
    (using select_related). It then filters the candidates to show only those
    marked as contenders and passes them to the template for rendering.

    Context:
        contenders (QuerySet): A queryset of Candidate objects that are marked
                            as contenders for the active year.

    Template:
        home.html
    """

    template_name = "ballon_dor/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_year = get_active_year()

        deadline = get_voting_deadline(active_year)
        voting_closed = timezone.now() > deadline

        # Get filter parameters from URL
        # Without default value ("") - CRASHES if key doesn't exist!
        club_filter = self.request.GET.get("club", "")
        country_filter = self.request.GET.get("country", "")
        search_filter = self.request.GET.get("search", "")

        # Base query (reused)
        base_queryset = Candidate.objects.filter(year=active_year).select_related(
            "player", "club"
        )

        # Apply filters to base query
        contenders = base_queryset

        if club_filter:
            contenders = contenders.filter(club__name=club_filter)

        if country_filter:
            contenders = contenders.filter(player__country=country_filter)

        if search_filter:
            contenders = contenders.filter(player__name__icontains=search_filter)

        # Randomize order
        contenders = contenders.order_by("?")

        paginator = Paginator(contenders, 15)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        # Reuse base queryset to get clubs and countries (don't filter)
        clubs = (
            base_queryset.values_list("club__name", flat=True)
            .distinct()
            .order_by("club__name")
        )
        countries = (
            base_queryset.values_list("player__country", flat=True)
            .distinct()
            .order_by("player__country")
        )

        # Clean the data - in case some candidates don't have clubs/countries set
        clubs_list = [club for club in clubs if club]
        countries_list = [country for country in countries if country]

        winner = None
        total_points = 0
        vote_stats = {}

        if voting_closed:
            scores = defaultdict(int)
            votes = Vote.objects.filter(is_verified=True, year=active_year)

            for vote in votes:
                scores[vote.player_1st] += 5
                scores[vote.player_2nd] += 3
                scores[vote.player_3rd] += 1

            if scores:
                winner, total_points = max(scores.items(), key=lambda item: item[1])
                vote_stats = {
                    "total_votes": votes.count(),
                    "countries": votes.values("voter_country").distinct().count(),
                    "votes_for_winner": votes.filter(player_1st=winner).count(),
                }

        context_data = {
            "contenders": contenders,
            "active_year": active_year,
            "clubs": clubs_list,
            "countries": countries_list,
            "current_club": club_filter,
            "current_country": country_filter,
            "current_search": search_filter,
            "results_count": contenders.count(),
            "page_obj": page_obj,
            "paginator": paginator,
            "voting_closed": voting_closed,
            "winner": winner,
            "total_points": total_points,
            "vote_stats": vote_stats,
            "deadline": deadline,
        }
        context.update(context_data)

        return context
