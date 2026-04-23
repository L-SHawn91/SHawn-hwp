"""HWP 5.x salvage extraction helpers for SHawn-hwp."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from shawn_hwp.converters.stub import ConversionResult
from shawn_hwp.converters.strategy_router import choose_route
from shawn_hwp.io_docx import write_docx
from shawn_hwp.io_markdown import render_markdown
from shawn_hwp.model import DocumentModel


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _venv_python() -> Path:
    return _repo_root() / ".venv-hwp" / "bin" / "python"


def hwp_salvage_available() -> bool:
    return _venv_python().exists()


def hwp_bridge_available() -> bool:
    return Path('/tmp/hwp2hwpx/build/classes/RunConvert.class').exists() and Path('/tmp/hwp2hwpx/lib').exists()


def _build_result(
    input_path: Path,
    output_path: Path,
    source_format: str,
    target_format: str,
    route: str | None,
    template: Path | None,
    preserve_original: bool,
) -> ConversionResult:
    chosen_route = route or choose_route(source_format, target_format)
    return ConversionResult(
        input_path=str(input_path),
        output_path=str(output_path),
        source_format=source_format,
        target_format=target_format,
        route=chosen_route,
        preserve_original=preserve_original,
        template=str(template) if template else None,
        input_size_bytes=input_path.stat().st_size,
        output_size_bytes=output_path.stat().st_size,
    )


def _normalize_hwp_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"^<표>\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+-\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def _split_compound_line(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped:
        return []
    parts = re.split(r"\s{2,}(?=(?:[가-힣]\.|[가-힣]-\d+\.|\d+\)|\(\d+\)|\d+\.))", stripped)
    return [part.strip() for part in parts if part.strip()]


def _heading_level(line: str) -> int | None:
    stripped = line.strip()
    if not stripped:
        return None
    if re.match(r"^#+\s+", stripped):
        return min(len(stripped.split()[0]), 6)
    if re.match(r"^목\s*차$", stripped):
        return 1
    if re.match(r"^\d+\.\s+", stripped):
        return 1
    if re.match(r"^\(\d+\)\s+", stripped):
        return 2
    if re.match(r"^[가-힣]\.\s+", stripped):
        return 3
    if re.match(r"^[가-힣]-\d+\.\s+", stripped):
        return 3
    if re.match(r"^\d+\)\s+", stripped):
        return 3
    if re.match(r"^[가-힣]\)\s+", stripped):
        return 4
    return None


def _is_paragraph_continuation(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("※") or stripped.startswith("-"):
        return True
    if stripped.startswith("(") and "단위:" in stripped:
        return True
    if stripped in {"설립"}:
        return True
    if len(stripped) <= 2:
        return True
    if re.match(r"^[가-힣A-Za-z0-9][^:]{0,80}$", stripped) and not _heading_level(stripped):
        return True
    return False


def _normalize_heading_text(text: str) -> str:
    return re.sub(r"\s+", "", text.strip())


def _strip_toc_echoes(model: DocumentModel) -> DocumentModel:
    blocks = model.blocks
    cleaned: list = []
    i = 0

    while i < len(blocks):
        block = blocks[i]
        is_toc = block.kind == "heading" and _normalize_heading_text(block.text) == "목차"
        if not is_toc:
            cleaned.append(block)
            i += 1
            continue

        j = i + 1
        toc_signature: list[tuple[int, str]] = []
        seen_toc_headings: set[tuple[int, str]] = set()
        while j < len(blocks) and blocks[j].kind == "heading":
            key = (blocks[j].level, _normalize_heading_text(blocks[j].text))
            if key in seen_toc_headings:
                break
            seen_toc_headings.add(key)
            toc_signature.append(key)
            j += 1

        if not toc_signature:
            cleaned.append(block)
            i += 1
            continue

        matched = False
        for k in range(j, len(blocks)):
            candidate: list[tuple[int, str]] = []
            m = k
            while m < len(blocks) and len(candidate) < len(toc_signature):
                if blocks[m].kind == "heading":
                    candidate.append((blocks[m].level, _normalize_heading_text(blocks[m].text)))
                m += 1
            if candidate[: len(toc_signature)] == toc_signature:
                matched = True
                break

        if matched:
            i = j
            continue

        cleaned.append(block)
        i += 1

    model.blocks = cleaned
    return model


def parse_hwp_text_to_model(text: str) -> DocumentModel:
    model = DocumentModel()
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            merged = "\n".join(line.strip() for line in paragraph_lines if line.strip()).strip()
            if merged:
                model.add_paragraph(merged, source_trace="hwp:paragraph")
            paragraph_lines = []

    for raw_line in text.splitlines():
        split_lines = _split_compound_line(raw_line) or ([raw_line.strip()] if raw_line.strip() else [])
        if not split_lines:
            flush_paragraph()
            continue

        for line in split_lines:
            markdown_heading = re.match(r"^(#+)\s+(.+)$", line)
            if markdown_heading:
                flush_paragraph()
                model.add_heading(
                    markdown_heading.group(2).strip(),
                    level=min(len(markdown_heading.group(1)), 6),
                    source_trace="hwp:normalized-markdown",
                )
                continue

            level = _heading_level(line)
            if level is not None:
                flush_paragraph()
                model.add_heading(line.strip(), level=level, source_trace=f"hwp:heading-l{level}")
                continue

            if paragraph_lines and _is_paragraph_continuation(line):
                paragraph_lines.append(line)
            else:
                flush_paragraph()
                paragraph_lines.append(line)

    flush_paragraph()
    return _strip_toc_echoes(model)


def extract_hwp_text(input_path: Path) -> str:
    python_bin = _venv_python()
    if not python_bin.exists():
        raise RuntimeError("HWP salvage environment is not available (.venv-hwp missing)")

    hwp5txt_bin = python_bin.parent / "hwp5txt"
    if not hwp5txt_bin.exists():
        raise RuntimeError("hwp5txt CLI is not available in .venv-hwp")

    proc = subprocess.run(
        [str(hwp5txt_bin), str(input_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return _normalize_hwp_text(proc.stdout)


def run_hwp_to_txt_conversion(
    input_path: Path,
    output_path: Path,
    source_format: str,
    target_format: str,
    route: str | None = None,
    template: Path | None = None,
    preserve_original: bool = True,
) -> ConversionResult:
    if source_format != "hwp" or target_format != "txt":
        raise ValueError("run_hwp_to_txt_conversion only supports hwp -> txt")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(extract_hwp_text(input_path), encoding="utf-8")
    return _build_result(input_path, output_path, source_format, target_format, route, template, preserve_original)


def run_hwp_to_md_conversion(
    input_path: Path,
    output_path: Path,
    source_format: str,
    target_format: str,
    route: str | None = None,
    template: Path | None = None,
    preserve_original: bool = True,
) -> ConversionResult:
    if source_format != "hwp" or target_format != "md":
        raise ValueError("run_hwp_to_md_conversion only supports hwp -> md")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    model = parse_hwp_text_to_model(extract_hwp_text(input_path))
    output_path.write_text(render_markdown(model), encoding="utf-8")
    return _build_result(input_path, output_path, source_format, target_format, route, template, preserve_original)


def run_hwp_to_docx_conversion(
    input_path: Path,
    output_path: Path,
    source_format: str,
    target_format: str,
    route: str | None = None,
    template: Path | None = None,
    preserve_original: bool = True,
) -> ConversionResult:
    if source_format != "hwp" or target_format != "docx":
        raise ValueError("run_hwp_to_docx_conversion only supports hwp -> docx")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    model = parse_hwp_text_to_model(extract_hwp_text(input_path))
    write_docx(model, output_path)
    return _build_result(input_path, output_path, source_format, target_format, route, template, preserve_original)


def run_hwp_to_hwpx_bridge_conversion(
    input_path: Path,
    output_path: Path,
    source_format: str,
    target_format: str,
    route: str | None = None,
    template: Path | None = None,
    preserve_original: bool = True,
) -> ConversionResult:
    if source_format != "hwp" or target_format != "hwpx":
        raise ValueError("run_hwp_to_hwpx_bridge_conversion only supports hwp -> hwpx")
    if not hwp_bridge_available():
        raise RuntimeError("hwp2hwpx bridge is not available")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    classpath = '/tmp/hwp2hwpx/lib/*:/tmp/hwp2hwpx/build/classes'
    subprocess.run(
        ['java', '-cp', classpath, 'RunConvert', str(input_path), str(output_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return _build_result(input_path, output_path, source_format, target_format, route, template, preserve_original)
