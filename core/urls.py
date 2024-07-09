from django.urls import path, include
from rest_framework import routers
from .views import (
    EmailViewSet,
    AddBulkEmailView,
    MailListViewSet,
    EmailMailListViewSet,
    CampaignViewSet,
    CreatePendingMails,
    # SendPendingMailsView,
    SendPendingMailsAsyncView,
    DeleteMailsView,
    TemplateViewSet,
    AttachmentsView,
)

router = routers.DefaultRouter()
router.register(r"emails", EmailViewSet, basename="email")
router.register(r"mail-lists", MailListViewSet, basename="maillist")
router.register(r"email-mail-list", EmailMailListViewSet, basename="emailmaillist")
router.register(r"campaigns", CampaignViewSet, basename="campaign")
router.register(r"templates", TemplateViewSet, basename="template")

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/add-bulk-email/", AddBulkEmailView.as_view(), name="add-bulk-email"),
    path(
        "api/attachments/",
        AttachmentsView.as_view(),
        name="attachments",
    ),
    path(
        "api/create-pending-mails/",
        CreatePendingMails.as_view(),
        name="create-pending-mails",
    ),
    # path(
    #     "api/send-pending-mails/",
    #     SendPendingMailsView.as_view(),
    #     name="send-pending-mails",
    # ),
    path(
        "api/send-pending-mails-async/",
        SendPendingMailsAsyncView.as_view(),
        name="send-pending-mails-async",
    ),
    path("api/delete-mails/", DeleteMailsView.as_view(), name="delete-mails"),
]
