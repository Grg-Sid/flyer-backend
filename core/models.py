from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model
from django.core import validators

USER_MODEL = get_user_model()
BOUNCE_THRESHOLD = 3


class Email(models.Model):
    email = models.EmailField(unique=True, validators=[validators.validate_email])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_inactive(self):
        self.is_active = False
        self.save()

    def increament_bounce_count(self):
        if self.is_active:
            self.bounce_count += 1
            self.save()

        if self.bounce_count >= BOUNCE_THRESHOLD:
            self.mark_inactive()

    def __str__(self):
        return self.email


class MailList(models.Model):
    user = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(
        max_length=255, blank=True, null=True
    )  # Optional category
    is_active = models.BooleanField(default=True)  # Enable/disable the mailing list
    email = models.ManyToManyField(Email, through="EmailMailList")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_inactive(self):
        self.is_active = False
        self.save()

    def __str__(self):
        return self.name


class EmailMailList(models.Model):
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    mail_list = models.ForeignKey(MailList, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)

    def unsubscribe(self):
        self.unsubscribed_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.email.email} in {self.mail_list.name}"


class TemplateModel(models.Model):
    name = models.CharField(max_length=200, unique=True)
    subject = models.CharField(
        max_length=255, null=True, blank=True
    )  # Optional subject
    template = models.TextField(default="null")
    html_file = models.FileField(upload_to="media/template", null=True, blank=True)

    def __str__(self):
        return self.name


class OutgoingMails(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE)
    sender = models.CharField(max_length=255)
    to = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    # TODO: Add template field
    # template = models.ForeignKey(TemplateModel, on_delete=models.CASCADE)
    have_attachment = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    delivery_attempts = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def increament_delivery_attempts(self):
        self.delivery_attempts += 1
        self.save()

    def mark_inactive(self):
        self.is_active = False
        self.save()

    def update_to_sent(self):
        self.status = "sent"
        self.save()

    def update_to_failed(self):
        self.status = "failed"
        self.save()

    def __str__(self):
        return f"{self.sender} to {self.to}"


class Attachment(models.Model):
    file = models.FileField(upload_to="media/attachments")
    mail = models.ForeignKey(OutgoingMails, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.file.name
