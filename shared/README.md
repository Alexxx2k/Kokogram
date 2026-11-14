# kokogram-shared

Общие абстракции и утилиты для всех микросервисов и API Gateway Kokogram.

## Установка

```bash
# Базовый пакет (без FastAPI)
pip install -e ./shared

# С поддержкой FastAPI-обработчиков и middleware
pip install -e "./shared[fastapi]"
```

## Модули

- `clock.py` — интерфейс `Clock`, реализации `SystemClock` и `FakeClock` (`advance`, `set`).
- `ids.py` — интерфейс `IdGenerator`, реализации `UuidGenerator` и `SequentialIdGenerator`.
- `tokens.py` — интерфейс `TokenGenerator`, реализации `SecretsTokenGenerator` и `FixedTokenGenerator`.
- `errors.py` — `ErrorCode`, `ValidationReason`, `AppError`, `error_body()`.
- `url_signer.py` — `UrlSigner` для генерации и проверки временных подписанных ссылок.
- `logging.py` — единое JSON-логирование в `stdout` (`configure_logging`, контекст `request_id` и `user_id`).
- `fastapi_handlers.py` — `register_error_handlers(app)` (требует extra `[fastapi]`).
- `fastapi_middleware.py` — `RequestContextMiddleware` и `setup_observability(app, service)` (требует extra `[fastapi]`).

## UrlSigner

Подписывает относительные пути к файлам, превью и аватарам (HLD §1.5) с помощью `HMAC-SHA256`:

```python
from datetime import timedelta
from kokogram_shared import FakeClock, UrlSigner

clock = FakeClock()
signer = UrlSigner(secret="super-secret", clock=clock, ttl=timedelta(minutes=15))

# Подпись ссылки (префикс /api/v1 при наличии автоматически удаляется)
signed_url = signer.sign("/messages/123/attachment", extra={"preview": "true"})
# -> "/messages/123/attachment?preview=true&expires=1767226500&sig=..."

# Проверка подписи (при несовпадении пути/extra/sig или истечении срока кидает AppError(UNAUTHORIZED))
signer.verify("/messages/123/attachment", expires=1767226500, sig="...", extra={"preview": "true"})
```

### Детали реализации
- В подпись попадают: канонический путь (без `/api/v1`), `expires` (Unix epoch UTC) и отсортированные `extra`-параметры через `\n`.
- Ссылка считается просроченной при `now >= expires`.
- Подпись передаётся в lower-case hex и проверяется через `hmac.compare_digest`.

## Логирование и трассировка запросов

Подключение JSON-логов и middleware `X-Request-ID` одной строкой в сервисе FastAPI:

```python
from fastapi import FastAPI
from kokogram_shared.fastapi_middleware import setup_observability

app = FastAPI(title="users")
setup_observability(app, service="users")
```

Каждый лог выводится в `stdout` в формате JSON с полями: `time`, `service`, `level`, `event`, `request_id`, `user_id`, `event_id`, `error_code`.
