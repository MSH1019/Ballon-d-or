"""
Create the 2026 candidates (the 30-man France Football shortlist).

Safe to run more than once:
  * Players that already exist (matched ignoring accents/case) are reused,
    so their photos and 2025 history are kept.
  * Candidates that already exist for 2026 are left alone, so stats you have
    typed in are never overwritten.

Usage:
    python manage.py seed_2026 --dry-run   # show what would happen
    python manage.py seed_2026             # do it
"""

import unicodedata

from django.core.management.base import BaseCommand
from django.db import transaction

from ballon_dor.models import Candidate, Player

YEAR = 2026

# (name, country, position). Country is only used when the player is new.
SHORTLIST = [
    ("Jude Bellingham", "England", "CAM"),
    ("Pau Cubarsí", "Spain", "DEF"),
    ("Marc Cucurella", "Spain", "DEF"),
    ("Ousmane Dembélé", "France", "FWD"),
    ("Luis Díaz", "Colombia", "FWD"),
    ("Bruno Fernandes", "Portugal", "CAM"),
    ("Gabriel Magalhães", "Brazil", "DEF"),
    ("Erling Haaland", "Norway", "FWD"),
    ("Achraf Hakimi", "Morocco", "DEF"),
    ("Harry Kane", "England", "FWD"),
    ("Khvicha Kvaratskhelia", "Georgia", "FWD"),
    ("Lamine Yamal", "Spain", "FWD"),
    ("Sadio Mané", "Senegal", "FWD"),
    ("Marquinhos", "Brazil", "DEF"),
    ("Lautaro Martínez", "Argentina", "FWD"),
    ("Kylian Mbappé", "France", "FWD"),
    ("Nuno Mendes", "Portugal", "DEF"),
    ("Lionel Messi", "Argentina", "FWD"),
    ("João Neves", "Portugal", "MID"),
    ("Michael Olise", "France", "FWD"),
    ("Willian Pacho", "Ecuador", "DEF"),
    ("Julián Quiñones", "Mexico", "FWD"),
    ("Declan Rice", "England", "MID"),
    ("Rodri", "Spain", "MID"),
    ("Fabián Ruiz", "Spain", "MID"),
    ("William Saliba", "France", "DEF"),
    ("Ferran Torres", "Spain", "FWD"),
    ("Dayot Upamecano", "France", "DEF"),
    ("Vinícius Jr.", "Brazil", "FWD"),
    ("Vitinha", "Portugal", "MID"),
]


def normalise(name):
    """'Vinícius Jr.' and 'Vinicius Junior' both become 'vinicius junior'."""
    text = unicodedata.normalize("NFKD", name)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    text = text.replace(".", "").replace("-", " ")
    words = ["junior" if w == "jr" else w for w in text.split()]
    return " ".join(words)


class Command(BaseCommand):
    help = "Create the 2026 Player and Candidate rows (no stats, no photos)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would happen without changing the database.",
        )
        parser.add_argument(
            "--update-positions",
            action="store_true",
            help="Also set the position on 2026 candidates that already exist.",
        )

    def handle(self, *args, **options):
        dry = options["dry_run"]
        existing = {normalise(p.name): p for p in Player.objects.all()}

        created_players = reused_players = created_candidates = skipped = 0

        with transaction.atomic():
            for name, country, position in SHORTLIST:
                player = existing.get(normalise(name))

                if player:
                    reused_players += 1
                    note = f"reuse player '{player.name}'"
                else:
                    created_players += 1
                    note = "NEW player"
                    if not dry:
                        player = Player.objects.create(name=name, country=country)
                        existing[normalise(name)] = player

                existing_candidate = (
                    Candidate.objects.filter(year=YEAR, player=player).first()
                    if player
                    else None
                )
                if existing_candidate:
                    skipped += 1
                    note += " | candidate already exists, left alone"
                    if (
                        options["update_positions"]
                        and existing_candidate.position != position
                    ):
                        note += f" (position {existing_candidate.position} -> {position})"
                        if not dry:
                            existing_candidate.position = position
                            existing_candidate.save(update_fields=["position"])
                else:
                    created_candidates += 1
                    note += f" | add {YEAR} candidate ({position})"
                    if not dry:
                        Candidate.objects.create(
                            player=player, year=YEAR, position=position
                        )

                self.stdout.write(f"{name:24} {note}")

            if dry:
                transaction.set_rollback(True)

        prefix = "[DRY RUN] " if dry else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{prefix}players reused: {reused_players}, new: {created_players} | "
                f"candidates added: {created_candidates}, already there: {skipped}"
            )
        )
        if not dry:
            self.stdout.write(
                "Next: open /admin/ballon_dor/candidate/?year=2026 to add clubs, "
                "photos and stats."
            )
