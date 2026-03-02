from fastapi import FastAPI
from app.routers import answer
import logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True}


app.include_router(answer.router)
