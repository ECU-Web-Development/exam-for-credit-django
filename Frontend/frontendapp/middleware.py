import requests
from django.http import HttpResponse
from django.shortcuts import redirect
from .views import task_api


class ApplicationAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view, args, kwargs):
        if request.resolver_match.url_name not in {
            'index', 'tasks', 'get-tasks', 'edit-task', 'add-task', 'notifications',
            'update-task', 'delete-task', 'add-comment', 'operation-status', 'register', 'accounts',
        }:
            return
        if not request.session.get('access_token'):
            return redirect('login')
        try:
            response = task_api(request, 'GET', 'me')
            if response.status_code == 401:
                request.session.flush()
                return redirect('login')
            if response.status_code == 403:
                return HttpResponse('Your account has no application role.', status=403)
            response.raise_for_status()
            request.application_role = response.json()['role']
            if request.resolver_match.url_name in ('register', 'accounts') and request.application_role != 'admin':
                return HttpResponse('Administrator role required.', status=403)
        except (requests.RequestException, ValueError, KeyError):
            return HttpResponse('Unable to check account access.', status=503)
