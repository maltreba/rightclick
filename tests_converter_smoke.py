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
