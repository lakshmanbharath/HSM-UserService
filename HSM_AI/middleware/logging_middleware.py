# middleware/logging_middleware.py
import logging
from datetime import datetime

logger = logging.getLogger("django.request")

class APILoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user = request.user if request.user.is_authenticated else None

        # Just a dict, not json.dumps()
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": getattr(user, "id", None),
            "action": f"{request.method} {request.path}",
            "status": "success" if response.status_code < 400 else "error",
            "status_code": response.status_code,
            "ip": self.get_client_ip(request),
            "details": {"method": request.method, "path": request.path},
        }

        logger.info("API log", extra={"structured": log_data})
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        return x_forwarded_for.split(",")[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")
