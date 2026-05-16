from __future__ import annotations

import sqlite3
from pathlib import Path

from app.schemas import AnalysisResult


class StorageError(Exception):
    pass


def init_db(database_path: str | Path) -> None:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sqlite3.connect(path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    result_json TEXT NOT NULL
                )
                """
            )
            connection.commit()
    except sqlite3.Error as exc:
        raise StorageError("Не удалось инициализировать хранилище результатов.") from exc


def save_result(result: AnalysisResult, database_path: str | Path) -> None:
    init_db(database_path)
    payload = result.model_dump_json()
    try:
        with sqlite3.connect(database_path) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO analyses (id, filename, created_at, result_json)
                VALUES (?, ?, ?, ?)
                """,
                (result.id, result.filename, result.created_at.isoformat(), payload),
            )
            connection.commit()
    except sqlite3.Error as exc:
        raise StorageError("Не удалось сохранить результат анализа.") from exc


def load_result(result_id: str, database_path: str | Path) -> AnalysisResult | None:
    init_db(database_path)
    try:
        with sqlite3.connect(database_path) as connection:
            row = connection.execute(
                "SELECT result_json FROM analyses WHERE id = ?",
                (result_id,),
            ).fetchone()
    except sqlite3.Error as exc:
        raise StorageError("Не удалось загрузить результат анализа.") from exc
    if row is None:
        return None
    return AnalysisResult.model_validate_json(row[0])


def list_recent_results(database_path: str | Path, limit: int = 5) -> list[tuple[str, str, str]]:
    init_db(database_path)
    try:
        with sqlite3.connect(database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, filename, created_at
                FROM analyses
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    except sqlite3.Error as exc:
        raise StorageError("Не удалось прочитать список результатов.") from exc
    return [(row[0], row[1], row[2]) for row in rows]

