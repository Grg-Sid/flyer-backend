from django.urls import path, include
from rest_framework import routers
from .views import (
    EmailViewSet,
    AddBulkEmailView,
    MailListViewSet,
    EmailMailListViewSet,
    CampaignViewSet,
    GetAllCampaignMails,
    CreateSendPendingMails,
    DeleteMailsView,
    TemplateViewSet,
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
        "api/get-all-campaign-mails/<int:campaign_id>/",
        GetAllCampaignMails.as_view(),
        name="get-all-campaign-mails",
    ),
    path(
        "api/create-send-pending-mails/",
        CreateSendPendingMails.as_view(),
        name="create-send-pending-mails",
    ),
    path("api/delete-mails/", DeleteMailsView.as_view(), name="delete-mails"),
]
