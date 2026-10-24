from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import settings

app = FastAPI(
    title="Document Copilot",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"health": "ok"}


if __name__ == "__main__":
    # Must use the string format if reload=True
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
