from django.db import migrations, models
from django.utils.text import slugify


def populate_candidate_slugs(apps, schema_editor):
    """Safely populate slug fields for existing candidates"""
    Candidate = apps.get_model("ballon_dor", "Candidate")

    for candidate in Candidate.objects.all():
        if not candidate.slug:  # Only update if slug is empty
            # Get the player name - we need to access the related object
            try:
                Player = apps.get_model("ballon_dor", "Player")
                player = Player.objects.get(pk=candidate.player_id)
                base_slug = slugify(player.name)
            except:
                # Fallback if player doesn't exist
                base_slug = f"candidate-{candidate.pk}"

            # Ensure uniqueness within the year
            slug = base_slug
            counter = 1
            while (
                Candidate.objects.filter(year=candidate.year, slug=slug)
                .exclude(pk=candidate.pk)
                .exists()
            ):
                slug = f"{base_slug}-{counter}"
                counter += 1

            candidate.slug = slug
            candidate.save(update_fields=["slug"])


def reverse_populate_slugs(apps, schema_editor):
    """Clear slugs if migration is reversed"""
    Candidate = apps.get_model("ballon_dor", "Candidate")
    Candidate.objects.update(slug="")


class Migration(migrations.Migration):

    dependencies = [
        (
            "ballon_dor",
            "0007_vote_unique_email_per_year",
        ),  # Replace with your actual latest migration
    ]

    operations = [
        # Step 1: Add new fields without constraints
        migrations.AddField(
            model_name="candidate",
            name="slug",
            field=models.SlugField(max_length=100, blank=True, default=""),
        ),
        migrations.AddField(
            model_name="candidate",
            name="achievements",
            field=models.TextField(blank=True, help_text="Key achievements this year"),
        ),
        migrations.AddField(
            model_name="candidate",
            name="stats",
            field=models.TextField(
                blank=True, help_text="Season stats (goals, assists, etc.)"
            ),
        ),
        migrations.AddField(
            model_name="candidate",
            name="why_contender",
            field=models.TextField(
                blank=True, help_text="Why they deserve the Ballon d'Or this year"
            ),
        ),
        # Step 2: Populate slug fields for existing data
        migrations.RunPython(populate_candidate_slugs, reverse_populate_slugs),
        # Step 3: Add constraints AFTER data is populated
        migrations.AddConstraint(
            model_name="candidate",
            constraint=models.UniqueConstraint(
                fields=["year", "slug"], name="unique_candidate_slug_per_year"
            ),
        ),
        migrations.AddConstraint(
            model_name="candidate",
            constraint=models.UniqueConstraint(
                fields=["year", "player"], name="unique_candidate_player_per_year"
            ),
        ),
    ]
