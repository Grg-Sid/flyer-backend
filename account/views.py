from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import UserSerializer, UserSmtpCredSerializer
from .models import UserSmtpCreds


class RegisterView(GenericAPIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [AllowAny()]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserSmtpCredsView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSmtpCredSerializer

    def post(self, request):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    

    def get(self, request):
        user = request.user
        try:
            smtp_creds = user.smtp_creds
        except UserSmtpCreds.DoesNotExist:
            return Response(
                {"detail": "SMTP credentials not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(smtp_creds)
        return Response(serializer.data, status=status.HTTP_200_OK)
