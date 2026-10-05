import io
import re
from datetime import datetime, timezone as dt_timezone
from unittest.mock import patch

from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .forms import VoteForm
from .models import BallonDorResult, Candidate, Club, NationalTeam, Player, Vote

# "Today" for tests: after the 2026 shortlist, before the 2026 deadline (Oct 25).
OPEN_VOTING = datetime(2026, 10, 6, 12, 0, tzinfo=dt_timezone.utc)
AFTER_DEADLINE = datetime(2026, 10, 26, 12, 0, tzinfo=dt_timezone.utc)


def at(moment):
    return patch("django.utils.timezone.now", return_value=moment)


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


class VoterDataTest(TestCase):
    """What we ask voters for, and nothing more."""

    def test_form_asks_only_for_picks_email_and_optional_country(self):
        self.assertEqual(
            list(VoteForm().fields),
            ["player_1st", "player_2nd", "player_3rd", "voter_country", "email"],
        )

    def test_vote_model_has_no_name_or_ip_columns(self):
        names = {f.name for f in Vote._meta.get_fields()}
        self.assertNotIn("voter_name", names)
        self.assertNotIn("ip_address", names)

    def test_privacy_page_and_note(self):
        with at(OPEN_VOTING):
            page = self.client.get(reverse("privacy"))
            self.assertContains(page, "What we collect when you vote")
            self.assertContains(page, "Google Analytics")  # we say what we use
            self.assertContains(self.client.get(reverse("vote")), "anonymised")


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class VoteFlowTest(TestCase):
    def setUp(self):
        self.p1 = Player.objects.create(name="Messi", country="Argentina")
        self.p2 = Player.objects.create(name="Ronaldo", country="Portugal")
        self.p3 = Player.objects.create(name="Neymar", country="Brazil")
        for p in (self.p1, self.p2, self.p3):
            Candidate.objects.create(player=p, year=2026)

    def data(self, email="fan@example.com", **over):
        d = {
            "player_1st": self.p1.id,
            "player_2nd": self.p2.id,
            "player_3rd": self.p3.id,
            "voter_country": "GB",
            "email": email,
        }
        d.update(over)
        return d

    def test_same_player_twice_is_rejected(self):
        form = VoteForm(data=self.data(player_2nd=self.p1.id))
        self.assertFalse(form.is_valid())
        self.assertIn("Each player must be unique", str(form.errors))

    def test_email_is_required(self):
        self.assertFalse(VoteForm(data=self.data(email="")).is_valid())

    def test_vote_is_pending_until_email_is_confirmed(self):
        with at(OPEN_VOTING):
            r = self.client.post(reverse("vote"), self.data())
            self.assertRedirects(r, reverse("vote_pending"))
            vote = Vote.objects.get()
            self.assertFalse(vote.is_verified)
            self.assertEqual(vote.year, 2026)
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn(vote.token, mail.outbox[0].body)
            # sender comes from DEFAULT_FROM_EMAIL, not from the SMTP login name
            self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)

            self.client.get(reverse("verify", args=[vote.token]))
            vote.refresh_from_db()
            self.assertTrue(vote.is_verified)
            self.assertEqual(vote.token, "")

    def test_same_email_cannot_vote_twice(self):
        with at(OPEN_VOTING):
            self.client.post(reverse("vote"), self.data())
            token = Vote.objects.get().token
            self.client.get(reverse("verify", args=[token]))

            again = self.client.post(reverse("vote"), self.data())
            self.assertRedirects(again, reverse("already_voted"))
            self.assertEqual(Vote.objects.count(), 1)

    def test_resubmitting_before_confirming_replaces_the_pending_vote(self):
        with at(OPEN_VOTING):
            self.client.post(reverse("vote"), self.data())
            self.client.post(reverse("vote"), self.data(player_1st=self.p2.id, player_2nd=self.p1.id))
            self.assertEqual(Vote.objects.count(), 1)
            self.assertEqual(Vote.objects.get().player_1st, self.p2)

    def test_voting_after_deadline_is_blocked(self):
        with at(AFTER_DEADLINE):
            r = self.client.post(reverse("vote"), self.data())
            self.assertRedirects(r, reverse("voting_closed"))
            self.assertEqual(Vote.objects.count(), 0)

    def test_live_results_point_tally(self):
        def vote(email, a, b, c):
            return Vote.objects.create(
                player_1st=a, player_2nd=b, player_3rd=c,
                voter_country="GB", year=2026, email=email, is_verified=True,
            )

        vote("a@example.com", self.p1, self.p2, self.p3)
        vote("b@example.com", self.p1, self.p3, self.p2)
        vote("c@example.com", self.p2, self.p1, self.p3)
        Vote.objects.create(  # an unverified vote must not count
            player_1st=self.p3, player_2nd=self.p2, player_3rd=self.p1,
            year=2026, email="d@example.com", is_verified=False,
        )

        with at(OPEN_VOTING):
            r = self.client.get(reverse("live_results"))
        self.assertEqual(r.status_code, 200)
        # results are (rank, player, points) tuples
        points = {player.name: pts for _rank, player, pts in r.context["results"]}
        self.assertEqual(points, {"Messi": 13, "Ronaldo": 9, "Neymar": 5})
        self.assertEqual(r.context["total_votes"], 3)  # the unverified vote is ignored


