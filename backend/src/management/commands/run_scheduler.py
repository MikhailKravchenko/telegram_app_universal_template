from datetime import datetime, time

from apscheduler.schedulers.background import BlockingScheduler
from django.core.management.base import BaseCommand

from src.accounts.tasks import (
    expire_bonuses, cleanup_old_bonuses, auto_activate_daily_bonuses, bonus_statistics_update,
    cleanup_old_activities,  # calculate_hourly_activity_bonuses - REMOVED: bonuses now instant
    update_referral_statistics, cleanup_old_referral_bonuses, 
    process_pending_referrals, send_referral_level_notifications
)
from src.betting.tasks import round_starter, round_closer_and_settler, news_fetcher, orphan_guard, long_round_starter
from src.presale.tasks import (
    check_and_advance_presale_rounds, auto_create_presale_if_none_active,
    cleanup_old_investments, update_presale_statistics, send_presale_notifications
)


class Command(BaseCommand):
    help = "Run blocking scheduler to create periodical tasks"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Preparing scheduler"))
        scheduler = BlockingScheduler()

        # Betting game tasks
        # Короткие раунды (5 минут) - каждые 5 минут
        scheduler.add_job(round_starter.send, "interval", minutes=5)
        # Длинные раунды (24 часа) - каждый день в 23:00 (создается раунд на следующие сутки)
        scheduler.add_job(long_round_starter.send, "cron", hour=23, minute=0)
        # Обработка и закрытие раундов - каждую минуту
        scheduler.add_job(round_closer_and_settler.send, "interval", minutes=1)
        # Загрузка новостей - каждые 3 минуты
        scheduler.add_job(news_fetcher.send, "interval", minutes=3)
        # orphan_guard каждые 5 минут со сдвигом на 2 минуты
        scheduler.add_job(orphan_guard.send, "interval", minutes=5, 
                         start_date=datetime.combine(datetime.today(), time(0, 2)))

        # Bonus system tasks
        # Истечение бонусов каждый час
        scheduler.add_job(expire_bonuses.send, "interval", hours=1)
        
        # Очистка старых бонусов раз в день в 3:00
        scheduler.add_job(cleanup_old_bonuses.send, "interval", days=1,
                         start_date=datetime.combine(datetime.today(), time(3, 0)))
        
        # Автоактивация ежедневных бонусов каждые 30 минут
        scheduler.add_job(auto_activate_daily_bonuses.send, "interval", minutes=30)
        
        # Статистика бонусов каждый час со сдвигом на 15 минут
        scheduler.add_job(bonus_statistics_update.send, "interval", hours=1,
                         start_date=datetime.combine(datetime.today(), time(0, 15)))
        
        # Activity system tasks
        # NOTE: calculate_hourly_activity_bonuses REMOVED - bonuses now granted instantly on bet
        
        # Очистка старых записей активности раз в день в 4:00
        scheduler.add_job(cleanup_old_activities.send, "interval", days=1,
                         start_date=datetime.combine(datetime.today(), time(4, 0)))
        
        # Presale system tasks
        # Проверка и переход между раундами каждые 30 минут
        scheduler.add_job(check_and_advance_presale_rounds.send, "interval", minutes=30)
        
        # Автосоздание пресейла если нет активных каждый час
        scheduler.add_job(auto_create_presale_if_none_active.send, "interval", hours=1)
        
        # Обновление статистики каждые 15 минут со сдвигом на 5 минут
        scheduler.add_job(update_presale_statistics.send, "interval", minutes=15,
                         start_date=datetime.combine(datetime.today(), time(0, 5)))
        
        # Отправка уведомлений каждые 10 минут
        scheduler.add_job(send_presale_notifications.send, "interval", minutes=10)
        
        # Очистка старых инвестиций еженедельно в воскресенье в 5:00
        scheduler.add_job(cleanup_old_investments.send, "interval", weeks=1,
                         start_date=datetime.combine(datetime.today(), time(5, 0)))

        # Referral system tasks
        # Обновление статистики рефералов каждые 30 минут со сдвигом на 10 минут
        scheduler.add_job(update_referral_statistics.send, "interval", minutes=30,
                         start_date=datetime.combine(datetime.today(), time(0, 10)))
        
        # Очистка старых реферальных бонусов еженедельно в понедельник в 6:00
        scheduler.add_job(cleanup_old_referral_bonuses.send, "interval", weeks=1,
                         start_date=datetime.combine(datetime.today(), time(6, 0)))
        
        # Обработка ожидающих рефералов каждый час со сдвигом на 30 минут
        scheduler.add_job(process_pending_referrals.send, "interval", hours=1,
                         start_date=datetime.combine(datetime.today(), time(0, 30)))
        
        # Уведомления о достижении уровней каждые 2 часа со сдвигом на 45 минут
        scheduler.add_job(send_referral_level_notifications.send, "interval", hours=2,
                         start_date=datetime.combine(datetime.today(), time(0, 45)))

        self.stdout.write(self.style.NOTICE("Start scheduler"))
        scheduler.start()
