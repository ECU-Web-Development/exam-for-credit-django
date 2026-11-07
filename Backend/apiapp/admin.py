from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import Task, Notification, TaskComment
from .permissions import role_for


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return role_for(request.user) == 'admin'

    def has_view_permission(self, request, obj=None):
        return role_for(request.user) == 'admin'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# Mutations use the queued application APIs/screens instead of synchronous admin saves.
for model in (get_user_model(), Group, Task, Notification, TaskComment):
    if admin.site.is_registered(model):
        admin.site.unregister(model)
    admin.site.register(model, ReadOnlyAdmin)
