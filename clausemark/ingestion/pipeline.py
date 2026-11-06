import os

from clausemark import config
from clausemark.chunking.clause_store import forget_parents
from clausemark.dataset.corpus import (
    UPLOAD_PREFIX,
    contract_disk_path,
    forget_contract,
    is_upload,
)
from clausemark.indexing import builder, vector_store
from clausemark.ingestion.parsers import UploadError, extract_text, safe_contract_name


def add_contract(filename, data):
    """Save an uploaded contract as text and index it. Returns its file path."""
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise UploadError("The file is too big. The limit is 5 MB.")

    text = extract_text(filename, data)
    if len(text.strip()) < config.MIN_CONTRACT_CHARACTERS:
        raise UploadError("Almost no text was found. A scanned PDF needs OCR first.")

    file_path = UPLOAD_PREFIX + safe_contract_name(filename) + ".txt"
    disk_path = contract_disk_path(config.UPLOADS_SET, file_path)
    os.makedirs(os.path.dirname(disk_path), exist_ok=True)

    with open(disk_path, "w", encoding="utf-8") as file:
        file.write(text)

    # Uploading the same name again replaces the old contract
    forget_contract(config.UPLOADS_SET, file_path)
    forget_parents(config.UPLOADS_SET, file_path)
    builder.index_one_contract(config.UPLOADS_SET, file_path)
    return file_path


def remove_contract(file_path):
    if not is_upload(file_path):
        raise UploadError("Only uploaded contracts can be removed.")

    disk_path = contract_disk_path(config.UPLOADS_SET, file_path)
    if os.path.exists(disk_path):
        os.remove(disk_path)

    forget_contract(config.UPLOADS_SET, file_path)
    forget_parents(config.UPLOADS_SET, file_path)
    vector_store.delete_contract(config.UPLOADS_SET, "clause", file_path)
