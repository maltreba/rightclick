from __future__ import annotations

import argparse
import datetime as dt
import html
import importlib
import importlib.util
import mimetypes
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

IMAGE_EXTENSIONS = {
    ".bmp",
    ".gif",
    ".heic",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
}

TEXT_EXTENSIONS = {
    ".bat",
    ".c",
    ".cfg",
    ".conf",
    ".cpp",
    ".cs",
    ".css",
    ".csv",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".log",
    ".md",
    ".php",
    ".ps1",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".sql",
    ".svg",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

CODE_FENCE_BY_EXTENSION = {
    ".bat": "bat",
    ".c": "c",
    ".cfg": "ini",
    ".conf": "ini",
    ".cpp": "cpp",
    ".cs": "csharp",
    ".css": "css",
    ".csv": "csv",
    ".go": "go",
    ".h": "c",
    ".hpp": "cpp",
    ".html": "html",
    ".ini": "ini",
    ".java": "java",
    ".js": "javascript",
    ".json": "json",
    ".jsx": "jsx",
    ".log": "text",
    ".php": "php",
    ".ps1": "powershell",
    ".py": "python",
    ".rb": "ruby",
    ".rs": "rust",
    ".sh": "bash",
    ".sql": "sql",
    ".svg": "xml",
    ".toml": "toml",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".txt": "text",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
}


@dataclass(frozen=True)
class ConversionResult:
    source: Path
    output: Path
    status: str
    warning: str | None = None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert files selected from Windows right-click into AI-friendly Markdown."
    )
    parser.add_argument("paths", nargs="+", type=Path, help="File or folder path to convert.")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="Directory for generated Markdown. Defaults to a sibling .ai-markdown folder.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="When a folder is selected, convert files recursively.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing Markdown outputs instead of creating numbered filenames.",
    )
    parser.add_argument(
        "--open-output",
        action="store_true",
        help="Open the output folder in File Explorer after conversion on Windows.",
    )
    parser.add_argument(
        "--ocr-language",
        default="eng+ind",
        help="Tesseract OCR language string. Default: eng+ind.",
    )
    args = parser.parse_args(argv)

    results: list[ConversionResult] = []
    failures = 0

    for input_path in args.paths:
        try:
            for file_path in iter_files(input_path, recursive=args.recursive):
                result = convert_file(
                    file_path=file_path,
                    output_dir=args.output_dir,
                    overwrite=args.overwrite,
                    ocr_language=args.ocr_language,
                )
                results.append(result)
                print(format_result(result))
        except Exception as exc:  # CLI boundary: show every selected-path error without a traceback.
            failures += 1
            print(f"ERROR: {input_path}: {exc}", file=sys.stderr)

    if args.open_output and results:
        open_in_file_explorer(results[-1].output.parent)

    warnings = sum(1 for result in results if result.warning)
    print(f"Done: {len(results)} converted, {warnings} warning(s), {failures} failure(s).")
    return 1 if failures else 0


def iter_files(path: Path, recursive: bool = False) -> Iterable[Path]:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Path does not exist: {resolved}")
    if resolved.is_file():
        yield resolved
        return
    if not resolved.is_dir():
        raise ValueError(f"Path is neither a file nor a directory: {resolved}")

    pattern = "**/*" if recursive else "*"
    for child in sorted(resolved.glob(pattern)):
        if child.is_file():
            yield child


def convert_file(
    file_path: Path,
    output_dir: Path | None = None,
    overwrite: bool = False,
    ocr_language: str = "eng+ind",
) -> ConversionResult:
    source = file_path.expanduser().resolve()
    target = build_output_path(source, output_dir=output_dir, overwrite=overwrite)
    target.parent.mkdir(parents=True, exist_ok=True)

    warning: str | None = None
    try:
        if source.suffix.lower() in IMAGE_EXTENSIONS:
            body, warning = convert_image_with_ocr(source, ocr_language=ocr_language)
        else:
            body, warning = convert_document(source)
    except Exception as exc:
        body = unsupported_markdown(source, f"Conversion failed: {exc}")
        warning = str(exc)

    target.write_text(body, encoding="utf-8")
    return ConversionResult(source=source, output=target, status="converted", warning=warning)


def build_output_path(source: Path, output_dir: Path | None = None, overwrite: bool = False) -> Path:
    destination_dir = output_dir.expanduser().resolve() if output_dir else source.parent / ".ai-markdown"
    stem = f"{source.stem}_converted" if source.suffix.lower() == ".md" else source.stem
    candidate = destination_dir / f"{stem}.md"
    if overwrite or not candidate.exists():
        return candidate

    counter = 2
    while True:
        numbered = destination_dir / f"{stem}-{counter}.md"
        if not numbered.exists():
            return numbered
        counter += 1


def convert_image_with_ocr(source: Path, ocr_language: str = "eng+ind") -> tuple[str, str | None]:
    text, engine, warning = ocr_image(source, ocr_language=ocr_language)
    lines = [
        metadata_header(source, converter=f"OCR image ({engine})"),
        "## OCR Text",
        "",
    ]
    if text.strip():
        lines.append(text.strip())
    else:
        lines.append("_No text was detected in this image._")
        warning = warning or "OCR completed but no text was detected."
    lines.extend(["", "## AI Notes", "", "- Source file was an image, so visible text was extracted with OCR."])
    if warning:
        lines.append(f"- Warning: {warning}")
    lines.append("")
    return "\n".join(lines), warning


