# Clausemark

Clausemark answers questions about a contract and highlights the exact words each answer comes from. It runs its retrieval on a laptop, and measures that retrieval against [LegalBench-RAG](https://arxiv.org/abs/2408.10343), a public benchmark where every question has its answer marked by character position.

## The problem

The usual "chat with a PDF" recipe does not hold up on contracts:

- **Clauses get cut.** A fixed 500 character split can separate a limit from its exception.
- **Clauses point at each other.** "Except for Excluded Claims as defined in Section 1.4" means nothing without Section 1.4.
- **Exact words matter.** Vector search can miss terms like "Force Majeure", party names and clause numbers.
- **A reader needs proof.** A lawyer wants to see the line in the contract, not a summary to trust.

## How it works

```
question
  -> search one contract: vectors + BM25, fused with RRF
  -> swap each match for its full clause
  -> follow references like "Section 1.4" or "Exhibit A"
  -> grade the clauses, and search once more with legal terms if they fall short
  -> the LLM answers with quotes
  -> code finds each quote in the retrieved clauses
  -> a quote that is not there is removed, with any point that relied on it
```

Three decisions matter most:

- **Character positions come from code.** The LLM copies a quote. A search in the contract finds where it is, because an LLM cannot be trusted to count characters.
- **The reference resolver uses no LLM.** It is regular expressions and a lookup in the same contract, so it costs nothing to evaluate.
- **Retrieval is scored with no LLM.** Comparing character positions is free, so every recipe can run on all the questions.

## Architecture

Imports go one way, so each layer can be tested without the ones above it:

```
api -> agent -> answering, retrieval, llm
                retrieval -> indexing, chunking -> dataset
ingestion -> indexing, chunking
evaluation -> retrieval, agent
```

How it behaves when something goes wrong:

| Situation | What happens |
|---|---|
| The grader fails | The answer still runs with what was found, and the steps say so |
| The answer step fails or times out | A clear 503 with the provider's reason |
| The model returns broken JSON | Asked once more, then a clear error |
| One citation is malformed | Only that citation is dropped |
| A quote is not in the retrieved clauses, or is under 4 words | The quote is removed, with any point that relied on it |
| The contract is not indexed | A 409 that names the command to run |
| A Gemini model is out of quota | The next configured model is tried, then it waits and retries |

Other choices:

- **Uploads have their own index.** A user's contract can never change a benchmark score.
- **Caches have a size limit.** A long-running server keeps steady memory. Uploaded contracts are never cached, because they can change under the same name.
- **Every answer is traced.** `data/traces/asks.jsonl` keeps the question, clauses, rejected quotes, model and time for each answer.
- **The agent is tested without a model.** `tests/test_agent.py` runs the real graph with a fake LLM, including failures, the retry limit and made-up quotes.

## Setup

Needs Python 3.11 or newer.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
```

Set one key in `.env`. Clausemark uses the first it finds in this order: Gemini, Anthropic, OpenAI. With no key it uses a local Ollama model. `LLM_PROVIDER` can force one.

## Try it on the sample contracts

The repo includes two made-up contracts, so this works without the dataset.

```bash
.venv/bin/python main.py index --set sample
.venv/bin/python main.py serve
```

Then open http://127.0.0.1:8010. To use your own contract, go to Contracts and add a `.pdf` or `.txt` file of up to 5 MB.

## Run the benchmark

Download the data from the [LegalBench-RAG repository](https://github.com/zeroentropy-ai/legalbenchrag), save the zip as `data/download/legalbenchrag.zip`, and then:

```bash
.venv/bin/python main.py prepare
.venv/bin/python main.py index --set mini
.venv/bin/python main.py experiment --set mini
```

`mini` is the paper's 776 question subset, picked with the paper's own method. `full` has all 6,889 questions in the published files (the paper's abstract says 6,858). Add `--limit 10` to try 10 questions per benchmark first. Qdrant runs in local mode and allows one process per set, so stop the web app before indexing the set it is using.

The experiments above make no LLM calls. This command scores the full agent with the same metric, and it does make LLM calls. Set `GEMINI_FALLBACK_MODELS` to empty first, so every question uses the same model:

```bash
.venv/bin/python main.py evaluate-answers --set mini --limit 10
```

The data is not in this repo. The four source datasets (CUAD, MAUD, ContractNLI and PrivacyQA) have their own usage terms.

## What the experiments compare

Each recipe adds one change, and the scores count characters. Scores are saved in `results/` on your machine and appear on the Benchmark page.

| Recipe | Change |
|---|---|
| 1 | Fixed 500 characters, vector search |
| 2 | + BM25 with RRF |
| 3 | + contract name in the search text |
| 4 | Clause chunks instead of fixed |
| 5 | + cross-encoder reranker |
| 6 | + return the full clause |
| 7 | + cross-reference resolver |
| 8 to 10 | Recipes 5 to 7 inside the contract that holds the answer |
| 11 to 13 | The same inside one contract, without the reranker. The app uses 13 |

Longer results find more text just by being longer. So every recipe is also scored on a fixed budget of 2,000, 5,000 and 10,000 characters.

## Project layout

```
main.py             commands: prepare, index, experiment, compare, ask, serve
clausemark/
  dataset/          questions, the mini set, reading contracts
  chunking/         headings, clauses, fixed-size baseline
  indexing/         embeddings, BM25 vectors, Qdrant in local mode
  ingestion/        reading uploaded PDF and text files
  retrieval/        recipes, search, fusion, reranker, reference resolver
  evaluation/       character-level metrics, retrieval and answer runners
  llm/              Gemini, Anthropic, OpenAI and Ollama clients
  agent/            the LangGraph workflow, prompts and traces
  answering/        answer schema, reply parsing, quote verification
  api/              FastAPI routes
  utils/            the size-limited cache
web/                plain HTML, CSS and JavaScript
tests/              run with: .venv/bin/python -m pytest
```

## Limits

- A PDF is shown as its extracted text, not its original pages, so tables lose their layout. A scanned PDF needs OCR first.
- Headings are found with patterns. A document with no numbered or capitalised headings becomes size-based chunks, or one clause if it is short.
- This runs on one machine for one user. Qdrant local mode allows one process, and there is no login.
- Answers appear when finished, with no streaming.
- The resolver follows one hop, and it finds only the clause a heading labels. A reference to "Section 4.1(b)" reaches all of Section 4.1.
- Each benchmark question has its answer in one document, so this does not test reasoning across contracts.
- A verified quote shows the words exist in the contract. It does not prove the model's explanation of them is right.
- This is an engineering project and not legal advice.
