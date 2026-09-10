from django.db import migrations,models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial=True
    dependencies=[]
    operations=[
        migrations.CreateModel(
            name="School",
            fields=[
                ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
                ("name",models.CharField(max_length=200)),
                ("slug",models.SlugField(max_length=80,unique=True)),
                ("acronym",models.CharField(blank=True,max_length=30)),
                ("city",models.CharField(blank=True,max_length=120)),
                ("country",models.CharField(default="Cameroun",max_length=120)),
                ("phone",models.CharField(blank=True,max_length=40)),
                ("email",models.EmailField(blank=True,max_length=254)),
                ("logo_url",models.URLField(blank=True)),
                ("language_mode",models.CharField(choices=[("FRENCH","Francophone"),("ENGLISH","Anglophone"),("BILINGUAL","Bilingue")],default="FRENCH",max_length=20)),
                ("education_level",models.CharField(choices=[("PRIMARY","Primaire"),("SECONDARY","Secondaire"),("PRIMARY_SECONDARY","Primaire + secondaire")],default="PRIMARY_SECONDARY",max_length=30)),
                ("teaching_model",models.CharField(choices=[("CLASS_TEACHER","Titulaire de classe"),("SUBJECT_TEACHER","Enseignants par matière"),("HYBRID","Hybride")],default="HYBRID",max_length=30)),
                ("status",models.CharField(choices=[("ACTIVE","Actif"),("SUSPENDED","Suspendu")],default="ACTIVE",max_length=20)),
                ("created_at",models.DateTimeField(auto_now_add=True)),
                ("updated_at",models.DateTimeField(auto_now=True)),
            ]
        ),
        migrations.CreateModel(
            name="SchoolDomain",
            fields=[
                ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
                ("domain",models.CharField(max_length=255,unique=True)),
                ("is_primary",models.BooleanField(default=False)),
                ("is_local",models.BooleanField(default=False)),
                ("created_at",models.DateTimeField(auto_now_add=True)),
                ("school",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="domains",to="tenants.school")),
            ]
        )
    ]
