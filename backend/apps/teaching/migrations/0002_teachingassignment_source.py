from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("teaching", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="teachingassignment",
            name="source",
            field=models.CharField(
                choices=[
                    ("MANUAL", "Affectation manuelle"),
                    (
                        "CLASS_TEACHER_AUTO",
                        "Générée depuis le titulaire de classe",
                    ),
                ],
                db_index=True,
                default="MANUAL",
                max_length=30,
            ),
        ),
    ]
