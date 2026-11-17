# Сервис пользователей

Запуск из каталога `users` после установки `requirements.txt`:

```bash
uvicorn app.main:app --reload
```

Настройки читаются из переменных окружения. Файл `.env` автоматически не загружается:
при локальном запуске переменные нужно экспортировать в окружение процесса.

| Переменная | Значение по умолчанию / назначение |
|---|---|
| `DATABASE_URL` | URL PostgreSQL; если не задан, собирается из `POSTGRES_*` |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | `kokogram` |
| `POSTGRES_HOST`, `POSTGRES_PORT` | `localhost`, `5432` |
| `S3_ENDPOINT_URL` | `http://localhost:8333` |
| `S3_REGION` | `us-east-1` |
| `S3_BUCKET` | `kokogram` |
| `S3_ACCESS_KEY`, `S3_SECRET_KEY` | Пустые; учётные данные выбранного S3-хранилища |
| `URL_SIGNING_SECRET` | Без значения по умолчанию; обязателен для создания `UrlSigner` |
| `SIGNED_URL_TTL_SECONDS` | `900`, допустимо от 1 до 900 секунд |
| `SESSION_TTL_DAYS` | `30`, допустимо от 1 до 30 суток |
| `AVATAR_MAX_BYTES` | `5242880`, допустимо от 1 до 5242880 байт |

`URL_SIGNING_SECRET` должен совпадать у сервисов пользователей, чатов и сообщений.
В Docker адреса зависимостей задаются именами контейнеров, например
`POSTGRES_HOST=postgres` и `S3_ENDPOINT_URL=http://seaweedfs:8333`.

Настройки и общие зависимости предоставляются функциями в `app/api/dependencies.py`.
В HTTP-проверках их можно подменять через `app.dependency_overrides`.
Обработчики ошибок и JSON-логирование подключены в `app/main.py`; middleware
сохраняет входящий `X-Request-ID` или создаёт новый и возвращает его в ответе.

На этом этапе `/health` возвращает `{"status": "ok"}` и подтверждает работу приложения;
проверки доступности PostgreSQL и S3 ещё не подключены.
