# Миграции БД

Один Alembic на все сервисы: в системе один экземпляр PostgreSQL и внешние ключи между
таблицами разных сервисов (HLD §3). История линейная, одна цепочка ревизий:

```
0001_users  ->  0002_chats  ->  0003_messages
```

| Ревизия | Таблицы | Владелец |
|---|---|---|
| `0001_users` | users, sessions, contacts, blocks | сервис пользователей |
| `0002_chats` | chats, chat_members | сервис чатов |
| `0003_messages` | messages, attachments, message_hidden | сервис сообщений |

## Применение

Из корня репозитория, при поднятой инфраструктуре (`make up`):

```
python -m venv db/.venv
source db/.venv/Scripts/activate  # Git Bash; macOS/Linux: db/.venv/bin/activate
pip install -r db/requirements.txt

make migrate  # alembic upgrade head
make migrate-down  # alembic downgrade base (удаляет все таблицы)
```

Вручную: `python -m alembic -c db/alembic.ini <команда>`, например `current`, `heads`,
`history`, `downgrade -1`, `upgrade head --sql` (напечатать SQL без подключения к БД).

Адрес БД: `DATABASE_URL` (например `postgresql://user:pass@localhost:5432/db`), а если он
не задан, то `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`
(по умолчанию `localhost`), `POSTGRES_PORT` (по умолчанию `5432`). Драйвер psycopg 3
нужен только миграциям; драйверы сервисов выбираются в их тикетах.

## Как писать миграцию

- Ревизии уже созданы и связаны в цепочку. Новые ревизии не создаём: каждый тикет
  заполняет `upgrade()` и `downgrade()` **своей** ревизии. Id и `down_revision` не менять,
  иначе появится вторая голова (`alembic heads` должен показывать одну).
- Автогенерации нет: миграции пишутся вручную через `op.create_table`, `op.create_index`,
  `op.create_check_constraint`; частичные индексы и составные внешние ключи через `op.execute`
  с SQL, например:
  ```python
  op.execute(
      "CREATE UNIQUE INDEX uq_chat_members_owner ON chat_members (chat_id) WHERE role = 'owner'"
  )
  ```
- `downgrade()` удаляет только таблицы своей ревизии, в обратном порядке зависимостей.
- Миграции применяются по порядку: для проверки своей ревизии нужны предыдущие, поэтому PR
  мержатся в порядке 0001, 0002, 0003.

## Соглашения

**Имена ограничений и индексов обязательны**, всегда задаются явно (не оставлять автоматические):

| Что | Шаблон | Пример |
|---|---|---|
| Первичный ключ | `pk_<таблица>` | `pk_users` |
| Уникальность | `uq_<таблица>_<суть>` | `uq_users_email`, `uq_users_phone`, `uq_users_username` |
| CHECK | `ck_<таблица>_<суть>` | `ck_contacts_not_self` |
| Внешний ключ | `fk_<таблица>_<столбец>_<таблица-цель>` | `fk_sessions_user_id_users` |
| Индекс | `ix_<таблица>_<столбцы>` | `ix_chat_members_user_id` |

Имена нужны, потому что по ним адаптеры сервисов превращают нарушение ограничения в код ошибки
(HLD §4.1): `uq_users_email` -> `email_taken`, `uq_users_phone` -> `phone_taken`,
`uq_users_username` -> `username_taken`, `uq_chats_direct_key` -> существующий личный чат.

**Типы:** идентификаторы `uuid` (`sa.Uuid()`), время `timestamptz` (`sa.DateTime(timezone=True)`).

**Без `DEFAULT`** на id и временных полях: значения подставляет приложение через `IdGenerator`
и `Clock` (HLD §5.3), чтобы тесты были детерминированными. Исключения (например, флаги) нужно
явно обосновать в PR.

Требуется PostgreSQL 15+ (используется в `0003_messages`: `ON DELETE SET NULL (reply_to_id)`).
