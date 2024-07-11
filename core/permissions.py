from rest_framework import permissions


class HasCompleteProfile(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.smpt_creds.exists()
