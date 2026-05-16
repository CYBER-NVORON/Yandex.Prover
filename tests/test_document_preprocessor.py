from app.analysis_pipeline import analyze_text
from app.document_preprocessor import is_noise_claim, preprocess_document
from app.llm.mock_provider import MockLLMProvider
from app.report_builder import build_markdown_report


VORONA_VORON_TEXT = """
Муниципальное бюджетное общеобразовательное учреждение
Средняя общеобразовательная школа № 1

Исследовательская работа
«Ворона и ворон»

Направление: естественнонаучное, окружающий мир
Выполнила: Иванова Мария
ученица 3 класса
Класс 3
Руководитель: Петрова Анна Ивановна
учитель начальных классов
1 квалификационная категория
2016

2016 2 Содержание
Содержание
3 1.Особенности внешнего строения птиц
5 1.1. Ворон
5 1.2.Ворона
7 Заключение
8 Литература

Введение
Ворон и ворона часто считаются одной и той же птицей.

Цель работы: изучить отличительные особенности вороны и ворона

Гипотеза: Ворон и ворона — разные птицы.

Задачи
1. Сравнить внешний вид вороны и ворона
2. Изучить сведения о поведении этих птиц

Методы исследования: наблюдение, сравнение, анализ литературы.

1.Особенности внешнего строения птиц
Ворон и ворона — разные птицы.
Ворон крупнее вороны на 10–15 см.
Вороны умеют создавать орудия труда.
Вороны умеют считать.
Вред от ворон незначительный по сравнению с пользой.

Анкетирование
Большинство опрошенных одноклассников не различают ворону и ворона.

Заключение
Таким образом, ворона и ворон — разные птицы.
Гипотеза подтвердилась: у этих птиц есть отличия во внешнем виде и поведении.

Литература
1. Энциклопедия птиц для детей.
2. Атлас птиц России.

Приложение 1
Фотографии наблюдений.
"""


def test_is_noise_claim_filters_pdf_furniture_examples():
    noise_examples = [
        "Класс 3",
        "Направление: естественнонаучное, окружающий мир",
        "1 квалификационная категория",
        "ученица 3 класса",
        "2016",
        "2016 2 Содержание",
        "3 1.Особенности внешнего строения птиц",
        "5 1.1. Ворон",
        "5 1.2.Ворона",
        "Литература",
        "Приложение 1",
        "Муниципальное бюджетное общеобразовательное учреждение",
        "Петрова Анна Ивановна",
    ]

    for example in noise_examples:
        assert is_noise_claim(example), example


def test_preprocess_document_splits_academic_pdf_sections():
    preprocessed = preprocess_document(VORONA_VORON_TEXT)

    assert "Класс 3" in preprocessed.metadata_text
    assert "5 1.1. Ворон" in preprocessed.toc_text
    assert "Энциклопедия птиц" in preprocessed.references_text
    assert "Фотографии наблюдений" in preprocessed.appendices_text
    assert "Класс 3" not in preprocessed.analysis_text
    assert "5 1.1. Ворон" not in preprocessed.analysis_text
    assert "Ворон крупнее вороны" in preprocessed.analysis_text


def test_vorona_voron_pipeline_filters_noise_claims_and_keeps_meaningful_claims():
    result = analyze_text(
        text=VORONA_VORON_TEXT,
        filename="vorona_voron.pdf",
        material_type="реферат",
        audience_type="учитель",
        provider=MockLLMProvider(),
    )

    assert result.provider_name == "mock"
    assert result.provider_model == "mock"
    assert result.provider_response_id is None
    assert result.is_mock is True

    claims_text = "\n".join(claim.text for claim in result.claims).lower()
    forbidden = [
        "класс 3",
        "1 квалификационная категория",
        "ученица 3 класса",
        "2016 2 содержание",
        "5 1.1. ворон",
        "3 1.особенности",
    ]
    for fragment in forbidden:
        assert fragment not in claims_text

    main_idea = result.main_idea.lower()
    assert "ворона" in main_idea
    assert "ворон" in main_idea
    assert "разные птицы" in main_idea

    assert result.structure_analysis.goal == "изучить отличительные особенности вороны и ворона"

    assert "ворон и ворона — разные птицы" in claims_text
    assert "ворон крупнее вороны на 10–15 см" in claims_text
    assert "вороны умеют создавать орудия труда" in claims_text
    assert "вороны умеют считать" in claims_text
    assert "вред от ворон незначительный по сравнению с пользой" in claims_text

    report_text = build_markdown_report(result).lower()
    assert "provider: mock" in report_text
    assert "model: mock" in report_text
    assert "mock mode: yes" in report_text
    assert "инвестор" not in report_text
    assert "жюри" not in report_text
    assert "бизнес-ценность" not in report_text
