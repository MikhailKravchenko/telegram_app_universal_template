# API Endpoints Documentation

Данный документ содержит описание всех эндпоинтов API проекта Pulse Backend.

## Базовый URL

```
http://localhost:8000/api/v1/
```

## Аутентификация

Большинство эндпоинтов требуют JWT аутентификации. Токен должен быть передан в заголовке:

```
Authorization: Bearer <access_token>
```

---

## 1. Accounts (Аккаунты и аутентификация)

### 1.1 Telegram Login

**Название:** Авторизация через Telegram  
**URL:** `POST /api/v1/accounts/telegram/login/`  
**Аутентификация:** Не требуется

**Input Data:**

```json
{
    "telegramData": "string (max 1000 chars) - Telegram initData string",
    "referredBy": "integer (optional) - ID пользователя, который пригласил"
}
```

**Output Data:**

```json
{
    "access": "string - JWT access token",
    "refresh": "string - JWT refresh token",
    "user": {
        "id": "integer",
        "username": "string",
        "telegram_id": "string",
        "first_name": "string",
        "last_name": "string"
    }
}
```

### 1.2 Telegram Auth Status

**Название:** Проверка статуса авторизации Telegram  
**URL:** `GET /api/v1/accounts/telegram/status/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "authenticated": "boolean",
    "user_id": "integer",
    "username": "string"
}
```

### 1.3 Logout

**Название:** Выход из системы  
**URL:** `POST /api/v1/accounts/logout/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "message": "string - Сообщение об успешном выходе"
}
```

### 1.4 User Info

**Название:** Информация о пользователе  
**URL:** `GET /api/v1/accounts/users/`  
**URL:** `GET /api/v1/accounts/users/{id}/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "id": "integer",
    "username": "string",
    "telegram_id": "string",
    "referral_count": "integer",
    "balance": {
        "coins_balance": "integer",
        "total_earned": "integer",
        "total_spent": "integer",
        "updated_at": "datetime"
    }
}
```

### 1.5 User Balance

**Название:** Баланс пользователя  
**URL:** `GET /api/v1/accounts/balances/`  
**URL:** `GET /api/v1/accounts/balances/{id}/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "coins_balance": "integer",
    "total_earned": "integer",
    "total_spent": "integer",
    "updated_at": "datetime"
}
```

### 1.6 Balance Summary

**Название:** Сводка по балансу  
**URL:** `GET /api/v1/accounts/balance-summary/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "current_balance": "integer",
    "total_earned": "integer",
    "total_spent": "integer",
    "pending_transactions": "integer",
    "last_transaction": {
        "id": "integer",
        "amount": "integer",
        "type": "string",
        "description": "string",
        "created_at": "datetime"
    }
}
```

### 1.7 Transactions

**Название:** История транзакций  
**URL:** `GET /api/v1/accounts/transactions/`  
**URL:** `GET /api/v1/accounts/transactions/{id}/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
[
    {
        "id": "integer",
        "amount": "integer",
        "type": "string",
        "description": "string",
        "reference_id": "string",
        "created_at": "datetime"
    }
]
```

### 1.8 Bonuses

**Название:** Управление бонусами  
**URL:** `GET /api/v1/accounts/bonuses/`  
**URL:** `GET /api/v1/accounts/bonuses/{id}/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
[
    {
        "id": "integer",
        "bonus_type": "string",
        "bonus_type_display": "string",
        "amount": "integer",
        "status": "string",
        "status_display": "string",
        "description": "string",
        "expires_at": "datetime",
        "created_at": "datetime",
        "used_at": "datetime",
        "can_be_used": "boolean",
        "is_expired": "boolean"
    }
]
```

### 1.9 Bonus Statistics

**Название:** Статистика бонусов  
**URL:** `GET /api/v1/accounts/bonuses/statistics/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "total_bonuses": "integer",
    "used_bonuses": "integer",
    "pending_bonuses": "integer",
    "active_bonuses": "integer",
    "expired_bonuses": "integer",
    "total_earned_from_bonuses": "integer",
    "bonus_types_stats": "object",
    "last_bonus": "object"
}
```

### 1.10 Claim Daily Bonus

**Название:** Получение ежедневного бонуса  
**URL:** `POST /api/v1/accounts/bonuses/claim_daily/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "success": "boolean",
    "message": "string",
    "bonus": "object"
}
```

### 1.11 Claim Social Bonus

