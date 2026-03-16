import logging
from datetime import datetime, timedelta
from typing import Dict, Type

from django.core.cache import cache

logger = logging.getLogger("security")


class SecurityMonitor:
    """Security monitoring and alert system."""

    # Cache keys
    CACHE_KEY_PREFIX = "security_monitor"
    SUSPICIOUS_IPS_KEY = f"{CACHE_KEY_PREFIX}:suspicious_ips"
    FAILED_LOGINS_KEY = f"{CACHE_KEY_PREFIX}:failed_logins"
    RATE_LIMIT_VIOLATIONS_KEY = f"{CACHE_KEY_PREFIX}:rate_limit_violations"

    # Alert thresholds
    ALERT_THRESHOLDS = {
        "failed_logins_per_hour": 10,
        "rate_limit_violations_per_hour": 20,
        "suspicious_activities_per_hour": 15,
        "admin_actions_per_hour": 50,
    }

    @classmethod
    def record_failed_login(
        cls: Type["SecurityMonitor"], ip_address: str, username: str
    ) -> None:
        """Record failed login attempt."""
        key = f"{cls.FAILED_LOGINS_KEY}:{ip_address}"
        failed_attempts = cache.get(key, [])

        # Add current attempt
        failed_attempts.append(
            {
                "timestamp": datetime.now().isoformat(),
                "username": username,
                "ip_address": ip_address,
            }
        )

        # Keep only attempts from the last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        failed_attempts = [
            attempt
            for attempt in failed_attempts
            if datetime.fromisoformat(attempt["timestamp"]) > one_hour_ago
        ]

        cache.set(key, failed_attempts, 3600)  # Cache for an hour

        # Check threshold for alert
        if len(failed_attempts) >= cls.ALERT_THRESHOLDS["failed_logins_per_hour"]:
            cls._trigger_alert(
                "high_failed_logins",
                {
                    "ip_address": ip_address,
                    "count": len(failed_attempts),
                    "attempts": failed_attempts,
                },
            )

    @classmethod
    def record_rate_limit_violation(
        cls: Type["SecurityMonitor"], ip_address: str, endpoint: str
    ) -> None:
        """Record rate limit violation."""
        key = f"{cls.RATE_LIMIT_VIOLATIONS_KEY}:{ip_address}"
        violations = cache.get(key, [])

        # Add current violation
        violations.append(
            {
                "timestamp": datetime.now().isoformat(),
                "endpoint": endpoint,
                "ip_address": ip_address,
            }
        )

        # Keep only violations from the last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        violations = [
            violation
            for violation in violations
            if datetime.fromisoformat(violation["timestamp"]) > one_hour_ago
        ]

        cache.set(key, violations, 3600)  # Cache for an hour

        # Check threshold for alert
        if len(violations) >= cls.ALERT_THRESHOLDS["rate_limit_violations_per_hour"]:
            cls._trigger_alert(
                "high_rate_limit_violations",
                {
                    "ip_address": ip_address,
                    "count": len(violations),
                    "violations": violations,
                },
            )

    @classmethod
    def record_suspicious_activity(
        cls: Type["SecurityMonitor"], ip_address: str, activity_type: str, details: str
    ) -> None:
        """Record suspicious activity."""
        key = f"{cls.SUSPICIOUS_IPS_KEY}:{ip_address}"
        activities = cache.get(key, [])

        # Add current activity
        activities.append(
            {
                "timestamp": datetime.now().isoformat(),
                "activity_type": activity_type,
                "details": details,
                "ip_address": ip_address,
            }
        )

        # Keep only activities from the last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        activities = [
            activity
            for activity in activities
            if datetime.fromisoformat(activity["timestamp"]) > one_hour_ago
        ]

        cache.set(key, activities, 3600)  # Cache for an hour

        # Check threshold for alert
        if len(activities) >= cls.ALERT_THRESHOLDS["suspicious_activities_per_hour"]:
            cls._trigger_alert(
                "high_suspicious_activities",
                {
                    "ip_address": ip_address,
                    "count": len(activities),
                    "activities": activities,
                },
            )

    @classmethod
    def record_admin_action(
        cls: Type["SecurityMonitor"], admin_user_id: int, action: str, target: str
    ) -> None:
        """Record administrator action."""
        key = f"{cls.CACHE_KEY_PREFIX}:admin_actions:{admin_user_id}"
        actions = cache.get(key, [])

        # Add current action
        actions.append(
            {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "target": target,
                "admin_user_id": admin_user_id,
            }
        )

        # Keep only actions from the last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        actions = [
            action_item
            for action_item in actions
            if datetime.fromisoformat(action_item["timestamp"]) > one_hour_ago
        ]

        cache.set(key, actions, 3600)  # Cache for an hour

        # Check threshold for alert
        if len(actions) >= cls.ALERT_THRESHOLDS["admin_actions_per_hour"]:
            cls._trigger_alert(
                "high_admin_actions",
                {
                    "admin_user_id": admin_user_id,
                    "count": len(actions),
                    "actions": actions,
                },
            )

    @classmethod
    def get_security_stats(cls: Type["SecurityMonitor"]) -> Dict[str, any]:
        """Get security statistics."""
        stats = {
            "failed_logins": {},
            "rate_limit_violations": {},
            "suspicious_activities": {},
            "admin_actions": {},
        }

        # Get failed login statistics
        failed_login_keys = cache.keys(f"{cls.FAILED_LOGINS_KEY}:*")
        for key in failed_login_keys:
            ip_address = key.split(":")[-1]
            attempts = cache.get(key, [])
            if attempts:
                stats["failed_logins"][ip_address] = len(attempts)

        # Get rate limit violation statistics
        rate_limit_keys = cache.keys(f"{cls.RATE_LIMIT_VIOLATIONS_KEY}:*")
        for key in rate_limit_keys:
            ip_address = key.split(":")[-1]
            violations = cache.get(key, [])
            if violations:
                stats["rate_limit_violations"][ip_address] = len(violations)

        # Get suspicious activity statistics
        suspicious_keys = cache.keys(f"{cls.SUSPICIOUS_IPS_KEY}:*")
        for key in suspicious_keys:
            ip_address = key.split(":")[-1]
            activities = cache.get(key, [])
            if activities:
                stats["suspicious_activities"][ip_address] = len(activities)

        return stats

    @classmethod
    def _trigger_alert(
        cls: Type["SecurityMonitor"], alert_type: str, data: Dict[str, any]
    ) -> None:
        """Trigger security alert."""
        alert_message = f"SECURITY ALERT: {alert_type.upper()}"

        # Log alert
        logger.critical(f"{alert_message} - {data}")

        """Here you can add notification sending (email, Slack, etc.)
         cls._send_notification(alert_type, data)"""

    @classmethod
    def _send_notification(
        cls: Type["SecurityMonitor"], alert_type: str, data: Dict[str, any]
    ) -> None:
        """Send security notification."""
        # TODO: Implement notification sending
        # For example, via email, Slack webhook, or other channels
        pass

    @classmethod
    def clear_old_data(cls: Type["SecurityMonitor"]) -> None:
        """Clear old monitoring data."""
        # Clear data older than 24 hours
        cache.delete_pattern(f"{cls.CACHE_KEY_PREFIX}:*")
        logger.info("Cleared old security monitoring data")


class SecurityMetrics:
    """Security metrics for monitoring."""

    @staticmethod
    def get_failed_login_rate() -> float:
        """Get failed login attempt percentage."""
        # TODO: Implement metric calculation
        return 0.0

    @staticmethod
    def get_rate_limit_violation_rate() -> float:
        """Get rate limit violation percentage."""
        # TODO: Implement metric calculation
        return 0.0

    @staticmethod
    def get_suspicious_activity_rate() -> float:
        """Get suspicious activity percentage."""
        # TODO: Implement metric calculation
        return 0.0
