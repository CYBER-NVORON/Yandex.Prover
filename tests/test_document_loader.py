from app.document_loader import load_document


def test_load_txt_and_md(tmp_path):
    txt_path = tmp_path / "sample.txt"
    md_path = tmp_path / "sample.md"
    txt_path.write_text("Главная мысль текста.", encoding="utf-8")
    md_path.write_text("# Заголовок\n\nМатериал для анализа.", encoding="utf-8")

    txt = load_document(txt_path)
    md = load_document(md_path)

    assert txt.extension == ".txt"
    assert "Главная мысль" in txt.text
    assert md.extension == ".md"
    assert "Материал для анализа" in md.text

