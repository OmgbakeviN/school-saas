import math
import random
import re
from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.academics.models import AcademicYear, Classroom, Subject
from apps.people.models import Enrollment, Guardian, Student, StudentGuardian, Teacher
from apps.tenants.models import School


DEMO_STUDENT_PREFIX = "DEMO-STU-"
DEMO_TEACHER_PREFIX = "DEMO-TCH-"
DEMO_EMAIL_DOMAIN = "demo.bewise.local"
DEMO_NOTE_MARKER = "[BEWISE_DEMO_DATA]"

FIRST_NAMES = [
    "Alain", "Amina", "Ange", "Audrey", "Boris", "Brenda", "Brice", "Carine",
    "Cédric", "Chantal", "Christian", "Clarisse", "Daniel", "Diane", "Dylan",
    "Emmanuel", "Estelle", "Fabrice", "Flore", "Francis", "Gaëlle", "Grace",
    "Hervé", "Inès", "Joël", "Jordan", "Joyce", "Junior", "Kevin", "Laura",
    "Linda", "Loïc", "Manuella", "Marc", "Marie", "Merveille", "Mickaël",
    "Nadine", "Nathan", "Noëlle", "Pascal", "Patricia", "Paul", "Prisca",
    "Raïssa", "Samuel", "Sandra", "Serge", "Stéphane", "Vanessa", "Yannick",
    "Yvan", "Ashley", "Brian", "Cynthia", "Deborah", "Elvis", "Faith",
    "Gloria", "Henry", "Irene", "Jason", "Jude", "Kelly", "Leslie", "Naomi",
    "Ruth", "Sharon", "Steve", "Victor", "Wendy",
]

SURNAMES = [
    "Abanda", "Abena", "Atangana", "Biloa", "Eboa", "Ekani", "Essomba",
    "Etoa", "Fokou", "Kamga", "Kengne", "Manga", "Mballa", "Mbarga", "Meka",
    "Mvondo", "Ndongo", "Nkom", "Nlend", "Njoya", "Ngono", "Nkoulou", "Nsom",
    "Onana", "Owona", "Tchana", "Tchoumi", "Wamba", "Zogo", "Mbianda",
    "Fouda", "Mendouga", "Nana", "Temgoua", "Fotso", "Mouafo", "Ndam",
    "Muna", "Moki", "Neba", "Nde", "Bih", "Fai", "Ngang", "Talla",
]

PARENT_FIRST_NAMES = [
    "Albert", "Alice", "André", "Anne", "Benoît", "Bernadette", "Charles",
    "Christine", "Claude", "Denis", "Dorothée", "Éric", "Evelyne", "Georges",
    "Germaine", "Henri", "Jacqueline", "Jean", "Jeanne", "Joseph", "Joséphine",
    "Luc", "Madeleine", "Marcel", "Marthe", "Michel", "Monique", "Nicolas",
    "Odette", "Pierre", "Rose", "Suzanne", "Thomas", "Thérèse", "Veronique",
    "Vincent", "Agnes", "Beatrice", "Catherine", "David", "Elizabeth", "George",
    "Helen", "James", "John", "Margaret", "Mary", "Peter", "Rebecca", "Robert",
]

OCCUPATIONS = [
    "Commerçant(e)", "Enseignant(e)", "Infirmier(ère)", "Agriculteur(trice)",
    "Entrepreneur(e)", "Fonctionnaire", "Chauffeur", "Technicien(ne)",
    "Comptable", "Informaticien(ne)", "Couturier(ère)", "Artisan(e)",
    "Agent de sécurité", "Mécanicien(ne)", "Pharmacien(ne)", "Juriste",
]

GENERIC_SPECIALITIES = [
    "Mathématiques", "Français", "English", "Sciences", "Histoire-Géographie",
    "Informatique", "Éducation physique", "Chimie", "Physique", "Biologie",
]