def ocr_image(source: Path, ocr_language: str = "eng+ind") -> tuple[str, str, str | None]:
    easyocr_result = try_easyocr(source)
    if easyocr_result is not None:
        return easyocr_result, "EasyOCR", None

    pytesseract_result = try_pytesseract(source, ocr_language=ocr_language)
    if pytesseract_result is not None:
        return pytesseract_result, "pytesseract/Tesseract", None

    cli_result = try_tesseract_cli(source, ocr_language=ocr_language)
    if cli_result is not None:
        return cli_result, "Tesseract CLI", None

    warning = (
        "No OCR engine is available. Install EasyOCR with `pip install --user easyocr` "
        "or install pytesseract plus a portable Tesseract executable on PATH."
    )
    return "", "not available", warning


def try_easyocr(source: Path) -> str | None:
    if importlib.util.find_spec("easyocr") is None:
        return None

    easyocr = importlib.import_module("easyocr")
    reader = easyocr.Reader(["en", "id"], gpu=False, verbose=False)
    parts = reader.readtext(str(source), detail=0, paragraph=True)
    return "\n".join(str(part) for part in parts).strip()


def try_pytesseract(source: Path, ocr_language: str = "eng+ind") -> str | None:
    if importlib.util.find_spec("PIL") is None or importlib.util.find_spec("pytesseract") is None:
        return None

    image_module = importlib.import_module("PIL.Image")
    pytesseract = importlib.import_module("pytesseract")
    with image_module.open(source) as image:
        for language in ocr_language_candidates(ocr_language):
            try:
                return str(pytesseract.image_to_string(image, lang=language)).strip()
            except pytesseract.TesseractError:
                image.seek(0)
        return None


def try_tesseract_cli(source: Path, ocr_language: str = "eng+ind") -> str | None:
    tesseract = shutil.which("tesseract")
    if not tesseract:
        return None

    for language in ocr_language_candidates(ocr_language):
        completed = subprocess.run(
            [tesseract, str(source), "stdout", "-l", language],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if completed.returncode == 0:
            return completed.stdout.strip()
    return None


def ocr_language_candidates(ocr_language: str) -> list[str]:
    candidates = [ocr_language]
    if "+" in ocr_language:
        candidates.extend(part for part in ocr_language.split("+") if part)
    if "eng" not in candidates:
        candidates.append("eng")
    return list(dict.fromkeys(candidates))


def convert_document(source: Path) -> tuple[str, str | None]:
    markdown = try_markitdown(source)
    if markdown is not None:
        return add_header_if_missing(markdown, source, converter="MarkItDown"), None

    if source.suffix.lower() in TEXT_EXTENSIONS or looks_like_text(source):
        return convert_text_file(source), None

    warning = "No converter recognized this file type; metadata-only Markdown was created."
    return unsupported_markdown(source, warning), warning


def try_markitdown(source: Path) -> str | None:
    if importlib.util.find_spec("markitdown") is None:
        return None

    markitdown = importlib.import_module("markitdown")
    converter = markitdown.MarkItDown()
    result = converter.convert(str(source))
    text_content = getattr(result, "text_content", "")
    if not text_content:
        return None
    return str(text_content).strip() + "\n"


def convert_text_file(source: Path) -> str:
    content = read_text_best_effort(source)
    suffix = source.suffix.lower()
    if suffix == ".md":
        body = content.strip() + "\n"
    else:
        language = CODE_FENCE_BY_EXTENSION.get(suffix, "text")
        body = f"```{language}\n{escape_code_fence(content)}\n```\n"
    return metadata_header(source, converter="plain text") + body


def read_text_best_effort(source: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return source.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return source.read_bytes().decode("utf-8", errors="replace")


def looks_like_text(source: Path, sample_size: int = 4096) -> bool:
    sample = source.read_bytes()[:sample_size]
    if not sample:
        return True
    if b"\x00" in sample:
        return False
    text_chars = sum(1 for byte in sample if byte in b"\n\r\t\b" or 32 <= byte <= 126 or byte >= 128)
    return text_chars / len(sample) > 0.85


def metadata_header(source: Path, converter: str) -> str:
    mime_type, _ = mimetypes.guess_type(source.name)
    size = source.stat().st_size
    timestamp = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
    return (
        "---\n"
        f"title: {yaml_scalar(source.name)}\n"
        f"source_path: {yaml_scalar(str(source))}\n"
        f"source_extension: {yaml_scalar(source.suffix.lower() or '(none)')}\n"
        f"mime_type: {yaml_scalar(mime_type or 'unknown')}\n"
        f"size_bytes: {size}\n"
        f"converted_at: {yaml_scalar(timestamp)}\n"
        f"converter: {yaml_scalar(converter)}\n"
        "---\n\n"
    )


def add_header_if_missing(markdown: str, source: Path, converter: str) -> str:
    stripped = markdown.lstrip()
    if stripped.startswith("---"):
        return markdown.rstrip() + "\n"
    return metadata_header(source, converter=converter) + markdown.rstrip() + "\n"


def unsupported_markdown(source: Path, reason: str) -> str:
    escaped_reason = html.escape(reason)
    return (
        metadata_header(source, converter="metadata only")
        + "## Conversion Warning\n\n"
        + f"{escaped_reason}\n\n"
        + "## Next Step\n\n"
        + "Re-run `scripts\\install-ai-markdown-context-menu.ps1` so the local `.venv` installs "
        + "the full `markitdown[all]` converter extras, or run "
        + "`.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt` from the repo root.\n"
    )


def yaml_scalar(value: str) -> str:
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def escape_code_fence(content: str) -> str:
    return content.replace("```", "``\\`")


def format_result(result: ConversionResult) -> str:
    suffix = f" WARNING: {result.warning}" if result.warning else ""
    return f"OK: {result.source} -> {result.output}{suffix}"


def open_in_file_explorer(path: Path) -> None:
    if os.name == "nt":
        subprocess.Popen(["explorer", str(path)])  # noqa: S603,S607 - Windows shell integration helper.
