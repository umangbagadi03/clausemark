import json
import logging
import os
import time

from clausemark import config

logger = logging.getLogger(__name__)


def save_trace(result):
    """Add one line per question to a local file, so a bad answer can be looked at later.
    Failing to write a trace must never fail the answer."""
    trace = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "file_path": result["file_path"],
        "question": result["question"],
        "model": result["model"],
        "seconds": result["seconds"],
        "found": result["found"],
        "steps": result["steps"],
        "clause_ids": [],
        "citations": len(result["citations"]),
        "rejected_quotes": result["rejected_quotes"],
    }
    for clause in result["clauses"]:
        trace["clause_ids"].append(clause["clause_id"])

    try:
        os.makedirs(os.path.dirname(config.TRACES_FILE), exist_ok=True)
        with open(config.TRACES_FILE, "a", encoding="utf-8") as file:
            file.write(json.dumps(trace) + "\n")
    except OSError as error:
        logger.warning("Could not save the trace: %s", error)