class CleanVotesTest(TestCase):
    def setUp(self):
        self.p = [Player.objects.create(name=n) for n in ("A", "B", "C")]

    def make(self, email, verified, created, year=2026):
        v = Vote.objects.create(
            player_1st=self.p[0], player_2nd=self.p[1], player_3rd=self.p[2],
            year=year, email=email, is_verified=verified, token="" if verified else "tok-" + email,
        )
        Vote.objects.filter(pk=v.pk).update(created_at=created)
        return v

    def run_cmd(self, *args):
        out = io.StringIO()
        call_command("clean_votes", *args, stdout=out)
        return out.getvalue()

    def test_old_unverified_votes_are_deleted_and_the_rest_is_kept(self):
        now = timezone.now()
        self.make("old-unverified@x.com", False, now.replace(year=now.year - 1))
        self.make("fresh-unverified@x.com", False, now)
        self.make("old-verified@x.com", True, now.replace(year=now.year - 1))

        self.run_cmd("--unverified-days", "7", "--dry-run")
        self.assertEqual(Vote.objects.count(), 3)  # dry run changes nothing

        self.run_cmd("--unverified-days", "7")
        self.assertEqual(
            sorted(Vote.objects.values_list("email", flat=True)),
            ["fresh-unverified@x.com", "old-verified@x.com"],
        )

    def test_anonymise_keeps_votes_but_removes_emails(self):
        self.make("one@x.com", True, timezone.now())
        self.make("two@x.com", True, timezone.now())
        with at(AFTER_DEADLINE):
            out = self.run_cmd("--anonymise-year", "2026")
        self.assertIn("anonymised for 2026: 2", out)

        emails = list(Vote.objects.values_list("email", flat=True))
        self.assertEqual(len(emails), 2)
        self.assertEqual(len(set(emails)), 2)  # still unique
        for e in emails:
            self.assertTrue(e.endswith("@anonymised.invalid"))
            self.assertNotIn("x.com", e)
        self.assertEqual(Vote.objects.filter(is_verified=True).count(), 2)

        with at(AFTER_DEADLINE):  # running it again changes nothing
            self.assertIn("anonymised for 2026: 0", self.run_cmd("--anonymise-year", "2026"))
        self.assertEqual(list(Vote.objects.values_list("email", flat=True)), emails)

    def test_anonymise_refuses_while_voting_is_open(self):
        self.make("one@x.com", True, timezone.now())
        with at(OPEN_VOTING):
            with self.assertRaises(CommandError):
                self.run_cmd("--anonymise-year", "2026")
        self.assertEqual(Vote.objects.get().email, "one@x.com")

    def test_needs_an_action(self):
        with self.assertRaises(CommandError):
            self.run_cmd()


class CandidateProfileTest(TestCase):
    """Which stat cards each position shows, and where."""

    def setUp(self):
        self.club = Club.objects.create(name="Test FC")

    def page(self, **fields):
        player = Player.objects.create(name=f"Player {Player.objects.count()}", country="France")
        c = Candidate.objects.create(player=player, year=2026, club=self.club, **fields)
        with at(OPEN_VOTING):
            html = self.client.get(reverse("candidate_detail", args=[c.year, c.slug])).content.decode()
        main, _, more = html.partition("<details")
        main = main[main.index("stats-section"):]
        labels = lambda chunk: re.findall(r'stat-label">([^<]+)<', chunk)
        return labels(main), labels(more.split("</details>")[0]), html

    def test_forward(self):
        main, more, _ = self.page(position="FWD", goals=20, assists=5, chances_created=40, expected_goals=18.5)
        self.assertEqual(main, ["Appearances", "Goals", "Assists", "Avg Rating"])
        self.assertEqual(more, ["G+A", "Chances Created", "Expected Goals (xG)"])

    def test_attacking_midfielder_leads_with_goals_and_assists(self):
        main, more, _ = self.page(position="CAM", goals=10, assists=8, chances_created=50, tackles_interceptions=70)
        self.assertEqual(main, ["Appearances", "Goals", "Assists", "Avg Rating"])
        self.assertEqual(more, ["G+A", "Chances Created", "Tackles + Interceptions"])

    def test_midfielder(self):
        main, more, _ = self.page(position="MID", chances_created=30, tackles_interceptions=100, goals=3, assists=4)
        self.assertEqual(main, ["Appearances", "Chances Created", "Tackles + Interceptions", "Avg Rating"])
        self.assertEqual(more, ["Goals", "Assists"])

    def test_defender(self):
        main, more, _ = self.page(position="DEF", clean_sheets=15, tackles_interceptions=120)
        self.assertEqual(main, ["Appearances", "Clean Sheets", "Tackles + Interceptions", "Avg Rating"])
        self.assertEqual(more, ["Goals", "Assists"])

    def test_signature_stat_shows_in_more_stats(self):
        _, more, _ = self.page(position="FWD", signature_label="Golden Boot", signature_value="Winner")
        self.assertIn("Golden Boot", more)

    def test_trophies_and_awards_are_lists_and_hidden_when_empty(self):
        _, _, html = self.page(position="FWD", trophies_won="Champions League\r\n\r\nLaLiga", awards="Golden Ball")
        self.assertEqual(html.count("honours-list"), 2)
        self.assertIn("🥇 Individual Awards", html)
        self.assertEqual(html.count("<li>"), 3)
        _, _, bare = self.page(position="FWD")
        self.assertNotIn("honours-list", bare)


class ViewTest(TestCase):
    def test_vote_page_loads(self):
        with at(OPEN_VOTING):
            self.assertEqual(self.client.get(reverse("vote")).status_code, 200)

    def test_live_results_page_loads(self):
        with at(OPEN_VOTING):
            self.assertEqual(self.client.get(reverse("live_results")).status_code, 200)
