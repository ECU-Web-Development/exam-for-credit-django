from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import *
import requests
from .serializers import *
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.contrib.auth.forms import UserCreationForm
from rest_framework.decorators import api_view, throttle_classes, permission_classes, authentication_classes
from django.shortcuts import get_object_or_404
from django.core import signing
from celery.result import AsyncResult
from .tasks import *
from django.contrib.auth.models import Group
from .logging import correlation_id, log
from .permissions import role_for, HasApplicationRole, HasAdminRole

@api_view(['GET', 'POST'])
@permission_classes([HasApplicationRole])
def get_tasks(request):
    task = owned_tasks(request.user).prefetch_related("comments__author")
    # # print(task.body)
    serialized_task = TaskSerializer(task, many=True).data
    # serialized_task = celery_get_tasks.delay(request)
    return JsonResponse({"tasks" : serialized_task})

def owned_tasks(user):
    return Task.objects.all() if role_for(user) == "admin" else Task.objects.filter(assigned_to=user)


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([HasApplicationRole])
def task_detail(request, id):
    task = get_object_or_404(owned_tasks(request.user), pk=id)
    if request.method == 'GET':
        return JsonResponse(TaskSerializer(task).data)
    if request.method == 'POST':
        serializer = TaskSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = {key: value for key, value in serializer.validated_data.items()
                if key in ('body', 'description', 'is_complete')}
        job = celery_update_task.delay(request.user.id, id, data)
    else:
        job = celery_delete_task.delay(request.user.id, id)
    token = signing.dumps({'job': job.id, 'user': request.user.id, 'correlation_id': correlation_id.get()})
    return JsonResponse({'operation': token}, status=202)


@api_view(['GET'])
@permission_classes([HasApplicationRole])
def operation_status(request, token):
    try:
        operation = signing.loads(token, max_age=3600)
    except signing.BadSignature:
        return JsonResponse({'error': 'Invalid operation'}, status=404)
    if operation['user'] != request.user.id and role_for(request.user) != 'admin':
        return JsonResponse({'error': 'Not found'}, status=404)
    job = AsyncResult(operation['job'])
    log('api', 'operation_polled', operation_id=operation['job'],
        original_correlation_id=operation.get('correlation_id', ''), outcome=job.state)
    return JsonResponse({'status': job.state})


@api_view(['POST'])
@permission_classes([HasAdminRole])
def register(request):
    form = UserCreationForm({
        'username': request.data.get('username', ''),
        'password1': request.data.get('password', ''),
        'password2': request.data.get('password', ''),
    })
    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)
    user = form.save(commit=False)  # Hash the password without writing an account.
    role = request.data.get('role', 'user')
    if role not in ('user', 'admin', 'none'):
        return JsonResponse({'errors': {'role': ['Invalid role.']}}, status=400)
    job = celery_register_user.delay(request.user.id, user.username, user.password, role)
    token = signing.dumps({'job': job.id, 'user': request.user.id, 'correlation_id': correlation_id.get()})
    return JsonResponse({'operation': token}, status=202)


@api_view(['POST'])
@permission_classes([HasApplicationRole])
def add_task(request):
    data = {key: request.data[key] for key in ('body', 'description', 'is_complete') if key in request.data}
    serializer = TaskSerializer(data={**data, 'assigned_to': request.user.id})
    serializer.is_valid(raise_exception=True)
    job = celery_add_task.delay(request.user.id, data)
    token = signing.dumps({'job': job.id, 'user': request.user.id, 'correlation_id': correlation_id.get()})
    return JsonResponse({'operation': token}, status=202)


@api_view(['GET'])
@permission_classes([HasApplicationRole])
def me(request):
    return JsonResponse({'username': request.user.username, 'role': role_for(request.user)})


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([HasAdminRole])
def users(request, id=None):
    User = get_user_model()
    if request.method == 'GET':
        accounts = User.objects.all() if id is None else [get_object_or_404(User, pk=id)]
        return JsonResponse({'users': [{'id': u.pk, 'username': u.username, 'role': role_for(u)} for u in accounts]})
    get_object_or_404(User, pk=id)
    data = {}
    if request.method == 'PATCH':
        role = request.data.get('role')
        if role not in ('user', 'admin', 'none'):
            return JsonResponse({'error': 'Choose user, admin, or none.'}, status=400)
        data['role'] = role
    job = celery_manage_user.delay(request.user.id, id, request.method, data)
    return JsonResponse({'operation': signing.dumps({'job': job.id, 'user': request.user.id, 'correlation_id': correlation_id.get()})}, status=202)


@api_view(['GET', 'POST', 'PATCH', 'DELETE'])
@permission_classes([HasAdminRole])
def roles(request, id=None):
    if request.method == 'GET':
        groups = Group.objects.all() if id is None else [get_object_or_404(Group, pk=id)]
        return JsonResponse({'roles': [{'id': g.pk, 'name': g.name} for g in groups]})
    if request.method != 'POST':
        group = get_object_or_404(Group, pk=id)
        if group.name in ('user', 'admin'):
            return JsonResponse({'error': 'Built-in application roles cannot be renamed or deleted.'}, status=400)
    name = request.data.get('name', '').strip()
    if request.method != 'DELETE' and (not name or len(name) > 150 or Group.objects.filter(name=name).exclude(pk=id).exists()):
        return JsonResponse({'error': 'Provide a unique role name, at most 150 characters.'}, status=400)
    job = celery_manage_role.delay(request.user.id, id, request.method, name)
    return JsonResponse({'operation': signing.dumps({'job': job.id, 'user': request.user.id, 'correlation_id': correlation_id.get()})}, status=202)


@api_view(['GET'])
@permission_classes([HasApplicationRole])
def notifications(request):
    items = Notification.objects.all() if role_for(request.user) == 'admin' else Notification.objects.filter(recipient=request.user)
    return JsonResponse({'notifications': list(items.order_by('-id').values('id', 'message'))})


@api_view(['POST'])
@permission_classes([HasApplicationRole])
def add_comment(request, id):
    get_object_or_404(owned_tasks(request.user), pk=id)
    serializer = TaskCommentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    job = celery_add_comment.delay(request.user.id, id, serializer.validated_data['message'])
    token = signing.dumps({'job': job.id, 'user': request.user.id, 'correlation_id': correlation_id.get()})
    return JsonResponse({'operation': token}, status=202)
