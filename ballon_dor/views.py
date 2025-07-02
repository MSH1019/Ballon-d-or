from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.shortcuts import render
from .models import Vote, Player
from .forms import VoteForm


class VoteCreateView(CreateView):
    model = Vote
    form_class = VoteForm
    template_name = "ballon_dor/vote.html"
    success_url = reverse_lazy("live_results")

    def form_valid(self, form):
        ip = self.get_client_ip()
        if Vote.objects.filter(ip_address=ip).exists():
            return HttpResponse("You have already voted. Thanks!")
        form.instance.ip_address = ip
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
        points_map = {"1st": 5, "2nd": 3, "3rd": 1}
        tally = {}

        for vote in Vote.objects.all():
            tally[vote.player_1st] = tally.get(vote.player_1st, 0) + points_map["1st"]
            tally[vote.player_2nd] = tally.get(vote.player_2nd, 0) + points_map["2nd"]
            tally[vote.player_3rd] = tally.get(vote.player_3rd, 0) + points_map["3rd"]

        # Sort and get top 20
        results = sorted(tally.items(), key=lambda x: x[1], reverse=True)[:20]
        context["results"] = results
        return context


class HomePageView(TemplateView):
    template_name = "ballon_dor/home.html"
