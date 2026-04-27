"""HWPX template profile extraction and slot-aware injection helpers."""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

SLOT_PATTERN = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}|\[\[\s*slot:([A-Za-z0-9_.-]+)\s*\]\]")
INSTRUCTION_PATTERNS = (
    r"작성요령",
    r"제출\s*시\s*삭제",
    r"예시",
    r"파란색으로 작성",
    r"※",
)
SECTION_SOURCE_MAP = {
    "need": "sections.need.body",
    "objectives": "sections.objectives.body",
    "innovation": "sections.innovation.body",
    "methods": "sections.methods.body",
    "timeline": "sections.timeline.body",
    "expected_outcomes": "sections.expected_outcomes.body",
    "references": "sections.references.body",
}
TOP_LEVEL_SOURCE_MAP = {
    "project_title": "project_title",
    "principal_investigator": "principal_investigator",
    "host_institution": "host_institution",
}


@dataclass
class EditableSlot:
    id: str
    source: str
    required: bool = True
    member: str | None = None
    placeholder: str | None = None


@dataclass
class ProtectedRegion:
    id: str
    reason: str
    member: str
    text_preview: str


@dataclass
class LayoutBaseline:
    section_count: int = 0
    xml_member_count: int = 0
    table_count: int = 0
    image_count: int = 0
    paragraph_count: int = 0
    slot_count: int = 0


@dataclass
class TemplateProfile:
    template_id: str
    display_name: str
    source_format: str
    source_hash: str
    source_path: str
    protected_regions: list[ProtectedRegion] = field(default_factory=list)
    editable_slots: list[EditableSlot] = field(default_factory=list)
    layout_baseline: LayoutBaseline = field(default_factory=LayoutBaseline)
    qa_rules: dict[str, Any] = field(default_factory=lambda: {
        "fail_if_placeholder_remains": True,
        "warn_if_table_count_delta_exceeds": 0,
        "require_pdf_export_check": True,
    })

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _xml_members(zf: zipfile.ZipFile) -> list[str]:
    return sorted(name for name in zf.namelist() if name.lower().endswith(".xml"))


def _section_members(xml_members: list[str]) -> list[str]:
    return [name for name in xml_members if "section" in name.lower() or "contents" in name.lower()]


def _plain_preview(xml_text: str, limit: int = 120) -> str:
    text = re.sub(r"<[^>]+>", " ", xml_text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _slot_source(slot_id: str) -> str:
    if slot_id in TOP_LEVEL_SOURCE_MAP:
        return TOP_LEVEL_SOURCE_MAP[slot_id]
    if slot_id in SECTION_SOURCE_MAP:
        return SECTION_SOURCE_MAP[slot_id]
    if slot_id.startswith("sections."):
        return slot_id
    return slot_id


def _extract_slots(xml_text: str, member: str) -> list[EditableSlot]:
    slots: list[EditableSlot] = []
    seen: set[str] = set()
    for match in SLOT_PATTERN.finditer(xml_text):
        slot_id = match.group(1) or match.group(2)
        if not slot_id or slot_id in seen:
            continue
        seen.add(slot_id)
        slots.append(
            EditableSlot(
                id=slot_id,
                source=_slot_source(slot_id),
                member=member,
                placeholder=match.group(0),
            )
        )
    return slots


def _detect_protected_region(xml_text: str, member: str, index: int) -> ProtectedRegion | None:
    for pattern in INSTRUCTION_PATTERNS:
        if re.search(pattern, xml_text, flags=re.IGNORECASE):
            return ProtectedRegion(
                id=f"instruction_region_{index}",
                reason="template instruction/example text detected; protect or remove before submission",
                member=member,
                text_preview=_plain_preview(xml_text),
            )
    return None


def extract_template_profile(path: Path, template_id: str | None = None, display_name: str | None = None) -> TemplateProfile:
    if not zipfile.is_zipfile(path):
        raise ValueError(f"Not a zip-based HWPX file: {path}")

    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist()
        xml_members = _xml_members(zf)
        section_members = _section_members(xml_members)
        table_count = 0
        paragraph_count = 0
        protected_regions: list[ProtectedRegion] = []
        editable_slots: list[EditableSlot] = []

        for idx, member in enumerate(xml_members, start=1):
            xml_text = zf.read(member).decode("utf-8", errors="ignore")
            table_count += len(re.findall(r"<(?:[A-Za-z0-9_]+:)?tbl\b", xml_text))
            paragraph_count += len(re.findall(r"<(?:[A-Za-z0-9_]+:)?p\b", xml_text))
            protected = _detect_protected_region(xml_text, member, idx)
            if protected:
                protected_regions.append(protected)
            editable_slots.extend(_extract_slots(xml_text, member))

        image_count = sum(
            1
            for name in names
            if name.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".wmf", ".emf"))
        )

    baseline = LayoutBaseline(
        section_count=len(section_members),
        xml_member_count=len(xml_members),
        table_count=table_count,
        image_count=image_count,
        paragraph_count=paragraph_count,
        slot_count=len(editable_slots),
    )
    return TemplateProfile(
        template_id=template_id or path.stem,
        display_name=display_name or path.stem,
        source_format="hwpx",
        source_hash=_sha256(path),
        source_path=str(path),
        protected_regions=protected_regions,
        editable_slots=editable_slots,
        layout_baseline=baseline,
    )


def _section_lookup(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sections = payload.get("sections", [])
    if not isinstance(sections, list):
        return {}
    return {str(section.get("id")): section for section in sections if isinstance(section, dict) and section.get("id")}


def resolve_source_value(payload: dict[str, Any], source: str) -> str:
    if source.startswith("sections."):
        parts = source.split(".")
        if len(parts) >= 3:
            section = _section_lookup(payload).get(parts[1], {})
            return str(section.get(parts[2], ""))
    current: Any = payload
    for part in source.split("."):
        if isinstance(current, dict):
            current = current.get(part, "")
        else:
            return ""
    return "" if current is None else str(current)


def inject_payload_into_hwpx_template(template_path: Path, payload: dict[str, Any], output_path: Path) -> TemplateProfile:
    """Replace explicit {{slot}} / [[slot:id]] markers in a copied HWPX template.

    This is a conservative v1 injection route. It only edits explicit markers and keeps every
    other zip member untouched.
    """

    profile = extract_template_profile(template_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    slot_values = {slot.placeholder: escape(resolve_source_value(payload, slot.source)) for slot in profile.editable_slots if slot.placeholder}

    with zipfile.ZipFile(template_path, "r") as ref_zip:
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as out_zip:
            for item in ref_zip.infolist():
                data = ref_zip.read(item.filename)
                if item.filename.lower().endswith(".xml"):
                    text = data.decode("utf-8", errors="ignore")
                    for placeholder, value in slot_values.items():
                        text = text.replace(placeholder, value)
                    out_zip.writestr(item, text.encode("utf-8"))
                else:
                    out_zip.writestr(item, data)
    return profile


def write_profile_json(profile: TemplateProfile, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(profile.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
