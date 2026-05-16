from __future__ import annotations

import html
from pathlib import Path

import pandas as pd
import streamlit as st

from app.analysis_pipeline import analyze_text
from app.config import get_settings
from app.document_loader import DocumentLoadError, LoadedDocument, load_document_from_bytes
from app.llm.base import LLMProviderError
from app.report_builder import build_markdown_report
from app.schemas import AnalysisResult, Claim
from app.storage import StorageError, save_result


MATERIAL_TYPES = [
    "сочинение",
    "доклад",
    "реферат",
    "курсовая",
    "диплом",
    "диссертация",
    "статья",
    "презентация",
    "питч проекта",
    "публичное выступление",
    "деловое письмо / обращение",
    "другое",
]

AUDIENCE_TYPES = [
    "учитель",
    "преподаватель",
    "научный руководитель",
    "комиссия",
    "жюри",
    "инвестор",
    "коллеги",
    "широкая аудитория",
]

VALID_RISKS = {"low", "medium", "high"}
RISK_LABELS = {"low": "низкий", "medium": "средний", "high": "высокий"}
RISK_ORDER = {"high": 0, "medium": 1, "low": 2}
EVIDENCE_LABELS = {
    "supported_by_text": "подтверждается текстом",
    "needs_source": "нужен источник",
    "weak_argument": "слабое обоснование",
    "too_strong": "слишком сильная формулировка",
    "unverifiable_from_text": "не подтверждается внутри материала",
    "ok": "ок",
}
CLAIM_TYPE_LABELS = {
    "fact": "факт",
    "number": "число",
    "comparison": "сравнение",
    "causality": "причинность",
    "generalization": "обобщение",
    "opinion": "мнение",
    "definition": "определение",
    "unsupported_conclusion": "вывод без опоры",
}


def safe_html(text: str) -> str:
    return html.escape(str(text), quote=True)


