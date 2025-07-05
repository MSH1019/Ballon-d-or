from django.test import TestCase
from django.urls import reverse
from .models import Player, Club, NationalTeam, BallonDorResult, Vote, Candidate
from .forms import VoteForm

from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch


class BallonDorModelTest(TestCase):
    def setUp(self):
        self.club = Club.objects.create(name="Barcelona")
        self.nt = NationalTeam.objects.create(name="Argentina")
        self.player = Player.objects.create(name="Lionel Messi", country="Argentina")
        self.result = BallonDorResult.objects.create(
            year=2021,
            rank=1,
            player=self.player,
            club_at_award=self.club,
            nationality_at_award=self.nt,
            points=500,
        )

    def test_player_creation(self):
        self.assertEqual(self.player.name, "Lionel Messi")
        self.assertEqual(self.player.country, "Argentina")

    def test_ballon_dor_result_creation(self):
        self.assertEqual(self.result.rank, 1)
        self.assertEqual(self.result.club_at_award.name, "Barcelona")


class VoteTest(TestCase):
    def setUp(self):
        self.player1 = Player.objects.create(name="Messi", country="Argentina")
        self.player2 = Player.objects.create(name="Ronaldo", country="Portugal")
        self.player3 = Player.objects.create(name="Neymar", country="Brazil")

        Candidate.objects.create(player=self.player1, year=2025)
        Candidate.objects.create(player=self.player2, year=2025)
        Candidate.objects.create(player=self.player3, year=2025)

    def test_valid_vote(self):
        vote = Vote.objects.create(
            player_1st=self.player1,
            player_2nd=self.player2,
            player_3rd=self.player3,
            voter_name="Test Voter",
            voter_country="Testland",
        )
        self.assertEqual(vote.player_1st.name, "Messi")

    def test_duplicate_vote_players_invalid(self):
        from .forms import VoteForm

        form = VoteForm(
            data={
                "player_1st": self.player1.id,
                "player_2nd": self.player1.id,
                "player_3rd": self.player3.id,
                "voter_name": "Test Voter",
                "voter_country": "Testland",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Each player must be unique", str(form.errors))

    def test_user_cannot_vote_twice_from_same_ip(self):
        # First vote
        response1 = self.client.post(
            reverse("vote"),
            {
                "player_1st": self.player1.id,
                "player_2nd": self.player2.id,
                "player_3rd": self.player3.id,
                "voter_name": "Tester",
                "voter_country": "Testland",
            },
            **{"REMOTE_ADDR": "123.123.123.123"},
            follow=False
        )
        self.assertRedirects(response1, reverse("live_results"))

        # Second vote
        response2 = self.client.post(
            reverse("vote"),
            {
                "player_1st": self.player1.id,
                "player_2nd": self.player2.id,
                "player_3rd": self.player3.id,
                "voter_name": "Tester2",
                "voter_country": "Testland",
            },
            **{"REMOTE_ADDR": "123.123.123.123"},
            follow=False
        )
        self.assertRedirects(response2, reverse("already_voted"))

    def test_voting_after_deadline_blocked(self):
        future_time = timezone.now() + timedelta(days=365)

        with patch("django.utils.timezone.now", return_value=future_time):
            response = self.client.post(
                reverse("vote"),
                {
                    "player_1st": self.player1.id,
                    "player_2nd": self.player2.id,
                    "player_3rd": self.player3.id,
                    "voter_name": "Late Voter",
                    "voter_country": "Testland",
                },
                **{"REMOTE_ADDR": "124.124.124.124"},
                follow=False
            )
            self.assertContains(response, "Voting has closed", status_code=200)

    # checks that the players show up on the page, and the points tally is correct
    def test_live_results_point_tally(self):
        Vote.objects.create(
            player_1st=self.player1,
            player_2nd=self.player2,
            player_3rd=self.player3,
            voter_name="Voter1",
            voter_country="Testland",
            ip_address="111.111.111.111",
            year=2025,
        )
        Vote.objects.create(
            player_1st=self.player1,
            player_2nd=self.player3,
            player_3rd=self.player2,
            voter_name="Voter2",
            voter_country="Testland",
            ip_address="112.112.112.112",
            year=2025,
        )

        response = self.client.get(reverse("live_results"))
        self.assertEqual(response.status_code, 200)

        results = response.context["results"]
        # Results should be a list of tuples (Player, points)
        expected = [
            (self.player1, 10),
            (self.player2, 4),
            (self.player3, 4),
        ]

        for (result_player, result_points), (expected_player, expected_points) in zip(
            results, expected
        ):
            self.assertEqual(result_player, expected_player)
            self.assertEqual(result_points, expected_points)


class ViewTest(TestCase):
    def test_vote_page_loads(self):
        response = self.client.get(reverse("vote"))  # adjust name if different
        self.assertEqual(response.status_code, 200)

    def test_live_results_page_loads(self):
        response = self.client.get(reverse("live_results"))  # adjust name if different
        self.assertEqual(response.status_code, 200)
