from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import auth, audit, chat, documents, prompts, templates, users, versions, workflow
from app.core.config import settings
from app.core.migrations import run_migrations


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if not settings.SKIP_STARTUP_MIGRATIONS:
        run_migrations()
    yield


app = FastAPI(title="SmartLawer V2 API", lifespan=lifespan)

app.include_router(auth.router, prefix="/api/v1", tags=["login"])
app.include_router(audit.router, prefix="/api/v1", tags=["audit"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(prompts.router, prefix="/api/v1/prompts", tags=["prompts"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["templates"])
app.include_router(versions.router, prefix="/api/v1", tags=["versions"])
app.include_router(workflow.router, prefix="/api/v1", tags=["workflow"])


@app.get("/health")
def health_check():
    return {"status": "healthy"}
