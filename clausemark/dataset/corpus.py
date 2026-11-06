import os

from clausemark import config
from clausemark.dataset.benchmark import load_questions

# Uploaded contracts are named "uploads/<file>", which is how we know their set.
UPLOAD_PREFIX = config.UPLOADS_SET + "/"

_questions_by_set = {}
_contract_paths_by_set = {}
_contract_text = {}


def get_questions(set_name):
    if set_name not in _questions_by_set:
        _questions_by_set[set_name] = load_questions(set_name)
    return _questions_by_set[set_name]


def is_upload(file_path):
    return file_path.startswith(UPLOAD_PREFIX)


def set_of_contract(active_set, file_path):
    if is_upload(file_path):
        return config.UPLOADS_SET
    return active_set


def list_benchmark_contracts(set_name):
    """Only the contracts the questions of this set use, like the paper does."""
    if set_name not in _contract_paths_by_set:
        paths = set()
        for question in get_questions(set_name):
            for snippet in question["snippets"]:
                paths.add(snippet["file_path"])
        _contract_paths_by_set[set_name] = sorted(paths)
    return _contract_paths_by_set[set_name]


def list_uploaded_contracts():
    folder = os.path.join(config.corpus_dir(config.UPLOADS_SET), config.UPLOADS_SET)
    if not os.path.isdir(folder):
        return []

    paths = []
    for name in sorted(os.listdir(folder)):
        if name.endswith(".txt"):
            paths.append(UPLOAD_PREFIX + name)
    return paths


def list_app_contracts(active_set):
    """What a user can open: their own uploads first, then the benchmark contracts."""
    return list_uploaded_contracts() + list_benchmark_contracts(active_set)


def contract_disk_path(set_name, file_path):
    return os.path.join(config.corpus_dir(set_name), file_path)


def read_contract(set_name, file_path):
    # Benchmark character positions depend on this exact way of reading the file.
    key = (set_name, file_path)
    if key not in _contract_text:
        with open(contract_disk_path(set_name, file_path), "r", encoding="utf-8") as file:
            _contract_text[key] = file.read()
    return _contract_text[key]


def forget_contract(set_name, file_path):
    key = (set_name, file_path)
    if key in _contract_text:
        del _contract_text[key]


def contract_title(file_path):
    name = os.path.basename(file_path)
    if name.lower().endswith(".txt"):
        name = name[:-4]
    return name.replace("_", " ").strip()


def contract_source(file_path):
    parts = file_path.split("/")
    if len(parts) > 1:
        return parts[0]
    return "contract"


def questions_for_contract(set_name, file_path):
    picked = []
    for question in get_questions(set_name):
        if question["snippets"][0]["file_path"] == file_path:
            picked.append(question)
    return picked
