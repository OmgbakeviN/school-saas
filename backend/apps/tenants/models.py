from django.db import models

class School(models.Model):
    class LanguageMode(models.TextChoices):
        FRENCH = "FRENCH", "Francophone"
        ENGLISH = "ENGLISH", "Anglophone"
        BILINGUAL = "BILINGUAL", "Bilingue"

    class EducationLevel(models.TextChoices):
        PRIMARY = "PRIMARY", "Primaire"
        SECONDARY = "SECONDARY", "Secondaire"
        PRIMARY_SECONDARY = "PRIMARY_SECONDARY", "Primaire + secondaire"

    class TeachingModel(models.TextChoices):
        CLASS_TEACHER = "CLASS_TEACHER", "Titulaire de classe"
        SUBJECT_TEACHER = "SUBJECT_TEACHER", "Enseignants par matière"
        HYBRID = "HYBRID", "Hybride"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Actif"
        SUSPENDED = "SUSPENDED", "Suspendu"

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=80, unique=True)
    acronym = models.CharField(max_length=30, blank=True)
    city = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=120, default="Cameroun")
    phone = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)

    # logo_url est conservé pour compatibilité avec les premières données.
    logo_url = models.URLField(blank=True)
    logo = models.ImageField(upload_to="school_logos/%Y/%m/", blank=True, null=True)

    motto = models.CharField(max_length=220, blank=True)
    primary_color = models.CharField(max_length=7, default="#0f172a")
    secondary_color = models.CharField(max_length=7, default="#2563eb")

    language_mode = models.CharField(
        max_length=20,
        choices=LanguageMode.choices,
        default=LanguageMode.FRENCH,
    )
    education_level = models.CharField(
        max_length=30,
        choices=EducationLevel.choices,
        default=EducationLevel.PRIMARY_SECONDARY,
    )
    teaching_model = models.CharField(
        max_length=30,
        choices=TeachingModel.choices,
        default=TeachingModel.HYBRID,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class SchoolDomain(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="domains",
    )
    domain = models.CharField(max_length=255, unique=True)
    is_primary = models.BooleanField(default=False)
    is_local = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.domain
