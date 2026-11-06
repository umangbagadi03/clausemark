import pytest

from clausemark.ingestion.parsers import UploadError, extract_text, safe_contract_name
from clausemark.utils.bounded_cache import BoundedCache


def make_pdf(words):
    """A tiny one-page PDF, written by hand so the tests need no extra library."""
    stream = "BT /F1 12 Tf 72 720 Td (" + words + ") Tj ET"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        "/Resources << /Font << /F1 5 0 R >> >> >>",
        "<< /Length " + str(len(stream)) + " >>\nstream\n" + stream + "\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    pdf = "%PDF-1.4\n"
    offsets = []
    for index, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf = pdf + str(index) + " 0 obj\n" + body + "\nendobj\n"

    table_start = len(pdf)
    pdf = pdf + "xref\n0 6\n0000000000 65535 f \n"
    for offset in offsets:
        pdf = pdf + str(offset).zfill(10) + " 00000 n \n"
    pdf = pdf + "trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n" + str(table_start) + "\n%%EOF\n"
    return pdf.encode("latin-1")


def test_reads_text_from_a_pdf():
    assert "Governing Law" in extract_text("deal.pdf", make_pdf("Governing Law of Delaware"))


def test_broken_pdf_gives_a_clear_error():
    with pytest.raises(UploadError):
        extract_text("deal.pdf", b"this is not a pdf")


def test_line_endings_become_one_kind():
    assert extract_text("a.txt", b"one\r\ntwo\rthree") == "one\ntwo\nthree"


def test_non_utf8_text_still_reads():
    assert extract_text("a.txt", "café".encode("latin-1")) == "café"


def test_other_file_types_are_refused():
    with pytest.raises(UploadError):
        extract_text("a.exe", b"data")


def test_safe_names():
    assert safe_contract_name("../../secret.txt") == "secret"
    assert safe_contract_name("C:\\files\\My Deal (final).pdf") == "My Deal final"
    assert safe_contract_name("???.txt") == "contract"
    assert len(safe_contract_name("a" * 300 + ".txt")) == 80


def test_cache_forgets_the_oldest_past_its_limit():
    cache = BoundedCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.get("a")
    cache.put("c", 3)

    assert cache.get("a") == 1
    assert cache.get("b") is None
    assert cache.get("c") == 3
