from __future__ import annotations

from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "deliverables" / "sample_documents" / "reliable_rag_demo_source.md"
OUTPUT = ROOT / "deliverables" / "sample_documents" / "reliable_rag_demo_handbook.pdf"


def escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def lines_from_markdown(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            lines.append("")
            continue
        if line.startswith("# "):
            lines.append(line[2:].upper())
            lines.append("")
        elif line.startswith("## "):
            lines.append(line[3:])
            lines.append("")
        else:
            lines.extend(textwrap.wrap(line, width=88))
            lines.append("")
    return lines


def paginate(lines: list[str], lines_per_page: int = 42) -> list[list[str]]:
    pages: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        current.append(line)
        if len(current) >= lines_per_page:
            pages.append(current)
            current = []
    if current:
        pages.append(current)
    return pages


def build_content_stream(page_lines: list[str], page_number: int) -> bytes:
    commands = [
        "BT",
        "/F1 11 Tf",
        "54 760 Td",
        "14 TL",
    ]
    for index, line in enumerate(page_lines):
        if index > 0:
            commands.append("T*")
        if line:
            commands.append(f"({escape_pdf_text(line)}) Tj")
    commands.extend(
        [
            "ET",
            "BT",
            "/F1 9 Tf",
            "54 34 Td",
            f"(Reliable RAG Platform Demo Handbook - Page {page_number}) Tj",
            "ET",
        ]
    )
    return ("\n".join(commands) + "\n").encode("latin-1", errors="replace")


def write_pdf(pages: list[list[str]]) -> None:
    objects: list[bytes] = []

    def add_object(data: str | bytes) -> int:
        if isinstance(data, str):
            data = data.encode("latin-1", errors="replace")
        objects.append(data)
        return len(objects)

    page_count = len(pages)
    catalog_id = add_object("<< /Type /Catalog /Pages 2 0 R >>")
    assert catalog_id == 1

    # Reserve object 2 for the pages tree once page ids are known.
    objects.append(b"")

    font_id = add_object("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_ids: list[int] = []

    for page_number, page_lines in enumerate(pages, start=1):
        stream = build_content_stream(page_lines, page_number)
        content_id = add_object(
            b"<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"endstream"
        )
        page_id = add_object(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        )
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {page_count} >>".encode("latin-1")

    output = bytearray()
    output.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_number, data in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{object_number} 0 obj\n".encode("ascii"))
        output.extend(data)
        output.extend(b"\nendobj\n")

    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(output)


def main() -> None:
    source_text = SOURCE.read_text(encoding="utf-8")
    pages = paginate(lines_from_markdown(source_text))
    write_pdf(pages)
    print(f"Created {OUTPUT}")
    print(f"Pages: {len(pages)}")


if __name__ == "__main__":
    main()
