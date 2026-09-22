from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("report_cards", "0003_reportcardtemplate_language_mode"),
    ]

    operations = [
        migrations.AddField(
            model_name="reportcardtemplate",
            name="show_student_photo",
            field=models.BooleanField(default=False),
        ),
    ]
