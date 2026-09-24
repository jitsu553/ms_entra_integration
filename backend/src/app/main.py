from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.graph.client import GraphClient
from app.graph.errors import GraphAPIError, GraphAuthError, GraphThrottledError
from app.routers.mail import router as mail_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.graph_client = GraphClient(settings)
    yield
    await app.state.graph_client.aclose()


app = FastAPI(
    title="MS Entra Mail Integration Service",
    description=(
        "Reads and sends mail for a single mailbox via Microsoft Graph, "
        "using app-only (client credentials) authentication. "
        "All /mail endpoints require the X-API-Key header — click Authorize below to set it."
    ),
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(mail_router)


@app.exception_handler(GraphAPIError)
async def graph_api_error_handler(request: Request, exc: GraphAPIError) -> JSONResponse:
    status_code = 502 if isinstance(exc, GraphAuthError) else exc.status_code
    headers = None
    if isinstance(exc, GraphThrottledError) and exc.retry_after:
        headers = {"Retry-After": exc.retry_after}
    return JSONResponse(status_code=status_code, content={"detail": exc.detail}, headers=headers)


@app.get("/healthz", tags=["health"], summary="Liveness check", include_in_schema=True)
async def healthz() -> dict:
    return {"status": "ok"}
