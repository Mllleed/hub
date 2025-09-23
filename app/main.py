from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.api import infobase, todos
from app.db import init_db
from app.auth import auth

from contextlib import asynccontextmanager




origins = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title='Mini Hub', lifespan=lifespan)
auth.handle_errors(app)
app.add_middleware(CORSMiddleware,
                   allow_origins=origins,
                   allow_methods=["*"],
                   allow_headers=["*"],
                   allow_credentials=True,
                   )
app.mount('/static', StaticFiles(directory='app/static'), name='static')

app.include_router(todos.router, prefix='/action')
app.include_router(infobase.router)


