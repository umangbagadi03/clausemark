import argparse
import json
import logging
import os
import zipfile

from clausemark import config


def prepare_command(args):
    """Unpack the downloaded dataset into data/corpus and data/benchmarks."""
    if not os.path.exists(config.DOWNLOADED_ZIP):
        print("Put the LegalBench-RAG zip here first:", config.DOWNLOADED_ZIP)
        return

    with zipfile.ZipFile(config.DOWNLOADED_ZIP) as archive:
        archive.extractall(config.DATA_DIR)

    if os.path.isdir(config.corpus_dir("mini")) and os.path.isdir(config.benchmarks_dir("mini")):
        print("Dataset is ready in", config.DATA_DIR)
    else:
        print("Unpacked, but data/corpus and data/benchmarks were not found.")
        print("Found:", os.listdir(config.DATA_DIR))


def index_command(args):
    from clausemark.indexing.builder import SCHEMES, build_index

    schemes = SCHEMES
    if args.scheme:
        schemes = [args.scheme]

    for scheme in schemes:
        build_index(args.set, scheme)


def experiment_command(args):
    from clausemark.evaluation.compare import print_comparison
    from clausemark.evaluation.runner import run_recipe, save_result
    from clausemark.retrieval.recipes import RECIPES, get_recipe

    recipes = RECIPES
    if args.recipe:
        recipes = [get_recipe(args.recipe)]

    for recipe in recipes:
        result = run_recipe(args.set, recipe, args.limit)
        print("  saved to", save_result(result))

    print()
    print_comparison(args.set)


def compare_command(args):
    from clausemark.evaluation.compare import print_comparison

    print_comparison(args.set)


def evaluate_answers_command(args):
    from clausemark.evaluation.answer_runner import run_answers, save_answer_result

    result = run_answers(args.set, args.limit)
    print(json.dumps(result, indent=2))
    print("Saved to", save_answer_result(result))


def ask_command(args):
    from clausemark.agent.ask import ask_contract
    from clausemark.dataset.corpus import set_of_contract

    set_name = set_of_contract(config.ACTIVE_SET, args.file_path)
    result = ask_contract(set_name, args.file_path, args.question)
    print(json.dumps(result, indent=2))


def serve_command(args):
    import uvicorn

    uvicorn.run("clausemark.api.server:app", host="127.0.0.1", port=args.port)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    parser = argparse.ArgumentParser(description="Clausemark: find and verify clauses in a contract")
    commands = parser.add_subparsers(dest="command", required=True)

    prepare_parser = commands.add_parser("prepare", help="unpack the downloaded dataset")
    prepare_parser.set_defaults(handler=prepare_command)

    index_parser = commands.add_parser("index", help="build the search indexes")
    index_parser.add_argument("--set", default=config.ACTIVE_SET, choices=config.BENCHMARK_SETS)
    index_parser.add_argument("--scheme", help="only build this index: fixed, fixed_titled or clause")
    index_parser.set_defaults(handler=index_command)

    experiment_parser = commands.add_parser("experiment", help="score the retrieval recipes, makes no LLM calls")
    experiment_parser.add_argument("--set", default=config.ACTIVE_SET, choices=config.BENCHMARK_SETS)
    experiment_parser.add_argument("--recipe", help="only run this recipe")
    experiment_parser.add_argument("--limit", type=int, default=None, help="only use the first N questions per benchmark")
    experiment_parser.set_defaults(handler=experiment_command)

    compare_parser = commands.add_parser("compare", help="print saved results as a table")
    compare_parser.add_argument("--set", default=config.ACTIVE_SET, choices=config.BENCHMARK_SETS)
    compare_parser.set_defaults(handler=compare_command)

    answers_parser = commands.add_parser("evaluate-answers", help="score the full agent, makes LLM calls")
    answers_parser.add_argument("--set", default=config.ACTIVE_SET, choices=config.BENCHMARK_SETS)
    answers_parser.add_argument("--limit", type=int, required=True, help="questions per benchmark, to control cost")
    answers_parser.set_defaults(handler=evaluate_answers_command)

    ask_parser = commands.add_parser("ask", help="ask one contract a question from the terminal")
    ask_parser.add_argument("file_path")
    ask_parser.add_argument("question")
    ask_parser.set_defaults(handler=ask_command)

    serve_parser = commands.add_parser("serve", help="start the web app")
    serve_parser.add_argument("--port", type=int, default=8010)
    serve_parser.set_defaults(handler=serve_command)

    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
