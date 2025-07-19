from django.db import migrations, models
from django.core.validators import MinValueValidator, MaxValueValidator


class Migration(migrations.Migration):

    dependencies = [
        ("ballon_dor", "0008_add_candidate_fields"),  # Your previous migration
    ]

    operations = [
        # Add essential statistics
        migrations.AddField(
            model_name="candidate",
            name="goals",
            field=models.PositiveIntegerField(
                default=0, help_text="Goals scored this season"
            ),
        ),
        migrations.AddField(
            model_name="candidate",
            name="assists",
            field=models.PositiveIntegerField(
                default=0, help_text="Assists this season"
            ),
        ),
        migrations.AddField(
            model_name="candidate",
            name="appearances",
            field=models.PositiveIntegerField(
                default=0, help_text="Games played this season"
            ),
        ),
        migrations.AddField(
            model_name="candidate",
            name="avg_match_rating",
            field=models.DecimalField(
                max_digits=3,
                decimal_places=1,
                default=0.0,
                validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
                help_text="Average match rating (0.0-10.0)",
            ),
        ),
        # Add trophies (keep existing field if you already have it, or add if new)
        migrations.AddField(
            model_name="candidate",
            name="trophies_won",
            field=models.TextField(
                blank=True, help_text="Major trophies won this season"
            ),
        ),
    ]
