import asyncio
import json
from contextlib import asynccontextmanager
import random
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from api import api

from bigtable_client import ensure_table_exists
from fastapi import FastAPI


# Initialize Bigtable on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_table_exists()
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/", api)
