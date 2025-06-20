from fastapi import FastAPI
from app.db.session import create_db_and_tables
from app.api.users import router as users_router
from app.api.orgs import router as orgs_router
from app.api.tasks import router as tasks_router
app = FastAPI()
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Your API",
        version="1.0.0",
        description="This is your project backend",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.include_router(users_router)
app.include_router(orgs_router)
app.include_router(tasks_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.on_event("startup")
def on_startup():
    create_db_and_tables()




