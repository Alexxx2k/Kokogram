# Kokogram

Веб-мессенджер, курсовая работа по курсу «Технологии разработки качественного программного обеспечения» (СПбПУ, ВШПИ, 2026).

**Команда:** Псарев А. С., Никифоров А. В., Зинаков С. С., Соболевский М. А., Ананьев А. М.
**Преподаватель:** Маслаков А. П.

## О проекте

Kokogram позволяет вести личные и групповые чаты, общаться, делиться файлами и GIF.
Работает в веб-браузере.

Архитектура: API Gateway и пять сервисов (пользователей, чатов, сообщений, онлайн-статусов, GIF) на Python/FastAPI; PostgreSQL, Redis, RabbitMQ, SeaweedFS; Giphy API как внешняя зависимость. Клиент на HTML/CSS/JavaScript.

## Документация

- FS-спецификация: `docs/FS-spec.pdf`
- HLD: `docs/HLD.pdf`

## Структура репозитория

```
Kokogram/
├── .github/
│   └── pull_request_template.md  # шаблон описания PR
├── docs/  # FS и HLD (PDF)
├── shared/  # общий пакет kokogram_shared: время, идентификаторы, токены, формат ошибок
├── web/  # веб-клиент (HTML, CSS, JavaScript)
│   ├── index.html
│   ├── css/
│   └── js/
├── gateway/  # API Gateway
├── users/  # сервис пользователей
├── chats/  # сервис чатов
├── messages/  # сервис сообщений
├── presence/  # сервис онлайн-статусов
├── gif/  # сервис GIF
├── .editorconfig
├── .gitignore
└── README.md
```

### Структура сервиса

Каждый сервис (`users`, `chats`, `messages`, `presence`, `gif`) устроен одинаково и повторяет слои из HLD §5.1:

```
<сервис>/
├── app/
│   ├── main.py  # создание приложения FastAPI, GET /health
│   ├── api/  # входящий слой: роутеры, схемы Pydantic, обработчики событий
│   ├── services/  # бизнес-логика (без импорта FastAPI, SQLAlchemy, httpx)
│   ├── ports/  # интерфейсы (typing.Protocol)
│   └── adapters/  # реализации портов: БД, Redis, S3, HTTP, RabbitMQ
├── tests/
│   ├── unit/  # модульные тесты
│   └── integration/  # интеграционные тесты
└── requirements.txt
```

### API Gateway

В Gateway нет бизнес-логики, поэтому вместо `services/` у него свои папки:

```
gateway/app/
├── main.py
├── api/  # проксирующие роутеры, WebSocket-эндпоинт, POST /internal/ws/deliver
├── routing/  # RouteTable: соответствие префикса пути сервису
├── ws/  # реестр WebSocket-соединений, протокол канала
├── ports/  # интерфейсы клиентов к другим сервисам
└── adapters/  # реализации клиентов на httpx
```

### Общий пакет `shared/`

Абстракции времени, идентификаторов и токенов и единый формат ошибок
(HLD §4.1, §5.3) лежат в `shared/` и подключаются ко всем сервисам, включая Gateway.
Пакет называется `kokogram-shared` (для pip), импортируется как `kokogram_shared`.

```
shared/
├── pyproject.toml
└── kokogram_shared/
    ├── clock.py  # Clock, SystemClock, FakeClock (advance, set)
    ├── ids.py  # IdGenerator, UuidGenerator, SequentialIdGenerator
    ├── tokens.py  # TokenGenerator, SecretsTokenGenerator, FixedTokenGenerator
    ├── errors.py  # ErrorCode, AppError, формат {error: {code, message, details}}
    └── fastapi_handlers.py  # register_error_handlers(app)
```

- Сервисы не вызывают `datetime.now()`, `uuid4()`, `secrets`, `random`, `time.sleep`
  напрямую: зависят от `Clock`, `IdGenerator`, `TokenGenerator` и получают их
  через конструктор. Прямые вызовы разрешены только в реализациях внутри `shared`.
- В продакшене подставляются `SystemClock`, `UuidGenerator`, `SecretsTokenGenerator`,
  в тестах `FakeClock`, `SequentialIdGenerator`, `FixedTokenGenerator`.

Пакет подключён ко всем сервисам строкой `-e ../shared[fastapi]` в их `requirements.txt`.

### Правила

- Бизнес-логика находится только в `services/`; роутеры и обработчики событий её не содержат.
- Всё внешнее (БД, кэш, брокер, хранилище, другие сервисы) сервис получает через порты, реализации лежат в `adapters/`.
- У каждого сервиса свой `requirements.txt`.
- Пустые папки хранятся через `.gitkeep`; когда в папке появляется реальный файл, `.gitkeep` удаляется.

## Запуск

### Требования

- Python 3.12
- Docker и Docker Compose
- `make`

### Инфраструктура

Поднимается PostgreSQL, Redis, RabbitMQ, SeaweedFS и заглушка Giphy (HLD §5.4, профиль `infra`) с помощью `make`:

```
cp .env.example .env  # один раз; значения по умолчанию подходят для разработки
make up  # поднять и дождаться готовности (все контейнеры healthy)
make ps  # статус контейнеров
make logs s=seaweedfs  # логи сервиса (без s: все)
make down  # остановить, данные сохраняются
make clean  # остановить и удалить данные
make help  # список всех команд
```

Порты: PostgreSQL `5432`, Redis `6379`, RabbitMQ `5672` (панель `15672`), SeaweedFS S3 `8333`, заглушка Giphy `8090`.

Заглушка Giphy: режим отказа включается запросом `POST http://localhost:8090/__admin/fail?enabled=true` (выключается `enabled=false`).

### Запуск сервиса локально

Из папки нужного сервиса, например `users`:

```
python -m venv .venv
source .venv/Scripts/activate  # Git Bash на Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Проверка: `http://127.0.0.1:8000/health` возвращает `{"status": "ok"}`. Документация эндпоинтов: `http://127.0.0.1:8000/docs`.

## Процесс разработки

### Git-модель: GitHub Flow

- `main` всегда в рабочем состоянии, прямые коммиты в неё запрещены.
- Каждая задача делается в отдельной ветке от `main`.
- Именование веток: `<тип>/<кратко-через-дефис>`, где тип из: `feat`, `fix`, `docs`, `infra`, `test`. Пример: `feat/auth-register`.
- Изменения попадают в `main` только через pull request.
- Название PR совпадает с названием ветки, из которой он открывается. Пример: ветка `feat/auth-register` -> PR `feat/auth-register`.
- При открытии PR обязательно заполняются Assignees (авторы), Reviewers (минимум один другой участник), Labels (как у тикета) и Project (Kokogram).
- Каждый PR одобряет минимум один другой участник команды (собственно, Reviewers).
- В описании PR указываются требования FS, разделы HLD и `Closes #N`.
- Коммиты: `<тип>: <описание>`, например `feat: add email validation`.

### Доска задач

GitHub Projects, статусы: Todo -> In progress -> Done. Каждая карточка ссылается на конкретные пункты FS и разделы HLD. Исполнитель назначается при взятии задачи в работу.

### Definition of Done

Карточка переводится в «Done», когда:

- [x] код влит в `main` через pull request с одобрением;
- [x] реализованы все требования FS, указанные в карточке;
- [x] проект собирается, приложение запускается;
- [x] изменения не ломают ранее реализованную функциональность.
