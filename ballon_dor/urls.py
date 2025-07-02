from django.urls import path
from .views import VoteCreateView, LiveResultsView, HomePageView

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("vote/", VoteCreateView.as_view(), name="vote"),
    path("live-results/", LiveResultsView.as_view(), name="live_results"),
]
