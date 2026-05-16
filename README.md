# Доказатель

«Доказатель» — AI-сервис для стресс-теста идеи перед аудиторией. Пользователь загружает готовый текст, реферат, доклад, диплом, презентацию, питч или выступление, а сервис оценивает убедительность, строит карту доказательности, показывает слабые места, готовит вопросы аудитории и Markdown-отчёт.

Сервис анализирует только загруженный материал. Внешняя проверка источников, web scraping и выдумывание ссылок в MVP не используются.

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

Основные значения для локального MVP:

```env
APP_ENV=development
DATABASE_URL=postgresql+psycopg://dokazatel:dokazatel@postgres:5432/dokazatel

LLM_PROVIDER=mock
ALLOW_MOCK_FALLBACK=true

YANDEX_API_KEY=
YANDEX_FOLDER_ID=
YANDEX_MODEL=aliceai-llm/latest
YANDEX_BASE_URL=https://rest-assistant.api.cloud.yandex.net/v1
YANDEX_MAX_OUTPUT_TOKENS=12000

MAX_CHARS_FOR_ANALYSIS=120000
SOFT_CHAR_LIMIT=50000
HARD_CHAR_LIMIT=120000
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

VITE_API_BASE_URL=http://localhost:8000
```

## Mock mode

Для запуска без ключей Yandex:

```env
LLM_PROVIDER=mock
ALLOW_MOCK_FALLBACK=true
```

Mock provider детерминированно использует локальные эвристики, текущий preprocessing, claim extractor, scoring, question generator и recommendation engine.

## Yandex / Alice AI

Для боевого анализа:

```env
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
$env:DATABASE_URL="sqlite+pysqlite:///./local_dev.sqlite"
$env:LLM_PROVIDER="mock"
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Для PostgreSQL вне Docker укажите свой `DATABASE_URL`.

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
- `POST /api/analyses` — загрузка файла и синхронный анализ.
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
- FastAPI mock analyze;
- storage service;
- Yandex provider JSON parsing.

## Ограничения MVP

- Нет авторизации.
- Нет Celery/RQ/Redis; анализ выполняется синхронно.
- Нет web scraping и внешнего сбора данных.
- Нет внешней фактологической проверки источников.
- Сервис не пишет работу за пользователя, а проверяет уже загруженный материал.
