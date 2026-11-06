import io
import os
import re

from pypdf import PdfReader
from pypdf.errors import PyPdfError

MAX_NAME_SIZE = 80


class UploadError(Exception):
    """The upload cannot be used. The message is safe to show to a user."""


def safe_contract_name(filename):
    """Keep only plain characters, so a file name can never point outside our folder."""
    name = os.path.basename(filename.replace("\\", "/"))
    name = os.path.splitext(name)[0]
    name = re.sub(r"[^A-Za-z0-9 _-]+", " ", name)
    name = " ".join(name.split())[:MAX_NAME_SIZE].strip()
    if not name:
        return "contract"
    return name


def read_pdf(data):
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise UploadError("This PDF is password protected.")

        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
    except (PyPdfError, ValueError, KeyError, OSError) as error:
        raise UploadError("This PDF could not be read.") from error

    return "\n\n".join(pages)


def read_text(data):
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")


def extract_text(filename, data):
    extension = os.path.splitext(filename)[1].lower()

    if extension == ".pdf":
        text = read_pdf(data)
    elif extension == ".txt":
        text = read_text(data)
    else:
        raise UploadError("Upload a .pdf or .txt file.")

    # One kind of line ending, so character positions stay the same when the file is read back
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    return text
