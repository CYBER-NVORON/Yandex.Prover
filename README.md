# Доказатель

«Доказатель» — AI-сервис для стресс-теста идеи перед аудиторией. Пользователь загружает готовый текст, реферат, доклад, диплом, презентацию, питч или выступление, а сервис оценивает убедительность, строит карту доказательности, показывает слабые места, готовит вопросы аудитории и отчёт.


## Хакатонный фокус

Проект сделан под задачу хакатона Alice AI / Yandex AI Studio: Алиса AI здесь не является чат-ботом, а работает как аналитический движок внутри законченного сценария подготовки к защите, питчу или выступлению.

### Проблема

Перед защитой проекта, учебной работы или бизнес-питча автору сложно понять, где аудитория «сломает» аргументацию: какой тезис не доказан, какой вывод слишком широкий, какой вопрос жюри будет самым опасным и что стоит исправить в первую очередь. Обычно такую обратную связь дают преподаватель, наставник или эксперт, но они не всегда доступны перед дедлайном.

### Целевой пользователь

- школьники и студенты, которые готовят реферат, исследовательскую работу, диплом или доклад;
- проектные команды, которым нужно проверить питч перед жюри, инвестором или экспертной комиссией;
- преподаватели, наставники и методисты, которым нужен быстрый первичный разбор материалов перед консультацией.

### Пользовательский сценарий

1. Пользователь загружает основной материал: TXT, Markdown, PDF, DOCX или PPTX.
2. Выбирает тип материала, аудиторию и уровень подготовленности аудитории.
3. При необходимости добавляет регламент конкурса/защиты и эталонную сильную работу.
4. Backend извлекает текст, удаляет шумовые части и собирает smart context для больших документов.
5. Alice AI через Yandex Responses API анализирует материал и возвращает экспертную рецензию.
6. Сервис превращает результат в dashboard: индекс убедительности, карту утверждений, риски, вопросы аудитории, план правок, соответствие регламенту, сравнение с эталоном и Markdown-отчёт.
7. История анализов сохраняется в PostgreSQL, чтобы пользователь мог вернуться к отчёту.

### Как используется Alice AI / Yandex AI Studio

- **Текстовая аналитика:** Alice AI рецензирует материал по промптам для предзащиты: главная мысль, слабые места, риски, рекомендации и вопросы аудитории.
- **Работа с файлами:** сервис принимает документы и презентации, извлекает текст и передаёт модели очищенный контекст.
- **Структурирование результата:** backend приводит ответ к стабильному DTO `AnalysisResult`, который используют frontend, storage и отчёт.
- **Контекст и персонализация:** пользователь задаёт тип аудитории и уровень её знаний; вопросы и рекомендации адаптируются под этот контекст.
- **Дополнительные документы:** регламент и эталонная работа используются как локальный контекст для проверки требований и сравнения структуры, без внешнего поиска.
- **Проверка результата:** backend валидирует схему, сохраняет provider metadata и запрещает production-запуск на mock-провайдере.

### Что уже реализовано

- React + Vite frontend с загрузкой материала, выбором аудитории, dashboard, историей и отчётом.
- FastAPI backend с загрузкой файлов, анализом, хранением истории и API для отчётов.
- Интеграция с Alice AI через OpenAI-compatible Responses API с configurable `YANDEX_BASE_URL`.
- Mock provider для локальной разработки и тестов через `LLM_PROVIDER=mock`.
- Preprocessing: исключение титульника, содержания, списка литературы, приложений, ФИО, класса, года и номеров страниц из claims.
- Smart context builder для больших документов при сохранении лимитов анализа.
- Анализ соответствия регламенту, сравнение с эталоном и anti-overthinking блок с тремя главными действиями.
- Markdown-отчёт, который можно скачать и использовать как чек-лист подготовки.

### Ограничения и развитие

MVP сознательно не делает web scraping, не проверяет источники во внешнем интернете и не пишет работу за пользователя. Следующие шаги развития: асинхронная очередь для долгих анализов, авторизация и кабинеты команд, версии одного материала, командные комментарии наставника, расширенная мультимодальная обработка слайдов и изображений, голосовая репетиция ответов перед аудиторией.

## Архитектура

- `backend/` — FastAPI, Pydantic, SQLAlchemy 2.x, Alembic, PostgreSQL storage.
- `frontend/` — React + Vite + TypeScript + Tailwind CSS + Framer Motion.
- `postgres` — хранит историю анализов в таблице `analysis_runs`.
- `streamlit_legacy/` — старый Streamlit MVP для демонстрации и обратной совместимости.
- `app/` — исходная legacy-бизнес-логика оставлена на месте; новый backend использует копию в `backend/app/services/`.

## Запуск через Docker Compose

Создайте `.env` на основе `.env.example`, затем:

```powershell
docker compose up --build
```

После запуска:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Swagger/OpenAPI: http://localhost:8000/docs
- PostgreSQL: `localhost:5432`, база `dokazatel`

## Переменные окружения

Основные значения для production-like запуска:

