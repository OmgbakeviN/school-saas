import apps.people.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("people", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="photo",
            field=models.ImageField(
                blank=True,
                max_length=500,
                null=True,
                upload_to=apps.people.models.student_photo_upload_to,
            ),
        ),
    ]
