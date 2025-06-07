from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(
    title="FastAPI Template",
    description="FastAPIのレイヤードアーキテクチャテンプレート",
    version="0.1.0",
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


# API v1のルーターを含める
app.include_router(api_router, prefix="/api/v1")
