from django.urls import path, include
from rest_framework import routers
from .views import (
    EmailViewSet,
    AddBulkEmailView,
    MailListViewSet,
    EmailMailListViewSet,
    CampaignViewSet,
    OutgoingMailViewSet,
    GetAllEmailsFromMailList,
)

router = routers.DefaultRouter()

router.register(r"emails", EmailViewSet, basename="email")
router.register(r"mail-lists", MailListViewSet, basename="maillist")
router.register(r"email-mail-list", EmailMailListViewSet, basename="emailmaillist")
router.register(r"campaigns", CampaignViewSet, basename="campaign")
router.register(r"outgoing-mails", OutgoingMailViewSet, basename="outgoingmail")

urlpatterns = [
    path("api/", include(router.urls)),
    path(
        "api/mail-list/<int:mail_list_id>/",
        GetAllEmailsFromMailList.as_view(),
        name="get-all-emails-from-mail-list",
    ),
    path("api/add-bulk-email/", AddBulkEmailView.as_view(), name="add-bulk-email"),
]
