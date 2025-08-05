from django.urls import path

from ballon_dor.views.voteView import VotingClosedView
from . import views
from .views import (
    HomePageView,
    LiveResultsView,
    VoteCreateView,
    AlreadyVotedView,
    VerifyView,
    VotePendingView,
    HistoryView,
    CandidateDetailView,
)

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("vote/", VoteCreateView.as_view(), name="vote"),
    path("live-results/", LiveResultsView.as_view(), name="live_results"),
    path("already-voted/", AlreadyVotedView.as_view(), name="already_voted"),
    path("vote-pending/", VotePendingView.as_view(), name="vote_pending"),
    path("verify/<str:token>/", VerifyView.as_view(), name="verify"),
    path("history/", HistoryView.as_view(), name="history"),
    # Candidate pages (year-specific)
    path(
        "candidate/<int:year>/<slug:slug>/",
        CandidateDetailView.as_view(),
        name="candidate_detail",
    ),
    path("voting-closed/", VotingClosedView.as_view(), name="voting_closed"),
]
