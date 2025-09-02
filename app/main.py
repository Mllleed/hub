from fastapi import FastAPI
from app.api import infobase, todos
from app.db import init_db
from fastapi.staticfiles import StaticFiles

app = FastAPI(title='Mini Hub')
app.mount('/static', StaticFiles(directory='app/static'), name='static')

app.include_router(todos.router, prefix='/action')
app.include_router(infobase.router)

@app.on_event('startup')
async def startup():
    await init_db()

