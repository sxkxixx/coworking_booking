# Серверная часть сервиса для бронирования коворкингов УрФУ

## Инструкция по запуску

* Установите зависимости (Makefile не описан полностью)

```bash
make install-prod
```

* Соберите образ приложения

```bash
  make build
```

* Запустите докер-образ в контейнере

```bash
make run
```

## API

Основное API построено на JSON-RPC архитектуре. 
Это значит, что HTTP статус-код при каждом ответе сервера равен 200.
В случае возникновения ошибок, код ошибки и детали описаны в ответе сервера. Примеры ниже.
OpenAPI-спецификация находится в файле specification/specification.json

### Аутентификация пользователя

* URL-адрес: ```/api/v1/auth```

#### Регистрация пользователя

Тело запроса:

```json
{
  "jsonrpc": "2.0",
  "id": "0",
  "method": "register",
  "params": {
    "data": {
      "email": "name.surname@urfu.ru",
      "password": "password",
      "last_name": "string",
      "first_name": "string",
      "patronymic": "string" // Опицональное поле
    }
  }
}
```

Ответ сервера:

```json
{
  "jsonrpc": "2.0",
  "id": "0",
  "result": {
    "id": "name.surname",
    "email": "name.surname@urfu.ru",
    "last_name": "string",
    "first_name": "string",
    "patronymic": "string",
    "is_student": true,
    "avatar_url": "string"
  }
}
```

Ошибки:

* Попытка зарегистрировать пользователя с неуникальным адресом эл. почты

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32001,
    "message": "Error while registering error",
    "data": "User with current email already exists"
  },
  "id": "0"
}
```

#### Аутентификация пользователя

Тело запроса:

```json
{
  "jsonrpc": "2.0",
  "id": "0",
  "method": "login",
  "params": {
    "data": {
      "email": "user.surname@urfu.me",
      "password": "password",
      "fingerprint": "string" // Подпись браузера
    }
  }
}
```

Ответ сервера:

```json
{
  "jsonrpc": "2.0",
  "id": "0",
  "result": {
    "access_token": "string",
    "token_header": "Authorization"
  }
}
```

Ошибки:

* Любое исключение при аутентификации

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32002,
    "message": "Invalid credentials"
  },
  "id": "0"
}
```

#### Обновление сессии

Тело запроса:

```json
{
  "jsonrpc": "2.0",
  "id": "0",
  "method": "refresh_session",
  "params": {
    "fingerprint": "string"
  }
}
```

Ответ сервера:

```json
{
  "jsonrpc": "2.0",
  "id": "0",
  "result": {
    "access_token": "string",
    "token_header": "Authorization"
  }
}
```

Ошибки:

* Любое исключение при обновлении сессии

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32003,
    "message": "Session is invalid"
  },
  "id": "0"
}
```

#### Удаление сессии (logout)

Тело запроса:

```json
{
  "jsonrpc": "2.0",
  "id": "0",
  "method": "logout",
  "params": {
    "fingerprint": "string"
  }
}
```

Ответ сервера:

```json
{
  "jsonrpc": "2.0",
  "id": "0",
  "result": null
}
```

Ошибки:

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32003,
    "message": "Session is invalid"
  },
  "id": "0"
}
```
