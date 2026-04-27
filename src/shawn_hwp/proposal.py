"""Research proposal structure and template QA helpers."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

REQUIRED_TOP_LEVEL_FIELDS = (
    "project_title",
    "principal_investigator",
    "host_institution",
    "sections",
)

REQUIRED_SECTION_IDS = (
    "need",
    "objectives",
    "innovation",
    "methods",
    "timeline",
    "expected_outcomes",
    "references",
)

SUBMISSION_NOISE_PATTERNS = (
    r"작성요령",
    r"제출\s*시\s*삭제",
    r"예시입니다",
    r"placeholder",
    r"TODO",
    r"TBD",
)


@dataclass
class ProposalIssue:
    level: str
    code: str
    message: str
    location: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class ProposalValidationResult:
    source: str
    valid: bool
    issues: list[ProposalIssue] = field(default_factory=list)
    required_section_count: int = len(REQUIRED_SECTION_IDS)
    present_required_section_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["issues"] = [issue.to_dict() for issue in self.issues]
        return payload


def load_proposal_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _section_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sections = payload.get("sections")
    if not isinstance(sections, list):
        return {}
    mapped: dict[str, dict[str, Any]] = {}
    for section in sections:
        if isinstance(section, dict) and section.get("id"):
            mapped[str(section["id"])] = section
    return mapped


def _contains_submission_noise(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in SUBMISSION_NOISE_PATTERNS)


def validate_proposal_payload(payload: dict[str, Any], source: str = "<memory>") -> ProposalValidationResult:
    issues: list[ProposalIssue] = []

    for field_name in REQUIRED_TOP_LEVEL_FIELDS:
        if field_name not in payload or payload[field_name] in (None, "", []):
            issues.append(
                ProposalIssue(
                    level="error",
                    code="missing_top_level_field",
                    message=f"Required top-level field is missing: {field_name}",
                    location=field_name,
                )
            )

    sections = payload.get("sections")
    if sections is not None and not isinstance(sections, list):
        issues.append(
            ProposalIssue(
                level="error",
                code="invalid_sections_type",
                message="sections must be a list of section objects",
                location="sections",
            )
        )

    mapped_sections = _section_map(payload)
    for section_id in REQUIRED_SECTION_IDS:
        if section_id not in mapped_sections:
            issues.append(
                ProposalIssue(
                    level="error",
                    code="missing_required_section",
                    message=f"Required research proposal section is missing: {section_id}",
                    location=f"sections.{section_id}",
                )
            )

    for section_id, section in mapped_sections.items():
        title = _as_text(section.get("title")).strip()
        body = _as_text(section.get("body")).strip()
        location = f"sections.{section_id}"
        if not title:
            issues.append(
                ProposalIssue(
                    level="warning",
                    code="missing_section_title",
                    message="Section title is empty",
                    location=f"{location}.title",
                )
            )
        if section_id in REQUIRED_SECTION_IDS and not body:
            issues.append(
                ProposalIssue(
                    level="error",
                    code="empty_required_section_body",
                    message=f"Required section has no body text: {section_id}",
                    location=f"{location}.body",
                )
            )
        if _contains_submission_noise(f"{title}\n{body}"):
            issues.append(
                ProposalIssue(
                    level="warning",
                    code="submission_noise_detected",
                    message="Template instruction/example/placeholder text may still remain",
                    location=location,
                )
            )

    present_required = sum(1 for section_id in REQUIRED_SECTION_IDS if section_id in mapped_sections)
    valid = not any(issue.level == "error" for issue in issues)
    return ProposalValidationResult(
        source=source,
        valid=valid,
        issues=issues,
        present_required_section_count=present_required,
    )


def validate_proposal_json(path: Path) -> ProposalValidationResult:
    return validate_proposal_payload(load_proposal_json(path), source=str(path))


def render_validation_markdown(result: ProposalValidationResult) -> str:
    status = "PASS" if result.valid else "FAIL"
    lines = [
        "# SHawn-hwp Research Proposal Validation",
        "",
        f"- source: `{result.source}`",
        f"- status: **{status}**",
        f"- required sections: **{result.present_required_section_count}/{result.required_section_count}**",
        "",
        "## Issues",
    ]
    if not result.issues:
        lines.append("- none")
    else:
        for issue in result.issues:
            lines.append(f"- **{issue.level}** `{issue.code}` at `{issue.location}`: {issue.message}")
    return "\n".join(lines).strip() + "\n"
