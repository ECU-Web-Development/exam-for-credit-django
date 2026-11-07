from .models import *
from time import sleep
from celery import shared_task
from .serializers import *
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .permissions import role_for, require_role

@shared_task
def add(x, y):
    return x + y

def editable_task(user_id, id):
    user = get_user_model().objects.get(pk=user_id, is_active=True)
    require_role(user)
    tasks = Task.objects.select_for_update()
    if role_for(user) != "admin":
        tasks = tasks.filter(assigned_to=user)
    return tasks.filter(pk=id).first()


@shared_task
def celery_update_task(user_id, id, data):
    with transaction.atomic():
        task = editable_task(user_id, id)
        if task is None:
            raise ValueError("Task no longer available")
        was_complete = task.is_complete
        for field, value in data.items():
            setattr(task, field, value)
        task.save(update_fields=list(data))
        if not was_complete and task.is_complete:
            transaction.on_commit(lambda: notify_user_of_completion.delay(
                task.assigned_to_id, task.body, {"task_id": task.pk}
            ))


@shared_task
def celery_delete_task(user_id, id):
    with transaction.atomic():
        task = editable_task(user_id, id)
        if task is not None:
            task.delete()


@shared_task
def celery_register_user(admin_id, username, password_hash, role='user'):
    with transaction.atomic():
        require_role(get_user_model().objects.get(pk=admin_id), admin=True)
        user = get_user_model().objects.create(username=username, password=password_hash, is_staff=role == 'admin')
        if role != 'none':
            user.groups.add(Group.objects.get(name=role))


@shared_task
def celery_add_task(user_id, data):
    user = get_user_model().objects.get(pk=user_id, is_active=True)
    require_role(user)
    sleep(6)
    with transaction.atomic():
        task = Task.objects.create(assigned_to=user, **data)
        transaction.on_commit(lambda: notify_user_of_completion.delay(
            user.pk, task.body, {"task_id": task.pk, "event": "Created"}
        ))


@shared_task
def celery_manage_user(admin_id, user_id, method, data):
    with transaction.atomic():
        require_role(get_user_model().objects.get(pk=admin_id), admin=True)
        user = get_user_model().objects.select_for_update().get(pk=user_id)
        if method == 'DELETE':
            user.delete()
        else:
            role = data['role']
            user.groups.remove(*Group.objects.filter(name__in=['user', 'admin']))
            if role != 'none':
                user.groups.add(Group.objects.get(name=role))
            user.is_staff = role == 'admin'
            if role != 'admin':
                user.is_superuser = False
            user.save(update_fields=['is_staff', 'is_superuser'])


@shared_task
def celery_manage_role(admin_id, role_id, method, name):
    with transaction.atomic():
        require_role(get_user_model().objects.get(pk=admin_id), admin=True)
        if method == 'POST':
            Group.objects.create(name=name)
        else:
            group = Group.objects.select_for_update().get(pk=role_id)
            if group.name in ('user', 'admin'):
                raise ValueError('Built-in roles are protected.')
            if method == 'DELETE':
                group.delete()
            else:
                group.name = name
                group.save(update_fields=['name'])

@shared_task
def notify_user_of_completion(user_id, task_title, task_details):
    Notification.objects.create(
        recipient_id=user_id,
        task_id=task_details["task_id"],
        message=f"{task_details.get('event', 'Completed')}: {task_title}",
    )


@shared_task
def celery_add_comment(user_id, task_id, message):
    with transaction.atomic():
        task = editable_task(user_id, task_id)
        if task is None:
            raise ValueError("Task no longer available")
        TaskComment.objects.create(task=task, author_id=user_id, message=message)