**Название:** Получение социального бонуса  
**URL:** `POST /api/v1/accounts/bonuses/claim_social/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "success": "boolean",
    "message": "string",
    "bonus": "object"
}
```

### 1.12 Use Bonus

**Название:** Использование бонуса  
**URL:** `POST /api/v1/accounts/bonuses/{id}/use/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "success": "boolean",
    "message": "string",
    "balance_updated": "integer"
}
```

### 1.12.1 Claim Telegram Channel 1 Bonus

**Название:** Получение бонуса за подписку на Telegram канал 1  
**URL:** `POST /api/v1/accounts/bonuses/claim_telegram_channel_1/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "success": "boolean",
    "message": "string",
    "bonus": {
        "id": "integer",
        "amount": "integer",
        "bonus_type": "string",
        "status": "string"
    }
}
```

### 1.12.2 Claim Telegram Channel 2 Bonus

**Название:** Получение бонуса за подписку на Telegram канал 2  
**URL:** `POST /api/v1/accounts/bonuses/claim_telegram_channel_2/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "success": "boolean",
    "message": "string",
    "bonus": {
        "id": "integer",
        "amount": "integer",
        "bonus_type": "string",
        "status": "string"
    }
}
```

### 1.13 Activity Stats

**Название:** Статистика активности  
**URL:** `GET /api/v1/accounts/bonuses/activity_stats/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "total_bets": "integer",
    "total_bet_amount": "decimal",
    "total_winnings": "decimal",
    "win_rate": "decimal",
    "last_bet_date": "datetime",
    "betting_streak": "integer"
}
```

### 1.14 Referral Stats

**Название:** Статистика рефералов  
**URL:** `GET /api/v1/accounts/referrals/my-stats/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "referrals_count": "integer",
    "total_bonuses_earned": "integer",
    "referral_link": "string",
    "current_level": "object",
    "next_level": "object",
    "recent_bonuses": "array",
    "referrals": "array"
}
```

### 1.15 Referral Link

**Название:** Реферальная ссылка  
**URL:** `GET /api/v1/accounts/referrals/my-link/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "referral_link": "string",
    "referral_code": "string"
}
```

### 1.16 Referral Bonuses

**Название:** Бонусы от рефералов  
**URL:** `GET /api/v1/accounts/referrals/my-bonuses/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
[
    {
        "id": "integer",
        "referrer_username": "string",
        "referred_username": "string",
        "investment_amount": "integer",
        "bonus_amount": "integer",
        "bonus_percentage": "decimal",
        "referral_level": "integer",
        "created_at": "datetime"
    }
]
```

### 1.17 Referral Levels

**Название:** Уровни рефералов  
**URL:** `GET /api/v1/accounts/referrals/levels/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
[
    {
        "id": "integer",
        "level": "integer",
        "min_referrals": "integer",
        "bonus_percentage": "decimal",
        "is_active": "boolean",
        "created_at": "datetime"
    }
]
```

### 1.18 Global Referral Stats

**Название:** Глобальная статистика рефералов  
**URL:** `GET /api/v1/accounts/referrals/global-stats/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "total_referrals": "integer",
    "total_bonuses_amount": "integer",
    "total_bonuses_count": "integer",
    "top_referrers": "array",
    "levels_distribution": "array"
}
```

---

## 2. Betting (Ставки)

### 2.1 Game Rounds List

**Название:** Список игровых раундов  
**URL:** `GET /api/v1/betting/rounds/`  
**Аутентификация:** Требуется

**Input Data (Query Parameters):**

- `status` - Статус раунда (open, closed, finished, void)
- `start_time_from` - Начальная дата/время раунда (ISO format)
- `start_time_to` - Конечная дата/время раунда (ISO format)
- `search` - Поиск по заголовку и содержимому новостей
- `ordering` - Сортировка (start_time, end_time, status)
- `page` - Номер страницы
- `page_size` - Размер страницы (максимум 100)

**Output Data:**

```json
{
    "count": "integer",
    "next": "string",
    "previous": "string",
    "results": [
        {
            "id": "integer",
            "start_time": "datetime",
            "end_time": "datetime",
            "status": "string",
            "result": "string",
            "pot_total": "integer",
            "pot_positive": "integer",
            "pot_negative": "integer",
            "fee_applied_rate": "decimal",
            "resolved_at": "datetime",
            "news_title": "string",
            "news_content": "string",
            "news_image_url": "string",
            "bets_count": "integer",
            "time_remaining": "integer",
            "can_bet": "boolean"
        }
    ]
}
```

### 2.2 Game Round Detail

