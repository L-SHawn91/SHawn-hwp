from __future__ import annotations
from pathlib import Path
from zipfile import ZipFile, BadZipFile

def qa_docx(path: str | Path) -> dict:
    p=Path(path)
    result={"path": p.name, "is_docx_zip": False, "has_document_xml": False, "warnings": []}
    try:
        with ZipFile(p) as z:
            names=set(z.namelist())
            result["is_docx_zip"]=True
            result["has_document_xml"]="word/document.xml" in names
            if "docProps/core.xml" not in names: result["warnings"].append("missing core metadata")
    except BadZipFile:
        result["warnings"].append("not a readable docx zip")
    return result
