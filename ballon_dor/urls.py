from django.urls import path
from .views import (
    HomePageView,
    LiveResultsView,
    VoteCreateView,
    AlreadyVotedView,
    VerifyView,
    VotePendingView,
    HistoryView,
)

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("vote/", VoteCreateView.as_view(), name="vote"),
    path("live-results/", LiveResultsView.as_view(), name="live_results"),
    path("already-voted/", AlreadyVotedView.as_view(), name="already_voted"),
    path("vote-pending/", VotePendingView.as_view(), name="vote_pending"),
    path("verify/<str:token>/", VerifyView.as_view(), name="verify"),
]
