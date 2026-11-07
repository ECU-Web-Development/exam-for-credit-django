SERVICE = "frontend"
import json
import re
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone

correlation_id = ContextVar("correlation_id", default="")
operation_id = ContextVar("operation_id", default="")


def log(service, event, severity="INFO", **fields):
    print(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(),
                      "severity": severity, "service": service, "event": event,
                      "correlation_id": correlation_id.get(), **fields}), flush=True)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.headers.get("X-Correlation-ID", "")
        value = incoming if re.fullmatch(r"[A-Za-z0-9_-]{1,64}", incoming) else str(uuid.uuid4())
        token = correlation_id.set(value)
        try:
            response = self.get_response(request)
            response["X-Correlation-ID"] = value
            if response.status_code >= 400 and response.get("Content-Type", "").startswith("application/json"):
                data = json.loads(response.content)
                if isinstance(data, dict):
                    data["correlation_id"] = value
                    response.content = json.dumps(data)
                    if response.has_header("Content-Length"):
                        response["Content-Length"] = len(response.content)
            route = request.resolver_match.view_name if request.resolver_match else "unmatched"
            log(SERVICE, "request_finished", severity="ERROR" if response.status_code >= 500 else "INFO",
                method=request.method, route=route, status=response.status_code,
                outcome="accepted" if response.status_code == 202 else "failed" if response.status_code >= 400 else "succeeded")
            return response
        finally:
            correlation_id.reset(token)
