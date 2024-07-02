from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model
from django.core import validators
from django.core.exceptions import ValidationError

USER_MODEL = get_user_model()
BOUNCE_THRESHOLD = 3


class MailList(models.Model):
    user = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_inactive(self):
        self.is_active = False
        self.save()

    def __str__(self):
        return self.name


class Email(models.Model):
    email = models.EmailField(unique=True, validators=[validators.validate_email])
    is_active = models.BooleanField(default=True)
    bounce_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_inactive(self):
        self.is_active = False
        self.save()

    def increment_bounce_count(self):
        if self.is_active:
            self.bounce_count += 1
            self.save()

        if self.bounce_count >= BOUNCE_THRESHOLD:
            self.mark_inactive()

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
        self.save()

    def __str__(self):
        return f"{self.email.email} in {self.maillist.name}"


class Campaign(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_COMPLETED, "Completed"),
    ]

    user = models.ForeignKey(
        USER_MODEL, on_delete=models.CASCADE, related_name="campaigns", default=1
    )
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True
    )
    maillists = models.ManyToManyField("MailList", related_name="campaigns", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def clean(self):
        if self.status not in dict(self.STATUS_CHOICES):
            raise ValidationError("Invalid status.")

    def activate(self):
        if self.status == self.STATUS_DRAFT:
            self.status = self.STATUS_ACTIVE
            self.save()

    def complete(self):
        if self.status == self.STATUS_ACTIVE:
            self.status = self.STATUS_COMPLETED
            self.save()

    def get_all_emails(self):
        maillist_ids = self.maillists.values_list("id", flat=True)
        email_ids = EmailMailList.objects.filter(maillist__in=maillist_ids).values_list(
            "email_id", flat=True
        )
        emails = Email.objects.filter(id__in=email_ids).values_list("email", flat=True)

        return list(emails)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class OutgoingMails(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, blank=True, null=True
    )
    user = models.ForeignKey(USER_MODEL, on_delete=models.CASCADE)
    sender = models.CharField(max_length=255)
    to = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    # TODO
    # template = models.ForeignKey(
    #     TemplateModel, on_delete=models.CASCADE, null=True, blank=True
    # )
    have_attachment = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete_sent_mails(self):
        if self.status == "sent":
            self.delete()

    def __str__(self):
        return f"{self.sender} to {self.to}"


class Attachment(models.Model):
    file = models.FileField(upload_to="media/attachments")
    mail = models.ForeignKey(OutgoingMails, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.file.name
