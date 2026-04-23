#!/usr/bin/env python3
"""Select best conversion route by running multiple candidates and scoring outputs."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from shawn_hwp.qa.reporting import generate_qa_result


def _safe_output(path: Path) -> str:
    if not path.exists() or path.stat().st_size == 0:
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _extract_hwp_anchor(source_path: Path) -> str:
    """Best-effort HWP anchor extraction using parser-backed markdown projection."""
    if source_path.suffix.lower() != ".hwp":
        return ""

    try:
        from shawn_hwp.converters.hwp_engine import extract_hwp_text, parse_hwp_text_to_model
        from shawn_hwp.io_markdown import render_markdown

        model = parse_hwp_text_to_model(extract_hwp_text(source_path))
        return render_markdown(model)
    except Exception:
        return ""


def _extract_xml_text(xml_path: str) -> str:
    root = ElementTree.fromstring(xml_path)
    texts: list[str] = []
    for el in root.iter():
        if el.text:
            texts.append(el.text)
        if el.tail:
            texts.append(el.tail)
    return " ".join(text.strip() for text in texts if text and text.strip())


def _extract_docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as zf:
            if "word/document.xml" not in zf.namelist():
                return ""
            xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
        return _extract_xml_text(xml)
    except Exception:
        return ""


def _extract_odt_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as zf:
            if "content.xml" not in zf.namelist():
                return ""
            xml = zf.read("content.xml").decode("utf-8", errors="ignore")
        return re.sub(r"\s+", " ", _extract_xml_text(xml)).strip()
    except Exception:
        return ""


def _extract_html_text(path: Path) -> str:
    text = _safe_output(path)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_text(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    if suffix in {"md", "txt", "json", "yml", "yaml"}:
        return _safe_output(path)
    if suffix == "docx":
        return _extract_docx_text(path)
    if suffix == "odt":
        return _extract_odt_text(path)
    if suffix in {"html", "htm"}:
        return _extract_html_text(path)
    if suffix == "pdf":
        return ""
    return ""


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + ("\n" if text and not text.endswith("\n") else ""), encoding="utf-8")
    return path


SELECTION_REASON_TEXT_THRESHOLD = 0.70
SELECTION_REASON_STRUCTURE_THRESHOLD = 0.60
SELECTION_REASON_TABLE_THRESHOLD = 0.70


def _build_selection_reasons(qa_payload: dict, status: str) -> list[str]:
    if status != "ok":
        return [f"route {qa_payload.get('reason', 'failed')}"]

    reasons: list[str] = []
    comparisons = qa_payload.get("comparisons", {})
    metrics = qa_payload.get("metrics", {})

    text_similarity = float(comparisons.get("text_similarity", 0.0))
    structure_similarity = float(comparisons.get("heading_similarity", 0.0))
    table_similarity = float(comparisons.get("table_similarity", 0.0))

    if text_similarity < SELECTION_REASON_TEXT_THRESHOLD:
        reasons.append(f"Text similarity low ({text_similarity:.4f}); candidate text deviates from anchor")
    if structure_similarity < SELECTION_REASON_STRUCTURE_THRESHOLD:
        reasons.append(f"Heading/structure similarity low ({structure_similarity:.4f}); heading recovery not stable")
    if table_similarity < SELECTION_REASON_TABLE_THRESHOLD:
        reasons.append(f"Table similarity low ({table_similarity:.4f})")

    source_tables = comparisons.get("source_table_count", 0)
    candidate_tables = comparisons.get("candidate_table_count", 0)
    source_headings = comparisons.get("source_heading_count", 0)
    candidate_headings = comparisons.get("candidate_heading_count", 0)
    if source_headings > 0 and candidate_headings == 0:
        reasons.append("No candidate headings detected while source has headings")
    if source_tables > candidate_tables:
        reasons.append(f"Table loss ({source_tables} -> {candidate_tables})")
    if source_tables < candidate_tables:
        reasons.append(f"Table gain ({source_tables} -> {candidate_tables}); noise candidates likely")

    if metrics:
        if metrics.get("text", 0) < 30:
            reasons.append("Low text score")
        if metrics.get("structure", 0) < 10:
            reasons.append("Low structure score")
        if metrics.get("table", 0) < 8:
            reasons.append("Low table score")

    if not reasons:
        reasons.append("good fidelity: no major risk deltas observed")

    return reasons


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run multiple conversion routes and choose the best by QA score")
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--from", dest="source_format", required=True)
    p.add_argument("--to", dest="target_format", required=True)
    p.add_argument("--outdir", required=True, type=Path)
    p.add_argument("--candidates", nargs="*")
    p.add_argument("--manifest", type=Path)
    return p


def _candidate_definitions(source_format: str, target_format: str) -> list[tuple[str, list[tuple[str, str]]]]:
    if source_format == "hwp" and target_format == "md":
        return [
            ("hwp-salvage", [("hwp", "md")]),
            ("hwp-bridge", [("hwp", "hwpx"), ("hwpx", "md")]),
        ]
    if source_format == "hwp" and target_format == "docx":
        return [
            ("hwp-salvage", [("hwp", "docx")]),
            ("hwp-bridge", [("hwp", "hwpx"), ("hwpx", "docx")]),
        ]
    if source_format == "hwp" and target_format == "odt":
        return [
            ("hwp-to-odt-via-docx", [("hwp", "docx"), ("docx", "odt")]),
            ("hwp-bridge-to-odt", [("hwp", "hwpx"), ("hwpx", "docx"), ("docx", "odt")]),
        ]
    if source_format == "hwpx" and target_format == "md":
        return [("hwpx-native", [("hwpx", "md")])]
    if source_format == "hwpx" and target_format == "docx":
        return [("hwpx-native", [("hwpx", "docx")])]
    if source_format == "hwpx" and target_format == "odt":
        return [("hwpx-to-odt", [("hwpx", "docx"), ("docx", "odt")])]
    if source_format == "docx" and target_format == "hwpx":
        return [("hwpx-native", [("docx", "hwpx")])]
    if source_format == "md" and target_format == "hwpx":
        return [("hwpx-native", [("md", "hwpx")])]
    raise ValueError(f"No candidate definitions for {source_format}->{target_format}")


def _run_convert(args: list[str]) -> tuple[bool, str, str, int]:
    completed = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    return (
        completed.returncode == 0,
        completed.stdout,
        completed.stderr,
        completed.returncode,
    )


def _run_route(source: Path, route_name: str, hops: list[tuple[str, str]], outdir: Path) -> tuple[bool, Path | None, dict]:
    py = sys.executable
    convert = ROOT / "scripts" / "convert.py"
    current = source
    for idx, (source_format, target_format) in enumerate(hops):
        step_output = outdir / f"{route_name}__step{idx}.{target_format}"
        meta_path = outdir / f"{route_name}__step{idx}.metadata.json"
        ok, stdout, stderr, returncode = _run_convert(
            [
                py,
                str(convert),
                "--input",
                str(current),
                "--from",
                source_format,
                "--to",
                target_format,
                "--output",
                str(step_output),
                "--emit-metadata",
                str(meta_path),
            ]
        )
        if not ok or not step_output.exists():
            return (
                False,
                None,
                {
                    "status": "failed",
                    "step": idx,
                    "returncode": returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                    "expected": f"{source_format}-to-{target_format}",
                },
            )
        current = step_output
    return True, current, {"status": "ok", "stdout": stdout, "stderr": stderr}


def _score_output(source_anchor: Path, candidate_path: Path, candidate_label: str) -> tuple[bool, dict]:
    if not source_anchor.exists():
        return False, {"status": "failed", "reason": "missing-anchor", "score": 0, "max": 100}
    if not source_anchor.stat().st_size:
        return False, {"status": "failed", "reason": "empty-anchor", "score": 0, "max": 100}
    try:
        candidate_format = candidate_path.suffix.lower().lstrip(".")
        qa = generate_qa_result(
            source=source_anchor,
            candidate=candidate_path,
            source_format="md",
            candidate_format=candidate_format,
            label=candidate_label,
        )
        return True, qa.to_dict()
    except Exception as exc:
        return False, {"status": "failed", "reason": f"score-failed:{type(exc).__name__}", "score": 0, "max": 100}


def main() -> int:
    args = build_parser().parse_args()

    source = args.input
    if not source.exists():
        raise SystemExit(f"input not found: {source}")

    try:
        candidates = _candidate_definitions(args.source_format, args.target_format)
    except ValueError as exc:
        raise SystemExit(str(exc))

    if args.candidates:
        wanted = set(args.candidates)
        candidates = [row for row in candidates if row[0] in wanted]
        if not candidates:
            raise SystemExit("No candidate names matched --candidates filter")

    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    # Anchor for scoring
    anchor_path = outdir / "source_anchor.md"
    source_text = ""

    if source.suffix.lower() == ".hwp":
        source_text = _extract_hwp_anchor(source)

    if not source_text:
        source_text = _extract_text(source)

    if source_text:
        _write_text(anchor_path, source_text)
    elif args.source_format in {"hwp", "hwpx"} and args.target_format != "md":
        anchor_tmp = outdir / "source_anchor_tmp.md"
        ok, stdout, stderr, returncode = _run_convert(
            [
                sys.executable,
                str(ROOT / "scripts" / "convert.py"),
                "--input",
                str(source),
                "--from",
                args.source_format,
                "--to",
                "md",
                "--output",
                str(anchor_tmp),
            ]
        )
        if ok:
            _write_text(anchor_path, _safe_output(anchor_tmp))
        else:
            _write_text(anchor_path, "")
            # preserve for diagnostics
            diagnostics = {
                "anchor_fallback_source": str(source),
                "anchor_stage": "hwp-to-md",
                "returncode": returncode,
                "stdout": stdout,
                "stderr": stderr,
            }
            (outdir / "source_anchor_diag.json").write_text(json.dumps(diagnostics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        _write_text(anchor_path, source_text)

    rows: list[dict] = []
    best = None

    for route_name, hops in candidates:
        ok, final_output, run_meta = _run_route(source, route_name, hops, outdir)
        if not ok or final_output is None:
            qa_payload = {
                "status": "failed",
                "reason": "route-execution-failed",
                "score": None,
                "max": 100,
            }
            row = {
                "route": route_name,
                "status": "failed",
                **run_meta,
                "score": None,
                "qa": qa_payload,
                "selection_reasons": _build_selection_reasons(qa_payload, "failed"),
                "qa_justification": _build_selection_reasons(qa_payload, "failed"),
                "readiness": "unsafe without repair",
                "risk_categories": ["route_failed"],
            }
            rows.append(row)
            continue

        scored_ok, qa_payload = _score_output(anchor_path, final_output, route_name)
        if scored_ok:
            row = {
                "route": route_name,
                "status": "ok",
                "output": str(final_output),
                "score": qa_payload["weighted_score"],
                "max_score": qa_payload["max_score"],
                "readiness": qa_payload["readiness"],
                "risk_categories": qa_payload["risk_categories"],
                "qa": qa_payload,
                "stdout": run_meta["stdout"],
                "stderr": run_meta["stderr"],
            }
        else:
            row = {
                "route": route_name,
                "status": "failed",
                "output": str(final_output),
                "score": qa_payload.get("score", 0),
                "max_score": qa_payload.get("max", 100),
                "readiness": "unsafe without repair",
                "risk_categories": ["text", "structure", "table", "footnote_numbering"],
                "qa": qa_payload,
                "stdout": run_meta["stdout"],
                "stderr": run_meta["stderr"],
            }

        row["selection_reasons"] = _build_selection_reasons(qa_payload, row["status"])
        row["qa_justification"] = {
            "status": row["status"],
            "reasons": row["selection_reasons"],
            "score": row.get("score"),
            "max_score": row.get("max_score"),
        }

        rows.append(row)

        if row["status"] == "ok":
            if best is None or (rows[-1]["score"] > best["score"]):
                best = row

    if best is None:
        # fallback to first failed row for deterministic output
        best = rows[0] if rows else {"route": "none", "score": 0, "max_score": 100, "output": "", "readiness": "unsafe without repair"}

    recommendation_path = outdir / "best_route_manifest.json"
    manifest_payload = {
        "input": str(source),
        "source_format": args.source_format,
        "target_format": args.target_format,
        "anchor": str(anchor_path),
        "outdir": str(outdir),
        "candidates": rows,
        "selected_route": best["route"],
        "selected_output": best.get("output"),
        "selected_score": best.get("score"),
        "selected_readiness": best.get("readiness"),
        "selected_reason": best.get("selection_reasons", []),
    }
    recommendation_path.write_text(json.dumps(manifest_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if args.manifest:
        args.manifest.write_text(json.dumps(manifest_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    md_report = outdir / "best_route_report.md"
    md_lines = [
        "# SHawn-hwp best-route selection",
        "",
        f"- input: `{source}`",
        f"- selected route: `{best['route']}`",
        f"- selected score: `{best.get('score')}`",
        "- reasons:",
    ]
    for reason in best.get("selection_reasons", []):
        md_lines.append(f"  - {reason}")

    md_lines.extend(["", "## Candidates"])
    for row in rows:
        md_lines.append(f"- {row['route']}: {row['status']} (score={row.get('score')})")
    md_report.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print("SHawn-hwp route selector")
    print(f"input={source}")
    print(f"selected_route={best['route']}")
    print(f"selected_output={best.get('output')}")
    print(f"selected_score={best.get('score')}/{best.get('max_score')}")
    print(f"selected_reason={'; '.join(best.get('selection_reasons', []))}")
    print(f"manifest={recommendation_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
