from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import UserSerializer, UserSmtpCreds


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

    def post(self, request):
        serializer = UserSmtpCreds(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        user = request.user
        smtp_creds = user.smtp_creds
        serializer = UserSmtpCreds(smtp_creds)
        return Response(serializer.data, status=status.HTTP_200_OK)
