from rest_framework import serializers


class AgentContextRequestSerializer(serializers.Serializer):
    instance_name = serializers.CharField(max_length=120)
    phone = serializers.CharField(max_length=64)
    message_text = serializers.CharField(required=False, allow_blank=True, max_length=4000)


class SendTermReportCardSerializer(AgentContextRequestSerializer):
    student_id = serializers.IntegerField(min_value=1)
    period = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=120,
    )


class SendTuitionInvoiceSerializer(AgentContextRequestSerializer):
    student_id = serializers.IntegerField(min_value=1)


class SendAgentTextSerializer(AgentContextRequestSerializer):
    text = serializers.CharField(max_length=4000)
