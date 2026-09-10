from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ("tenants", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="school",
            name="logo",
            field=models.ImageField(blank=True, null=True, upload_to="school_logos/%Y/%m/"),
        ),
        migrations.AddField(
            model_name="school",
            name="motto",
            field=models.CharField(blank=True, max_length=220),
        ),
        migrations.AddField(
            model_name="school",
            name="primary_color",
            field=models.CharField(default="#0f172a", max_length=7),
        ),
        migrations.AddField(
            model_name="school",
            name="secondary_color",
            field=models.CharField(default="#2563eb", max_length=7),
        ),
    ]
