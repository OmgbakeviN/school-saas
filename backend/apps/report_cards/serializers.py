from rest_framework import serializers

from .models import ReportCardSnapshot


class ReportCardOptionsSerializer(serializers.Serializer):
    years = serializers.ListField(child=serializers.DictField())
    periods = serializers.ListField(child=serializers.DictField())
    classrooms = serializers.ListField(child=serializers.DictField())
    subjects = serializers.ListField(child=serializers.DictField())
    full_report_class_ids = serializers.ListField(
        child=serializers.IntegerField()
    )
    classroom_subjects = serializers.DictField(
        child=serializers.ListField(
            child=serializers.IntegerField()
        )
    )


class PublishReportCardSerializer(serializers.Serializer):
    enrollment = serializers.IntegerField(min_value=1)
    report_type = serializers.ChoiceField(
        choices=ReportCardSnapshot.ReportType.choices
    )
    academic_period = serializers.IntegerField(
        min_value=1,
        required=False,
        allow_null=True,
    )
    general_comment = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1200,
    )
    teacher_comment = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1200,
    )
    subject_comments = serializers.DictField(
        child=serializers.CharField(
            allow_blank=True,
            max_length=500,
        ),
        required=False,
    )

    def validate(self, attrs):
        report_type = attrs["report_type"]
        period = attrs.get("academic_period")

        if (
            report_type == ReportCardSnapshot.ReportType.PERIOD
            and not period
        ):
            raise serializers.ValidationError({
                "academic_period": (
                    "La période est obligatoire pour un bulletin de période."
                )
            })

        if (
            report_type == ReportCardSnapshot.ReportType.ANNUAL
            and period
        ):
            raise serializers.ValidationError({
                "academic_period": (
                    "Un bulletin annuel ne doit pas recevoir de période."
                )
            })

        return attrs


class BulkPublishReportCardsSerializer(serializers.Serializer):
    classroom = serializers.IntegerField(min_value=1)
    report_type = serializers.ChoiceField(
        choices=ReportCardSnapshot.ReportType.choices
    )
    academic_period = serializers.IntegerField(
        min_value=1,
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        report_type = attrs["report_type"]
        period = attrs.get("academic_period")

        if (
            report_type == ReportCardSnapshot.ReportType.PERIOD
            and not period
        ):
            raise serializers.ValidationError({
                "academic_period": "Sélectionnez une période."
            })

        if (
            report_type == ReportCardSnapshot.ReportType.ANNUAL
            and period
        ):
            raise serializers.ValidationError({
                "academic_period": "Le bulletin annuel n'utilise pas de période."
            })

        return attrs


class ReportCardSnapshotSerializer(serializers.ModelSerializer):
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
    academic_year_name = serializers.CharField(
        source="academic_year.name",
        read_only=True,
    )
    period_name = serializers.CharField(
        source="academic_period.name",
        read_only=True,
        allow_null=True,
    )
    report_type_label = serializers.CharField(
        source="get_report_type_display",
        read_only=True,
    )
    pdf_url = serializers.SerializerMethodField()
    verification_url = serializers.SerializerMethodField()

    class Meta:
        model = ReportCardSnapshot
        fields = (
            "id",
            "report_type",
            "report_type_label",
            "version",
            "student_id",
            "student_name",
            "matricule",
            "classroom_id",
            "classroom_name",
            "academic_year",
            "academic_year_name",
            "academic_period",
            "period_name",
            "published_at",
            "payload_sha256",
            "pdf_sha256",
            "pdf_url",
            "verification_url",
        )

    def get_student_name(self, obj):
        return (
            f"{obj.enrollment.student.last_name} "
            f"{obj.enrollment.student.first_name}"
        ).strip()

    def get_pdf_url(self, obj):
        request = self.context.get("request")
        path = f"/api/report-cards/snapshots/{obj.id}/pdf/"
        return request.build_absolute_uri(path) if request else path

    def get_verification_url(self, obj):
        request = self.context.get("request")
        path = (
            "/verify/report-card/"
            f"{obj.verification_token}/"
        )
        return request.build_absolute_uri(path) if request else path


class ReportCardPublishResultSerializer(serializers.Serializer):
    snapshot = ReportCardSnapshotSerializer()
    created_new_version = serializers.BooleanField()
    unchanged = serializers.BooleanField()


class BulkPublishResultSerializer(serializers.Serializer):
    created = serializers.IntegerField()
    unchanged = serializers.IntegerField()
    failed = serializers.IntegerField()
    snapshots = ReportCardSnapshotSerializer(many=True)
    errors = serializers.ListField(child=serializers.DictField())


class ClassroomReportCardsZipSerializer(serializers.Serializer):
    classroom = serializers.IntegerField(min_value=1)
    report_type = serializers.ChoiceField(
        choices=ReportCardSnapshot.ReportType.choices
    )
    academic_period = serializers.IntegerField(
        min_value=1,
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        report_type = attrs["report_type"]
        period = attrs.get("academic_period")

        if (
            report_type == ReportCardSnapshot.ReportType.PERIOD
            and not period
        ):
            raise serializers.ValidationError({
                "academic_period": "Sélectionnez une période."
            })

        if (
            report_type == ReportCardSnapshot.ReportType.ANNUAL
            and period
        ):
            raise serializers.ValidationError({
                "academic_period": (
                    "Un téléchargement annuel ne reçoit pas de période."
                )
            })

        return attrs
