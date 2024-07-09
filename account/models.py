from django.db import models
from django.contrib.auth.models import AbstractUser

from .utils import encrypt, decrypt
from .managers import UserManager


class CustomUser(AbstractUser):
    objects = UserManager()

    username = None
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    # TODO add OTP mechanism
    is_verified = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]


class UserSmtpCreds(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    smtp_server = models.CharField(max_length=255)
    email = models.EmailField()
    _password = models.CharField(max_length=255)
    host = models.CharField(max_length=255)
    port = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_password(self, _password):
        self._password = encrypt(_password)

    def get_password(self):
        return decrypt(self._password)

    @property
    def password(self):
        return self.get_password()

    @password.setter
    def password(self, value):
        self.set_password(value)

    def mark_inactive(self):
        self.is_active = False
        self.save()

    def __str__(self):
        return self.email
