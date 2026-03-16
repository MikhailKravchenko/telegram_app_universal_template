## Django backend template for Telegram WebApp

- **Назначение**: универсальный бэкенд‑шаблон для проектов с фронтом в Telegram WebApp.
- **Что входит**:
  - Django + DRF + PostgreSQL
  - авторизация через Telegram WebApp (валидация `initData`, выдача JWT)
  - минимальный `User` с Telegram‑полями (`telegram_id`, `telegram_username`, `telegram_first_name` и др.)
  - базовые endpoint'ы: `auth` и `me`, health‑проверка

Доменные модули (игра, ставки, пресейл и т.п.) полностью удалены — шаблон подходит как отправная точка для любого проекта.

## Getting Started

После клонирования репозитория:

```bash
make init
```

Это создаст:

- `.env` — настройки БД и порта Django
- `config.yaml` — DEBUG/SECRET_KEY/ALLOWED_HOSTS и `TELEGRAM_BOT_TOKEN`

Дальше:

1. **Заполнить `.env` и `config.yaml`**
2. **Собрать и запустить через Docker**:

```bash
make build
```

3. **Применить миграции и создать админа**:

```bash
make full-migrate
make admin
```

## API Overview

Базовый префикс API: `/api/v1/`.

- **POST** `/api/v1/accounts/telegram/login/`
  - Тело: `{ "telegramData": "<initData из Telegram WebApp>" }`
  - Ответ: `{ "access": "<jwt>", "refresh": "<jwt>" }`

- **GET** `/api/v1/accounts/me/`
  - Заголовок: `Authorization: Bearer <access>`
  - Ответ: минимальный профиль пользователя с Telegram‑полями.

- **GET** `/health/`
  - Простой health‑check: `{"status": "ok"}`.

## Makefile

Доступные команды:

```bash
make init          # скопировать env.example и config.example.yaml
make build         # собрать и поднять docker-compose
make web-logs      # логи веб-сервиса
make full-migrate  # makemigrations и migrate
make admin         # создать суперпользователя
make collectstatic # собрать статику
```

## Pre-Commit

Используется [pre-commit](https://pre-commit.com/) с базовыми линтерами:

- black
- flake8
- isort
