from pathlib import Path
from tempfile import TemporaryDirectory

from rightclick_ai_markdown.converter import build_output_path, convert_file


def test_text_file_converts_to_markdown_text_only():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "sample.txt"
        source.write_text("hello AI", encoding="utf-8")

        result = convert_file(source, output_dir=root / "out")

        markdown = result.output.read_text(encoding="utf-8")
        assert result.output.name == "sample.md"
        assert "converter:" not in markdown
        assert "hello AI" in markdown


def test_markdown_source_gets_converted_suffix():
    with TemporaryDirectory() as tmp:
        source = Path(tmp) / "notes.md"
        source.write_text("# Notes", encoding="utf-8")

        output = build_output_path(source, output_dir=Path(tmp), overwrite=True)

        assert output.name == "notes_converted.md"


def test_requirements_install_full_markitdown_extras_for_office_files():
    requirements = Path("requirements.txt").read_text(encoding="utf-8")
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "markitdown[all]" in requirements
    assert "markitdown[all]" in pyproject


def test_metadata_only_next_step_points_to_local_venv_dependency_install():
    from rightclick_ai_markdown.converter import unsupported_markdown

    with TemporaryDirectory() as tmp:
        source = Path(tmp) / "sample.xlsx"
        source.write_bytes(b"not a real workbook")

        markdown = unsupported_markdown(source, "MissingDependencyException: install markitdown[xlsx]")

        assert "markitdown[all]" not in markdown
        assert "MissingDependencyException" in markdown


def test_scanned_pdf_routes_to_pdf_ocr_when_markitdown_has_too_little_text(monkeypatch):
    from rightclick_ai_markdown import converter

    with TemporaryDirectory() as tmp:
        source = Path(tmp) / "scan.pdf"
        source.write_bytes(b"%PDF-1.4\n% fake scanned pdf")

        monkeypatch.setattr(converter, "try_markitdown", lambda path: "\n")
        monkeypatch.setattr(
            converter,
            "convert_pdf_with_ocr",
            lambda path, ocr_language="eng+ind", pdf_ocr_dpi=200: ("OCR markdown", "OCR warning"),
        )

        markdown, warning = converter.convert_document(source)

        assert markdown == "OCR markdown"
        assert warning == "OCR warning"


def test_ocr_requirements_include_pdf_renderer_for_scanned_pdfs():
    requirements_ocr = Path("requirements-ocr.txt").read_text(encoding="utf-8").lower()
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8").lower()

    assert "pymupdf" in requirements_ocr
    assert "pymupdf" in pyproject



def test_text_only_output_has_no_metadata_headers():
    from rightclick_ai_markdown.converter import convert_text_file

    with TemporaryDirectory() as tmp:
        source = Path(tmp) / "a.txt"
        source.write_text("hello", encoding="utf-8")
        output = convert_text_file(source)
        assert not output.lstrip().startswith("---")
        assert "## AI Notes" not in output
