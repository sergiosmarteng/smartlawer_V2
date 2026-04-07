from fastapi import FastAPI
from app.api.routes import auth, users, documents, templates

app = FastAPI(title="SmartLawer V2 API")

app.include_router(auth.router, prefix="/api/v1", tags=["login"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["templates"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}
