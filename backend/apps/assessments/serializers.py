from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.accounts.models import SchoolMembership
from apps.accounts.permissions import get_school_membership
from apps.academics.models import AcademicPeriod
from apps.people.models import Enrollment
from apps.teaching.models import TeachingAssignment
from apps.teaching.services import (
    get_teacher_profile_for_user,
    teacher_can_enter_scores,
)

from .models import Assessment, AssessmentPeriodControl, Grade
from .services import (
    can_edit_assessment_metadata,
    can_edit_gradebook,
    can_view_assessment,
    get_period_control,
    teacher_can_work_on_assessment,
    user_is_assessment_manager,
)


class AssessmentPeriodControlSerializer(serializers.ModelSerializer):
    academic_year = serializers.IntegerField(
        source="academic_period.academic_year_id",
        read_only=True,
    )
    academic_year_name = serializers.CharField(
        source="academic_period.academic_year.name",
        read_only=True,
    )
    period_name = serializers.CharField(
        source="academic_period.name",
        read_only=True,
    )
    period_code = serializers.CharField(
        source="academic_period.code",
        read_only=True,
    )
    opened_by_email = serializers.EmailField(
        source="opened_by.email",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = AssessmentPeriodControl
        fields = [
            "id",
            "academic_period",
            "academic_year",
            "academic_year_name",
            "period_name",
            "period_code",
            "score_entry_open",
            "opened_by_email",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "academic_period",
            "academic_year",
            "academic_year_name",
            "period_name",
            "period_code",
            "opened_by_email",
            "updated_at",
        ]


class AssessmentSerializer(serializers.ModelSerializer):
    academic_year = serializers.IntegerField(
        source="teaching_assignment.academic_year_id",
        read_only=True,
    )
    academic_year_name = serializers.CharField(
        source="teaching_assignment.academic_year.name",
        read_only=True,
    )
    classroom = serializers.IntegerField(
        source="teaching_assignment.classroom_id",
        read_only=True,
    )
    classroom_name = serializers.CharField(
        source="teaching_assignment.classroom.name",
        read_only=True,
    )
    level_name = serializers.CharField(
        source="teaching_assignment.classroom.level.name",
        read_only=True,
    )
    subject = serializers.IntegerField(
        source="teaching_assignment.subject_id",
        read_only=True,
    )
    subject_name = serializers.CharField(
        source="teaching_assignment.subject.name",
        read_only=True,
    )
    teacher = serializers.IntegerField(
        source="teaching_assignment.teacher_id",
        read_only=True,
    )
    teacher_name = serializers.SerializerMethodField()
    period_name = serializers.CharField(
        source="academic_period.name",
        read_only=True,
    )
    period_entry_open = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_enter_grades = serializers.SerializerMethodField()
    grade_count = serializers.IntegerField(source="grades.count", read_only=True)

    class Meta:
        model = Assessment
        fields = [
            "id",
            "teaching_assignment",
            "academic_period",
            "period_name",
            "period_entry_open",
            "academic_year",
            "academic_year_name",
            "classroom",
            "classroom_name",
            "level_name",
            "subject",
            "subject_name",
            "teacher",
            "teacher_name",
            "title",
            "kind",
            "assessment_date",
            "max_score",
            "weight",
            "instructions",
            "status",
            "can_edit",
            "can_enter_grades",
            "grade_count",
            "submitted_at",
            "validated_at",
            "published_at",
            "reopened_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "submitted_at",
            "validated_at",
            "published_at",
            "reopened_at",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(serializers.CharField())
    def get_teacher_name(self, obj):
        teacher = obj.teaching_assignment.teacher
        return f"{teacher.last_name} {teacher.first_name}".strip()

    @extend_schema_field(serializers.BooleanField())
    def get_period_entry_open(self, obj):
        request = self.context.get("request")
        if not request:
            return False
        control = get_period_control(
            school=request.school,
            academic_period=obj.academic_period,
        )
        return control.score_entry_open

    @extend_schema_field(serializers.BooleanField())
    def get_can_edit(self, obj):
        request = self.context.get("request")
        return bool(
            request
            and can_edit_assessment_metadata(
                request=request,
                assessment=obj,
            )
        )

    @extend_schema_field(serializers.BooleanField())
    def get_can_enter_grades(self, obj):
        request = self.context.get("request")
        return bool(
            request
            and can_edit_gradebook(
                request=request,
                assessment=obj,
            )
        )

    def validate_teaching_assignment(self, assignment):
        request = self.context["request"]
        if assignment.school_id != request.school.id:
            raise serializers.ValidationError(
                "Cette affectation n'appartient pas à votre établissement."
            )
        return assignment

    def validate_academic_period(self, period):
        request = self.context["request"]
        if period.school_id != request.school.id:
            raise serializers.ValidationError(
                "Cette période n'appartient pas à votre établissement."
            )
        return period

    def validate(self, attrs):
        request = self.context["request"]
        assignment = attrs.get(
            "teaching_assignment",
            getattr(self.instance, "teaching_assignment", None),
        )
        period = attrs.get(
            "academic_period",
            getattr(self.instance, "academic_period", None),
        )

        if assignment and period and assignment.academic_year_id != period.academic_year_id:
            raise serializers.ValidationError({
                "academic_period": (
                    "La période doit appartenir à l'année scolaire de l'affectation."
                )
            })

        max_score = attrs.get(
            "max_score",
            getattr(self.instance, "max_score", None),
        )
        if max_score is not None and max_score <= 0:
            raise serializers.ValidationError({
                "max_score": "La note maximale doit être supérieure à zéro."
            })

        weight = attrs.get("weight", getattr(self.instance, "weight", None))
        if weight is not None and weight <= 0:
            raise serializers.ValidationError({
                "weight": "Le poids doit être supérieur à zéro."
            })

        membership = get_school_membership(request)
        if membership and membership.role == SchoolMembership.Role.TEACHER:
            teacher = get_teacher_profile_for_user(
                user=request.user,
                school=request.school,
            )
            if not teacher or not assignment or assignment.teacher_id != teacher.id:
                raise serializers.ValidationError({
                    "teaching_assignment": "Cette affectation ne vous appartient pas."
                })

            if not teacher_can_enter_scores(
                user=request.user,
                school=request.school,
                academic_year_id=assignment.academic_year_id,
                classroom_id=assignment.classroom_id,
                subject_id=assignment.subject_id,
            ):
                raise serializers.ValidationError({
                    "teaching_assignment": (
                        "Vous n'êtes pas autorisé à saisir les notes de cette "
                        "matière dans cette classe."
                    )
                })

        if self.instance:
            if not can_edit_assessment_metadata(
                request=request,
                assessment=self.instance,
            ):
                raise serializers.ValidationError(
                    "Cette évaluation est verrouillée dans son état actuel."
                )

            if self.instance.grades.exists():
                protected = {
                    "teaching_assignment",
                    "academic_period",
                    "max_score",
                }
                changed = [
                    field
                    for field in protected
                    if field in attrs
                    and attrs[field] != getattr(self.instance, field)
                ]
                if changed:
                    raise serializers.ValidationError(
                        "L'affectation, la période et le barème ne peuvent plus être modifiés après la première saisie."
                    )

        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        assessment = Assessment(
            school=request.school,
            created_by=request.user,
            **validated_data,
        )
        try:
            assessment.full_clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)
        assessment.save()
        return assessment

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        try:
            instance.full_clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)
        instance.save()
        return instance


