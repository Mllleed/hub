from fastapi import FastAPI
from api import notes, todos
from db import init_db

app = FastAPI(title='Mini Hub')

# app.include_router(notes.router, prefix='/notes')
app.include_router(todos.router, prefix='/action')

@app.on_event('startup')
async def startup():
    await init_db()

@app.get('/')
async def read_root():
    return {'Message': 'Добро пожаловать в MiniHub'}
