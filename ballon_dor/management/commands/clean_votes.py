"""
Keep the amount of voter data we hold as small as possible.

    python manage.py clean_votes --dry-run --unverified-days 7
    python manage.py clean_votes --unverified-days 7
    python manage.py clean_votes --anonymise-year 2026

--unverified-days N   Delete votes that were never confirmed by email and are
                      older than N days.
--anonymise-year Y    Replace the email on every vote of year Y with an
                      irreversible code (HMAC keyed with SECRET_KEY). Vote
                      counts are untouched. Only allowed once voting for that
                      year has closed, unless --force is given.
"""

import hashlib
import hmac
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from ballon_dor.models import Vote
from ballon_dor.utils import get_voting_deadline

ANON_DOMAIN = "@anonymised.invalid"


def anonymise(email):
    digest = hmac.new(
        settings.SECRET_KEY.encode(), email.lower().encode(), hashlib.sha256
    ).hexdigest()[:24]
    return f"{digest}{ANON_DOMAIN}"


class Command(BaseCommand):
    help = "Delete stale unverified votes and/or anonymise emails of a finished year."

    def add_arguments(self, parser):
        parser.add_argument("--unverified-days", type=int, metavar="N")
        parser.add_argument("--anonymise-year", type=int, metavar="YEAR")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Anonymise even though voting for that year is still open.",
        )

    def handle(self, *args, **options):
        days = options["unverified_days"]
        year = options["anonymise_year"]
        dry = options["dry_run"]

        if days is None and year is None:
            raise CommandError("Give --unverified-days and/or --anonymise-year.")

        prefix = "[DRY RUN] " if dry else ""

        with transaction.atomic():
            if days is not None:
                cutoff = timezone.now() - timedelta(days=days)
                stale = Vote.objects.filter(is_verified=False, created_at__lt=cutoff)
                count = stale.count()
                if not dry:
                    stale.delete()
                self.stdout.write(
                    f"{prefix}Unverified votes older than {days} days deleted: {count}"
                )

            if year is not None:
                if not options["force"] and timezone.now() <= get_voting_deadline(year):
                    raise CommandError(
                        f"Voting for {year} is still open. Wait until it closes "
                        "(or pass --force if you really mean it)."
                    )
                todo = Vote.objects.filter(year=year).exclude(
                    email__endswith=ANON_DOMAIN
                )
                count = 0
                for vote in todo:
                    count += 1
                    if not dry:
                        vote.email = anonymise(vote.email)
                        vote.token = ""
                        vote.save(update_fields=["email", "token"])
                self.stdout.write(f"{prefix}Emails anonymised for {year}: {count}")

            if dry:
                transaction.set_rollback(True)
