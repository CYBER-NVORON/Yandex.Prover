from app.config import HARD_CHAR_LIMIT, SOFT_CHAR_LIMIT
from app.services.document_preprocessor import preprocess_document


def test_small_document_is_analyzed_after_preprocessing_as_whole_text():
    text = """
    Титульный лист
    Реферат
    Введение
    Главная мысль: проект помогает готовиться к защите.
    Заключение
    Материал можно улучшить источниками.
    """

    document = preprocess_document(text)

    assert document.smart_context_used is False
    assert "Главная мысль" in document.analysis_text
    assert "Материал можно улучшить" in document.analysis_text


def test_large_document_uses_smart_context_and_keeps_goal_and_conclusion():
    filler = "\n".join(f"Основная часть показывает аргумент {index}." for index in range(7000))
    text = f"""
    Муниципальная школа
    Выполнил: Иванов Иван
    2026

    Содержание
    Введение 3
    Литература 20

    Введение
    Работа объясняет проблему подготовки к защите.

    Цель работы: проверить, помогает ли сервис находить слабые места.

    Гипотеза: если автор видит вопросы аудитории заранее, защита становится сильнее.

    Задачи
    1. Собрать типовые вопросы.
    2. Сравнить ответы.

    Методы исследования: анализ текста и анкетирование.

    Анкетирование
    Большинство участников отметили, что вопросы помогли улучшить защиту.

    {filler}

    Заключение
    Цель достигнута: сервис помогает увидеть слабые места и подготовить ответы.

    Литература
    1. Учебное пособие.
    """

    document = preprocess_document(text, soft_char_limit=SOFT_CHAR_LIMIT, hard_char_limit=HARD_CHAR_LIMIT)

    assert document.smart_context_used is True
    assert "Документ большой, анализ выполнен по ключевым секциям." in document.warnings
    assert "проверить, помогает ли сервис" in document.analysis_text
    assert "Цель достигнута" in document.analysis_text
    assert len(document.analysis_text) <= HARD_CHAR_LIMIT


def test_smart_context_excludes_title_page_toc_references_from_analysis_text():
    filler = "\n".join("Основная часть содержит проверяемое утверждение." for _ in range(4000))
    text = f"""
    Муниципальная школа
    Выполнил: Иванов Иван
    Класс 9
    2026

    Содержание
    Введение 3
    Литература 8

    Введение
    Материал проверяет идею перед аудиторией.
    {filler}

    Заключение
    Идея требует дополнительных доказательств.

    Литература
    1. Источник, который нельзя считать claim.
    """

    document = preprocess_document(text)

    assert "Муниципальная школа" not in document.analysis_text
    assert "Класс 9" not in document.analysis_text
    assert "Введение 3" not in document.analysis_text
    assert "Источник, который нельзя считать claim" not in document.analysis_text
    assert "Источник, который нельзя считать claim" in document.references_text
