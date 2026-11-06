import json
import logging
import os

from clausemark import config
from clausemark.agent.ask import ask_contract
from clausemark.dataset.benchmark import limit_per_benchmark
from clausemark.dataset.corpus import get_questions
from clausemark.evaluation.metrics import score_retrieval
from clausemark.llm.errors import LLMError
from clausemark.llm.provider import get_llm

logger = logging.getLogger(__name__)

ANSWER_RESULT_FILE = "answers.json"


def citations_as_spans(result):
    spans = []
    for citation in result["citations"]:
        spans.append({
            "file_path": result["file_path"],
            "start": citation["start_char"],
            "end": citation["end_char"],
        })
    return spans


def average(total, count):
    if count == 0:
        return 0.0
    return round(total / count, 4)


def run_answers(set_name, limit):
    """Score the full agent with the same metric as retrieval: do its verified quotes
    overlap the benchmark's answer? This one makes LLM calls, so it has a limit."""
    questions = limit_per_benchmark(get_questions(set_name), limit)

    quote_recall = 0.0
    quote_precision = 0.0
    answered = 0
    failed = 0
    kept_quotes = 0
    rejected_quotes = 0
    seconds = 0.0

    for number, question in enumerate(questions, start=1):
        file_path = question["snippets"][0]["file_path"]
        print("  question", number, "of", len(questions))

        try:
            result = ask_contract(set_name, file_path, question["question"])
        except LLMError as error:
            logger.warning("Question %s failed: %s", number, error)
            failed = failed + 1
            continue

        score = score_retrieval(citations_as_spans(result), question["snippets"])
        quote_recall = quote_recall + score["recall"]
        quote_precision = quote_precision + score["precision"]
        kept_quotes = kept_quotes + len(result["citations"])
        rejected_quotes = rejected_quotes + len(result["rejected_quotes"])
        seconds = seconds + result["seconds"]
        if result["found"]:
            answered = answered + 1

    finished = len(questions) - failed
    return {
        "set": set_name,
        "model": get_llm().name,
        "questions": len(questions),
        "failed": failed,
        "answered_share": average(answered, finished),
        "quote_recall": average(quote_recall, finished),
        "quote_precision": average(quote_precision, finished),
        "rejected_quote_share": average(rejected_quotes, kept_quotes + rejected_quotes),
        "average_seconds": round(average(seconds, finished), 1),
    }


def save_answer_result(result):
    folder = config.results_dir(result["set"])
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, ANSWER_RESULT_FILE)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)
    return path
