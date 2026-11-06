import json
import os
import random

from clausemark import config

BENCHMARK_NAMES = ["privacy_qa", "contractnli", "maud", "cuad"]
MINI_QUESTIONS_PER_BENCHMARK = 194


def read_benchmark_file(path, benchmark_name):
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    questions = []
    for test in data["tests"]:
        snippets = []
        for snippet in test["snippets"]:
            snippets.append({
                "file_path": snippet["file_path"],
                "start": snippet["span"][0],
                "end": snippet["span"][1],
            })

        questions.append({
            "question": test["query"],
            "benchmark": benchmark_name,
            "snippets": snippets,
        })
    return questions


def document_sort_key(question):
    # The paper's own way to pick the mini set. Questions about the same
    # contract get the same number, so they stay together after sorting.
    random.seed(question["snippets"][0]["file_path"])
    return random.random()


def pick_mini_questions(questions):
    if len(questions) <= MINI_QUESTIONS_PER_BENCHMARK:
        return questions
    ordered = sorted(questions, key=document_sort_key)
    return ordered[:MINI_QUESTIONS_PER_BENCHMARK]


def load_questions(set_name):
    # A contract a user uploads has no benchmark questions
    if set_name == config.UPLOADS_SET:
        return []

    if set_name == "sample":
        path = os.path.join(config.benchmarks_dir("sample"), "sample.json")
        return read_benchmark_file(path, "sample")

    questions = []
    for benchmark_name in BENCHMARK_NAMES:
        path = os.path.join(config.benchmarks_dir(set_name), benchmark_name + ".json")
        benchmark_questions = read_benchmark_file(path, benchmark_name)
        if set_name == "mini":
            benchmark_questions = pick_mini_questions(benchmark_questions)
        questions.extend(benchmark_questions)
    return questions


def limit_per_benchmark(questions, limit):
    """Take the first few questions of each benchmark, for a quick trial run."""
    if limit is None:
        return questions

    picked = []
    count_by_benchmark = {}
    for question in questions:
        used = count_by_benchmark.get(question["benchmark"], 0)
        if used < limit:
            picked.append(question)
            count_by_benchmark[question["benchmark"]] = used + 1
    return picked
