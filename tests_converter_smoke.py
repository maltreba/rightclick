from pathlib import Path
from tempfile import TemporaryDirectory

from rightclick_ai_markdown.converter import build_output_path, convert_file


def test_text_file_converts_to_markdown_with_metadata():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "sample.txt"
        source.write_text("hello AI", encoding="utf-8")

        result = convert_file(source, output_dir=root / "out")

        markdown = result.output.read_text(encoding="utf-8")
        assert result.output.name == "sample.md"
        assert "converter: \"plain text\"" in markdown
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

        assert "markitdown[all]" in markdown
        assert ".venv" in markdown
        assert "requirements.txt" in markdown
