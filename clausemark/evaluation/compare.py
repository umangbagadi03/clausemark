import json
import os

from clausemark import config
from clausemark.retrieval.recipes import RECIPES


def read_json_if_present(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_results(set_name):
    """Saved results in recipe order. Recipes that have not run are left out."""
    results = []
    for recipe in RECIPES:
        path = os.path.join(config.results_dir(set_name), recipe["name"] + ".json")
        result = read_json_if_present(path)
        if result is not None:
            results.append(result)
    return results


def load_answer_result(set_name):
    return read_json_if_present(os.path.join(config.results_dir(set_name), "answers.json"))


def percent(value):
    return "{:.1f}".format(value * 100)


def print_comparison(set_name):
    results = load_results(set_name)
    if len(results) == 0:
        print("No results yet. Run: python main.py experiment --set", set_name)
        return

    print("| Recipe | Scope | Recall@4 | Precision@4 | Recall@16 | Recall in 5000 chars | Precision in 5000 chars |")
    print("|---|---|---|---|---|---|---|")
    for result in results:
        overall = result["overall"]
        row = [
            result["recipe"] + ": " + result["label"],
            result["scope"],
            percent(overall["k4"]["recall"]),
            percent(overall["k4"]["precision"]),
            percent(overall["k16"]["recall"]),
            percent(overall["budget5000"]["recall"]),
            percent(overall["budget5000"]["precision"]),
        ]
        print("| " + " | ".join(row) + " |")
