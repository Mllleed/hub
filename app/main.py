from fastapi import FastAPI
from app.api import infobase, todos
from app.db import init_db
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title='Mini Hub', lifespan=lifespan)

app.mount('/static', StaticFiles(directory='app/static'), name='static')

app.include_router(todos.router, prefix='/action')
app.include_router(infobase.router)


