from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, SchoolMembership

class TenantTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        request = self.context["request"]
        school = getattr(request, "school", None)

        if school is None:
            raise serializers.ValidationError(
                "Ouvrez le portail de votre établissement avant de vous connecter."
            )

        data = super().validate(attrs)

        membership = SchoolMembership.objects.filter(
            school=school,
            user=self.user,
            is_active=True,
        ).first()

        if not membership:
            raise serializers.ValidationError(
                "Ce compte n'a pas accès à cet établissement."
            )

        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
        }
        data["membership"] = {
            "role": membership.role,
            "role_label": membership.get_role_display(),
        }
        data["school"] = {
            "id": school.id,
            "name": school.name,
            "slug": school.slug,
        }

        return data

class SchoolMemberSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    role_label = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = SchoolMembership
        fields = [
            "id",
            "user_id",
            "email",
            "first_name",
            "last_name",
            "role",
            "role_label",
            "is_active",
            "created_at",
        ]

class SchoolMemberCreateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    role = serializers.ChoiceField(
        choices=[
            SchoolMembership.Role.DIRECTOR,
            SchoolMembership.Role.MANAGER,
            SchoolMembership.Role.TEACHER,
            SchoolMembership.Role.ACCOUNTANT,
        ]
    )

    def validate_email(self, value):
        return value.strip().lower()

    @transaction.atomic
    def create(self, validated_data):
        school = self.context["school"]
        email = validated_data["email"]

        user = User.objects.filter(email=email).first()

        if user:
            if SchoolMembership.objects.filter(
                school=school,
                user=user,
            ).exists():
                raise serializers.ValidationError({
                    "email": "Cet utilisateur appartient déjà à l'établissement."
                })
        else:
            user = User.objects.create_user(
                email=email,
                password=validated_data["password"],
                first_name=validated_data["first_name"],
                last_name=validated_data["last_name"],
            )

        membership = SchoolMembership.objects.create(
            school=school,
            user=user,
            role=validated_data["role"],
            is_active=True,
        )
        return membership

class SchoolMemberUpdateSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(
        choices=[
            SchoolMembership.Role.DIRECTOR,
            SchoolMembership.Role.MANAGER,
            SchoolMembership.Role.TEACHER,
            SchoolMembership.Role.ACCOUNTANT,
        ],
        required=False,
    )

    class Meta:
        model = SchoolMembership
        fields = ["role", "is_active"]

    def validate(self, attrs):
        if self.instance.role == SchoolMembership.Role.OWNER:
            raise serializers.ValidationError(
                "Le propriétaire principal ne peut pas être modifié depuis cet écran."
            )
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=8, write_only=True)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Mot de passe actuel incorrect.")
        return value

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user
