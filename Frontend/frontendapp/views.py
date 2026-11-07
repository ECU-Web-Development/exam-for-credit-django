import requests
from .logging import correlation_id
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


@require_http_methods(["GET", "POST"])
def login(request):
    error = ""
    status = 200
    if request.method == "POST":
        try:
            response = requests.post(
                f"{settings.BACKEND_URL}/api/token/",
                headers={"X-Correlation-ID": correlation_id.get()},
                json={"username": request.POST.get("username", "").strip(), "password": request.POST.get("password", ""),},
                timeout=10,
            )
            print(response.text)
            if response.status_code == 200:
                tokens = response.json()
                access, refresh = tokens["access"], tokens["refresh"]
                request.session.flush()
                request.session["access_token"] = access
                request.session["refresh_token"] = refresh
                return redirect("tasks")

            if response.status_code in (400, 401):
                error = "Invalid username or password."
                status = 401
            else:
                error = "Login service is unavailable. Please try again."
                status = 503
        except (requests.RequestException, ValueError, KeyError, TypeError):
            error = "Login service is unavailable. Please try again."
            status = 503

    return render(request, "frontendapp/login.html", {"error": error}, status=status)

@require_http_methods(["GET"])
@never_cache
def logout(request):
    request.session.flush()
    request.META["CSRF_COOKIE_NEEDS_UPDATE"] = False
    response = redirect("login")
    response.delete_cookie(settings.SESSION_COOKIE_NAME, path=settings.SESSION_COOKIE_PATH, domain=settings.SESSION_COOKIE_DOMAIN)
    response.delete_cookie(settings.CSRF_COOKIE_NAME, path=settings.CSRF_COOKIE_PATH, domain=settings.CSRF_COOKIE_DOMAIN)
    response["HX-Redirect"] = "/login"
    return response

@require_http_methods(["GET"])
@never_cache
def show_tasks(request):
    if not request.session.get("access_token"):
        return redirect("login")
    if request.method == "GET":
        return render(request, "frontendapp/tasks.html")

@require_http_methods(["GET"])
@never_cache
def get_tasks(request):
    try:
        response = task_api(request, "GET", "get-tasks")
        if response.status_code == 401:
            return HttpResponse("", headers={"HX-Redirect": "/login"})
        response.raise_for_status()
        tasks = response.json()["tasks"]
    except (requests.RequestException, ValueError, KeyError):
        return HttpResponse("Unable to load tasks. Please reload to try again.")

    return render(request, "frontendapp/_tasks.html", {"tasks": tasks})

def task_api(request, method, path, **kwargs):
    def send():
        return requests.request(
            method, f"{settings.BACKEND_URL}/api/{path}",
            headers={"Authorization": f"Bearer {request.session.get('access_token', '')}",
                     "X-Correlation-ID": correlation_id.get()},
            timeout=10, **kwargs,
        )

    response = send()
    if response.status_code == 401 and request.session.get("refresh_token"):
        refresh = requests.post(
            f"{settings.BACKEND_URL}/api/token/refresh/",
            json={"refresh": request.session["refresh_token"]}, timeout=10,
            headers={"X-Correlation-ID": correlation_id.get()},
        )
        if refresh.status_code == 200:
            request.session["access_token"] = refresh.json()["access"]
            response = send()
    return response

@require_http_methods(["POST"])
def add_task(request):
    return mutate_task(request, None, "POST")

@require_http_methods(["GET"])
@never_cache
def edit_task(request, id):
    try:
        response = task_api(request, "GET", f"tasks/{id}")
        response.raise_for_status()
        return render(request, "frontendapp/_edit_task.html", {"task": response.json()})
    except (requests.RequestException, ValueError):
        return HttpResponse("Unable to edit task.", status=503)


@require_http_methods(["POST"])
def update_task(request, id):
    return mutate_task(request, id, "POST")


@require_http_methods(["POST"])
def delete_task(request, id):
    return mutate_task(request, id, "DELETE")


