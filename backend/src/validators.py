from typing import Any

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _








def validate_positive_integer(value: Any) -> None:
    """Positive integer validation."""
    try:
        int_value = int(value)
        if int_value < 0:
            raise ValidationError(_("Value must be a positive number"))
    except (ValueError, TypeError):
        raise ValidationError(_("Value must be an integer"))


def validate_balance_limit(value: int) -> None:
    """Balance limit validation."""
    if value < 0:
        raise ValidationError(_("Balance cannot be negative"))
    if value > 999999999:  # Maximum balance
        raise ValidationError(_("Balance exceeds maximum allowed value"))


def validate_points_limit(value: int) -> None:
    """Points limit validation."""
    if value < 0:
        raise ValidationError(_("Points cannot be negative"))
    if value > 999999:  # Maximum number of points
        raise ValidationError(_("Number of points exceeds maximum allowed value"))


def validate_price_limit(value: int) -> None:
    """Price limit validation."""
    if value < 0:
        raise ValidationError(_("Price cannot be negative"))
    if value > 999999:  # Maximum price
        raise ValidationError(_("Price exceeds maximum allowed value"))


def validate_game_damage(value: int) -> None:
    """Game element damage validation."""
    if value < 0:
        raise ValidationError(_("Damage cannot be negative"))
    if value > 1000:  # Maximum damage
        raise ValidationError(_("Damage exceeds maximum allowed value"))


def validate_game_health(value: int) -> None:
    """Game element health validation."""
    if value < 0:
        raise ValidationError(_("Health cannot be negative"))
    if value > 10000:  # Maximum health
        raise ValidationError(_("Health exceeds maximum allowed value"))


def validate_game_fire_rate(value: float) -> None:
    """Game element fire rate validation."""
    if value < 0:
        raise ValidationError(_("Fire rate cannot be negative"))
    if value > 10.0:  # Maximum fire rate
        raise ValidationError(_("Fire rate exceeds maximum allowed value"))


def validate_game_record(value: int) -> None:
    """Game record validation."""
    if value < 0:
        raise ValidationError(_("Record cannot be negative"))
    if value > 9999999:  # Maximum record
        raise ValidationError(_("Record exceeds maximum allowed value"))


def validate_config_coefficient(value: float) -> None:
    """Configuration coefficient validation."""
    if value < 0:
        raise ValidationError(_("Coefficient cannot be negative"))
    if value > 100.0:  # Maximum coefficient
        raise ValidationError(_("Coefficient exceeds maximum allowed value"))


def validate_file_size(value: int) -> None:
    """File size validation (in bytes)."""
    if value < 0:
        raise ValidationError(_("File size cannot be negative"))
    if value > 10 * 1024 * 1024:  # Maximum 10MB
        raise ValidationError(_("File size exceeds maximum allowed value (10MB)"))
