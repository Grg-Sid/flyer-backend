from celery import shared_task
from django.core.mail import send_mail

from .models import OutgoingMails


@shared_task
def send_mail_task(mail_id, subject, body, sender, to):
    try:
        send_mail(subject, body, sender, [to], fail_silently=False)
        mail = OutgoingMails.objects.get(id=mail_id)
        mail.status = "sent"
        mail.save()
    except Exception as e:
        mail = OutgoingMails.objects.get(id=mail_id)
        mail.status = "failed"
        mail.save()
        raise e
