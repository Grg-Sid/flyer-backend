from celery import shared_task
from django.core.mail import EmailMessage
from django.core.mail.backends.smtp import EmailBackend

from .models import OutgoingMails


@shared_task
def send_mail_task(mail_id, subject, body, sender, to):
    mail = OutgoingMails.objects.get(id=mail_id)
    user = mail.user
    smtp_creds = user.smtp_creds

    try:
        email_backend = EmailBackend(
            host=smtp_creds.host,
            port=smtp_creds.port,
            username=smtp_creds.username,
            password=smtp_creds.password,
            use_tls=smtp_creds.use_tls,
            use_ssl=smtp_creds.use_ssl,
        )
        attachments = mail.campaign.get_attachments()
        email = EmailMessage(subject, body, sender, [to], connection=email_backend)
        for attachment in attachments:
            email.attach_file(attachment.file.path)
        email.send()
        mail.status = "sent"
        mail.save()
    except Exception as e:
        mail = OutgoingMails.objects.get(id=mail_id)
        mail.status = "failed"
        mail.save()
        raise e
