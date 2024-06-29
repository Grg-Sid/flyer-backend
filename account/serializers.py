from rest_framework import serializers

from .models import CustomUser


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