**Название:** Детали игрового раунда  
**URL:** `GET /api/v1/betting/rounds/{id}/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "id": "integer",
    "start_time": "datetime",
    "end_time": "datetime",
    "status": "string",
    "result": "string",
    "pot_total": "integer",
    "pot_positive": "integer",
    "pot_negative": "integer",
    "fee_applied_rate": "decimal",
    "resolved_at": "datetime",
    "news_title": "string",
    "news_content": "string",
    "news_image_url": "string",
    "bets_count": "integer",
    "time_remaining": "integer",
    "can_bet": "boolean"
}
```

### 2.3 Current Round

**Название:** Текущий активный раунд  
**URL:** `GET /api/v1/betting/rounds/current/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "current_round": "object",
    "user_bet": "object",
    "settings": "object",
    "can_place_bet": "boolean"
}
```

### 2.4 Bonus Per Round

**Название:** Автоматическое участие в раунде с бонусом  
**URL:** `POST /api/v1/betting/rounds/bonus_per_round/`  
**Аутентификация:** Требуется

**Input Data:**

```json
{
    "round_id": "integer"
}
```

**Output Data:**

```json
{
    "success": "boolean",
    "message": "string",
    "bonus_info": {
        "amount": "integer",
        "type": "string"
    }
}
```

### 2.5 Bets List

**Название:** Список ставок пользователя  
**URL:** `GET /api/v1/betting/bets/`  
**Аутентификация:** Требуется

**Input Data (Query Parameters):**

- `choice` - Выбор ставки (positive, negative)
- `status` - Статус ставки (pending, won, lost, refunded)
- `amount_from` - Минимальная сумма ставки
- `amount_to` - Максимальная сумма ставки
- `created_at_from` - Начальная дата создания ставки
- `created_at_to` - Конечная дата создания ставки
- `ordering` - Сортировка
- `page` - Номер страницы
- `page_size` - Размер страницы

**Output Data:**

```json
{
    "count": "integer",
    "next": "string",
    "previous": "string",
    "results": [
        {
            "id": "integer",
            "user": "integer",
            "username": "string",
            "round": "integer",
            "round_status": "string",
            "round_result": "string",
            "amount": "integer",
            "choice": "string",
            "status": "string",
            "payout_amount": "integer",
            "payout_coefficient": "decimal",
            "created_at": "datetime"
        }
    ]
}
```

### 2.6 Create Bet

**Название:** Создание ставки  
**URL:** `POST /api/v1/betting/bets/`  
**Аутентификация:** Требуется

**Input Data:**

```json
{
    "round": "integer",
    "amount": "integer",
    "choice": "string (positive/negative)"
}
```

**Output Data:**

```json
{
    "id": "integer",
    "user": "integer",
    "round": "integer",
    "amount": "integer",
    "choice": "string",
    "status": "string",
    "created_at": "datetime"
}
```

### 2.7 Bet Detail

**Название:** Детали ставки  
**URL:** `GET /api/v1/betting/bets/{id}/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "id": "integer",
    "user": "integer",
    "username": "string",
    "round": "integer",
    "round_status": "string",
    "round_result": "string",
    "amount": "integer",
    "choice": "string",
    "status": "string",
    "payout_amount": "integer",
    "payout_coefficient": "decimal",
    "created_at": "datetime"
}
```

### 2.8 News List

**Название:** Список новостей  
**URL:** `GET /api/v1/betting/news/`  
**Аутентификация:** Не требуется

**Input Data (Query Parameters):**

- `page` - Номер страницы
- `page_size` - Размер страницы (максимум 100)

**Output Data:**

```json
{
    "count": "integer",
    "next": "string",
    "previous": "string",
    "results": [
        {
            "id": "integer",
            "title": "string",
            "content": "string",
            "image_url": "string",
            "source_url": "string",
            "category": "string",
            "language": "string",
            "created_at": "datetime"
        }
    ]
}
```

### 2.9 News Detail

