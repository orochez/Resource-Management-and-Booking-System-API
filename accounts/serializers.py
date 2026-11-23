
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


User = get_user_model()


# ==========================================
# USER PROFILE SERIALIZER
# ==========================================

class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "username",
            "role",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def validate_email(self, value):
        email = value.strip().lower()

        queryset = User.objects.filter(
            email__iexact=email
        )

        if self.instance:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "This email address is already registered."
            )

        return email


# ==========================================
# USER REGISTRATION SERIALIZER
# ==========================================

class UserRegistrationSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )

    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    email = serializers.EmailField(
        required=True
    )

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "password",
            "password_confirm",
        ]

        read_only_fields = ["id"]

    def validate_email(self, value):
        email = value.strip().lower()

        if User.objects.filter(
            email__iexact=email
        ).exists():
            raise serializers.ValidationError(
                "This email address is already registered."
            )

        return email

    def validate(self, attrs):

        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })

        return attrs

    def create(self, validated_data):

        validated_data.pop("password_confirm")

        password = validated_data.pop("password")

        user = User(
            **validated_data,
            role=User.Role.EMPLOYEE,
            is_staff=False,
            is_superuser=False,
        )

        user.set_password(password)
        user.save()

        return user


# ==========================================
# JWT LOGIN SERIALIZER
# ==========================================

class CustomTokenObtainPairSerializer(
    TokenObtainPairSerializer
):

    def validate(self, attrs):

        data = super().validate(attrs)

        data["user"] = UserProfileSerializer(
            self.user
        ).data

        return data


# ==========================================
# ADMIN USER MANAGEMENT SERIALIZER
# ==========================================

class AdminUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "username",
            "created_at",
            "updated_at",
        ]

    def validate_email(self, value):

        email = value.strip().lower()

        queryset = User.objects.filter(
            email__iexact=email
        )

        if self.instance:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "This email address is already registered."
            )

        return email

    def validate(self, attrs):

        if self.instance and self.instance.is_superuser:
            if attrs.get("is_active") is False:
                raise serializers.ValidationError({
                    "is_active": (
                        "Superuser accounts cannot be "
                        "deactivated through this API."
                    )
                })

            if (
                "role" in attrs
                and attrs["role"] != User.Role.ADMIN
            ):
                raise serializers.ValidationError({
                    "role": (
                        "Superuser accounts must retain "
                        "the Admin role."
                    )
                })

        return attrs
