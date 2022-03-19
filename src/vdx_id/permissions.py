##
# © Copyright 2021 VaDiX Solutions <www.vadix.io>
##

import logging

from django.conf import settings
from rest_framework import permissions

logger = logging.getLogger("%s" % __name__)


class IsStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        else:
            return False


class IsPortunusAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        is_superuser = request.user.is_superuser
        is_portunus_admin = request.user.groups.filter(
            name=settings.GROUP_PORTUNUS_ADMIN
        ).exists()
        return is_superuser or is_portunus_admin

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsPortunusAccessManager(permissions.BasePermission):
    def has_permission(self, request, view):
        is_superuser = request.user.is_superuser
        return is_superuser

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        is_owner = getattr(obj, "owner") == request.user
        return is_owner


class IsUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        is_user = getattr(obj, "user") == request.user
        return is_user


class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.method in permissions.SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class IsGettingOrCreating(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in ["GET", "POST", "OPTIONS"]

    def has_object_permission(self, request, view, obj):
        return False


class IsOwnerOrCreate(permissions.BasePermission):
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        logger.info("Method: %s" % request.method)
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        return True


class IsAdminOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Check SuperUser
        if request.user.is_superuser:
            return True
        # Check Portunus Admin
        is_portunus_admin = request.user.groups.filter(
            name=settings.GROUP_PORTUNUS_ADMIN
        ).exists()
        if is_portunus_admin:
            return True
        # Check Owner
        if hasattr(obj, "owner"):
            return obj.owner == request.user
        return False
