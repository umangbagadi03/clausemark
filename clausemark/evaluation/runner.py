import json
import os
import time

from clausemark import config
from clausemark.dataset.benchmark import limit_per_benchmark
from clausemark.dataset.corpus import get_questions
from clausemark.evaluation.metrics import score_retrieval, trim_to_budget
from clausemark.retrieval.pipeline import retrieve

TOP_K_VALUES = [1, 2, 4, 8, 16, 32]
BUDGETS = [2000, 5000, 10000]


def scope_of(recipe, question):
    if recipe["scope"] == "contract":
        return question["snippets"][0]["file_path"]
    return None


def add_score(totals, key, score):
    if key not in totals:
        totals[key] = {"precision": 0.0, "recall": 0.0, "chars": 0.0, "count": 0}
    totals[key]["precision"] = totals[key]["precision"] + score["precision"]
    totals[key]["recall"] = totals[key]["recall"] + score["recall"]
    totals[key]["chars"] = totals[key]["chars"] + score["chars"]
    totals[key]["count"] = totals[key]["count"] + 1


def average_totals(totals):
    averages = {}
    for key, total in totals.items():
        count = total["count"]
        averages[key] = {
            "precision": round(total["precision"] / count, 4),
            "recall": round(total["recall"] / count, 4),
            "chars": round(total["chars"] / count),
        }
    return averages


def score_question(recipe, set_name, question):
    results = retrieve(set_name, question["question"], recipe, scope_of(recipe, question))

    scores = {}
    for k in TOP_K_VALUES:
        scores["k" + str(k)] = score_retrieval(results[:k], question["snippets"])
    for budget in BUDGETS:
        trimmed = trim_to_budget(results, budget)
        scores["budget" + str(budget)] = score_retrieval(trimmed, question["snippets"])
    return scores


def run_recipe(set_name, recipe, limit=None):
    questions = limit_per_benchmark(get_questions(set_name), limit)
    print("Running", recipe["name"], "on", len(questions), "questions")

    overall = {}
    by_benchmark = {}
    started = time.time()

    for number, question in enumerate(questions, start=1):
        scores = score_question(recipe, set_name, question)

        benchmark = question["benchmark"]
        if benchmark not in by_benchmark:
            by_benchmark[benchmark] = {}

        for key, score in scores.items():
            add_score(overall, key, score)
            add_score(by_benchmark[benchmark], key, score)

        if number % 50 == 0:
            print("  ", number, "of", len(questions))

    benchmark_averages = {}
    for benchmark, totals in by_benchmark.items():
        benchmark_averages[benchmark] = average_totals(totals)

    return {
        "recipe": recipe["name"],
        "label": recipe["label"],
        "scope": recipe["scope"],
        "set": set_name,
        "questions": len(questions),
        "seconds": round(time.time() - started, 1),
        "overall": average_totals(overall),
        "by_benchmark": benchmark_averages,
    }


def save_result(result):
    folder = config.results_dir(result["set"])
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, result["recipe"] + ".json")
    with open(path, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)
    return path
