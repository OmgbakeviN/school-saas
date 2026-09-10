from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.accounts.models import SchoolMembership, User
from apps.academics.models import AcademicYear, Classroom, LevelSubject, Subject
from apps.people.models import Teacher

from .models import ClassroomLeadership, TeachingAssignment
from .services import sync_classroom_class_teacher_assignments


class TenantSerializerMixin:
    def get_school(self):
        return self.context["request"].school


class TeachingAssignmentSerializer(TenantSerializerMixin, serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()
    teacher_employee_number = serializers.CharField(
        source="teacher.employee_number",
        read_only=True,
    )
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    classroom_name = serializers.CharField(source="classroom.name", read_only=True)
    level_name = serializers.CharField(source="classroom.level.name", read_only=True)
    cycle_name = serializers.CharField(source="classroom.level.cycle.name", read_only=True)
    section_name = serializers.CharField(
        source="classroom.level.cycle.section.name",
        read_only=True,
    )
    academic_year_name = serializers.CharField(
        source="academic_year.name",
        read_only=True,
    )
    source_label = serializers.CharField(
        source="get_source_display",
        read_only=True,
    )
    is_automatic = serializers.SerializerMethodField()

    class Meta:
        model = TeachingAssignment
        fields = [
            "id",
            "academic_year",
            "academic_year_name",
            "teacher",
            "teacher_name",
            "teacher_employee_number",
            "subject",
            "subject_name",
            "classroom",
            "classroom_name",
            "level_name",
            "cycle_name",
            "section_name",
            "source",
            "source_label",
            "is_automatic",
            "can_enter_scores",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = (
            "source",
            "source_label",
            "is_automatic",
            "created_at",
            "updated_at",
        )

    @extend_schema_field(serializers.BooleanField())
    def get_is_automatic(self, obj):
        return obj.source == TeachingAssignment.Source.CLASS_TEACHER_AUTO

    @extend_schema_field(serializers.CharField())
    def get_teacher_name(self, obj):
        return f"{obj.teacher.last_name} {obj.teacher.first_name}".strip()

    def validate_academic_year(self, academic_year):
        if academic_year.school_id != self.get_school().id:
            raise serializers.ValidationError(
                "Cette année scolaire n'appartient pas à votre établissement."
            )
        return academic_year

    def validate_teacher(self, teacher):
        if teacher.school_id != self.get_school().id:
            raise serializers.ValidationError(
                "Cet enseignant n'appartient pas à votre établissement."
            )
        if teacher.status != Teacher.Status.ACTIVE:
            raise serializers.ValidationError(
                "Cet enseignant est inactif."
            )
        return teacher

    def validate_subject(self, subject):
        if subject.school_id != self.get_school().id:
            raise serializers.ValidationError(
                "Cette matière n'appartient pas à votre établissement."
            )
        return subject

    def validate_classroom(self, classroom):
        if classroom.school_id != self.get_school().id:
            raise serializers.ValidationError(
                "Cette classe n'appartient pas à votre établissement."
            )
        return classroom

    def validate(self, attrs):
        school = self.get_school()
        if (
            self.instance
            and self.instance.source
            == TeachingAssignment.Source.CLASS_TEACHER_AUTO
        ):
            raise serializers.ValidationError(
                "Cette affectation est gérée automatiquement par le titulaire "
                "de classe. Modifiez plutôt le titulaire ou le programme du niveau."
            )
        year = attrs.get("academic_year", getattr(self.instance, "academic_year", None))
        teacher = attrs.get("teacher", getattr(self.instance, "teacher", None))
        subject = attrs.get("subject", getattr(self.instance, "subject", None))
        classroom = attrs.get("classroom", getattr(self.instance, "classroom", None))

        if classroom and year and classroom.academic_year_id != year.id:
            raise serializers.ValidationError({
                "classroom": "La classe doit appartenir à l'année scolaire sélectionnée."
            })

        if classroom and subject:
            allowed = LevelSubject.objects.filter(
                school=school,
                level=classroom.level,
                subject=subject,
                is_active=True,
            ).exists()
            if not allowed:
                raise serializers.ValidationError({
                    "subject": (
                        "Cette matière n'est pas configurée dans le programme "
                        "du niveau de cette classe."
                    )
                })

        if year and teacher and subject and classroom:
            duplicate = TeachingAssignment.objects.filter(
                school=school,
                academic_year=year,
                teacher=teacher,
                subject=subject,
                classroom=classroom,
            )
            if self.instance:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise serializers.ValidationError(
                    "Cette affectation pédagogique existe déjà."
                )

        return attrs

    def create(self, validated_data):
        return TeachingAssignment.objects.create(
            school=self.get_school(),
            source=TeachingAssignment.Source.MANUAL,
            **validated_data,
        )


class ClassroomLeadershipSerializer(TenantSerializerMixin, serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()
    classroom_name = serializers.CharField(source="classroom.name", read_only=True)
    level_name = serializers.CharField(source="classroom.level.name", read_only=True)
    academic_year_name = serializers.CharField(
        source="academic_year.name",
        read_only=True,
    )
    role_label = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = ClassroomLeadership
        fields = [
            "id",
            "academic_year",
            "academic_year_name",
            "classroom",
            "classroom_name",
            "level_name",
            "teacher",
            "teacher_name",
            "role",
            "role_label",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("created_at", "updated_at")

    @extend_schema_field(serializers.CharField())
    def get_teacher_name(self, obj):
        return f"{obj.teacher.last_name} {obj.teacher.first_name}".strip()

    def validate(self, attrs):
        school = self.get_school()
        year = attrs.get("academic_year", getattr(self.instance, "academic_year", None))
        classroom = attrs.get("classroom", getattr(self.instance, "classroom", None))
        teacher = attrs.get("teacher", getattr(self.instance, "teacher", None))
        role = attrs.get("role", getattr(self.instance, "role", None))
        is_active = attrs.get("is_active", getattr(self.instance, "is_active", True))

        for name, obj in (
            ("academic_year", year),
            ("classroom", classroom),
            ("teacher", teacher),
        ):
            if obj and obj.school_id != school.id:
                raise serializers.ValidationError({
                    name: "Cet élément n'appartient pas à votre établissement."
                })

        if teacher and teacher.status != Teacher.Status.ACTIVE:
            raise serializers.ValidationError({"teacher": "Cet enseignant est inactif."})

        if classroom and year and classroom.academic_year_id != year.id:
            raise serializers.ValidationError({
                "classroom": "La classe doit appartenir à l'année scolaire sélectionnée."
            })

        if year and classroom and role and is_active:
            duplicate = ClassroomLeadership.objects.filter(
                school=school,
                academic_year=year,
                classroom=classroom,
                role=role,
                is_active=True,
            )
            if self.instance:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise serializers.ValidationError({
                    "role": (
                        "Un responsable actif de ce type existe déjà pour cette classe."
                    )
                })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        leadership = ClassroomLeadership.objects.create(
            school=self.get_school(),
            **validated_data,
        )
        sync_classroom_class_teacher_assignments(
            school=leadership.school,
            academic_year_id=leadership.academic_year_id,
            classroom_id=leadership.classroom_id,
        )
        return leadership

    @transaction.atomic
    def update(self, instance, validated_data):
        old_context = (
            instance.academic_year_id,
            instance.classroom_id,
        )
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        sync_classroom_class_teacher_assignments(
            school=instance.school,
            academic_year_id=old_context[0],
            classroom_id=old_context[1],
        )
        if old_context != (
            instance.academic_year_id,
            instance.classroom_id,
        ):
            sync_classroom_class_teacher_assignments(
                school=instance.school,
                academic_year_id=instance.academic_year_id,
                classroom_id=instance.classroom_id,
            )
        return instance


class TeacherAccountProvisionSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        min_length=8,
        write_only=True,
        required=False,
        allow_blank=False,
    )

    def validate_email(self, value):
        return value.strip().lower()

    def validate(self, attrs):
        teacher = self.context["teacher"]
        school = self.context["request"].school

        if teacher.school_id != school.id:
            raise serializers.ValidationError(
                "Cet enseignant n'appartient pas à votre établissement."
            )

        if teacher.user_id:
            raise serializers.ValidationError(
                "Ce profil enseignant possède déjà un compte de connexion."
            )

        user = User.objects.filter(email=attrs["email"]).first()
        attrs["existing_user"] = user

        if not user and not attrs.get("password"):
            raise serializers.ValidationError({
                "password": "Un mot de passe initial est obligatoire pour un nouveau compte."
            })

        if user:
            membership = SchoolMembership.objects.filter(
                school=school,
                user=user,
            ).first()

            if membership and membership.role != SchoolMembership.Role.TEACHER:
                raise serializers.ValidationError({
                    "email": (
                        "Ce compte appartient déjà à l'établissement avec un autre rôle."
                    )
                })

            if Teacher.objects.filter(
                school=school,
                user=user,
            ).exclude(pk=teacher.pk).exists():
                raise serializers.ValidationError({
                    "email": "Ce compte est déjà lié à un autre enseignant."
                })

        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        teacher = self.context["teacher"]
        school = self.context["request"].school
        email = self.validated_data["email"]
        user = self.validated_data.get("existing_user")
        created_user = False
        created_membership = False

        if not user:
            user = User.objects.create_user(
                email=email,
                password=self.validated_data["password"],
                first_name=teacher.first_name,
                last_name=teacher.last_name,
            )
            created_user = True

        membership, created_membership = SchoolMembership.objects.get_or_create(
            school=school,
            user=user,
            defaults={
                "role": SchoolMembership.Role.TEACHER,
                "is_active": True,
            },
        )

        if membership.role != SchoolMembership.Role.TEACHER:
            raise serializers.ValidationError(
                "Le compte lié doit avoir le rôle Enseignant."
            )

        if not membership.is_active:
            membership.is_active = True
            membership.save(update_fields=["is_active"])

        teacher.user = user
        if not teacher.email:
            teacher.email = email
        teacher.save(update_fields=["user", "email", "updated_at"])

        return {
            "teacher": teacher,
            "user": user,
            "membership": membership,
            "created_user": created_user,
            "created_membership": created_membership,
        }


class TeacherAccountResultSerializer(serializers.Serializer):
    teacher_id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    role = serializers.CharField()
    created_user = serializers.BooleanField()
    created_membership = serializers.BooleanField()


class MyTeachingAccessSerializer(serializers.Serializer):
    teacher = serializers.DictField(allow_null=True)
    assignments = TeachingAssignmentSerializer(many=True)
    leaderships = ClassroomLeadershipSerializer(many=True)
