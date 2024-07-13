from rest_framework import serializers

from .models import CustomUser, UserSmtpCreds


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["id", "email", "name", "password"]

    def create(self, validated_data):
        user = CustomUser.objects.create(
            email=validated_data["email"], name=validated_data["name"]
        )
        user.set_password(validated_data["password"])
        user.save()

        return user

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop("password")
        return data


class UserSmtpCredSerializer(serializers.ModelSerializer):
    _password = serializers.CharField(write_only=True)

    class Meta:
        model = UserSmtpCreds
        fields = [
            "id",
            "_password",
            "username",
            "password",
            "host",
            "port",
            "use_tls",
            "use_ssl",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_at",
            "updated_at",
            "id",
        ]

    def create(self, validated_data):
        password = validated_data.pop("_password")
        smtp_creds = UserSmtpCreds.objects.create(**validated_data)
        smtp_creds.set_password(password)
        smtp_creds.save()
        return smtp_creds

    def update(self, instance, validated_data):
        password = validated_data.pop("_password")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.set_password(password)
        instance.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop("password", None)
        return data
