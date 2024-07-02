from rest_framework import generics, status, viewsets, parsers, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Email, MailList, EmailMailList, Campaign, OutgoingMails
from .serializers import (
    EmailSerializer,
    EmailMailListSerializer,
    BulkAddEmailSerializer,
    MailListSerializer,
    OutgoingMailSerializer,
    CampaignSerializer,
)
from .producer import send_email_to_queue


class EmailViewSet(viewsets.ModelViewSet):
    queryset = Email.objects.all()
    serializer_class = EmailSerializer
    permission_classes = [IsAuthenticated]
    # http_method_names = ["get", "post", "patch", "delete"]


class AddBulkEmailView(generics.CreateAPIView):
    serializer_class = BulkAddEmailSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser]

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get("csv_file")
        mail_list_id = request.data.get("mail_list")
        if not csv_file or not mail_list_id:
            return Response(
                {"error": "CSV file and mail list are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        mail_list = MailList.objects.filter(id=mail_list_id, user=request.user).first()
        if not mail_list:
            return Response(
                {
                    "error": "Mail list does not exist or you do not have permission to access it"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(
            data={"csv_file": csv_file, "mail_list": mail_list}
        )
        if serializer.is_valid():
            serializer.save(mail_list=mail_list)
            return Response(
                {"success": "Emails have been added successfully"},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MailListViewSet(viewsets.ModelViewSet):
    queryset = MailList.objects.all()
    serializer_class = MailListSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return MailList.objects.filter(user=self.request.user)


class EmailMailListViewSet(viewsets.ModelViewSet):
    queryset = EmailMailList.objects.all()
    serializer_class = EmailMailListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EmailMailList.objects.filter(mail_list__user=self.request.user)


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated]


class OutgoingMailViewSet(viewsets.ModelViewSet):
    queryset = OutgoingMails.objects.all()
    serializer_class = OutgoingMailSerializer
    permission_classes = [IsAuthenticated]


class GetAllEmailsFromMailList(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        mail_list_id = self.kwargs.get("mail_list_id")
        mail_list = MailList.objects.filter(id=mail_list_id, user=request.user).first()
        if not mail_list:
            return Response(
                {
                    "error": "Mail list does not exist or you do not have permission to access it"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        emails = EmailMailList.objects.filter(mail_list=mail_list)
        serializer = EmailMailListSerializer(emails, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OutgoingMailViewSet(viewsets.ModelViewSet):
    queryset = OutgoingMails.objects.all()
    serializer_class = OutgoingMailSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        instance = serializer.save()
        email_data = {
            "sender": instance.sender,
            "to": instance.to,
            "subject": instance.subject,
            "body": instance.body,
            "have_attachment": instance.have_attachment,
        }
        send_email_to_queue(email_data)
