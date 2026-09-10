from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User, SchoolMembership
from apps.tenants.models import School

DEMO_PASSWORD = "Demo1234!"

class Command(BaseCommand):
    help = "Crée deux établissements locaux pour tester l'isolation multi-tenant."

    @transaction.atomic
    def handle(self, *args, **options):
        demos = [
            {
                "name": "Collège Saint Joseph",
                "slug": "saint-joseph",
                "email": "director@saint-joseph.local",
                "language_mode": School.LanguageMode.FRENCH,
            },
            {
                "name": "Complexe Scolaire Excellence",
                "slug": "excellence",
                "email": "director@excellence.local",
                "language_mode": School.LanguageMode.BILINGUAL,
            },
        ]

        for data in demos:
            school, _ = School.objects.get_or_create(
                slug=data["slug"],
                defaults={
                    "name": data["name"],
                    "language_mode": data["language_mode"],
                    "education_level": School.EducationLevel.PRIMARY_SECONDARY,
                    "teaching_model": School.TeachingModel.HYBRID,
                    "city": "Yaoundé",
                    "country": "Cameroun",
                    "motto": "Excellence, discipline et réussite",
                },
            )

            user, created = User.objects.get_or_create(
                email=data["email"],
                defaults={
                    "username": data["email"],
                    "first_name": "Directeur",
                    "last_name": school.name,
                },
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()

            SchoolMembership.objects.get_or_create(
                user=user,
                school=school,
                defaults={"role": SchoolMembership.Role.DIRECTOR},
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"{school.name}: http://{school.slug}.localhost:5173"
                )
            )

        self.stdout.write("")
        self.stdout.write(f"Password commun : {DEMO_PASSWORD}")
