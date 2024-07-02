import csv
from rest_framework import serializers
from .models import Email, MailList, OutgoingMails, Campaign, EmailMailList


class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = [
            "id",
            "email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "id"]


class BulkAddEmailSerializer(serializers.Serializer):
    csv_file = serializers.FileField()
    mail_list = serializers.PrimaryKeyRelatedField(queryset=MailList.objects.all())

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
        mail_list = validated_data.get("mail_list")
        emails_to_create = []

        try:
            decoded_file = csv_file.read().decode("utf-8").splitlines()
            reader = csv.reader(decoded_file)
            next(reader)

            for row in reader:
                email_str = row[0].strip()
                if "@" in email_str:
                    email, created = Email.objects.get_or_create(email=email_str)
                    if not EmailMailList.objects.filter(
                        email=email, mail_list=mail_list
                    ).exists():
                        emails_to_create.append(
                            EmailMailList(email=email, mail_list=mail_list)
                        )

            EmailMailList.objects.bulk_create(emails_to_create)

            return {"success": "Emails added to the mail list"}
        except Exception as e:
            raise serializers.ValidationError(f"Error processing CSV file: {e}")


# class MailListSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = MailList
#         fields = [
#             "id",
#             "user",
#             "name",
#             "description",
#             "category",
#             "is_active",
#             "email",
#             "created_at",
#             "updated_at",
#         ]
#         read_only_fields = ["created_at", "updated_at", "email"]


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
    mail_list = serializers.PrimaryKeyRelatedField(queryset=MailList.objects.all())

    class Meta:
        model = EmailMailList
        fields = [
            "id",
            "email",
            "mail_list",
            "created_at",
            "unsubscribed_at",
        ]
        read_only_fields = ["created_at", "id"]

    def validate(self, attrs):
        email = attrs.get("email")
        mail_list = attrs.get("mail_list")
        request = self.context.get("request")

        if not request:
            raise serializers.ValidationError("Request context is required.")

        if not Email.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email does not exist.")

        if not MailList.objects.filter(id=mail_list.id, user=request.user).exists():
            raise serializers.ValidationError(
                "Mail list does not exist or you do not have access to it."
            )

        if EmailMailList.objects.filter(
            email__email=email, mail_list=mail_list
        ).exists():
            raise serializers.ValidationError("Email already exists in this mail list.")

        return attrs

    def create(self, validated_data):
        email_str = validated_data.get("email")
        mail_list = validated_data.get("mail_list")

        email = Email.objects.get(email=email_str)
        email_mail_list = EmailMailList.objects.create(email=email, mail_list=mail_list)

        return email_mail_list


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = [
            "id",
            "name",
            "mail_lists",
            "description",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


# TODO: Add TemplateSerializer
# class TemplateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TemplateModel
#         fields = [
#             "id",
#             "name",
#             "subject",
#             "template",
#             "html_file",
#         ]


class OutgoingMailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutgoingMails
        fields = [
            "id",
            "sender",
            "to",
            "subject",
            "body",
            "have_attachment",
            "status",
            "delivery_attempts",
            "is_active",
        ]

    read_only_fields = ["status", "delivery_attempts", "is_active"]
