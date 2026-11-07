from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


def role_for(user):
    if not user.is_authenticated or not user.is_active:
        return 'none'
    if user.is_superuser or user.groups.filter(name='admin').exists():
        return 'admin'
    return 'user' if user.groups.filter(name='user').exists() else 'none'


class HasApplicationRole(BasePermission):
    def has_permission(self, request, view):
        return role_for(request.user) in ('user', 'admin')


class HasAdminRole(BasePermission):
    def has_permission(self, request, view):
        return role_for(request.user) == 'admin'


def require_role(user, admin=False):
    role = role_for(user)
    if role == 'none' or (admin and role != 'admin'):
        raise PermissionDenied('Current account role does not permit this action.')
