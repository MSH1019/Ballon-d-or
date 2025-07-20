from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
import uuid
from ballon_dor.models import Vote
from ballon_dor.forms import VoteForm
from ballon_dor.utils import get_active_year, get_voting_deadline


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
                f"Ballon D'or App <{settings.EMAIL_HOST_USER}>",
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


class VotePendingView(TemplateView):
    template_name = "ballon_dor/vote_pending.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["message"] = "Please check your email to confirm your vote!"
        return context


class AlreadyVotedView(TemplateView):
    template_name = "ballon_dor/already_voted.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["message"] = "You have already voted. Thank you!"
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
