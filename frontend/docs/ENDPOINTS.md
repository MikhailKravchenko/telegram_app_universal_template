# API Endpoints Documentation

Документация эндпоинтов backend для шаблона Telegram Mini App.

## Базовый URL

```text
http://localhost:8000/api/v1/
```

## Аутентификация

Шаблон использует авторизацию через Telegram WebApp. Бэкенд должен поддерживать JWT (или аналогичный механизм), токен может передаваться либо в cookie, либо в заголовке:

```text
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
  "referredBy": "integer (optional)"
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

**Название:** Проверка статуса авторизации  
**URL:** `GET /api/v1/accounts/telegram/status/`  
**Аутентификация:** Требуется

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

**Output Data:**

```json
{
  "message": "string"
}
```

### 1.4 User Info

**Название:** Информация о текущем пользователе  
**URL:** `GET /api/v1/accounts/users/`  
**URL:** `GET /api/v1/accounts/users/{id}/` (опционально)  
**Аутентификация:** Требуется

**Output Data:**

```json
{
  "id": "integer",
  "username": "string",
  "telegram_id": "string"
}
```

---

## 2. Swagger Documentation (опционально)

Если backend использует Swagger / drf-spectacular и т.п., можно предоставить интерактивную документацию:

**URL:** `GET /api/v1/swagger/`  
**Аутентификация:** Не требуется

---

## Коды ошибок

### HTTP Status Codes

- `200 OK` - успешный запрос  
- `201 Created` - ресурс создан  
- `400 Bad Request` - неверные данные  
- `401 Unauthorized` - требуется аутентификация  
- `403 Forbidden` - доступ запрещён  
- `404 Not Found` - ресурс не найден  
- `500 Internal Server Error` - внутренняя ошибка сервера

### Формат ошибки (рекомендация)

```json
{
  "error": "string",
  "detail": "string",
  "code": "string"
}
```