def setup_page() -> None:
    st.set_page_config(
        page_title="Доказатель",
        page_icon="🔎",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(
        """
        <style>
        :root {
            --page: #f6f3ea;
            --paper: #ffffff;
            --ink: #101114;
            --muted: #60616a;
            --line: #e8e0cf;
            --accent: #facc15;
            --accent-strong: #d97706;
            --green-bg: #e8f7ef;
            --green: #166534;
            --yellow-bg: #fff3c4;
            --yellow: #8a5a00;
            --red-bg: #ffe4e6;
            --red: #9f1239;
        }
        .stApp {
            background: var(--page);
            color: var(--ink);
        }
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1180px;
        }
        h1, h2, h3, p, li {
            letter-spacing: 0;
        }
        .hero {
            background: var(--paper);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 2.2rem 2.4rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 18px 45px rgba(16, 17, 20, 0.08);
        }
        .hero-badge {
            display: inline-flex;
            align-items: center;
            background: #fff1a8;
            border: 1px solid #f0d24a;
            border-radius: 999px;
            color: #201a05;
            font-size: 0.86rem;
            font-weight: 750;
            padding: 0.28rem 0.7rem;
            margin-bottom: 1rem;
        }
        .hero-title {
            color: var(--ink);
            font-size: 3.15rem;
            line-height: 1.04;
            font-weight: 850;
            margin: 0 0 0.65rem 0;
        }
        .hero-subtitle {
            color: var(--ink);
            font-size: 1.25rem;
            line-height: 1.5;
            max-width: 780px;
            margin: 0;
        }
        .hero-note {
            color: var(--muted);
            font-size: 1rem;
            max-width: 760px;
            margin-top: 1rem;
        }
        .feature-card {
            background: var(--paper);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem 1.05rem;
            min-height: 142px;
            box-shadow: 0 10px 26px rgba(16, 17, 20, 0.05);
        }
        .feature-card h3 {
            color: var(--ink);
            font-size: 1.05rem;
            margin: 0 0 0.45rem 0;
        }
        .feature-card p {
            color: var(--muted);
            font-size: 0.95rem;
            line-height: 1.45;
            margin: 0;
        }
        .score-band {
            border-left: 5px solid var(--accent);
            border-radius: 8px;
            padding: 0.95rem 1rem;
            background: var(--paper);
            margin: 0.5rem 0 1rem 0;
            color: var(--ink);
        }
        .top-risk-card {
            background: var(--paper);
            border: 1px solid var(--line);
            border-left: 5px solid var(--accent-strong);
            border-radius: 8px;
            padding: 0.95rem 1rem;
            margin: 0.7rem 0;
            box-shadow: 0 8px 22px rgba(16, 17, 20, 0.05);
        }
        .top-risk-card strong {
            color: var(--ink);
        }
        .top-risk-card p {
            color: var(--muted);
            margin: 0.35rem 0;
            line-height: 1.45;
        }
        .risk-badge {
            display: inline-block;
            min-width: 76px;
            text-align: center;
            border-radius: 999px;
            padding: 0.18rem 0.55rem;
            font-size: 0.82rem;
            font-weight: 700;
        }
        .risk-low {
            background: var(--green-bg);
            color: var(--green);
        }
        .risk-medium {
            background: var(--yellow-bg);
            color: var(--yellow);
        }
        .risk-high {
            background: var(--red-bg);
            color: var(--red);
        }
        .section-rule {
            border-top: 1px solid var(--line);
            margin: 1rem 0;
        }
        div[data-testid="stMetric"] {
            background: var(--paper);
            border: 1px solid var(--line);
            padding: 0.85rem 1rem;
            border-radius: 8px;
            box-shadow: 0 8px 22px rgba(16, 17, 20, 0.04);
        }
        .stButton > button {
            border-radius: 8px;
            font-weight: 700;
        }
        @media (max-width: 640px) {
            .hero {
                padding: 1.5rem;
            }
            .hero-title {
                font-size: 2.3rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def risk_badge(risk_level: str) -> str:
    normalized = risk_level if risk_level in VALID_RISKS else "medium"
    label = RISK_LABELS[normalized]
    return f'<span class="risk-badge risk-{normalized}">{safe_html(label)}</span>'


def score_verdict(score: int) -> tuple[str, str]:
    if score >= 80:
        return "Идея выглядит убедительно", "low"
    if score >= 60:
        return "Есть сильная база, но есть риски", "medium"
    return "Материал нужно усилить перед показом аудитории", "high"


def render_bullet_list(items: list[str]) -> None:
    if not items:
        st.caption("Нет данных.")
        return
    for item in items:
        st.markdown(f"- {item}")


def style_risk_dataframe(dataframe: pd.DataFrame) -> pd.io.formats.style.Styler:
    def color_risk(value: str) -> str:
        if value == "высокий":
            return "background-color: #ffe4e6; color: #9f1239; font-weight: 700"
        if value == "средний":
            return "background-color: #fff3c4; color: #8a5a00; font-weight: 700"
        if value == "низкий":
            return "background-color: #e8f7ef; color: #166534; font-weight: 700"
        return ""

    styler = dataframe.style
    if "Риск" not in dataframe.columns:
        return styler
    return styler.map(color_risk, subset=["Риск"])


def claims_dataframe(result: AnalysisResult) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Утверждение": claim.text,
                "Тип": CLAIM_TYPE_LABELS.get(claim.claim_type, claim.claim_type),
                "Статус доказательности": EVIDENCE_LABELS.get(claim.evidence_status, claim.evidence_status),
                "Риск": RISK_LABELS.get(claim.risk_level, claim.risk_level),
                "Почему это проблема": claim.explanation,
                "Рекомендация": claim.recommendation,
                "Более осторожная формулировка": claim.suggested_rewrite,
            }
            for claim in result.claims
        ]
    )


def questions_dataframe(result: AnalysisResult) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Вопрос": question.question,
                "Кто может задать": question.asked_by,
                "Категория": question.category,
                "Почему могут задать": question.why_asked,
                "Риск": RISK_LABELS.get(question.risk_level, question.risk_level),
                "Рекомендуемый ответ": question.suggested_answer,
                "Что добавить": question.how_to_improve_material,
            }
            for question in result.audience_questions
        ]
    )


def render_hero() -> None:
    st.markdown(
        """
        <section class="hero">
            <div class="hero-badge">ИИ-рецензент для предзащиты</div>
            <h1 class="hero-title">Доказатель</h1>
            <p class="hero-subtitle">Проверь, выдержит ли твоя идея вопросы аудитории.</p>
            <p class="hero-note">Сервис анализирует готовый материал, находит слабые места до того, как их найдёт аудитория, и помогает подготовить доказательную защиту.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_product_explanation() -> None:
    cards = [
        (
            "Находит слабые места",
            "Показывает, где главная мысль теряется, аргумент звучит как мнение или вывод слишком широкий для текущего текста.",
        ),
        (
            "Проверяет доказательность",
            "Отмечает утверждения, которым нужен источник, пример или подтверждение внутри материала. Внешние источники не подставляются.",
        ),
        (
            "Готовит вопросы аудитории",
            "Формирует вопросы для предзащиты и стресс-теста идеи. Сервис не создаёт материал вместо автора, а проверяет уже готовую работу.",
        ),
    ]
    columns = st.columns(3)
    for column, (title, body) in zip(columns, cards, strict=True):
        with column:
            st.markdown(
                f"""
                <div class="feature-card">
                    <h3>{safe_html(title)}</h3>
                    <p>{safe_html(body)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def top_threats(result: AnalysisResult) -> list[tuple[str, str, str, str]]:
    threats: list[tuple[str, str, str, str]] = []
    sorted_claims = sorted(result.claims, key=lambda claim: RISK_ORDER.get(claim.risk_level, 1))
    for claim in sorted_claims:
        if claim.risk_level == "high":
            threats.append(
                (
                    f"Рискованное утверждение: {claim.text}",
                    claim.risk_level,
                    claim.explanation,
                    claim.recommendation,
                )
            )
    for weakness in result.weaknesses:
        threats.append((weakness.problem, "medium", weakness.why_problem, weakness.fix))
    if len(threats) < 3:
        for claim in sorted_claims:
            if claim.risk_level != "high":
                threats.append(
                    (
                        f"Утверждение требует внимания: {claim.text}",
                        claim.risk_level,
                        claim.explanation,
                        claim.recommendation,
                    )
                )
            if len(threats) >= 3:
                break
    return threats[:3]


def render_top_threats(result: AnalysisResult) -> None:
    threats = top_threats(result)
    if not threats:
        return
    st.markdown("**Топ-3 главных угроз**")
    columns = st.columns(len(threats))
    for column, (title, risk, reason, action) in zip(columns, threats, strict=True):
        with column:
            st.markdown(
                f"""
                <div class="top-risk-card">
                    <strong>{safe_html(title)}</strong><br>
                    {risk_badge(risk)}
                    <p>{safe_html(reason)}</p>
                    <p><strong>Что сделать:</strong> {safe_html(action)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_overview(result: AnalysisResult) -> None:
    verdict_text, verdict_risk = score_verdict(result.persuasiveness_score)
    metric_col, detail_col = st.columns([1, 2])
    with metric_col:
        st.metric("Индекс убедительности", f"{result.persuasiveness_score}/100")
        st.progress(result.persuasiveness_score / 100)
    with detail_col:
        st.markdown(
            f"""
            <div class="score-band">
                <strong>{safe_html(verdict_text)}</strong> {risk_badge(verdict_risk)}
                <p>{safe_html(result.summary)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("**Главная мысль**")
        st.write(result.main_idea)

    render_top_threats(result)

    score_cols = st.columns(6)
    breakdown = result.scoring_breakdown
    metrics = [
        ("Ясность", breakdown.clarity_score),
        ("Структура", breakdown.structure_score),
        ("Аргументы", breakdown.argument_score),
        ("Доказательность", breakdown.evidence_score),
        ("Аудитория", breakdown.audience_score),
        ("Вопросы", breakdown.question_readiness_score),
    ]
    for column, (label, value) in zip(score_cols, metrics, strict=True):
        column.metric(label, f"{value}/100")

    left, middle, right = st.columns(3)
    with left:
        st.markdown("**Сильные стороны**")
        render_bullet_list(result.strengths)
    with middle:
        st.markdown("**Слабые стороны**")
        render_bullet_list([weakness.problem for weakness in result.weaknesses])
    with right:
        st.markdown("**Главные риски**")
        render_bullet_list(result.risks)


def render_structure(result: AnalysisResult) -> None:
    structure = result.structure_analysis
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.markdown("**Главная мысль**")
        st.write(structure.main_idea)
        st.markdown("**Цель**")
        st.write(structure.goal)
        st.markdown("**Структура материала**")
        st.write(structure.structure_summary)
    with col_b:
        st.metric("Ясность", f"{structure.clarity_score}/100")
        st.metric("Логика структуры", f"{structure.logic_quality_score}/100")
        st.markdown("**Аудитория**")
        st.write(structure.target_audience)

    st.markdown("**Логические разрывы**")
    render_bullet_list(structure.problems)
    st.markdown("**Рекомендации по структуре**")
    render_bullet_list(structure.suggestions)


def risky_claims(claims: list[Claim], limit: int = 5) -> list[Claim]:
    return sorted(claims, key=lambda claim: RISK_ORDER.get(claim.risk_level, 1))[:limit]


def render_risky_claim_cards(claims: list[Claim]) -> None:
    selected = risky_claims(claims)
    if not selected:
        return
    st.markdown("**Самые рискованные утверждения**")
    columns = st.columns(min(3, len(selected)))
    for index, claim in enumerate(selected):
        with columns[index % len(columns)]:
            rewrite = claim.suggested_rewrite.strip()
            rewrite_html = ""
            if rewrite:
                rewrite_html = f"<p><strong>Осторожнее:</strong> {safe_html(rewrite)}</p>"
            st.markdown(
                f"""
                <div class="top-risk-card">
                    <strong>{safe_html(claim.text)}</strong><br>
                    {risk_badge(claim.risk_level)}
                    <p><strong>Статус:</strong> {safe_html(EVIDENCE_LABELS.get(claim.evidence_status, claim.evidence_status))}</p>
                    <p><strong>Почему это проблема:</strong> {safe_html(claim.explanation)}</p>
                    <p><strong>Рекомендация:</strong> {safe_html(claim.recommendation)}</p>
                    {rewrite_html}
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_claims(result: AnalysisResult) -> None:
    dataframe = claims_dataframe(result)
    if dataframe.empty:
        st.info("В материале не найдено утверждений, требующих отдельной проверки.")
        return
    render_risky_claim_cards(result.claims)
    st.markdown("**Подробная таблица**")
    st.dataframe(style_risk_dataframe(dataframe), width="stretch", hide_index=True)
    st.caption("Оценка строится только по загруженному материалу. Если подтверждения нет в тексте, статус не считается внешней проверкой.")


def render_weaknesses(result: AnalysisResult) -> None:
    if not result.weaknesses:
        st.info("Слабые места не выявлены.")
        return
    for weakness in result.weaknesses:
        st.markdown(f"**{weakness.problem}**")
        st.write(weakness.why_problem)
        st.markdown(f"**Как это может заметить аудитория:** {weakness.audience_signal}")
        st.markdown(f"**Что исправить:** {weakness.fix}")
        st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)


def render_questions(result: AnalysisResult) -> None:
    dataframe = questions_dataframe(result)
    if dataframe.empty:
        st.info("Вопросы аудитории не сформированы.")
        return
    st.dataframe(style_risk_dataframe(dataframe), width="stretch", hide_index=True)

    st.markdown("**Подробные ответы**")
    for question in result.audience_questions:
        st.markdown(
            f"**{safe_html(question.question)}** {risk_badge(question.risk_level)}",
            unsafe_allow_html=True,
        )
        st.write(question.suggested_answer)
        st.caption(question.how_to_improve_material)


def render_plan(result: AnalysisResult) -> None:
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("**Что исправить за 30 минут**")
        render_bullet_list(result.improvement_plan.quick_fixes_30_min)
    with col_b:
        st.markdown("**Что улучшить за 2 часа**")
        render_bullet_list(result.improvement_plan.improvements_2_hours)
    with col_c:
        st.markdown("**Что добавить до финальной версии**")
        render_bullet_list(result.improvement_plan.final_polish)

    st.markdown("**Рекомендации**")
    rows = [
        {
            "Риск": RISK_LABELS.get(rec.priority, rec.priority),
            "Категория": rec.category,
            "Проблема": rec.problem,
            "Действие": rec.action,
            "Ожидаемый эффект": rec.expected_effect,
        }
        for rec in result.recommendations
    ]
    if rows:
        st.dataframe(style_risk_dataframe(pd.DataFrame(rows)), width="stretch", hide_index=True)


def render_stress_test(result: AnalysisResult) -> None:
    stress = result.stress_test
    st.markdown("**Самый опасный вопрос**")
    st.markdown(f"### {stress.most_dangerous_question}")
    st.markdown("**Почему он опасен**")
    st.write(stress.why_dangerous)
    st.markdown("**Слабое место, на которое он указывает**")
    st.write(stress.exposed_weakness)
    st.markdown("**Как ответить**")
    st.write(stress.suggested_answer)
    st.markdown("**Что добавить в материал**")
    st.write(stress.what_to_add)


def render_report(result: AnalysisResult) -> None:
    report = build_markdown_report(result)
    st.download_button(
        "Скачать отчёт",
        data=report.encode("utf-8"),
        file_name="otchet.md",
        mime="text/markdown",
        width="stretch",
    )
    st.markdown(report)


def render_dashboard(result: AnalysisResult) -> None:
    tabs = st.tabs(
        [
            "Обзор",
            "Главная мысль и структура",
            "Карта доказательности",
            "Слабые места",
            "Вопросы аудитории",
            "План улучшения",
            "Разнеси мою идею",
            "Отчёт",
        ]
    )
    with tabs[0]:
        render_overview(result)
    with tabs[1]:
        render_structure(result)
    with tabs[2]:
        render_claims(result)
    with tabs[3]:
        render_weaknesses(result)
    with tabs[4]:
        render_questions(result)
    with tabs[5]:
        render_plan(result)
    with tabs[6]:
        render_stress_test(result)
    with tabs[7]:
        render_report(result)


def render_provider_notice(result: AnalysisResult) -> None:
    if result.is_mock:
        st.warning("Анализ выполнен в демонстрационном режиме. Реальная модель Алисы не отвечала.")
    elif result.provider_name == "yandex":
        st.success(f"Ответ получен от Yandex AI: {result.provider_model}")


def analyze_loaded_document(
    *,
    loaded: LoadedDocument,
    material_type: str,
    audience_type: str,
    database_path: Path,
) -> AnalysisResult:
    result = analyze_text(
        text=loaded.text,
        filename=loaded.filename,
        material_type=material_type,
        audience_type=audience_type,
    )
    save_result(result, database_path)
    st.session_state["analysis_result"] = result
    return result


def run_demo_analysis(settings) -> None:
    demo_path = Path(__file__).parent / "examples" / "sample_pitch.txt"
    if not demo_path.exists():
        st.error("Демо-файл examples/sample_pitch.txt не найден.")
        return
    try:
        loaded = load_document_from_bytes(
            demo_path.name,
            demo_path.read_bytes(),
            max_chars=settings.max_chars_for_analysis,
        )
        with st.spinner("Идёт демо-анализ питча проекта..."):
            analyze_loaded_document(
                loaded=loaded,
                material_type="питч проекта",
                audience_type="жюри",
                database_path=settings.database_path,
            )
        st.success("Анализ готов")
    except OSError:
        st.error("Не удалось прочитать демо-файл examples/sample_pitch.txt.")
    except (DocumentLoadError, LLMProviderError, StorageError) as exc:
        st.error(str(exc))
    except Exception as exc:  # pragma: no cover - defensive UI guard
        st.error(f"Не удалось выполнить демо-анализ: {exc}")


def main() -> None:
    setup_page()
    settings = get_settings()

    render_hero()
    render_product_explanation()

    with st.sidebar:
        st.markdown("**Режим модели**")
        st.write("Локальный демонстрационный режим" if settings.llm_provider == "mock" else settings.llm_provider)
        if settings.llm_provider == "mock":
            st.caption("Демонстрационный режим подходит для хакатонного демо без API-ключей.")
        st.markdown("**Хранилище**")
        st.caption(str(settings.database_path))
        if st.button("Сбросить результат", width="stretch"):
            st.session_state.pop("analysis_result", None)
            st.rerun()

    st.markdown("### Загрузить материал")
    input_col, meta_col = st.columns([1.2, 1])
    with input_col:
        uploaded_file = st.file_uploader(
            "Файл материала",
            type=["txt", "md", "pdf", "docx", "pptx"],
            accept_multiple_files=False,
            help="Поддерживаются TXT, MD, PDF, DOCX и PPTX. Большие файлы будут обрезаны до 50000 символов для анализа.",
        )
    with meta_col:
        material_type = st.selectbox("Тип материала", MATERIAL_TYPES, index=MATERIAL_TYPES.index("питч проекта"))
        audience_type = st.selectbox("Аудитория", AUDIENCE_TYPES, index=AUDIENCE_TYPES.index("жюри"))

    action_col, demo_col = st.columns([1, 1])
    with action_col:
        analyze_clicked = st.button("Проанализировать", type="primary", width="stretch")
    with demo_col:
        demo_clicked = st.button("Запустить демо на питче проекта", width="stretch")

    if demo_clicked:
        run_demo_analysis(settings)

    if analyze_clicked:
        if uploaded_file is None:
            st.error("Загрузите файл TXT, MD, PDF, DOCX или PPTX.")
        else:
            try:
                loaded = load_document_from_bytes(
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    max_chars=settings.max_chars_for_analysis,
                )
                if loaded.was_truncated:
                    st.warning(
                        f"Файл содержит {loaded.original_chars} символов. Для анализа взяты первые "
                        f"{settings.max_chars_for_analysis} символов."
                    )
                with st.spinner("Идёт анализ материала..."):
                    analyze_loaded_document(
                        loaded=loaded,
                        material_type=material_type,
                        audience_type=audience_type,
                        database_path=settings.database_path,
                    )
                st.success("Анализ готов")
            except DocumentLoadError as exc:
                st.error(str(exc))
            except LLMProviderError as exc:
                st.error(str(exc))
            except StorageError as exc:
                st.error(str(exc))
            except Exception as exc:  # pragma: no cover - defensive UI guard
                st.error(f"Не удалось выполнить анализ: {exc}")

    result = st.session_state.get("analysis_result")
    with st.sidebar:
        st.markdown("**Ответ модели**")
        if isinstance(result, AnalysisResult):
            st.caption(f"Поставщик: {result.provider_name}")
            st.caption(f"Модель: {result.provider_model}")
            st.caption(f"ID ответа: {result.provider_response_id or '-'}")
            st.caption(f"Демо-режим: {'да' if result.is_mock else 'нет'}")
        else:
            st.caption("Поставщик: -")
            st.caption("Модель: -")
            st.caption("ID ответа: -")
            st.caption("Демо-режим: -")
    if isinstance(result, AnalysisResult):
        render_provider_notice(result)
        render_dashboard(result)


if __name__ == "__main__":
    main()
