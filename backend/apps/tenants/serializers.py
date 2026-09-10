from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers

from apps.accounts.models import User, SchoolMembership
from .models import School

RESERVED_SLUGS = {
    "www", "api", "admin", "app", "school", "support",
    "mail", "demo", "static", "media", "verify",
}

def validate_hex_color(value):
    if not value:
        return value
    if len(value) != 7 or not value.startswith("#"):
        raise serializers.ValidationError("Utilisez une couleur hexadécimale comme #0f172a.")
    try:
        int(value[1:], 16)
    except ValueError:
        raise serializers.ValidationError("Couleur hexadécimale invalide.")
    return value.lower()

class SchoolOnboardingSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    slug = serializers.CharField(max_length=80)
    acronym = serializers.CharField(max_length=30, required=False, allow_blank=True)
    city = serializers.CharField(max_length=120, required=False, allow_blank=True)
    country = serializers.CharField(max_length=120, required=False, default="Cameroun")
    phone = serializers.CharField(max_length=40, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)

    language_mode = serializers.ChoiceField(choices=School.LanguageMode.choices)
    education_level = serializers.ChoiceField(choices=School.EducationLevel.choices)
    teaching_model = serializers.ChoiceField(choices=School.TeachingModel.choices)

    owner_first_name = serializers.CharField(max_length=150)
    owner_last_name = serializers.CharField(max_length=150)
    owner_email = serializers.EmailField()
    owner_password = serializers.CharField(min_length=8, write_only=True)

    def validate_slug(self, value):
        normalized = slugify(value).lower()

        if not normalized:
            raise serializers.ValidationError("Sous-domaine invalide.")

        if normalized in RESERVED_SLUGS:
            raise serializers.ValidationError("Ce sous-domaine est réservé.")

        if School.objects.filter(slug=normalized).exists():
            raise serializers.ValidationError("Ce sous-domaine est déjà utilisé.")

        return normalized

    def validate_owner_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Un utilisateur existe déjà avec cette adresse e-mail."
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        owner_data = {
            "first_name": validated_data.pop("owner_first_name"),
            "last_name": validated_data.pop("owner_last_name"),
            "email": validated_data.pop("owner_email"),
            "password": validated_data.pop("owner_password"),
        }

        school = School.objects.create(**validated_data)

        owner = User.objects.create_user(
            email=owner_data["email"],
            password=owner_data["password"],
            first_name=owner_data["first_name"],
            last_name=owner_data["last_name"],
        )

        SchoolMembership.objects.create(
            school=school,
            user=owner,
            role=SchoolMembership.Role.OWNER,
        )

        return school

class SchoolSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = School
        fields = [
            "id",
            "name",
            "slug",
            "acronym",
            "city",
            "country",
            "phone",
            "email",
            "logo",
            "motto",
            "primary_color",
            "secondary_color",
            "language_mode",
            "education_level",
            "teaching_model",
            "status",
        ]

    def get_logo(self, obj):
        request = self.context.get("request")

        if obj.logo:
            url = obj.logo.url
            return request.build_absolute_uri(url) if request else url

        return obj.logo_url or None

class SchoolSettingsSerializer(serializers.ModelSerializer):
    primary_color = serializers.CharField(validators=[validate_hex_color])
    secondary_color = serializers.CharField(validators=[validate_hex_color])

    class Meta:
        model = School
        fields = [
            "name",
            "acronym",
            "city",
            "country",
            "phone",
            "email",
            "logo",
            "motto",
            "primary_color",
            "secondary_color",
            "language_mode",
            "education_level",
            "teaching_model",
        ]

    def validate_logo(self, value):
        if value and value.size > 3 * 1024 * 1024:
            raise serializers.ValidationError("Le logo ne doit pas dépasser 3 Mo.")
        return value
