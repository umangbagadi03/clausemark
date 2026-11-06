from clausemark.chunking.clauses import build_parents
from clausemark.dataset.corpus import read_contract

# Clauses come from the contract text with the same result every time,
# so there is no file to keep in sync. They are built on first use.
_parents_by_contract = {}


def get_parents(set_name, file_path):
    key = (set_name, file_path)
    if key not in _parents_by_contract:
        text = read_contract(set_name, file_path)
        _parents_by_contract[key] = build_parents(file_path, text)
    return _parents_by_contract[key]


def forget_parents(set_name, file_path):
    key = (set_name, file_path)
    if key in _parents_by_contract:
        del _parents_by_contract[key]


def get_parent(set_name, file_path, parent_id):
    for parent in get_parents(set_name, file_path):
        if parent["parent_id"] == parent_id:
            return parent
    return None


def find_parent_by_label(set_name, file_path, label):
    for parent in get_parents(set_name, file_path):
        if label in parent["labels"]:
            return parent
    return None
