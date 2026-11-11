"""Exercise the public QA contract with synthetic OOXML packages only."""

from hashlib import sha256
from pathlib import Path
from zipfile import ZipFile

import pytest

from shawn_docx_qa import qa_docx


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
</Types>"""
RELATIONSHIPS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="document" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="core" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
</Relationships>"""
DOCUMENT = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body><w:p><w:r><w:t>Synthetic QA example</w:t></w:r></w:p></w:body>
</w:document>"""
CORE = """<?xml version="1.0" encoding="UTF-8"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Synthetic example</dc:title></cp:coreProperties>"""


def synthetic_docx(path: Path, *, document=True, core=True):
    with ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("_rels/.rels", RELATIONSHIPS)
        if document:
            archive.writestr("word/document.xml", DOCUMENT)
        if core:
            archive.writestr("docProps/core.xml", CORE)
    return path


def test_complete_synthetic_docx_is_read_only_and_hides_parent_path(tmp_path):
    path = synthetic_docx(tmp_path / "example.docx")
    before = sha256(path.read_bytes()).hexdigest()

    result = qa_docx(path)

    assert result == {
        "path": "example.docx",
        "is_docx_zip": True,
        "has_document_xml": True,
        "warnings": [],
    }
    assert sha256(path.read_bytes()).hexdigest() == before


def test_missing_core_metadata_is_reported(tmp_path):
    path = synthetic_docx(tmp_path / "no-core.docx", core=False)

    result = qa_docx(path)

    assert result["is_docx_zip"] is True
    assert result["has_document_xml"] is True
    assert result["warnings"] == ["missing core metadata"]


def test_missing_document_part_does_not_pass_structure_check(tmp_path):
    path = synthetic_docx(tmp_path / "no-document.docx", document=False)

    result = qa_docx(path)

    assert result["is_docx_zip"] is True
    assert result["has_document_xml"] is False


@pytest.mark.parametrize("payload", [b"This is plain text.", b"PK\x03\x04truncated zip"])
def test_non_zip_and_damaged_zip_are_reported_without_changing_input(tmp_path, payload):
    path = tmp_path / "damaged.docx"
    path.write_bytes(payload)

    result = qa_docx(path)

    assert result["is_docx_zip"] is False
    assert result["has_document_xml"] is False
    assert result["warnings"] == ["not a readable docx zip"]
    assert path.read_bytes() == payload


def test_path_string_is_supported(tmp_path):
    path = synthetic_docx(tmp_path / "string-path.docx")

    assert qa_docx(str(path))["has_document_xml"] is True
