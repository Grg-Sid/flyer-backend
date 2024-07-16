from django.db.models import Q
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import generics, status, viewsets, parsers, views
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .permissions import HasCompleteProfile

from .models import (
    Email,
    MailList,
    EmailMailList,
    Campaign,
    OutgoingMails,
    EmailTemplate,
)
from .serializers import (
    EmailSerializer,
    EmailMailListSerializer,
    BulkAddEmailSerializer,
    MailListSerializer,
    OutgoingMailSerializer,
    CampaignSerializer,
    EmailTemplateSerializer,
    AttachmentSerializer,
)
from .tasks import send_mail_task


class GetAllCampaignMails(views.APIView):
    permission_classes = [IsAuthenticated, HasCompleteProfile]

    def get(self, request, campaign_id):
        if not campaign_id:
            return Response(
                {"error": "Campaign ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            campaign_id = int(campaign_id)
        except ValueError:
            return Response(
                {"error": "Campaign ID must be an integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            campaign = Campaign.objects.get(id=campaign_id)
        except ObjectDoesNotExist:
            return Response(
                {"error": "Campaign does not exist"}, status=status.HTTP_404_NOT_FOUND
            )

        emails = campaign.get_all_emails()
        if emails is None:
            return Response(
                {"error": "No emails found for this campaign"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"emails": emails}, status=status.HTTP_200_OK)


class EmailViewSet(viewsets.ModelViewSet):
    queryset = Email.objects.all()
    serializer_class = EmailSerializer
    permission_classes = [IsAuthenticated, HasCompleteProfile]


class AddBulkEmailView(generics.CreateAPIView):
    serializer_class = BulkAddEmailSerializer
    permission_classes = [IsAuthenticated, HasCompleteProfile]
    parser_classes = [parsers.MultiPartParser]

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get("csv_file")
        maillist_id = request.data.get("maillist")

        if not csv_file or not maillist_id:
            return Response(
                {"error": "CSV file and mail list are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        maillist = MailList.objects.filter(id=maillist_id, user=request.user).first()
        if not maillist:
            return Response(
                {
                    "error": "Mail list does not exist or you do not have permission to access it"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(
            data={"csv_file": csv_file, "maillist": maillist}
        )
        if serializer.is_valid():
            serializer.save(maillist=maillist)
            return Response(
                {"success": "Emails have been added successfully"},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MailListViewSet(viewsets.ModelViewSet):
    queryset = MailList.objects.all()
    serializer_class = MailListSerializer
    permission_classes = [IsAuthenticated, HasCompleteProfile]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return MailList.objects.filter(user=self.request.user)


class EmailMailListViewSet(viewsets.ModelViewSet):
    queryset = EmailMailList.objects.all()
    serializer_class = EmailMailListSerializer
    permission_classes = [IsAuthenticated, HasCompleteProfile]

    def get_queryset(self):
        return EmailMailList.objects.filter(maillist__user=self.request.user)


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated, HasCompleteProfile]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)
        return super().perform_create(serializer)

    def get_queryset(self):
        return Campaign.objects.filter(user=self.request.user).prefetch_related(
            "maillists"
        )

    @action(detail=True, methods=["post"])
    def add_attachment(self, request, pk=None):
        campaign = self.get_object()
        attachment_serializer = AttachmentSerializer(data=request.data)
        if attachment_serializer.is_valid():
            attachment_serializer.save(campaign=campaign)
            return Response(
                {"success": "Attachment has been added successfully"},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            attachment_serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )


class TemplateViewSet(viewsets.ModelViewSet):
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    permission_classes = [IsAuthenticated, HasCompleteProfile]

    def get_queryset(self):
        return EmailTemplate.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DeleteMailsView(views.APIView):
    permission_classes = [IsAuthenticated, HasCompleteProfile]

    def delete_mails(self, campaign_id, status_list):
        mails = OutgoingMails.objects.filter(
            Q(status__in=status_list) & Q(campaign=campaign_id)
        )
        mails.delete()
        return Response(
            {"message": f"All {', '.join(status_list)} mails have been deleted"}
        )

    def delete(self, request):
        campaign_id = request.data.get("campaign")
        if not campaign_id:
            return Response(
                {"error": "Campaign ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        status_list = request.data.get("status", ["sent", "failed"])
        OutgoingMails.objects.filter(
            Q(status__in=status_list) & Q(campaign=campaign_id) & Q(user=request.user)
        ).delete()

        return Response({"message": "All selected mails have been deleted"})


class CreateSendPendingMails(generics.CreateAPIView):
    serializer_class = OutgoingMailSerializer
    permission_classes = [IsAuthenticated, HasCompleteProfile]

    def create(self, request):
        campaign_id = request.data.get("campaign")
        user = request.user

        try:
            campaign = Campaign.objects.get(id=campaign_id, user=request.user)
        except Campaign.DoesNotExist:
            return Response(
                {"error": "Campaign does not exist or you do not have access to it"},
                status=status.HTTP_404_NOT_FOUND,
            )

        emails = campaign.get_all_emails()
        total_emails = len(emails)

        bulk_mails = []
        for email in emails:
            mail_data = {
                "campaign": campaign,
                "user": request.user,
                "to": email,
                "sender": user.smtp_creds.username,
                "status": "queued",
            }
            bulk_mails.append(OutgoingMails(**mail_data))

        try:
            with transaction.atomic():
                created_mails = OutgoingMails.objects.bulk_create(bulk_mails)

                for mails in created_mails:
                    send_mail_task.delay(
                        mails.id,
                        campaign.subject,
                        campaign.body,
                        mails.sender,
                        mails.to,
                    )
        except Exception as e:
            return Response(
                {"error": f"An error occurred while sending mails: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": f"All {total_emails} emails have been queued for sending"},
            status=status.HTTP_201_CREATED,
        )
