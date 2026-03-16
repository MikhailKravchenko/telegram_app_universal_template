from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum, Count
from .models import Investment, UserPresaleStats, Presale


@receiver(post_save, sender=Investment)
def update_user_presale_stats(sender, instance, created, **kwargs):
    """Обновление статистики пользователя при создании инвестиции"""
    if created:
        user = instance.user
        stats, created = UserPresaleStats.objects.get_or_create(user=user)
        
        # Пересчитать статистику пользователя
        user_investments = Investment.objects.filter(user=user)
        aggregated = user_investments.aggregate(
            total_invested=Sum('amount'),
            total_tokens=Sum('tokens_received'),
            count=Count('id')
        )
        
        stats.total_invested = aggregated['total_invested'] or 0
        stats.total_tokens = aggregated['total_tokens'] or 0
        stats.investments_count = aggregated['count'] or 0
        
        if stats.investments_count > 0:
            if not stats.first_investment_at:
                stats.first_investment_at = user_investments.order_by('created_at').first().created_at
            stats.last_investment_at = user_investments.order_by('-created_at').first().created_at
        
        stats.save()
        
        # Обновить общую статистику пресейла
        presale = instance.presale
        presale_aggregated = Investment.objects.filter(presale=presale).aggregate(
            total_invested=Sum('amount'),
            total_tokens=Sum('tokens_received')
        )
        
        presale.total_invested = presale_aggregated['total_invested'] or 0
        presale.total_tokens_sold = presale_aggregated['total_tokens'] or 0
        presale.save(update_fields=['total_invested', 'total_tokens_sold'])
