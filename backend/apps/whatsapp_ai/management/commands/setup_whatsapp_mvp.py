from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from django.utils import timezone

from apps.people.models import Guardian, StudentGuardian
from apps.tenants.models import School

from apps.whatsapp_ai.models import (
    GuardianWhatsAppIdentity,
    StudentGuardianDocumentPermission,
    WhatsAppConnection,
)
from apps.whatsapp_ai.phone import normalize_phone


class Command(BaseCommand):
    help = (
        "Configure l'instance WhatsApp d'un établissement et initialise "
        "les identités parents pour le MVP IA."
    )

    def add_arguments(self, parser):
        parser.add_argument("--school", required=True, help="Slug de l'établissement")
        parser.add_argument("--instance", required=True, help="Nom de l'instance Evolution API")
        parser.add_argument("--phone-number", default="", help="Numéro WhatsApp de l'établissement")
        parser.add_argument(
            "--verify-guardians",
            action="store_true",
            help="Marque les numéros parents existants comme vérifiés pour les tests.",
        )
        parser.add_argument(
            "--enable-finance",
            action="store_true",
            help="Autorise la facture de pension pour les liens parent/élève existants.",
        )

    def handle(self, *args, **options):
        try:
            school = School.objects.get(slug=options["school"])
        except School.DoesNotExist as exc:
            raise CommandError("Établissement introuvable.") from exc

        connection, created = WhatsAppConnection.objects.update_or_create(
            school=school,
            defaults={
                "instance_name": options["instance"],
                "phone_number": options["phone_number"],
                "is_active": True,
            },
        )

        identity_created = 0
        identity_updated = 0
        skipped = []

        for guardian in Guardian.objects.filter(school=school, is_active=True):
            normalized = normalize_phone(guardian.phone)
            if not normalized:
                skipped.append(f"{guardian}: numéro vide/invalide")
                continue

            try:
                identity, was_created = GuardianWhatsAppIdentity.objects.get_or_create(
                    school=school,
                    guardian=guardian,
                    defaults={
                        "normalized_phone": normalized,
                        "phone_verified": options["verify_guardians"],
                        "whatsapp_enabled": True,
                        "verified_at": (
                            timezone.now() if options["verify_guardians"] else None
                        ),
                    },
                )
            except IntegrityError:
                skipped.append(
                    f"{guardian}: le numéro {normalized} est déjà utilisé par un autre parent"
                )
                continue

            changed = False
            if identity.normalized_phone != normalized:
                identity.normalized_phone = normalized
                changed = True
            if not identity.whatsapp_enabled:
                identity.whatsapp_enabled = True
                changed = True
            if options["verify_guardians"] and not identity.phone_verified:
                identity.phone_verified = True
                identity.verified_at = timezone.now()
                changed = True

            if changed:
                try:
                    identity.save()
                except IntegrityError:
                    skipped.append(
                        f"{guardian}: conflit sur le numéro {normalized}"
                    )
                    continue

            if was_created:
                identity_created += 1
            else:
                identity_updated += 1

        permission_count = 0
        for link in StudentGuardian.objects.filter(school=school):
            permission, _ = StudentGuardianDocumentPermission.objects.get_or_create(
                school=school,
                student_guardian=link,
                defaults={
                    "can_receive_report_cards": bool(link.can_receive_results),
                    "can_receive_finance": bool(options["enable_finance"]),
                },
            )
            changed = False
            if permission.can_receive_report_cards != bool(link.can_receive_results):
                permission.can_receive_report_cards = bool(link.can_receive_results)
                changed = True
            if options["enable_finance"] and not permission.can_receive_finance:
                permission.can_receive_finance = True
                changed = True
            if changed:
                permission.save()
            permission_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"WhatsApp MVP configuré pour {school.name}."
        ))
        self.stdout.write(
            f"Instance: {connection.instance_name} ({'créée' if created else 'mise à jour'})"
        )
        self.stdout.write(
            f"Identités: {identity_created} créée(s), {identity_updated} existante(s)."
        )
        self.stdout.write(f"Permissions parent/élève: {permission_count}.")
        if options["verify_guardians"]:
            self.stdout.write(self.style.WARNING(
                "Les numéros ont été marqués vérifiés. Utiliser uniquement pour un environnement de test ou après vérification réelle."
            ))
        if skipped:
            self.stdout.write(self.style.WARNING("Éléments ignorés:"))
            for item in skipped:
                self.stdout.write(f" - {item}")
