from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from .models import Vote, Player, Candidate
from .forms import VoteForm
from django.utils import timezone
from datetime import datetime
from datetime import timezone as dt_timezone
from django.db.models import Max
import pytz
from .utils import get_active_year, get_voting_deadline


class VoteCreateView(CreateView):
    model = Vote
    form_class = VoteForm
    template_name = "ballon_dor/vote.html"
    success_url = reverse_lazy("live_results")

    def dispatch(self, request, *args, **kwargs):
        active_year = get_active_year()
        deadline = get_voting_deadline(active_year)
        if timezone.now() > deadline:
            return HttpResponse("Voting has closed. Thank you for your interest!")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        active_year = get_active_year()
        ip = self.get_client_ip()
        print(f"DEBUG: IP detected: {ip}")
        if Vote.objects.filter(ip_address=ip, year=active_year).exists():
            return redirect("already_voted")

        form.instance.ip_address = ip
        form.instance.year = active_year
        return super().form_valid(form)

    def form_invalid(self, form):
        print("DEBUG: form_invalid called")
        print(f"DEBUG: Form errors: {form.errors}")
        return super().form_invalid(form)

    def get_client_ip(self):
        x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = self.request.META.get("REMOTE_ADDR")
        return ip

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["year"] = get_active_year()
        return kwargs


class LiveResultsView(TemplateView):
    template_name = "ballon_dor/live_results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_year = get_active_year()
        points_map = {
            "player_1st": 5,
            "player_2nd": 3,
            "player_3rd": 1,
        }
        tally = {}

        for vote in Vote.objects.filter(year=active_year):
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


class AlreadyVotedView(TemplateView):
    template_name = "ballon_dor/already_voted.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["message"] = "⚠️ You have already voted. Thank you!"
        return context
