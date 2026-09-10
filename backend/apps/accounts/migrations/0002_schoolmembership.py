from django.db import migrations,models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[("accounts","0001_initial"),("tenants","0001_initial")]
    operations=[
        migrations.CreateModel(
            name="SchoolMembership",
            fields=[
                ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
                ("role",models.CharField(choices=[("OWNER","Propriétaire"),("DIRECTOR","Directeur"),("MANAGER","Gestionnaire"),("TEACHER","Enseignant"),("ACCOUNTANT","Comptable")],max_length=32)),
                ("is_active",models.BooleanField(default=True)),
                ("created_at",models.DateTimeField(auto_now_add=True)),
                ("school",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="memberships",to="tenants.school")),
                ("user",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="school_memberships",to="accounts.user")),
            ],
            options={"unique_together":{("user","school")}},
        )
    ]
