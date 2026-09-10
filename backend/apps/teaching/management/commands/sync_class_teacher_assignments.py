from django.core.management.base import BaseCommand, CommandError

from apps.tenants.models import School
from apps.teaching.services import sync_school_class_teacher_assignments


class Command(BaseCommand):
    help = (
        "Synchronise les affectations automatiques des titulaires de classe "
        "avec les matières actives du programme."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--school",
            dest="school_slug",
            help="Slug d'un établissement. Sans option, toutes les écoles sont synchronisées.",
        )

    def handle(self, *args, **options):
        schools = School.objects.all().order_by("id")

        if options.get("school_slug"):
            schools = schools.filter(slug=options["school_slug"])
            if not schools.exists():
                raise CommandError("Établissement introuvable.")

        total_created = 0
        total_reactivated = 0
        total_disabled = 0

        for school in schools:
            result = sync_school_class_teacher_assignments(
                school=school,
            )
            total_created += result["created"]
            total_reactivated += result["reactivated"]
            total_disabled += result["disabled"]

            self.stdout.write(
                f"{school.slug}: "
                f"{result['created']} créée(s), "
                f"{result['reactivated']} réactivée(s), "
                f"{result['disabled']} désactivée(s)"
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Synchronisation terminée — "
                f"{total_created} créée(s), "
                f"{total_reactivated} réactivée(s), "
                f"{total_disabled} désactivée(s)."
            )
        )
