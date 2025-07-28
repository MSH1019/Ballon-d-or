from django.views.generic.edit import CreateView
from django.views.generic import TemplateView, DetailView, ListView
from django.http import HttpResponse
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from django.db.models import Count, Q
import uuid
from .models import BallonDorResult, Candidate, Vote, Player, Club
from .forms import VoteForm
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
        email = form.cleaned_data["email"]

        # Check if user already has a verified vote
        if Vote.objects.filter(
            email=email, year=active_year, is_verified=True
        ).exists():
            return redirect("already_voted")

        # Check if user has an unverified vote - delete it and create new one
        existing_vote = Vote.objects.filter(
            email=email, year=active_year, is_verified=False
        ).first()
        if existing_vote:
            existing_vote.delete()

        # Now create the new vote
        vote = form.save(commit=False)
        vote.year = active_year
        vote.token = str(uuid.uuid4())
        vote.save()

        verify_url = self.request.build_absolute_uri(
            reverse("verify", args=[vote.token])
        )

        html_body = f"""
        <html>
        <body>
        <h2>Confirm Your Vote</h2>
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
                f"Fan Award App <{settings.EMAIL_HOST_USER}>",
                [email],
            )
            msg.content_subtype = "html"
            msg.send()
        except Exception as e:
            print(f"Email send failed: {e}")
            return HttpResponse("Error sending verification email. Please try again.")

        return redirect("vote_pending")

    def form_invalid(self, form):
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

        return context


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


class AlreadyVotedView(TemplateView):
    template_name = "ballon_dor/already_voted.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["message"] = "You have already voted. Thank you!"
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
    ordering = ["-year"]


# NEW: Candidate Detail View (year-specific)
class CandidateDetailView(DetailView):
    model = Candidate
    template_name = "ballon_dor/candidate_detail.html"
    context_object_name = "candidate"

    def get_object(self):
        return get_object_or_404(
            Candidate, year=self.kwargs["year"], slug=self.kwargs["slug"]
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        candidate = self.get_object()
        player = candidate.player
        year = candidate.year

        # Get voting stats for this player in this year
        first_votes = Vote.objects.filter(
            player_1st=player, year=year, is_verified=True
        ).count()
        second_votes = Vote.objects.filter(
            player_2nd=player, year=year, is_verified=True
        ).count()
        third_votes = Vote.objects.filter(
            player_3rd=player, year=year, is_verified=True
        ).count()

        total_points = (first_votes * 5) + (second_votes * 3) + (third_votes * 1)

        # Calculate current ranking
        points_map = {
            "player_1st": 5,
            "player_2nd": 3,
            "player_3rd": 1,
        }
        tally = {}

        # Get all verified votes for this year
        verified_votes = Vote.objects.filter(year=year, is_verified=True)

        for vote in verified_votes:
            for field, points in points_map.items():
                vote_player = getattr(vote, field)
                tally[vote_player] = tally.get(vote_player, 0) + points

        # Sort and find current player's rank
        sorted_results = sorted(tally.items(), key=lambda x: x[1], reverse=True)

        current_rank = None
        for i, (ranked_player, points) in enumerate(sorted_results):
            if ranked_player.id == player.id:
                current_rank = i + 1
                break

        # If player hasn't received votes yet, they're not ranked
        if current_rank is None:
            current_rank = "Unranked"

        context["voting_stats"] = {
            "first_votes": first_votes,
            "second_votes": second_votes,
            "third_votes": third_votes,
            "total_points": total_points,
            "current_rank": current_rank,
        }

        # Get other candidates from same year for comparison
        context["other_candidates"] = (
            Candidate.objects.filter(year=year)
            .exclude(pk=candidate.pk)
            .select_related("player", "club")
            .order_by("?")[:5]  # Add random ordering!
        )

        return context
