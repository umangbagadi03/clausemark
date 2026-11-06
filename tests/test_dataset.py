from clausemark.dataset.benchmark import limit_per_benchmark, pick_mini_questions
from clausemark.llm import provider


def make_question(file_path, number):
    return {
        "question": "q" + str(number),
        "benchmark": "cuad",
        "snippets": [{"file_path": file_path, "start": 0, "end": 1}],
    }


def test_mini_picks_194_and_is_repeatable():
    questions = []
    for number in range(500):
        questions.append(make_question("doc" + str(number % 40) + ".txt", number))

    first = pick_mini_questions(questions)
    second = pick_mini_questions(list(reversed(questions)))

    assert len(first) == 194
    first_files = set()
    second_files = set()
    for question in first:
        first_files.add(question["snippets"][0]["file_path"])
    for question in second:
        second_files.add(question["snippets"][0]["file_path"])
    assert first_files == second_files


def test_small_benchmark_is_kept_whole():
    questions = [make_question("a.txt", 1), make_question("a.txt", 2)]
    assert len(pick_mini_questions(questions)) == 2


def test_limit_is_per_benchmark():
    questions = [make_question("a.txt", 1), make_question("a.txt", 2), make_question("a.txt", 3)]
    questions[2]["benchmark"] = "maud"
    assert len(limit_per_benchmark(questions, 1)) == 2


def test_key_order_picks_the_provider(monkeypatch):
    monkeypatch.setattr(provider.config, "LLM_PROVIDER", "")
    monkeypatch.setattr(provider.config, "GEMINI_API_KEY", "")
    monkeypatch.setattr(provider.config, "ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(provider.config, "OPENAI_API_KEY", "")
    assert provider.pick_provider_name() == "ollama"

    monkeypatch.setattr(provider.config, "OPENAI_API_KEY", "x")
    assert provider.pick_provider_name() == "openai"

    monkeypatch.setattr(provider.config, "ANTHROPIC_API_KEY", "x")
    assert provider.pick_provider_name() == "anthropic"

    monkeypatch.setattr(provider.config, "GEMINI_API_KEY", "x")
    assert provider.pick_provider_name() == "gemini"


def test_forced_provider_wins(monkeypatch):
    monkeypatch.setattr(provider.config, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(provider.config, "GEMINI_API_KEY", "x")
    assert provider.pick_provider_name() == "ollama"
