from django.views.generic import TemplateView
from ballon_dor.models import Candidate
from ballon_dor.utils import get_active_year


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

        # Get filter parameters from URL
        # Without default value ("") - CRASHES if key doesn't exist!
        club_filter = self.request.GET.get("club", "")
        country_filter = self.request.GET.get("country", "")
        search_filter = self.request.GET.get("search", "")

        # Base query (reused)
        base_queryset = Candidate.objects.filter(year=active_year).select_related("player", "club")

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

        context_data = {
            "contenders": contenders,
            "active_year": active_year,
            "clubs": clubs_list,
            "countries": countries_list,
            "current_club": club_filter,
            "current_country": country_filter,
            "current_search": search_filter,
            "results_count": contenders.count(),
        }
        context.update(context_data)

        return context
