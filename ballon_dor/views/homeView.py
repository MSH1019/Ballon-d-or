from django.views.generic import TemplateView
from ballon_dor.models import Candidate
from ballon_dor.utils import get_active_year


class HomePageView(TemplateView):
    template_name = "ballon_dor/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Use the same get_active_year() function from your other views
        active_year = get_active_year()

        context["contenders"] = (
            Candidate.objects.filter(year=active_year)
            .select_related("player", "club")
            .order_by("?")
        )

        # Optional: Pass the year to template for display
        context["active_year"] = active_year

        return context

