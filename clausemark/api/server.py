import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from clausemark import config
from clausemark.api import contract_routes
from clausemark.evaluation.compare import load_answer_result, load_results
from clausemark.llm.provider import pick_provider_name

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Clausemark")
app.include_router(contract_routes.router)


@app.middleware("http")
async def always_revalidate(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache"
    return response


@app.get("/api/status")
def status():
    return {
        "provider": pick_provider_name(),
        "active_set": config.ACTIVE_SET,
    }


@app.get("/api/benchmark")
def benchmark():
    return {
        "set": config.ACTIVE_SET,
        "results": load_results(config.ACTIVE_SET),
        "answers": load_answer_result(config.ACTIVE_SET),
    }


# The web app is plain HTML, CSS and JS, served from the web folder
app.mount("/", StaticFiles(directory="web", html=True), name="web")
