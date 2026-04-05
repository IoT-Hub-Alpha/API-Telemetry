import os
import httpx
from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime
from .services.database import get_db
from .models import Telemetry
from .services.schemas import TelemetryResponse
from fastapi_pagination.links import Page
from fastapi_pagination import add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi.middleware.cors import CORSMiddleware
from iot_logging import FastAPIRequestContextMiddleware, StructuredJsonFormatter
from iot_auth.fastapi import require_permissions
from iot_auth.types import JWTPayload
import logging

app = FastAPI()

add_pagination(app)

logging.basicConfig(level=logging.INFO)
for handler in logging.root.handlers:
    handler.setFormatter(StructuredJsonFormatter())

app.add_middleware(FastAPIRequestContextMiddleware)


# allow everyone, since its dev, why the hell not, right???
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/v1/telemetry/health")
async def ready():
    return {"health": "ok"}

@app.get("/v1/telemetry", response_model=Page[TelemetryResponse])
async def get_telemetry(device: str | None = None, after: datetime | None = None, before: datetime | None = None, db: Session = Depends(get_db), auth: JWTPayload = Depends(require_permissions("telemetry.view"))):
    qs = db.query(Telemetry)
    
    if device:
        qs = qs.filter(
            Telemetry.device==device,
            )
    
    if after:
        qs = qs.filter(
            Telemetry.timestamp > after
        )
        
    if before:
        qs = qs.filter(
            Telemetry.timestamp < before
        )
        
    logging.info("fetching telemetry...", extra={"device": device, "after": after, "before": before})
    return paginate(qs)

@app.get("/v1/telemetry/aggregates")
async def get_aggregates(request: Request, auth: JWTPayload = Depends(require_permissions("telemetry.view"))):
    url = os.getenv("SCALA_URL", "http://scala-aggregation-service:8081/agg")
    logging.info("forwarding request to scala...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=request.query_params)
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError as exc:
        logging.info("HTTPException", extra={"error": repr(exc), "code": 502})
        raise HTTPException(status_code=502, detail=f"Connect error: {repr(exc)}")
    except httpx.ReadTimeout as exc:
        logging.info("ReadTimeout", extra={"error": repr(exc), "code": 502})
        raise HTTPException(status_code=502, detail=f"Timeout: {repr(exc)}")
    except httpx.HTTPStatusError as exc:
        logging.info("HTTPStatusError", extra={"error": repr(exc), "code": 502})
        raise HTTPException(
            status_code=502,
            detail=f"Scala returned {exc.response.status_code}: {exc.response.text}"
        )
    except httpx.RequestError as exc:
        logging.info("RequestError", extra={"error": repr(exc), "code": 502})
        raise HTTPException(status_code=502, detail=f"Request error: {repr(exc)}")