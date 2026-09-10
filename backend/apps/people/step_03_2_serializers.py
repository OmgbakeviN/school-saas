from rest_framework import serializers

from apps.academics.models import AcademicYear, Classroom
from .models import Enrollment


class PeopleImportRequestSerializer(serializers.Serializer):
    file = serializers.FileField()
    dry_run = serializers.BooleanField(default=False)
    academic_year = serializers.IntegerField(required=False, allow_null=True)
    classroom = serializers.IntegerField(required=False, allow_null=True)


class ImportRowErrorSerializer(serializers.Serializer):
    row = serializers.IntegerField()
    message = serializers.CharField()


class PeopleImportResultSerializer(serializers.Serializer):
    entity = serializers.CharField()
    dry_run = serializers.BooleanField()
    total_rows = serializers.IntegerField()
    created = serializers.IntegerField()
    updated = serializers.IntegerField()
    enrolled = serializers.IntegerField()
    errors = ImportRowErrorSerializer(many=True)


class BulkClassAssignmentRequestSerializer(serializers.Serializer):
    student_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )
    academic_year = serializers.IntegerField(min_value=1)
    classroom = serializers.IntegerField(min_value=1)
    enrollment_date = serializers.DateField(required=False, allow_null=True)


class BulkClassAssignmentResultSerializer(serializers.Serializer):
    created = serializers.IntegerField()
    updated = serializers.IntegerField()
    total = serializers.IntegerField()


class PromotionPreviewRequestSerializer(serializers.Serializer):
    academic_year = serializers.IntegerField(min_value=1)
    classroom = serializers.IntegerField(
        min_value=1,
        required=False,
        allow_null=True,
    )


class PromotionPreviewItemSerializer(serializers.Serializer):
    enrollment_id = serializers.IntegerField()
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    matricule = serializers.CharField()
    classroom_id = serializers.IntegerField()
    classroom_name = serializers.CharField()
    level_id = serializers.IntegerField()
    level_name = serializers.CharField()
    final_average = serializers.DecimalField(
        max_digits=7,
        decimal_places=3,
        allow_null=True,
    )
    threshold = serializers.DecimalField(
        max_digits=7,
        decimal_places=2,
    )
    suggested_decision = serializers.CharField()


class PromotionPreviewResultSerializer(serializers.Serializer):
    academic_year = serializers.IntegerField()
    count = serializers.IntegerField()
    items = PromotionPreviewItemSerializer(many=True)


class PromotionItemSerializer(serializers.Serializer):
    enrollment_id = serializers.IntegerField(min_value=1)
    decision = serializers.ChoiceField(
        choices=[
            Enrollment.PromotionDecision.PROMOTED,
            Enrollment.PromotionDecision.REPEATED,
            Enrollment.PromotionDecision.GRADUATED,
            Enrollment.PromotionDecision.TRANSFERRED,
            Enrollment.PromotionDecision.WITHDRAWN,
        ]
    )
    target_classroom = serializers.IntegerField(
        min_value=1,
        required=False,
        allow_null=True,
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )


class ApplyPromotionRequestSerializer(serializers.Serializer):
    items = PromotionItemSerializer(many=True, allow_empty=False)


class ApplyPromotionResultSerializer(serializers.Serializer):
    processed = serializers.IntegerField()
    promoted = serializers.IntegerField()
    repeated = serializers.IntegerField()
    graduated = serializers.IntegerField()
    transferred = serializers.IntegerField()
    withdrawn = serializers.IntegerField()
    next_enrollments_created = serializers.IntegerField()
    next_enrollments_updated = serializers.IntegerField()


class ReEnrollRepeatersRequestSerializer(serializers.Serializer):
    enrollment_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )
    target_classroom = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )


class ExitStudentsRequestSerializer(serializers.Serializer):
    enrollment_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )
    action = serializers.ChoiceField(
        choices=[
            Enrollment.PromotionDecision.TRANSFERRED,
            Enrollment.PromotionDecision.WITHDRAWN,
        ]
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )


class ActionResultSerializer(serializers.Serializer):
    processed = serializers.IntegerField()


class PrepareAcademicYearRequestSerializer(serializers.Serializer):
    source_academic_year = serializers.IntegerField(min_value=1)
    name = serializers.CharField(max_length=30)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    period_system = serializers.ChoiceField(
        choices=AcademicYear.PeriodSystem.choices,
        required=False,
    )
    is_active = serializers.BooleanField(default=False)
    clone_classrooms = serializers.BooleanField(default=True)
    clone_periods = serializers.BooleanField(default=True)

    def validate(self, attrs):
        if attrs["start_date"] >= attrs["end_date"]:
            raise serializers.ValidationError({
                "end_date": "La date de fin doit être postérieure à la date de début."
            })
        return attrs


class PrepareAcademicYearResultSerializer(serializers.Serializer):
    academic_year_id = serializers.IntegerField()
    academic_year_name = serializers.CharField()
    classrooms_created = serializers.IntegerField()
    periods_created = serializers.IntegerField()


class ExportQuerySerializer(serializers.Serializer):
    format = serializers.ChoiceField(
        choices=["csv", "xlsx"],
        default="csv",
    )
    academic_year = serializers.IntegerField(
        required=False,
        allow_null=True,
    )
    classroom = serializers.IntegerField(
        required=False,
        allow_null=True,
    )
