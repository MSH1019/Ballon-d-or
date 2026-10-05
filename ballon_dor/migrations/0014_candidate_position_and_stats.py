from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ballon_dor", "0013_alter_candidate_image_alter_club_logo_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="candidate",
            name="position",
            field=models.CharField(
                choices=[("FWD", "Forward"), ("MID", "Midfielder"), ("DEF", "Defender")],
                default="FWD",
                help_text="Controls which stats show on the profile page",
                max_length=3,
            ),
        ),
        migrations.AddField(
            model_name="candidate",
            name="chances_created",
            field=models.PositiveIntegerField(
                default=0, help_text="Midfielders: chances created this season"
            ),
        ),
        migrations.AddField(
            model_name="candidate",
            name="tackles_interceptions",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Midfielders/defenders: tackles + interceptions combined",
            ),
        ),
        migrations.AddField(
            model_name="candidate",
            name="clean_sheets",
            field=models.PositiveIntegerField(
                default=0, help_text="Defenders: clean sheets this season"
            ),
        ),
        migrations.AddField(
            model_name="candidate",
            name="signature_label",
            field=models.CharField(
                blank=True,
                help_text="e.g. World Cup Golden Ball (optional, needs a value too)",
                max_length=60,
            ),
        ),
        migrations.AddField(
            model_name="candidate",
            name="signature_value",
            field=models.CharField(
                blank=True, help_text="e.g. Winner (optional)", max_length=60
            ),
        ),
    ]
