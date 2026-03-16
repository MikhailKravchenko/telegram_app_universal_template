from django.db.models.signals import post_save
from django.dispatch import receiver

from src.accounts.models import CustomUser, UserBalance, Transaction
from src.config import config


@receiver(post_save, sender=CustomUser)
def create_user_balance(created: bool, instance: CustomUser, **kwargs) -> None:
    """
    Create UserBalance and starting balance transaction for new users
    """
    if created:
        # Create UserBalance record
        user_balance = UserBalance.objects.create(
            user=instance,
            coins_balance=0,
            total_earned=0,
            total_spent=0
        )
        
        # Create starting balance transaction
        Transaction.objects.create(
            user=instance,
            amount=config.STARTING_BALANCE,
            type='starting_balance',
            description=f'Starting balance for new user: {config.STARTING_BALANCE} coins'
        )