from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, audit, chat, documents, precedents, prompts, templates, users, versions, workflow, analysis_v2
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.migrations import run_migrations
from app.core.precedents import ensure_precedents


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if not settings.SKIP_STARTUP_MIGRATIONS:
        run_migrations()
    if settings.PRECEDENTS_AUTO_SEED:
        db = SessionLocal()
        try:
            ensure_precedents(db)
        finally:
            db.close()
    yield


app = FastAPI(title="SmartLawer V2 API", lifespan=lifespan)

# Browser frontend (Next.js dev on :3000/:3001) calls this API cross-origin;
# without CORS the browser blocks register/login/uploads while curl works.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1", tags=["login"])
app.include_router(audit.router, prefix="/api/v1", tags=["audit"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(precedents.router, prefix="/api/v1/precedents", tags=["precedents"])
app.include_router(prompts.router, prefix="/api/v1/prompts", tags=["prompts"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["templates"])
app.include_router(versions.router, prefix="/api/v1", tags=["versions"])
app.include_router(workflow.router, prefix="/api/v1", tags=["workflow"])
app.include_router(analysis_v2.router, prefix="/api/v2", tags=["analysis-v2"])


@app.get("/health")
def health_check():
    return {"status": "healthy"}