def mutate_task(request, id, method):
    data = {"body": request.POST.get("body", ""),
            "description": request.POST.get("description", ""),
            "is_complete": request.POST.get("is_complete") == "on"}
    try:
        response = task_api(request, method, f"tasks/{id}" if id is not None else "add-task",
                            json=data if method == "POST" else None)
        if response.status_code != 202:
            return HttpResponse("Unable to save task. Check your input and login.", status=response.status_code)
        return render(request, "frontendapp/_pending_task.html", response.json(), status=202)
    except (requests.RequestException, ValueError):
        return HttpResponse("Task service unavailable.", status=503)


@require_http_methods(["GET"])
def operation_status(request, token):
    try:
        response = task_api(request, "GET", f"operations/{token}")
        response.raise_for_status()
        state = response.json()["status"]
        if state == "SUCCESS":
            return HttpResponse("", headers={"HX-Trigger": "tasksChanged"})
        if state in ("FAILURE", "REVOKED"):
            return HttpResponse('<div class="row"><p>Task change failed. Reload to try again.</p></div>')
        return render(request, "frontendapp/_pending_task.html", {"operation": token})
    except (requests.RequestException, ValueError):
        return HttpResponse('<div class="row"><p>Unable to check task status. Reload to try again.</p></div>')


@require_http_methods(["GET", "POST"])
def register(request):
    message = ""
    if request.method == "POST":
        try:
            response = task_api(request, "POST", "register", json={
                "username": request.POST.get("username", "").strip(),
                "password": request.POST.get("password", ""),
                "role": request.POST.get("role", "user"),
            })
            if response.status_code == 202:
                message = "Account creation queued."
            elif response.status_code == 400:
                message = " ".join(error for errors in response.json()["errors"].values() for error in errors)
            elif response.status_code in (401, 403):
                message = "Unable to register account."
            else:
                message = "Unable to register account."
        except (requests.RequestException, ValueError, KeyError):
            message = "Registration service unavailable."
    return render(request, "frontendapp/register.html", {"message": message})


@require_http_methods(["GET", "POST"])
@never_cache
def accounts(request):
    message = ""
    try:
        if request.method == "POST":
            kind = request.POST.get("kind")
            if kind not in ("users", "roles"):
                return HttpResponse("Invalid action.", status=400)
            action = request.POST.get("action")
            if action not in ("POST", "PATCH", "DELETE") or (kind == "users" and action == "POST"):
                return HttpResponse("Invalid action.", status=400)
            object_id = request.POST.get("id", "")
            if action != "POST" and not object_id.isdigit():
                return HttpResponse("Invalid ID.", status=400)
            path = kind if action == "POST" else f"{kind}/{object_id}"
            result = task_api(request, action, path, json={"role": request.POST.get("role"), "name": request.POST.get("name", "")})
            message = "Change queued. Reload to see the result." if result.status_code == 202 else "Change rejected."
        users = task_api(request, "GET", "users")
        roles = task_api(request, "GET", "roles")
        users.raise_for_status(); roles.raise_for_status()
        return render(request, "frontendapp/accounts.html", {**users.json(), **roles.json(), "message": message})
    except (requests.RequestException, ValueError):
        return HttpResponse("Account service unavailable.", status=503)


@require_GET
@never_cache
def notifications(request):
    try:
        response = task_api(request, "GET", "notifications")
        response.raise_for_status()
        return render(request, "frontendapp/_notifications.html", response.json())
    except (requests.RequestException, ValueError):
        return HttpResponse("Unable to load notifications.")


@require_http_methods(["POST"])
def add_comment(request, id):
    try:
        response = task_api(request, "POST", f"tasks/{id}/comments",
                            json={"message": request.POST.get("message", "")})
        if response.status_code != 202:
            return HttpResponse("Unable to add comment.", status=response.status_code)
        return render(request, "frontendapp/_pending_task.html", response.json(), status=202)
    except (requests.RequestException, ValueError):
        return HttpResponse("Task service unavailable.", status=503)