```env
APP_ENV=production
DATABASE_URL=postgresql+psycopg://dokazatel:dokazatel@postgres:5432/dokazatel

LLM_PROVIDER=yandex
ALLOW_MOCK_FALLBACK=false

YANDEX_API_KEY=...
YANDEX_FOLDER_ID=...
YANDEX_MODEL=aliceai-llm/latest
YANDEX_BASE_URL=https://rest-assistant.api.cloud.yandex.net/v1
YANDEX_MAX_OUTPUT_TOKENS=12000

MAX_CHARS_FOR_ANALYSIS=120000
SOFT_CHAR_LIMIT=50000
HARD_CHAR_LIMIT=120000
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

VITE_API_BASE_URL=http://localhost:8000
```
## Yandex / Alice AI

Для боевого анализа:

```env
APP_ENV=production
LLM_PROVIDER=yandex
ALLOW_MOCK_FALLBACK=false
YANDEX_API_KEY=...
YANDEX_FOLDER_ID=...
YANDEX_MODEL=aliceai-llm/latest
YANDEX_BASE_URL=https://rest-assistant.api.cloud.yandex.net/v1
YANDEX_MAX_OUTPUT_TOKENS=12000
```

Backend формирует model URI:

```text
gpt://{YANDEX_FOLDER_ID}/{YANDEX_MODEL}
```

Для Responses API используется configurable `YANDEX_BASE_URL`; дефолт должен оставаться `https://rest-assistant.api.cloud.yandex.net/v1`.
Если модель возвращает обрезанный JSON, увеличьте `YANDEX_MAX_OUTPUT_TOKENS` или повторите анализ с меньшим документом. Дефолт backend — `12000`.

В Yandex Cloud нужны роли:

- `ai.assistants.editor`
- `ai.languageModels.user`

Также должен быть активный биллинг. Если Yandex вернёт 403, backend отдаст понятную ошибку с подсказкой проверить folder id, API key, роли и биллинг.

Проверить интеграцию можно через Swagger: отправьте файл в `POST /api/analyses` при `LLM_PROVIDER=yandex`.

## Backend отдельно

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
$env:APP_ENV="development"
$env:DATABASE_URL="sqlite+pysqlite:///./local_dev.sqlite"
$env:LLM_PROVIDER="mock"
$env:ALLOW_MOCK_FALLBACK="true"
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Для PostgreSQL вне Docker укажите свой `DATABASE_URL`. Для production используйте `LLM_PROVIDER=yandex`, `ALLOW_MOCK_FALLBACK=false` и реальные `YANDEX_API_KEY`/`YANDEX_FOLDER_ID`.

## Frontend отдельно

```powershell
cd frontend
npm install
$env:VITE_API_BASE_URL="http://localhost:8000"
npm run dev -- --host 0.0.0.0
```

UI доступен на http://localhost:5173.

## API

- `GET /api/health` — healthcheck.
- `POST /api/analyses` — загрузка основного файла и синхронный анализ; дополнительно принимает `regulation_file`, `benchmark_file`, `material_type`, `audience_type`, `audience_knowledge_level`, `title`.
- `GET /api/analyses` — список последних анализов.
- `GET /api/analyses/{analysis_id}` — полный `AnalysisResult`.
- `GET /api/analyses/{analysis_id}/report` — Markdown-отчёт в JSON.
- `GET /api/analyses/{analysis_id}/report/download` — скачивание `report.md`.
- `DELETE /api/analyses/{analysis_id}` — удаление анализа.

Поддерживаемые файлы: TXT, Markdown, PDF, DOCX, PPTX.

## PostgreSQL storage

Таблица `analysis_runs` хранит:

- UUID анализа;
- filename, material_type, audience_type, title;
- provider metadata;
- persuasiveness_score;
- полный `AnalysisResult` в `result_json` JSONB;
- `created_at`.

Claims/questions пока не нормализованы в отдельные таблицы, чтобы не усложнять MVP. Storage service изолирован так, чтобы эту нормализацию можно было добавить позже.

## Большие документы

Лимиты не отключены:

- `SOFT_CHAR_LIMIT=50000`
- `HARD_CHAR_LIMIT=120000`
- `MAX_CHARS_FOR_ANALYSIS=120000`

Если документ меньше soft limit, backend анализирует весь текст после preprocessing. Если больше, smart context builder сохраняет ключевые секции: введение, цель, гипотезу, задачи, методы, заключение, анкетирование/результаты и затем части main body по приоритету. Титульник, содержание, список литературы и приложения исключаются из analysis text; список литературы сохраняется отдельно как `references_text`.

Frontend показывает warning: «Документ большой, анализ выполнен по ключевым секциям».

## Тесты

```powershell
.\.venv\Scripts\python -m pytest backend\tests -q
```

Покрыто:

- document loader;
- preprocessing и smart context builder;
- claim extractor;
- scoring;
- FastAPI health;
- FastAPI analyze в локальном тестовом режиме;
- storage service;
- contextual features: регламент, эталон, уровень знаний аудитории, overthinking guard;
- Yandex provider JSON parsing.

## Ограничения MVP

- Нет авторизации.
- Нет Celery/RQ/Redis; анализ выполняется синхронно.
- Нет web scraping и внешнего сбора данных.
- Нет внешней фактологической проверки источников.
- Сервис не пишет работу за пользователя, а проверяет уже загруженный материал.