from django.db import models
from django.contrib.auth.models import AbstractUser

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
