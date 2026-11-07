from . import views
from django.urls import path, include
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from django.conf import settings


urlpatterns = [
    path("tasks/<int:id>/comments", views.add_comment, name="add-comment"),
    path("notifications", views.notifications, name="notifications"),
    path("accounts", views.accounts, name="accounts"),
    path("logout", views.logout, name="logout"),
    path("add-task", views.add_task, name="add-task"),
    path("register", views.register, name="register"),
    path("", views.index, name="index"),
    path("login", views.login, name="login"),
    path("tasks", views.show_tasks, name="tasks"),

    path("get-tasks", views.get_tasks, name="get-tasks"),
    path("tasks/<int:id>/edit", views.edit_task, name="edit-task"),
    path("tasks/<int:id>/update", views.update_task, name="update-task"),
    path("tasks/<int:id>/delete", views.delete_task, name="delete-task"),
    path("operations/<str:token>", views.operation_status, name="operation-status"),
]