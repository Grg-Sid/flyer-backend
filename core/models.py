from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

USER_MODEL = get_user_model()


class MailList(models.Model):
    user = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_inactive(self):
        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])

    def __str__(self):
        return self.name


class Email(models.Model):
    email = models.EmailField(unique=True, validators=[validators.validate_email])
    first_name = models.CharField(max_length=255, default="")
    last_name = models.CharField(max_length=255, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email


class EmailMailList(models.Model):
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    maillist = models.ForeignKey(MailList, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("email", "maillist")

    def unsubscribe(self):
        self.unsubscribed_at = timezone.now()
        self.save(update_fields=["unsubscribed_at"])

    def __str__(self):
        return f"{self.email.email} in {self.maillist.name}"


class EmailTemplate(models.Model):
    name = models.CharField(max_length=255, unique=True)
    html_content = models.TextField(help_text="HTML content for the email template")
    user = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def formatted_html_content(self):
        return mark_safe(self.html_content)

    class Meta:
        verbose_name = "Email Template"
        verbose_name_plural = "Email Templates"


class Campaign(models.Model):
    STATUS_INACTIVE = "inactive"
    STATUS_ACTIVE = "active"

    STATUS_CHOICES = [
        (STATUS_INACTIVE, "Inactive"),
        (STATUS_ACTIVE, "Active"),
    ]

    user = models.ForeignKey(
        USER_MODEL, on_delete=models.CASCADE, related_name="campaigns", default=1
    )
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(default="")
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE
    )
    maillists = models.ManyToManyField("MailList", related_name="campaigns", blank=True)
    subject = models.CharField(max_length=255, blank=True, null=True, default="")
    body = models.TextField(null=True, blank=True)
    template = models.ForeignKey(
        "EmailTemplate", on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def clean(self):
        if self.status not in dict(self.STATUS_CHOICES):
            raise ValidationError("Invalid status.")

    def set_inactive(self):
        self.status = self.STATUS_INACTIVE
        self.save(update_fields=["status", "updated_at"])

    def get_all_emails(self):
        return (
            Email.objects.filter(
                emailmaillist__maillist__campaigns=self,
                emailmaillist__unsubscribed_at__isnull=True,
            )
            .distinct()
            .values_list("email", flat=True)
        )

    def get_attachments(self):
        attachments_list = list(self.attachments.all())
        return attachments_list

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Attachment(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True, default="")
    file = models.FileField(
        upload_to="media/attachments",
        validators=[
            validators.FileExtensionValidator(
                ["pdf", "doc", "docx", "xls", "xlsx", "csv", "jpg", "png", "gif"]
            )
        ],
    )
    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, null=True, related_name="attachments"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.file.name


class OutgoingMails(models.Model):
    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="outgoing_mails", default=None
    )
    user = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE)
    sender = models.CharField(max_length=255)
    to = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="queued")
    custom_attachments = models.ManyToManyField(
        Attachment, related_name="custom_mails", blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_attachments(self):
        return list(self.custom_attachments.all()) + list(
            self.campaign.attachments.all()
        )

    def __str__(self):
        return f"{self.sender} to {self.to}"


class ColdMailing(models.Model):
    user = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    company = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.first_name} {self.last_name} from {self.company}"
