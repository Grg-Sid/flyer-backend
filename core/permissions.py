from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class HasCompleteProfile(permissions.BasePermission):
    message = "You need to set up your SMTP credentials before performing this action."

    def has_permission(self, request, view):
        if not hasattr(request.user, "smtp_creds"):
            raise PermissionDenied(detail=self.message)
        return True
