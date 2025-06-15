from fastapi import FastAPI
from inner_app import app as inner_app

app = FastAPI()
app.mount("/api", inner_app)