import os

from dotenv import load_dotenv

load_dotenv()


# Folders
DATA_DIR = "data"
SAMPLE_DIR = "sample_data"
RESULTS_DIR = "results"
DOWNLOADED_ZIP = os.path.join(DATA_DIR, "download", "legalbenchrag.zip")
UPLOADS_CORPUS_DIR = os.path.join(DATA_DIR, "user_contracts")
TRACES_FILE = os.path.join(DATA_DIR, "traces", "asks.jsonl")


# Benchmark sets. "uploads" is separate, so a user's contract can never change a benchmark score.
BENCHMARK_SETS = ["sample", "mini", "full"]
UPLOADS_SET = "uploads"


def corpus_dir(set_name):
    if set_name == UPLOADS_SET:
        return UPLOADS_CORPUS_DIR
    if set_name == "sample":
        return os.path.join(SAMPLE_DIR, "corpus")
    return os.path.join(DATA_DIR, "corpus")


def benchmarks_dir(set_name):
    if set_name == "sample":
        return os.path.join(SAMPLE_DIR, "benchmarks")
    return os.path.join(DATA_DIR, "benchmarks")


def qdrant_dir(set_name):
    return os.path.join(DATA_DIR, "qdrant", set_name)


def results_dir(set_name):
    return os.path.join(RESULTS_DIR, set_name)


def default_set():
    if os.path.isdir(corpus_dir("mini")):
        return "mini"
    return "sample"


# The benchmark set the web app and `ask` command use
ACTIVE_SET = os.getenv("ACTIVE_SET", "").strip().lower() or default_set()
if ACTIVE_SET not in BENCHMARK_SETS:
    raise ValueError("ACTIVE_SET must be one of: " + ", ".join(BENCHMARK_SETS))


# Local models. Both are small enough for a laptop with 8 GB of memory.
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
RERANKER_MODEL = "Xenova/ms-marco-MiniLM-L-12-v2"

# Searches are cached because experiments repeat them. The limit keeps a long-running server's memory steady.
CACHE_MAX_ITEMS = 8000

# Uploads
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MIN_CONTRACT_CHARACTERS = 200


# LLM providers. Leave LLM_PROVIDER empty to pick one from whichever API key is set.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").strip().lower()
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

GEMINI_FALLBACK_MODELS = []
for fallback_model in os.getenv("GEMINI_FALLBACK_MODELS", "").split(","):
    if fallback_model.strip():
        GEMINI_FALLBACK_MODELS.append(fallback_model.strip())

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