class GradeReadSerializer(serializers.ModelSerializer):
    enrollment_id = serializers.IntegerField(source="enrollment.id", read_only=True)
    student_id = serializers.IntegerField(source="enrollment.student_id", read_only=True)
    student_matricule = serializers.CharField(
        source="enrollment.student.matricule",
        read_only=True,
    )
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = Grade
        fields = [
            "id",
            "enrollment_id",
            "student_id",
            "student_matricule",
            "student_name",
            "score",
            "is_absent",
            "is_exempt",
            "comment",
            "updated_at",
        ]

    @extend_schema_field(serializers.CharField())
    def get_student_name(self, obj):
        student = obj.enrollment.student
        return f"{student.last_name} {student.first_name}".strip()


class GradeBulkItemSerializer(serializers.Serializer):
    enrollment = serializers.IntegerField(min_value=1)
    score = serializers.DecimalField(
        max_digits=7,
        decimal_places=3,
        required=False,
        allow_null=True,
    )
    is_absent = serializers.BooleanField(default=False)
    is_exempt = serializers.BooleanField(default=False)
    comment = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default="",
    )

    def validate(self, attrs):
        if attrs.get("is_absent") and attrs.get("is_exempt"):
            raise serializers.ValidationError(
                "Une note ne peut pas être à la fois ABS et dispensée."
            )
        if attrs.get("is_absent") or attrs.get("is_exempt"):
            attrs["score"] = None
        return attrs


class GradeBulkRequestSerializer(serializers.Serializer):
    grades = GradeBulkItemSerializer(many=True, allow_empty=False)


class GradebookRowSerializer(serializers.Serializer):
    enrollment_id = serializers.IntegerField()
    student_id = serializers.IntegerField()
    matricule = serializers.CharField()
    student_name = serializers.CharField()
    score = serializers.DecimalField(
        max_digits=7,
        decimal_places=3,
        allow_null=True,
    )
    is_absent = serializers.BooleanField()
    is_exempt = serializers.BooleanField()
    comment = serializers.CharField(allow_blank=True)


class GradebookSerializer(serializers.Serializer):
    assessment = AssessmentSerializer()
    can_edit = serializers.BooleanField()
    rows = GradebookRowSerializer(many=True)


class AssessmentActionResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.CharField()
    detail = serializers.CharField()


class PeriodSubjectResultSerializer(serializers.Serializer):
    subject_id = serializers.IntegerField()
    subject_name = serializers.CharField()
    average = serializers.DecimalField(max_digits=7, decimal_places=3)
    max_score = serializers.DecimalField(max_digits=7, decimal_places=2)
    coefficient = serializers.DecimalField(max_digits=7, decimal_places=3)
    assessment_count = serializers.IntegerField()


class StudentPeriodResultSerializer(serializers.Serializer):
    enrollment_id = serializers.IntegerField()
    student_id = serializers.IntegerField()
    matricule = serializers.CharField()
    student_name = serializers.CharField()
    subjects = PeriodSubjectResultSerializer(many=True)
    overall_average = serializers.DecimalField(
        max_digits=7,
        decimal_places=3,
        allow_null=True,
    )


class ClassroomPeriodResultSerializer(serializers.Serializer):
    classroom_id = serializers.IntegerField()
    classroom_name = serializers.CharField()
    period_id = serializers.IntegerField()
    period_name = serializers.CharField()
    students = StudentPeriodResultSerializer(many=True)


class RecalculateYearResultSerializer(serializers.Serializer):
    updated = serializers.IntegerField()
    with_average = serializers.IntegerField()
