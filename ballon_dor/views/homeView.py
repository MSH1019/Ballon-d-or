from django.views.generic import TemplateView
from ballon_dor.models import Candidate
from ballon_dor.utils import get_active_year


class HomePageView(TemplateView):
    template_name = "ballon_dor/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_year = get_active_year()

        # Get filter parameters from URL
        # Without default value ("") - CRASHES if key doesn't exist!
        club_filter = self.request.GET.get("club", "")
        country_filter = self.request.GET.get("country", "")
        search_filter = self.request.GET.get("search", "")

        print(
            f"Filters: club={club_filter}, country={country_filter}, search={search_filter}"
        )

        # Start with all candidates
        contenders = Candidate.objects.filter(year=active_year).select_related(
            "player", "club"
        )

        # Apply filters
        if club_filter:
            contenders = contenders.filter(club__name=club_filter)

        if country_filter:
            contenders = contenders.filter(player__country=country_filter)

        if search_filter:
            contenders = contenders.filter(player__name__icontains=search_filter)

        # Randomize order
        contenders = contenders.order_by("?")

        # Get all unique clubs and countries for filter dropdowns
        all_candidates = Candidate.objects.filter(year=active_year).select_related(
            "player", "club"
        )
        clubs = (
            all_candidates.values_list("club__name", flat=True)
            .distinct()
            .order_by("club__name")
        )
        countries = (
            all_candidates.values_list("player__country", flat=True)
            .distinct()
            .order_by("player__country")
        )

        # Clean the data - in case some candidates don't have clubs/countries set
        clubs_list = [club for club in clubs if club]
        countries_list = [country for country in countries if country]

        # basically means:
        # clubs_list = []
        #   for club in clubs:
        #   if club:
        #       clubs_list.append(club)

        print(f"Found {len(clubs_list)} clubs and {len(countries_list)} countries")
        print(f"Results: {contenders.count()} candidates")

        context.update(
            {
                "contenders": contenders,
                "active_year": active_year,
                "clubs": clubs_list,
                "countries": countries_list,
                "current_club": club_filter,
                "current_country": country_filter,
                "current_search": search_filter,
                "results_count": contenders.count(),
            }
        )

        return context
