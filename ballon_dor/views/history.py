from ballon_dor.models import BallonDorResult
from django.views.generic import ListView


class HistoryView(ListView):
    model = BallonDorResult
    template_name = "ballon_dor/history.html"
    context_object_name = "results"
    ordering = ["-year"]