**Название:** Детали новости  
**URL:** `GET /api/v1/betting/news/{id}/`  
**Аутентификация:** Не требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "id": "integer",
    "title": "string",
    "content": "string",
    "image_url": "string",
    "source_url": "string",
    "category": "string",
    "language": "string",
    "created_at": "datetime"
}
```

---

## 3. Presale (Предпродажа)

### 3.1 Presales List

**Название:** Список пресейлов  
**URL:** `GET /api/v1/presale/api/presales/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
[
    {
        "id": "integer",
        "name": "string",
        "status": "string",
        "current_round": "integer",
        "total_rounds": "integer",
        "total_invested": "integer",
        "total_tokens_sold": "decimal",
        "current_rate": "decimal",
        "current_round_investment": "integer",
        "current_round_target": "integer",
        "progress_percent": "float",
        "start_time": "datetime",
        "end_time": "datetime",
        "created_at": "datetime",
        "updated_at": "datetime"
    }
]
```

### 3.2 Current Presale

**Название:** Текущий активный пресейл  
**URL:** `GET /api/v1/presale/api/presales/current/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "id": "integer",
    "name": "string",
    "status": "string",
    "current_round": "integer",
    "total_rounds": "integer",
    "total_invested": "integer",
    "total_tokens_sold": "decimal",
    "start_time": "datetime",
    "end_time": "datetime",
    "current_round_info": {
        "round_number": "integer",
        "tokens_per_coin": "decimal",
        "target_investment": "integer",
        "current_investment": "integer",
        "progress_percent": "float",
        "remaining_investment": "integer",
        "is_completed": "boolean"
    }
}
```

### 3.3 Presale Round Info

**Название:** Информация о раунде пресейла  
**URL:** `GET /api/v1/presale/presales/{id}/round_info/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "current_round": {
        "id": "integer",
        "round_number": "integer",
        "price_per_token": "decimal",
        "tokens_available": "decimal",
        "tokens_sold": "decimal",
        "start_time": "datetime",
        "end_time": "datetime",
        "is_active": "boolean"
    },
    "next_round": {
        "id": "integer",
        "round_number": "integer",
        "price_per_token": "decimal",
        "start_time": "datetime"
    }
}
```

### 3.4 Presale Rounds Stats

**Название:** Статистика раундов пресейла  
**URL:** `GET /api/v1/presale/presales/{id}/rounds_stats/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
[
    {
        "round_number": "integer",
        "price_per_token": "decimal",
        "tokens_available": "decimal",
        "tokens_sold": "decimal",
        "total_invested": "decimal",
        "investors_count": "integer",
        "completion_percentage": "decimal",
        "start_time": "datetime",
        "end_time": "datetime",
        "status": "string"
    }
]
```

### 3.5 Presale Rounds List

**Название:** Список раундов пресейла  
**URL:** `GET /api/v1/presale/api/rounds/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
[
    {
        "round_number": "integer",
        "tokens_per_coin": "decimal",
        "target_investment": "integer",
        "is_active": "boolean",
        "created_at": "datetime"
    }
]
```

### 3.6 Create Default Rounds

**Название:** Создание дефолтных раундов  
**URL:** `POST /api/v1/presale/presale-rounds/create_defaults/`  
**Аутентификация:** Требуется (только администраторы)

**Input Data:** Нет

**Output Data:**

```json
{
    "created_count": "integer",
    "rounds": [
        {
            "id": "integer",
            "round_number": "integer",
            "price_per_token": "decimal",
            "tokens_available": "decimal",
            "start_time": "datetime",
            "end_time": "datetime",
            "is_active": "boolean"
        }
    ]
}
```

### 3.7 Investments List

**Название:** Список инвестиций пользователя  
**URL:** `GET /api/v1/presale/api/investments/`  
**Аутентификация:** Требуется

**Input Data (Query Parameters):**

- `page` - Номер страницы
- `page_size` - Размер страницы

**Output Data:**

```json
{
    "count": "integer",
    "next": "string",
    "previous": "string",
    "results": [
        {
            "id": "integer",
            "user": "integer",
            "user_username": "string",
            "presale": "integer",
            "amount": "integer",
            "tokens_received": "decimal",
            "round_number": "integer",
            "rate_at_purchase": "decimal",
            "transaction_id": "string",
            "created_at": "datetime"
        }
    ]
}
```

### 3.8 Create Investment

**Название:** Создание инвестиции  
**URL:** `POST /api/v1/presale/api/investments/`  
**Аутентификация:** Требуется

**Input Data:**

```json
{
    "amount": "integer (min: 10, max: 1000000)"
}
```

**Output Data:**

```json
{
    "id": "integer",
    "user": "integer",
    "user_username": "string",
    "presale": "integer",
    "amount": "integer",
    "tokens_received": "decimal",
    "round_number": "integer",
    "rate_at_purchase": "decimal",
    "transaction_id": "string",
    "created_at": "datetime"
}
```

### 3.9 Investment Summary

**Название:** Сводка инвестиций пользователя  
**URL:** `GET /api/v1/presale/investments/summary/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "total_invested": "decimal",
    "total_tokens": "decimal",
    "investments_count": "integer",
    "average_investment": "decimal",
    "first_investment_date": "datetime",
    "last_investment_date": "datetime"
}
```

### 3.10 All Presales Investments

**Название:** Инвестиции пользователя по всем пресейлам  
**URL:** `GET /api/v1/presale/investments/all_presales/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "total_invested": "decimal",
    "total_tokens": "decimal",
    "investments_count": "integer",
    "average_investment": "decimal",
    "first_investment_date": "datetime",
    "last_investment_date": "datetime"
}
```

### 3.11 User Presale Stats

**Название:** Статистика пользователя по пресейлу  
**URL:** `GET /api/v1/presale/user-presale-stats/my_stats/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "user": "integer",
    "user_username": "string",
    "total_invested": "decimal",
    "total_tokens": "decimal",
    "investments_count": "integer",
    "first_investment_at": "datetime",
    "last_investment_at": "datetime",
    "updated_at": "datetime"
}
```

### 3.12 Leaderboard

**Название:** Топ инвесторов  
**URL:** `GET /api/v1/presale/user-presale-stats/leaderboard/`  
**Аутентификация:** Требуется (только администраторы)

**Input Data:** Нет

**Output Data:**

```json
{
    "top_by_tokens": [
        {
            "user": "integer",
            "user_username": "string",
            "total_invested": "decimal",
            "total_tokens": "decimal",
            "investments_count": "integer"
        }
    ],
    "top_by_investment": [
        {
            "user": "integer",
            "user_username": "string",
            "total_invested": "decimal",
            "total_tokens": "decimal",
            "investments_count": "integer"
        }
    ]
}
```

### 3.13 My Presale Stats

**Название:** Моя статистика по пресейлам  
**URL:** `GET /api/v1/presale/api/user-stats/my_stats/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "user": "integer",
    "user_username": "string",
    "total_invested": "integer",
    "total_tokens": "decimal",
    "investments_count": "integer",
    "first_investment_at": "datetime",
    "last_investment_at": "datetime",
    "updated_at": "datetime"
}
```

### 3.14 Leaderboard

**Название:** Таблица лидеров по инвестициям  
**URL:** `GET /api/v1/presale/api/user-stats/leaderboard/`  
**Аутентификация:** Требуется

**Input Data (Query Parameters):**

- `limit` - Количество записей (по умолчанию 10)

**Output Data:**

```json
[
    {
        "user": "integer",
        "user_username": "string",
        "total_invested": "integer",
        "total_tokens": "decimal",
        "investments_count": "integer",
        "rank": "integer"
    }
]
```

### 3.15 Global Presale Stats

**Название:** Глобальная статистика пресейла  
**URL:** `GET /api/v1/presale/presale-stats/global_stats/`  
**Аутентификация:** Требуется

**Input Data:** Нет

**Output Data:**

```json
{
    "total_presales": "integer",
    "total_invested": "decimal",
    "total_tokens_sold": "decimal",
    "total_investors": "integer",
    "active_presales": "integer",
    "completed_presales": "integer",
    "average_investment": "decimal"
}
```

---

## 4. Swagger Documentation

### 4.1 Swagger UI

**Название:** Интерактивная документация API  
**URL:** `GET /api/v1/swagger/`  
**Аутентификация:** Не требуется

Предоставляет интерактивную документацию всех эндпоинтов API с возможностью тестирования.

---

## Коды ошибок

### HTTP Status Codes

- `200 OK` - Успешный запрос
- `201 Created` - Ресурс успешно создан
- `400 Bad Request` - Неверные данные запроса
- `401 Unauthorized` - Требуется аутентификация
- `403 Forbidden` - Доступ запрещен
- `404 Not Found` - Ресурс не найден
- `429 Too Many Requests` - Превышен лимит запросов
- `500 Internal Server Error` - Внутренняя ошибка сервера

### Типичные ошибки

```json
{
    "error": "string - Описание ошибки",
    "detail": "string - Детальное описание",
    "code": "string - Код ошибки"
}
```

---

## Rate Limiting

Большинство эндпоинтов имеют ограничения по количеству запросов:

- Аутентификация: 60 запросов в минуту
- API методы: 100 запросов в минуту
- Игровые методы: 30 запросов в минуту
- Создание инвестиций: 10 запросов в минуту

При превышении лимита возвращается ошибка 429 с заголовком `Retry-After`.