class Command(BaseCommand):
    help = (
        "Génère des données fictives cohérentes pour un établissement existant "
        "sans modifier sa structure académique."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--school",
            type=str,
            help="Slug de l'établissement. Facultatif s'il n'y a qu'une seule école.",
        )
        parser.add_argument("--students", type=int, default=120)
        parser.add_argument("--teachers", type=int, default=20)
        parser.add_argument(
            "--guardians",
            type=int,
            default=None,
            help="Nombre de parents/tuteurs. Par défaut: environ 80%% du nombre d'élèves.",
        )
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Supprime uniquement les données de démonstration générées et quitte.",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Supprime les anciennes données de démonstration puis en génère de nouvelles.",
        )

    def handle(self, *args, **options):
        school = self._resolve_school(options.get("school"))

        if options["students"] < 0 or options["teachers"] < 0:
            raise CommandError("Les nombres d'élèves et d'enseignants doivent être positifs.")

        guardian_count = options["guardians"]
        if guardian_count is None:
            guardian_count = max(1, round(options["students"] * 0.8)) if options["students"] else 0
        if guardian_count < 0:
            raise CommandError("Le nombre de parents/tuteurs doit être positif.")

        if options["clear"] and options["reset"]:
            raise CommandError("Utilisez --clear ou --reset, pas les deux en même temps.")

        random.seed(options["seed"])

        if options["clear"]:
            counts = self._clear_demo_data(school)
            self._print_clear_summary(school, counts)
            return

        if options["reset"]:
            counts = self._clear_demo_data(school)
            self.stdout.write(
                self.style.WARNING(
                    "Anciennes données demo supprimées: "
                    f"{counts['students']} élèves, {counts['teachers']} enseignants, "
                    f"{counts['guardians']} parents/tuteurs."
                )
            )

        if options["students"]:
            year = AcademicYear.objects.filter(school=school, is_active=True).first()
            if not year:
                raise CommandError(
                    "Aucune année scolaire active. Activez une année avant de générer les élèves."
                )

            classrooms = list(
                Classroom.objects.filter(
                    school=school,
                    academic_year=year,
                    is_active=True,
                ).select_related("level", "level__cycle", "level__cycle__section")
            )
            if not classrooms:
                raise CommandError(
                    "Aucune classe active pour l'année scolaire active. Créez les classes d'abord."
                )
        else:
            year = None
            classrooms = []

        with transaction.atomic():
            students = self._create_students(
                school=school,
                year=year,
                classrooms=classrooms,
                count=options["students"],
            )
            teachers = self._create_teachers(
                school=school,
                count=options["teachers"],
            )
            guardians = self._create_guardians(
                school=school,
                count=guardian_count,
            )
            links = self._link_families(
                school=school,
                students=students,
                guardians=guardians,
            )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Données de démonstration générées avec succès."))
        self.stdout.write(f"Établissement : {school.name} ({school.slug})")
        if year:
            self.stdout.write(f"Année active  : {year.name}")
        self.stdout.write(f"Élèves        : {len(students)}")
        self.stdout.write(f"Enseignants   : {len(teachers)}")
        self.stdout.write(f"Parents/tuteurs: {len(guardians)}")
        self.stdout.write(f"Liens familiaux: {links}")
        self.stdout.write("")
        self.stdout.write(
            "Les matricules demo commencent par DEMO-STU- et DEMO-TCH-. "
            "Les données réelles de l'école ne sont pas modifiées."
        )

    def _resolve_school(self, slug):
        if slug:
            try:
                return School.objects.get(slug=slug)
            except School.DoesNotExist as exc:
                raise CommandError(f"Établissement introuvable: {slug}") from exc

        schools = list(School.objects.all().order_by("id")[:20])
        if not schools:
            raise CommandError("Aucun établissement n'existe dans la base.")
        if len(schools) == 1:
            return schools[0]

        slugs = ", ".join(school.slug for school in schools)
        raise CommandError(
            "Plusieurs établissements existent. Précisez --school <slug>. "
            f"Exemples disponibles: {slugs}"
        )

    def _clear_demo_data(self, school):
        demo_students = Student.objects.filter(
            school=school,
            matricule__startswith=DEMO_STUDENT_PREFIX,
        )
        demo_guardians = Guardian.objects.filter(
            school=school,
            email__endswith=f"@{DEMO_EMAIL_DOMAIN}",
        )
        demo_teachers = Teacher.objects.filter(
            school=school,
            employee_number__startswith=DEMO_TEACHER_PREFIX,
        )

        student_count = demo_students.count()
        teacher_count = demo_teachers.count()
        guardian_count = demo_guardians.count()

        Enrollment.objects.filter(school=school, student__in=demo_students).delete()
        StudentGuardian.objects.filter(
            school=school,
        ).filter(
            models_q_demo_links(demo_students, demo_guardians)
        ).delete()
        demo_guardians.delete()
        demo_students.delete()
        demo_teachers.delete()

        return {
            "students": student_count,
            "teachers": teacher_count,
            "guardians": guardian_count,
        }

    def _print_clear_summary(self, school, counts):
        self.stdout.write(
            self.style.SUCCESS(
                f"Données demo supprimées pour {school.name}: "
                f"{counts['students']} élèves, {counts['teachers']} enseignants, "
                f"{counts['guardians']} parents/tuteurs."
            )
        )

    def _create_students(self, school, year, classrooms, count):
        if not count:
            return []

        start_index = self._next_numeric_suffix(
            Student.objects.filter(
                school=school,
                matricule__startswith=DEMO_STUDENT_PREFIX,
            ).values_list("matricule", flat=True),
            DEMO_STUDENT_PREFIX,
        )

        occupancy = {
            classroom.id: Enrollment.objects.filter(
                school=school,
                academic_year=year,
                classroom=classroom,
                status=Enrollment.Status.ACTIVE,
            ).count()
            for classroom in classrooms
        }

        students = []
        class_rolls = dict(occupancy)

        for offset in range(count):
            classroom = self._pick_classroom(classrooms, occupancy)
            index = start_index + offset
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(SURNAMES)
            gender = random.choice([Student.Gender.MALE, Student.Gender.FEMALE])
            birth_date = self._birth_date_for_classroom(classroom, year)

            student = Student.objects.create(
                school=school,
                matricule=f"{DEMO_STUDENT_PREFIX}{index:05d}",
                first_name=first_name,
                last_name=last_name,
                gender=gender,
                date_of_birth=birth_date,
                place_of_birth=random.choice(["Yaoundé", "Douala", "Bafoussam", "Bamenda", "Ebolowa", "Bertoua"]),
                nationality="Camerounaise",
                address=random.choice(["Yaoundé", "Douala", "Biyem-Assi", "Mendong", "Nkolbisson", "Essos", "Mvan"]),
                admission_date=year.start_date,
                status=Student.Status.ACTIVE,
                notes=DEMO_NOTE_MARKER,
            )

            occupancy[classroom.id] += 1
            class_rolls[classroom.id] += 1

            Enrollment.objects.create(
                school=school,
                student=student,
                academic_year=year,
                classroom=classroom,
                enrollment_date=year.start_date,
                roll_number=str(class_rolls[classroom.id]),
                status=Enrollment.Status.ACTIVE,
                promotion_decision=Enrollment.PromotionDecision.PENDING,
            )
            students.append(student)

        return students

    def _pick_classroom(self, classrooms, occupancy):
        available = []
        for classroom in classrooms:
            capacity = classroom.capacity
            if capacity is None or occupancy[classroom.id] < capacity:
                available.append(classroom)

        if not available:
            raise CommandError(
                "Toutes les classes ont atteint leur capacité avant la fin de la génération. "
                "Réduisez --students ou augmentez les capacités."
            )

        minimum = min(occupancy[classroom.id] for classroom in available)
        least_loaded = [
            classroom
            for classroom in available
            if occupancy[classroom.id] == minimum
        ]
        return random.choice(least_loaded)

    def _birth_date_for_classroom(self, classroom, year):
        order = max(1, classroom.level.order or 1)
        kind = classroom.level.cycle.kind

        if kind == "PRIMARY":
            age = 5 + order
        elif kind == "SECONDARY":
            age = 10 + order
        else:
            age = 8 + order

        age += random.choice([-1, 0, 0, 0, 1])
        target_year = year.start_date.year - max(4, age)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        return date(target_year, month, day)

    def _create_teachers(self, school, count):
        if not count:
            return []

        start_index = self._next_numeric_suffix(
            Teacher.objects.filter(
                school=school,
                employee_number__startswith=DEMO_TEACHER_PREFIX,
            ).values_list("employee_number", flat=True),
            DEMO_TEACHER_PREFIX,
        )

        subject_names = list(
            Subject.objects.filter(school=school, is_active=True)
            .order_by("name")
            .values_list("name", flat=True)
        )
        specialities = subject_names or GENERIC_SPECIALITIES

        teachers = []
        for offset in range(count):
            index = start_index + offset
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(SURNAMES)
            teachers.append(
                Teacher.objects.create(
                    school=school,
                    employee_number=f"{DEMO_TEACHER_PREFIX}{index:05d}",
                    first_name=first_name,
                    last_name=last_name,
                    phone=self._phone(index + 50000),
                    email=(
                        f"demo.teacher.{school.slug}.{index}@{DEMO_EMAIL_DOMAIN}"
                    ).lower(),
                    speciality=random.choice(specialities),
                    hire_date=date.today() - timedelta(days=random.randint(120, 3650)),
                    status=Teacher.Status.ACTIVE,
                    notes=DEMO_NOTE_MARKER,
                )
            )
        return teachers

    def _create_guardians(self, school, count):
        if not count:
            return []

        existing = Guardian.objects.filter(
            school=school,
            email__endswith=f"@{DEMO_EMAIL_DOMAIN}",
        ).count()
        start_index = existing + 1

        guardians = []
        for offset in range(count):
            index = start_index + offset
            guardians.append(
                Guardian.objects.create(
                    school=school,
                    first_name=random.choice(PARENT_FIRST_NAMES),
                    last_name=random.choice(SURNAMES),
                    phone=self._phone(index + 10000),
                    alternate_phone=(self._phone(index + 30000) if random.random() < 0.25 else ""),
                    email=f"demo.guardian.{school.slug}.{index}@{DEMO_EMAIL_DOMAIN}".lower(),
                    occupation=random.choice(OCCUPATIONS),
                    address=random.choice(["Yaoundé", "Douala", "Biyem-Assi", "Mendong", "Essos", "Mvan"]),
                    preferred_language=random.choice(["FR", "FR", "FR", "EN"]),
                    is_active=True,
                )
            )
        return guardians

    def _link_families(self, school, students, guardians):
        if not students or not guardians:
            return 0

        shuffled_students = students[:]
        random.shuffle(shuffled_students)

        families = []
        cursor = 0
        while cursor < len(shuffled_students):
            remaining = len(shuffled_students) - cursor
            roll = random.random()
            size = 1
            if remaining >= 3 and roll < 0.08:
                size = 3
            elif remaining >= 2 and roll < 0.35:
                size = 2
            family = shuffled_students[cursor : cursor + size]
            families.append(family)
            cursor += size

        guardian_cursor = 0
        links = 0

        # Garantit d'abord au moins un responsable par famille.
        for family_index, family in enumerate(families):
            guardian = guardians[guardian_cursor % len(guardians)]
            guardian_cursor += 1
            relationship = random.choice([
                StudentGuardian.Relationship.MOTHER,
                StudentGuardian.Relationship.FATHER,
                StudentGuardian.Relationship.GUARDIAN,
            ])
            for student in family:
                StudentGuardian.objects.create(
                    school=school,
                    student=student,
                    guardian=guardian,
                    relationship=relationship,
                    is_primary=True,
                    receives_notifications=True,
                    can_receive_results=True,
                )
                links += 1

        # Les responsables restants deviennent souvent un second parent/tuteur.
        extra_guardians = guardians[guardian_cursor:]
        for extra_index, guardian in enumerate(extra_guardians):
            family = families[extra_index % len(families)]
            relationship = random.choice([
                StudentGuardian.Relationship.MOTHER,
                StudentGuardian.Relationship.FATHER,
                StudentGuardian.Relationship.GUARDIAN,
            ])
            for student in family:
                if StudentGuardian.objects.filter(
                    school=school,
                    student=student,
                    guardian=guardian,
                ).exists():
                    continue
                StudentGuardian.objects.create(
                    school=school,
                    student=student,
                    guardian=guardian,
                    relationship=relationship,
                    is_primary=False,
                    receives_notifications=True,
                    can_receive_results=True,
                )
                links += 1

        return links

    def _phone(self, index):
        # Numéro fictif de démonstration au format camerounais.
        suffix = (70000000 + index) % 100000000
        return f"+237 6{suffix:08d}"

    def _next_numeric_suffix(self, values, prefix):
        maximum = 0
        pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
        for value in values:
            match = pattern.match(value or "")
            if match:
                maximum = max(maximum, int(match.group(1)))
        return maximum + 1


def models_q_demo_links(demo_students, demo_guardians):
    # Import local pour garder le haut du fichier centré sur les modèles métier.
    from django.db.models import Q

    return Q(student__in=demo_students) | Q(guardian__in=demo_guardians)
