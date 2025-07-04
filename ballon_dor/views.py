from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.shortcuts import render
from .models import Vote, Player
from .forms import VoteForm
from django.utils import timezone
from datetime import datetime
from datetime import timezone as dt_timezone


VOTING_DEADLINE = datetime(2025, 9, 21, 23, 59, 59, tzinfo=dt_timezone.utc)


class VoteCreateView(CreateView):
    model = Vote
    form_class = VoteForm
    template_name = "ballon_dor/vote.html"
    success_url = reverse_lazy("live_results")

    def dispatch(self, request, *args, **kwargs):
        if timezone.now() > VOTING_DEADLINE:
            return HttpResponse("⚠️ Voting has closed. Thank you for your interest!")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        ip = self.get_client_ip()
        if Vote.objects.filter(ip_address=ip, year=2025).exists():
            return HttpResponse("⚠️ You have already voted. Thanks!")
        form.instance.ip_address = ip
        form.instance.year = 2025  # store the year with the vote
        return super().form_valid(form)

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = self.request.META.get("REMOTE_ADDR")
        return ip


class LiveResultsView(TemplateView):
    template_name = "ballon_dor/live_results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        points_map = {
            "player_1st": 5,
            "player_2nd": 3,
            "player_3rd": 1,
        }
        tally = {}

        for vote in Vote.objects.filter(year=2025):
            for field, points in points_map.items():
                player = getattr(
                    vote, field
                )  # This is a Python trick: getattr(vote, "player_1st") is the same as vote.player_1st - So this grabs the actual Player object for that field.
                tally[player] = (
                    tally.get(player, 0) + points
                )  # If player is already in tally, add points to their total. If player isn’t in tally yet, start at 0 and add points.

        # Sort and get top 20
        results = sorted(tally.items(), key=lambda x: x[1], reverse=True)[:20]
        context["results"] = results
        return context


class HomePageView(TemplateView):
    template_name = "ballon_dor/home.html"
