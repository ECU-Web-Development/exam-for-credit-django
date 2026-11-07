from . import views
from django.urls import path, include


urlpatterns = [
    path("tasks/<int:id>/comments", views.add_comment, name="add-comment"),
    path("notifications", views.notifications, name="notifications"),
    path("me", views.me, name="me"),
    path("users", views.users, name="users"),
    path("users/<int:id>", views.users, name="user-detail"),
    path("roles", views.roles, name="roles"),
    path("roles/<int:id>", views.roles, name="role-detail"),
    path("add-task", views.add_task, name="add-task"),
    path("register", views.register, name="register"),
    path("get-tasks", views.get_tasks, name="get-tasks"),
    path("tasks/<int:id>", views.task_detail, name="task-detail"),
    path("operations/<str:token>", views.operation_status, name="operation-status")
]