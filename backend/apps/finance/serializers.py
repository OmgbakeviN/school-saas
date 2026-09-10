from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from apps.academics.models import AcademicYear, Classroom, Level
from apps.people.models import Enrollment

from .models import (
    PaymentAllocation,
    PaymentReceiptSnapshot,
    StudentTuitionAccount,
    TuitionInstallment,
    TuitionPayment,
    TuitionPlan,
)


class TuitionInstallmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TuitionInstallment
        fields = (
            "id",
            "name",
            "amount",
            "due_date",
            "order",
            "is_active",
        )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Le montant doit être supérieur à zéro."
            )
        return value


class TuitionPlanSerializer(serializers.ModelSerializer):
    academic_year_name = serializers.CharField(
        source="academic_year.name",
        read_only=True,
    )
    level_name = serializers.CharField(
        source="level.name",
        read_only=True,
        allow_null=True,
    )
    classroom_name = serializers.CharField(
        source="classroom.name",
        read_only=True,
        allow_null=True,
    )
    installments = TuitionInstallmentSerializer(
        many=True,
        read_only=True,
    )
    total_amount = serializers.SerializerMethodField()
    assigned_accounts_count = serializers.IntegerField(
        source="student_accounts.count",
        read_only=True,
    )

    class Meta:
        model = TuitionPlan
        fields = (
            "id",
            "academic_year",
            "academic_year_name",
            "name",
            "currency",
            "level",
            "level_name",
            "classroom",
            "classroom_name",
            "is_active",
            "notes",
            "installments",
            "total_amount",
            "assigned_accounts_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "created_at",
            "updated_at",
        )

    def get_total_amount(self, obj):
        value = (
            obj.installments
            .filter(is_active=True)
            .aggregate(total=Sum("amount"))
            .get("total")
        )
        return value or Decimal("0")

    def validate(self, attrs):
        request = self.context["request"]
        school = request.school

        year = attrs.get(
            "academic_year",
            getattr(self.instance, "academic_year", None),
        )
        level = attrs.get(
            "level",
            getattr(self.instance, "level", None),
        )
        classroom = attrs.get(
            "classroom",
            getattr(self.instance, "classroom", None),
        )

        if year and year.school_id != school.id:
            raise serializers.ValidationError({
                "academic_year": "Cette année n'appartient pas à l'établissement."
            })

        if level and level.school_id != school.id:
            raise serializers.ValidationError({
                "level": "Ce niveau n'appartient pas à l'établissement."
            })

        if classroom:
            if classroom.school_id != school.id:
                raise serializers.ValidationError({
                    "classroom": "Cette classe n'appartient pas à l'établissement."
                })
            if year and classroom.academic_year_id != year.id:
                raise serializers.ValidationError({
                    "classroom": (
                        "La classe doit appartenir à l'année scolaire du plan."
                    )
                })

        if level and classroom:
            raise serializers.ValidationError(
                "Choisissez soit un niveau, soit une classe."
            )

        return attrs

    def create(self, validated_data):
        return TuitionPlan.objects.create(
            school=self.context["request"].school,
            **validated_data,
        )


class StudentTuitionAccountSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(
        source="enrollment.student_id",
        read_only=True,
    )
    student_name = serializers.SerializerMethodField()
    matricule = serializers.CharField(
        source="enrollment.student.matricule",
        read_only=True,
    )
    classroom_id = serializers.IntegerField(
        source="enrollment.classroom_id",
        read_only=True,
    )
    classroom_name = serializers.CharField(
        source="enrollment.classroom.name",
        read_only=True,
    )
    academic_year_id = serializers.IntegerField(
        source="enrollment.academic_year_id",
        read_only=True,
    )
    academic_year_name = serializers.CharField(
        source="enrollment.academic_year.name",
        read_only=True,
    )
    plan_name = serializers.CharField(
        source="plan.name",
        read_only=True,
    )
    currency = serializers.CharField(
        source="plan.currency",
        read_only=True,
    )
    expected_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    paid_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    balance = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    payment_status = serializers.CharField(read_only=True)
    installments = serializers.ListField(
        child=serializers.DictField(),
        read_only=True,
    )

    class Meta:
        model = StudentTuitionAccount
        fields = (
            "id",
            "enrollment",
            "student_id",
            "student_name",
            "matricule",
            "classroom_id",
            "classroom_name",
            "academic_year_id",
            "academic_year_name",
            "plan",
            "plan_name",
            "currency",
            "expected_amount",
            "paid_amount",
            "balance",
            "payment_status",
            "installments",
            "notes",
            "created_at",
        )
        read_only_fields = (
            "enrollment",
            "plan",
            "created_at",
        )

    def get_student_name(self, obj):
        return (
            f"{obj.enrollment.student.last_name} "
            f"{obj.enrollment.student.first_name}"
        ).strip()


