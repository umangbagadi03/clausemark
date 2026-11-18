---
title: Clausemark
sdk: docker
app_port: 7860
pinned: false
short_description: Ask a contract a question and see the exact source line
---

# Clausemark

Ask a question about a contract. Clausemark finds the clauses that answer it and highlights the exact words.

- **Search only, no key needed.** The real search runs: vector and keyword search, full clauses, and references like "Section 1.4".
- **With your own key** (Gemini, Claude or OpenAI), the agent writes an answer. Code checks that every quote is really in the contract.

Your key stays in your browser tab. The server uses it for one question and never saves or logs it.

This demo has two made-up sample contracts, and uploads are turned off. The code, the benchmark and how to run it locally are on GitHub: https://github.com/umangbagadi03/clausemark
