from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("report_cards", "0002_reportcardtemplate"),
    ]

    operations = [
        migrations.AddField(
            model_name="reportcardtemplate",
            name="language_mode",
            field=models.CharField(
                choices=[
                    ("AUTO", "Automatique selon la section"),
                    ("FRENCH", "Français"),
                    ("ENGLISH", "English"),
                ],
                default="AUTO",
                help_text=(
                    "AUTO utilise la langue de la section de l'élève. "
                    "Français ou English force la langue du PDF."
                ),
                max_length=20,
            ),
        ),
    ]
