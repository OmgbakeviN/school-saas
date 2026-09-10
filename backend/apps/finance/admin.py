from django.contrib import admin

from .models import (
    PaymentAllocation,
    PaymentReceiptSnapshot,
    StudentTuitionAccount,
    TuitionInstallment,
    TuitionPayment,
    TuitionPlan,
)


class TuitionInstallmentInline(admin.TabularInline):
    model = TuitionInstallment
    extra = 0


@admin.register(TuitionPlan)
class TuitionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "school",
        "academic_year",
        "level",
        "classroom",
        "currency",
        "is_active",
    )
    list_filter = (
        "school",
        "academic_year",
        "is_active",
    )
    inlines = [TuitionInstallmentInline]


@admin.register(StudentTuitionAccount)
class StudentTuitionAccountAdmin(admin.ModelAdmin):
    list_display = (
        "enrollment",
        "plan",
        "school",
        "created_at",
    )
    list_filter = (
        "school",
        "plan__academic_year",
    )


class PaymentAllocationInline(admin.TabularInline):
    model = PaymentAllocation
    extra = 0
    can_delete = False
    readonly_fields = (
        "school",
        "installment",
        "amount",
    )


@admin.register(TuitionPayment)
class TuitionPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "receipt_number",
        "tuition_account",
        "amount",
        "method",
        "paid_at",
        "received_by",
    )
    list_filter = (
        "school",
        "method",
        "paid_at",
    )
    search_fields = (
        "receipt_number",
        "reference",
        "tuition_account__enrollment__student__matricule",
        "tuition_account__enrollment__student__last_name",
    )
    readonly_fields = (
        "school",
        "tuition_account",
        "amount",
        "method",
        "reference",
        "notes",
        "paid_at",
        "received_by",
        "receipt_number",
        "created_at",
    )
    inlines = [PaymentAllocationInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PaymentReceiptSnapshot)
class PaymentReceiptSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "payment",
        "school",
        "created_at",
        "payload_sha256",
    )
    readonly_fields = (
        "school",
        "payment",
        "payload",
        "payload_sha256",
        "pdf_file",
        "pdf_sha256",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
