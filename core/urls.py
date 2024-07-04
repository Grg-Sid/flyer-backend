from django.urls import path, include
from rest_framework import routers
from .views import (
    EmailViewSet,
    AddBulkEmailView,
    MailListViewSet,
    EmailMailListViewSet,
    CampaignViewSet,
    SendMailsView,
    SendPendingMailsView,
)

router = routers.DefaultRouter()

router.register(r"emails", EmailViewSet, basename="email")
router.register(r"mail-lists", MailListViewSet, basename="maillist")
router.register(r"email-mail-list", EmailMailListViewSet, basename="emailmaillist")
router.register(r"campaigns", CampaignViewSet, basename="campaign")

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/send-mails/", SendMailsView.as_view(), name="send-mails"),
    path(
        "api/send-pending-mails/",
        SendPendingMailsView.as_view(),
        name="send-pending-mails",
    ),
    path("api/add-bulk-email/", AddBulkEmailView.as_view(), name="add-bulk-email"),
]
