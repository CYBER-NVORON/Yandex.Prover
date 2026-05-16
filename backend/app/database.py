from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _engine_kwargs(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}


settings = get_settings()
engine = create_engine(settings.database_url, **_engine_kwargs(settings.database_url))
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    from app import models  # noqa: F401

    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
        return

    _run_alembic_migrations()


def _run_alembic_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    _stamp_legacy_schema_if_needed(alembic_cfg)
    command.upgrade(alembic_cfg, "head")


def _stamp_legacy_schema_if_needed(alembic_cfg) -> None:
    from alembic import command

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "analysis_runs" not in table_names:
        return

    if "alembic_version" in table_names:
        with engine.begin() as connection:
            version = connection.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar_one_or_none()
        if version:
            return

    columns = {column["name"] for column in inspector.get_columns("analysis_runs")}
    has_context_fields = {
        "has_regulation",
        "has_benchmark",
        "audience_knowledge_level",
        "readiness_verdict",
    }.issubset(columns)
    command.stamp(alembic_cfg, "0002_add_analysis_context_fields" if has_context_fields else "0001_create_analysis_runs")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
