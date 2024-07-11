from django.db.models import Q
from django.db import transaction
from django.core.paginator import Paginator

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
    Attachment,
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


class EmailViewSet(viewsets.ModelViewSet):
    queryset = Email.objects.all()
    serializer_class = EmailSerializer
    permission_classes = [IsAuthenticated]


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


class CreatePendingMails(generics.CreateAPIView):
    serializer_class = OutgoingMailSerializer
    permission_classes = [IsAuthenticated, HasCompleteProfile]

    def create(self, request, *args, **kwargs):
        campaign_id = request.data.get("campaign")
        campaign = Campaign.objects.filter(id=campaign_id).first()

        if not campaign:
            return Response(
                {"error": "Campaign does not exist or you do not have access to it"},
                status=status.HTTP_404_NOT_FOUND,
            )

        emails = campaign.get_all_emails()
        created_mails = []

        with transaction.atomic():
            for email in emails:
                mail_data = {
                    "campaign": campaign.id,
                    "user": request.user.id,
                    "sender": "hello@world.com",
                    "to": email,
                    "subject": "Hello World",
                    "body": "How Are You?",
                }
                serializer = self.get_serializer(data=mail_data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                created_mails.append(serializer.data)

        headers = self.get_success_headers(serializer.data)
        return Response(created_mails, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save()


class TemplateViewSet(viewsets.ModelViewSet):
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    permission_classes = [IsAuthenticated, HasCompleteProfile]

    def get_queryset(self):
        return EmailTemplate.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AttachmentsView(generics.CreateAPIView):
    serializer_class = AttachmentSerializer
    permission_classes = [IsAuthenticated, HasCompleteProfile]

    def create(self, request, *args, **kwargs):
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "File is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data={"file": file})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success": "File has been uploaded successfully"},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


class SendPendingMailsAsyncView(views.APIView):

    permission_classes = [IsAuthenticated, HasCompleteProfile]

    def get(self, request):
        campaign_id = request.data.get("campaign")
        if not campaign_id:
            return Response(
                {"error": "Campaign ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        pending_mails = OutgoingMails.objects.filter(
            Q(status="pending") & Q(campaign=campaign_id) & Q(user=request.user)
        )
        with transaction.atomic():
            for mail in pending_mails:
                send_mail_task.delay(
                    mail.id, mail.subject, mail.body, mail.sender, mail.to
                )
                mail.status = "queued"
                mail.save()

        return Response({"message": "All pending mails have been queued for sending"})


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
        batch_size = 100
        paginator = Paginator(emails, batch_size)

        try:
            with transaction.atomic():
                for page_num in paginator.page_range:
                    page = paginator.page(page_num)
                    bulk_mails = []
                    for email in page:
                        mail_data = {
                            "campaign": campaign.id,
                            "user": request.user.id,
                            "to": email,
                            "sender": user.smtp_creds.email,
                            "status": "queued",
                        }
                        bulk_mails.append(OutgoingMails(**mail_data))
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
