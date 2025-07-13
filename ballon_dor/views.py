from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect
from .models import BallonDorResult, Candidate, Vote
from .forms import VoteForm
from django.utils import timezone
from .utils import get_active_year, get_voting_deadline
import uuid
from django.core.mail import EmailMessage
from django.conf import settings
from django.views.generic import ListView


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
        email = form.cleaned_data["email"]
        if Vote.objects.filter(
            email=email, year=active_year, is_verified=True
        ).exists():
            return redirect("already_voted")
        vote = form.save(commit=False)
        vote.year = active_year
        vote.token = str(uuid.uuid4())
        vote.save()
        verify_url = self.request.build_absolute_uri(
            reverse("verify", args=[vote.token])
        )
        # HTML email body
        html_body = f"""
        <html>
        <body>
        <h2>Confirm Your Ballon D'or Vote</h2>
        <p>Thanks for voting! Click the button below to verify:</p>
        <a href="{verify_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none;">Verify Vote</a>
        <p>If the button doesn't work, copy this link: {verify_url}</p>
        <p>Best,</p>
        </body>
        </html>
        """

        try:
            msg = EmailMessage(
                "Confirm Your Vote",
                html_body,
                f"Ballon D'or App <{settings.EMAIL_HOST_USER}>",  # Sender name + email
                [email],
            )
            msg.content_subtype = "html"  # For HTML rendering
            msg.send()
        except Exception as e:
            print(f"Email send failed: {e}")
            return HttpResponse("Error sending verification email. Please try again.")

        return redirect("vote_pending")

    def form_invalid(self, form):
        print("DEBUG: form_invalid called")
        print(f"DEBUG: Form errors: {form.errors}")
        return super().form_invalid(form)

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

        for vote in Vote.objects.filter(year=active_year, is_verified=True):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["contenders"] = (
            Candidate.objects.filter(year=2025)
            .select_related("player", "club")
            .order_by("?")
        )  # All, randomized for variety
        return context


class AlreadyVotedView(TemplateView):
    template_name = "ballon_dor/already_voted.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["message"] = "⚠️ You have already voted. Thank you!"
        return context


class VotePendingView(TemplateView):
    template_name = "ballon_dor/vote_pending.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["message"] = "Please check your email to confirm your vote!"
        return context


class VerifyView(TemplateView):
    def get(self, request, token):
        vote = Vote.objects.filter(token=token, is_verified=False).first()
        if vote:
            vote.is_verified = True
            vote.token = ""
            vote.save()
            return redirect("live_results")
        return HttpResponse("Invalid or already verified link.")


class HistoryView(ListView):
    model = BallonDorResult
    template_name = "ballon_dor/history.html"
    context_object_name = "results"
    ordering = ["-year"]  # Newest first
