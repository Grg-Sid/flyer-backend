from django.contrib import admin

from .models import EmailMailList, MailList, Email

admin.site.register(EmailMailList)
admin.site.register(MailList)
admin.site.register(Email)
