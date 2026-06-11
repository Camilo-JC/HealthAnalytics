from rest_framework import permissions
from .rbac import has_module_permission


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and request.user.role == 'admin'


class CanManageUsers(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and has_module_permission(request.user, 'users_manage')
