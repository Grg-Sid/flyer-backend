import csv

from django.db import transaction
from django.contrib.auth import get_user_model

from rest_framework import serializers
from .models import (
    Email,
    MailList,
    OutgoingMails,
    Campaign,
    EmailMailList,
    EmailTemplate,
    Attachment,
)

USER_MODEL = get_user_model()


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "id"]


class BulkAddEmailSerializer(serializers.Serializer):
    csv_file = serializers.FileField()
    maillist = serializers.PrimaryKeyRelatedField(queryset=MailList.objects.all())

    def validate_csv_file(self, value):
        if not value.name.endswith(".csv"):
            raise serializers.ValidationError("Invalid file type")

        try:
            decoded_file = value.read().decode("utf-8").splitlines()
            reader = csv.reader(decoded_file)
            next(reader)

            invalid_emails = []

            for row in reader:
                email = row[0].strip()
                if "@" not in email:
                    invalid_emails.append(email)

            if invalid_emails:
                raise serializers.ValidationError(
                    f"Invalid emails found: {', '.join(invalid_emails)}"
                )
        except Exception as e:
            raise serializers.ValidationError(f"Error reading CSV file: {e}")

        return value

    def create(self, validated_data):
        csv_file = validated_data.get("csv_file")
        maillist = validated_data.get("maillist")
        emails_to_create = []
        email_maillist_to_create = []

        try:
            decoded_file = csv_file.read().decode("utf-8").splitlines()
            reader = csv.reader(decoded_file)
            next(reader)

            with transaction.atomic():
                for row in reader:
                    email_str = row[0].strip()
                    if "@" in email_str:
                        email, created = Email.objects.get_or_create(email=email_str)
                        if created:
                            emails_to_create.append(email)
                            email_maillist_to_create.append(
                                EmailMailList(email=email, maillist=maillist)
                            )

                Email.objects.bulk_create(emails_to_create, ignore_conflicts=True)
                EmailMailList.objects.bulk_create(
                    email_maillist_to_create, ignore_conflicts=True
                )

                return {"success": "Emails added to the mail list"}
        except Exception as e:
            raise serializers.ValidationError(f"Error processing CSV file: {e}")


class MailListSerializer(serializers.ModelSerializer):

    class Meta:
        model = MailList
        fields = [
            "id",
            "user",
            "name",
            "description",
            "category",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "id", "user"]


class EmailMailListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    maillist = serializers.PrimaryKeyRelatedField(queryset=MailList.objects.all())

    class Meta:
        model = EmailMailList
        fields = [
            "id",
            "email",
            "maillist",
            "created_at",
            "unsubscribed_at",
        ]
        read_only_fields = ["created_at", "id"]

    def validate(self, attrs):
        email = attrs.get("email")
        maillist = attrs.get("maillist")
        request = self.context.get("request")

        if not request:
            raise serializers.ValidationError("Request context is required.")

        if not Email.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email does not exist.")

        if not MailList.objects.filter(id=maillist.id, user=request.user).exists():
            raise serializers.ValidationError(
                "Mail list does not exist or you do not have access to it."
            )

        if EmailMailList.objects.filter(email__email=email, maillist=maillist).exists():
            raise serializers.ValidationError("Email already exists in this mail list.")

        return attrs

    def create(self, validated_data):
        email_str = validated_data.get("email")
        maillist = validated_data.get("maillist")

        email = Email.objects.get(email=email_str)
        email_maillist = EmailMailList.objects.create(email=email, maillist=maillist)

        return email_maillist


class EmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplate
        fields = [
            "id",
            "name",
            "html_content",
            "user",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "id", "user"]


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = [
            "id",
            "name",
            "file",
            "campaign",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "campaign", "id"]


class CampaignSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Campaign
        fields = [
            "id",
            "user",
            "name",
            "maillists",
            "description",
            "subject",
            "body",
            "status",
            "template",
            "attachments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class OutgoingMailSerializer(serializers.ModelSerializer):
    custom_attachments = AttachmentSerializer(many=True, required=False)

    class Meta:
        model = OutgoingMails
        fields = [
            "id",
            "sender",
            "to",
            "subject",
            "campaign",
            "body",
            "status",
            "custom_attachments",
            "created_at",
            "updated_at",
        ]

    read_only_fields = [
        "status",
        "created_at",
        "updated_at",
        "id",
    ]
