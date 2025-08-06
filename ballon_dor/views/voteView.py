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
    active_year = get_active_year()
    voting_deadline = get_voting_deadline(active_year)

    def dispatch(self, request, *args, **kwargs):
        active_year = get_active_year()
        deadline = get_voting_deadline(active_year)
        if timezone.now() > deadline:
            return redirect("voting_closed")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_year = get_active_year()
        deadline = get_voting_deadline(active_year)

        context.update(
            {
                "active_year": active_year,
                "deadline": deadline,
            }
        )
        return context

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

        verify_url = f"https://fansaward.com{reverse('verify', args=[vote.token])}"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 600px; margin: auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.05);">
            <h2 style="color: #333;">Confirm Your Vote</h2>
            <p style="font-size: 16px; color: #444;">
                Thank you for submitting your vote for the <strong>{active_year} vote</strong>.
                To confirm your vote, please click the button below:
            </p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verify_url}" style="background-color: #1d4ed8; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">✅ Verify Your Vote</a>
            </div>
            <p style="font-size: 14px; color: #555;">
                Or copy and paste this link into your browser:<br>
                <a href="{verify_url}" style="color: #1d4ed8;">{verify_url}</a>
            </p>
            <hr style="border: none; border-top: 1px solid #eee; margin: 40px 0;">
            <p style="font-size: 12px; color: #888;">
                If you didn't request this, you can ignore this email.<br>
                — FansAward Team
            </p>
            </div>
        </body>
        </html>
        """

        try:
            msg = EmailMessage(
                "Confirm Your Vote",
                html_body,
                f"FansAward App <{settings.EMAIL_HOST_USER}>",
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
        active_year = get_active_year()
        deadline = get_voting_deadline(active_year)

        context.update(
            {
                "message": "Please check your email to confirm your vote!",
                "active_year": active_year,
                "deadline": deadline,
            }
        )
        return context


class AlreadyVotedView(TemplateView):
    template_name = "ballon_dor/already_voted.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_year = get_active_year()
        deadline = get_voting_deadline(active_year)

        context.update(
            {
                "message": "You have already voted. Thank you!",
                "active_year": active_year,
                "deadline": deadline,
            }
        )
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


class VotingClosedView(TemplateView):
    template_name = "ballon_dor/voting_closed.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_year = get_active_year()
        deadline = get_voting_deadline(active_year)

        context.update(
            {
                "active_year": active_year,
                "deadline": deadline,
            }
        )
        return context
