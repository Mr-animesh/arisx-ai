"""FastAPI server exposing pipeline status and program data."""

import dataclasses

from fastapi import FastAPI

from api.status import get_status
from db.database import get_all_programs

app = FastAPI(title="ArisX Credits Scraper API")


@app.get("/status")
def status():
    return get_status()


@app.get("/programs")
def programs():
    return [dataclasses.asdict(p) for p in get_all_programs()]
