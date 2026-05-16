# Инструкции для coding agents

- Проект написан на Python 3.11+ и TypeScript.
- Основной новый путь продукта: `frontend/` React + Vite и `backend/` FastAPI.
- Legacy Streamlit сохранён в `streamlit_legacy/streamlit_app.py`; не удаляйте его без отдельного решения.
- Не ломайте контракт `AnalysisResult`: frontend и storage ожидают этот DTO целиком.
- Preprocessing обязателен перед анализом. Титульник, содержание, список литературы, приложения, ФИО, класс, год и номера страниц не должны попадать в claims.
- Не добавляйте web scraping, парсинг сайтов, MCP или внешний сбор данных в MVP.
- Сервис оценивает доказательность только по загруженному материалу и не выдумывает источники, ссылки, цитаты или факты.
- Не превращайте сервис в чат-бота и не добавляйте функции, которые пишут работу за пользователя.
- Все новые функции должны усиливать сценарий: стресс-тест идеи перед аудиторией.
- Yandex/Alice AI должен работать через Responses API с configurable `YANDEX_BASE_URL`. Дефолт: `https://rest-assistant.api.cloud.yandex.net/v1`.
- Mock provider должен оставаться доступным через `LLM_PROVIDER=mock`.
- Лимит анализа не убирайте: `SOFT_CHAR_LIMIT=50000`, `HARD_CHAR_LIMIT=120000`, `MAX_CHARS_FOR_ANALYSIS=120000`. Для больших документов используйте smart context builder.
- Frontend должен сохранять текущий product flow: загрузка материала, выбор типа, выбор аудитории, dashboard, история, отчёт.
- После изменений запускайте backend tests: `.\.venv\Scripts\python -m pytest backend\tests -q`.
