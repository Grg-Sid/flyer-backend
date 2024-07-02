from django.contrib import admin

from .models import Campaign, MailList, Email

admin.site.register(Campaign)
admin.site.register(MailList)
admin.site.register(Email)
