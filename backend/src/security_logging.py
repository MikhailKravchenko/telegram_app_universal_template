import json
import logging
from typing import Any, Callable, Optional

from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.utils import timezone

# Create security logger
security_logger = logging.getLogger("security")


class SecurityLogger:
    """Class for logging security events."""

    @staticmethod
    def log_auth_failure(request: HttpRequest, username: str, reason: str) -> None:
        """Log failed authentication attempt."""
        log_data = {
            "event_type": "auth_failure",
            "timestamp": timezone.now().isoformat(),
            "ip_address": SecurityLogger._get_client_ip(request),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "username": username,
            "reason": reason,
            "path": request.path,
            "method": request.method,
        }
        security_logger.warning(f"Authentication failure: {json.dumps(log_data)}")

    @staticmethod
    def log_rate_limit_violation(
        request: HttpRequest, endpoint: str, limit: str
    ) -> None:
        """Log rate limit violation."""
        log_data = {
            "event_type": "rate_limit_violation",
            "timestamp": timezone.now().isoformat(),
            "ip_address": SecurityLogger._get_client_ip(request),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "endpoint": endpoint,
            "limit": limit,
            "path": request.path,
            "method": request.method,
        }
        security_logger.warning(f"Rate limit violation: {json.dumps(log_data)}")

    @staticmethod
    def log_suspicious_activity(
        request: HttpRequest, activity_type: str, details: str
    ) -> None:
        """Log suspicious activity."""
        log_data = {
            "event_type": "suspicious_activity",
            "timestamp": timezone.now().isoformat(),
            "ip_address": SecurityLogger._get_client_ip(request),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "activity_type": activity_type,
            "details": details,
            "path": request.path,
            "method": request.method,
        }
        security_logger.warning(f"Suspicious activity: {json.dumps(log_data)}")

    @staticmethod
    def log_balance_change(
        request: HttpRequest,
        user: User,
        old_balance: int,
        new_balance: int,
        reason: str,
    ) -> None:
        """Log user balance change."""
        log_data = {
            "event_type": "balance_change",
            "timestamp": timezone.now().isoformat(),
            "ip_address": SecurityLogger._get_client_ip(request),
            "user_id": user.id,
            "username": user.username,
            "old_balance": old_balance,
            "new_balance": new_balance,
            "change_amount": new_balance - old_balance,
            "reason": reason,
            "path": request.path,
            "method": request.method,
        }
        security_logger.info(f"Balance change: {json.dumps(log_data)}")

    @staticmethod
    def log_admin_action(
        request: HttpRequest, user: User, action: str, target: str, details: str
    ) -> None:
        """Log administrator actions."""
        log_data = {
            "event_type": "admin_action",
            "timestamp": timezone.now().isoformat(),
            "ip_address": SecurityLogger._get_client_ip(request),
            "admin_user_id": user.id,
            "admin_username": user.username,
            "action": action,
            "target": target,
            "details": details,
            "path": request.path,
            "method": request.method,
        }
        security_logger.info(f"Admin action: {json.dumps(log_data)}")

    @staticmethod
    def log_file_upload(
        request: HttpRequest, user: User, filename: str, file_size: int
    ) -> None:
        """Log file uploads."""
        log_data = {
            "event_type": "file_upload",
            "timestamp": timezone.now().isoformat(),
            "ip_address": SecurityLogger._get_client_ip(request),
            "user_id": user.id if user.is_authenticated else None,
            "username": user.username if user.is_authenticated else "anonymous",
            "filename": filename,
            "file_size": file_size,
            "path": request.path,
            "method": request.method,
        }
        security_logger.info(f"File upload: {json.dumps(log_data)}")

    @staticmethod
    def log_purchase_modification(
        request: HttpRequest,
        user: User,
        modification_type: str,
        price: int,
        element_template: str,
    ) -> None:
        """Log modification purchase."""
        log_data = {
            "event_type": "purchase_modification",
            "timestamp": timezone.now().isoformat(),
            "ip_address": SecurityLogger._get_client_ip(request),
            "user_id": user.id,
            "username": user.username,
            "modification_type": modification_type,
            "price": price,
            "element_template": element_template,
            "path": request.path,
            "method": request.method,
        }
        security_logger.info(f"Purchase modification: {json.dumps(log_data)}")

    @staticmethod
    def log_purchase_weapon(
        request: HttpRequest, user: User, weapon_name: str, price: int
    ) -> None:
        """Log weapon purchase."""
        log_data = {
            "event_type": "purchase_weapon",
            "timestamp": timezone.now().isoformat(),
            "ip_address": SecurityLogger._get_client_ip(request),
            "user_id": user.id,
            "username": user.username,
            "weapon_name": weapon_name,
            "price": price,
            "path": request.path,
            "method": request.method,
        }
        security_logger.info(f"Purchase weapon: {json.dumps(log_data)}")

    @staticmethod
    def log_wheel_spin(
        request: HttpRequest, user: User, result: str, points_spent: int
    ) -> None:
        """Log wheel of fortune spin."""
        log_data = {
            "event_type": "wheel_spin",
            "timestamp": timezone.now().isoformat(),
            "ip_address": SecurityLogger._get_client_ip(request),
            "user_id": user.id,
            "username": user.username,
            "result": result,
            "points_spent": points_spent,
            "path": request.path,
            "method": request.method,
        }
        security_logger.info(f"Wheel spin: {json.dumps(log_data)}")

    @staticmethod
    def log_game_result(
        request: HttpRequest, user: User, game_id: str, score: int, duration: int
    ) -> None:
        """Log game result."""
        log_data = {
            "event_type": "game_result",
            "timestamp": timezone.now().isoformat(),
            "ip_address": SecurityLogger._get_client_ip(request),
            "user_id": user.id,
            "username": user.username,
            "game_id": game_id,
            "score": score,
            "duration": duration,
            "path": request.path,
            "method": request.method,
        }
        security_logger.info(f"Game result: {json.dumps(log_data)}")

    @staticmethod
    def log_configuration_change(
        request: HttpRequest,
        user: User,
        field_name: str,
        old_value: Any,
        new_value: Any,
    ) -> None:
        """Log configuration change."""
        log_data = {
            "event_type": "configuration_change",
            "timestamp": timezone.now().isoformat(),
            "ip_address": SecurityLogger._get_client_ip(request),
            "user_id": user.id,
            "username": user.username,
            "field_name": field_name,
            "old_value": old_value,
            "new_value": new_value,
            "path": request.path,
            "method": request.method,
        }
        security_logger.warning(f"Configuration change: {json.dumps(log_data)}")

    @staticmethod
    def log_referral_activity(
        request: HttpRequest, user: User, referred_user: User, action: str
    ) -> None:
        """Log referral activity."""
        log_data = {
            "event_type": "referral_activity",
            "timestamp": timezone.now().isoformat(),
            "ip_address": SecurityLogger._get_client_ip(request),
            "user_id": user.id,
            "username": user.username,
            "referred_user_id": referred_user.id,
            "referred_username": referred_user.username,
            "action": action,
            "path": request.path,
            "method": request.method,
        }
        security_logger.info(f"Referral activity: {json.dumps(log_data)}")

    @staticmethod
    def log_suspicious_game_data(
        request: HttpRequest, user: User, data_type: str, value: Any, threshold: Any
    ) -> None:
        """Log suspicious game data."""
        log_data = {
            "event_type": "suspicious_game_data",
            "timestamp": timezone.now().isoformat(),
            "ip_address": SecurityLogger._get_client_ip(request),
            "user_id": user.id,
            "username": user.username,
            "data_type": data_type,
            "value": value,
            "threshold": threshold,
            "path": request.path,
            "method": request.method,
        }
        security_logger.warning(f"Suspicious game data: {json.dumps(log_data)}")

    @staticmethod
    def log_api_access(
        request: HttpRequest, user: Optional[User], endpoint: str, response_status: int
    ) -> None:
        """Log access to API endpoints."""
        # Log only critical endpoints or errors
        if response_status >= 400 or endpoint in ["/api/v1/admin/", "/api/v1/game/"]:
            log_data = {
                "event_type": "api_access",
                "timestamp": timezone.now().isoformat(),
                "ip_address": SecurityLogger._get_client_ip(request),
                "user_id": user.id if user and user.is_authenticated else None,
                "username": user.username
                if user and user.is_authenticated
                else "anonymous",
                "endpoint": endpoint,
                "response_status": response_status,
                "path": request.path,
                "method": request.method,
            }
            security_logger.info(f"API access: {json.dumps(log_data)}")

    @staticmethod
    def _get_client_ip(request: HttpRequest) -> str:
        """Get client IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", "unknown")
        return ip


class SecurityMiddleware:
    """Middleware for security monitoring."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Log suspicious patterns
        self._check_suspicious_patterns(request)

        response = self.get_response(request)

        # Log API access
        if hasattr(request, "user"):
            SecurityLogger.log_api_access(
                request, request.user, request.path, response.status_code
            )

        return response

    def _check_suspicious_patterns(self, request: HttpRequest) -> None:
        """Check for suspicious patterns in request."""
        # Check suspicious User-Agents
        user_agent = request.META.get("HTTP_USER_AGENT", "").lower()
        suspicious_agents = ["bot", "crawler", "scraper", "spider", "curl", "wget"]

        if any(agent in user_agent for agent in suspicious_agents):
            SecurityLogger.log_suspicious_activity(
                request, "suspicious_user_agent", f"User-Agent: {user_agent}"
            )

        # Check suspicious paths
        suspicious_paths = ["/admin/", "/wp-admin/", "/phpmyadmin/", "/config/"]
        if any(path in request.path.lower() for path in suspicious_paths):
            SecurityLogger.log_suspicious_activity(
                request, "suspicious_path_access", f"Path: {request.path}"
            )

        # Check request frequency (basic check)
        if hasattr(request, "session"):
            request_count = request.session.get("request_count", 0)
            request.session["request_count"] = request_count + 1

            if request_count > 100:  # More than 100 requests in session
                SecurityLogger.log_suspicious_activity(
                    request, "high_request_frequency", f"Request count: {request_count}"
                )

        # Check suspicious game endpoints
        if request.path.startswith("/api/v1/game/"):
            self._check_game_endpoints(request)

    def _check_game_endpoints(self, request: HttpRequest) -> None:
        """Check for suspicious activity in game endpoints."""
        # Check game request frequency
        if hasattr(request, "session"):
            game_request_count = request.session.get("game_request_count", 0)
            request.session["game_request_count"] = game_request_count + 1

            if game_request_count > 50:  # More than 50 game requests in session
                SecurityLogger.log_suspicious_activity(
                    request,
                    "high_game_request_frequency",
                    f"Game request count: {game_request_count}",
                )

        # Check suspicious POST requests to game endpoints
        if request.method == "POST" and request.path.endswith("/points/"):
            # Check data size
            content_length = request.META.get("CONTENT_LENGTH", 0)
            if content_length and int(content_length) > 10000:  # More than 10KB data
                SecurityLogger.log_suspicious_activity(
                    request, "large_game_data", f"Content length: {content_length}"
                )

        # Check suspicious game results
        if request.method == "POST" and request.path.endswith("/result/"):
            # Check data size
            content_length = request.META.get("CONTENT_LENGTH", 0)
            if content_length and int(content_length) > 5000:  # More than 5KB data
                SecurityLogger.log_suspicious_activity(
                    request, "large_result_data", f"Content length: {content_length}"
                )