class BulkAssignPlanSerializer(serializers.Serializer):
    plan = serializers.IntegerField(min_value=1)


class RecordPaymentSerializer(serializers.Serializer):
    tuition_account = serializers.IntegerField(min_value=1)
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("1"),
    )
    method = serializers.ChoiceField(
        choices=TuitionPayment.Method.choices,
        default=TuitionPayment.Method.CASH,
    )
    reference = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=120,
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
    )
    paid_at = serializers.DateTimeField(required=False)


class PaymentAllocationSerializer(serializers.ModelSerializer):
    installment_name = serializers.CharField(
        source="installment.name",
        read_only=True,
    )

    class Meta:
        model = PaymentAllocation
        fields = (
            "installment",
            "installment_name",
            "amount",
        )


class TuitionPaymentSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(
        source="tuition_account.enrollment.student_id",
        read_only=True,
    )
    student_name = serializers.SerializerMethodField()
    matricule = serializers.CharField(
        source="tuition_account.enrollment.student.matricule",
        read_only=True,
    )
    classroom_name = serializers.CharField(
        source="tuition_account.enrollment.classroom.name",
        read_only=True,
    )
    academic_year_name = serializers.CharField(
        source="tuition_account.enrollment.academic_year.name",
        read_only=True,
    )
    currency = serializers.CharField(
        source="tuition_account.plan.currency",
        read_only=True,
    )
    method_label = serializers.CharField(
        source="get_method_display",
        read_only=True,
    )
    allocations = PaymentAllocationSerializer(
        many=True,
        read_only=True,
    )
    receipt_url = serializers.SerializerMethodField()
    received_by_name = serializers.SerializerMethodField()

    class Meta:
        model = TuitionPayment
        fields = (
            "id",
            "receipt_number",
            "tuition_account",
            "student_id",
            "student_name",
            "matricule",
            "classroom_name",
            "academic_year_name",
            "currency",
            "amount",
            "method",
            "method_label",
            "reference",
            "notes",
            "paid_at",
            "received_by_name",
            "allocations",
            "receipt_url",
            "created_at",
        )

    def get_student_name(self, obj):
        student = obj.tuition_account.enrollment.student
        return f"{student.last_name} {student.first_name}".strip()

    def get_received_by_name(self, obj):
        name = obj.received_by.get_full_name().strip()
        return name or obj.received_by.email

    def get_receipt_url(self, obj):
        request = self.context.get("request")
        path = f"/api/finance/payments/{obj.id}/receipt/"
        return request.build_absolute_uri(path) if request else path


class RecordPaymentResultSerializer(serializers.Serializer):
    payment = TuitionPaymentSerializer()
    account = StudentTuitionAccountSerializer()


class FinanceDashboardSerializer(serializers.Serializer):
    academic_year = serializers.IntegerField(allow_null=True)
    expected_total = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    collected_total = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    outstanding_total = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )
    collection_rate = serializers.DecimalField(
        max_digits=7,
        decimal_places=2,
    )
    accounts_count = serializers.IntegerField()
    paid_count = serializers.IntegerField()
    partial_count = serializers.IntegerField()
    unpaid_count = serializers.IntegerField()
    payments_today = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
    )


class FinanceOptionsSerializer(serializers.Serializer):
    years = serializers.ListField(child=serializers.DictField())
    levels = serializers.ListField(child=serializers.DictField())
    classrooms = serializers.ListField(child=serializers.DictField())
