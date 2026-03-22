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

app = FastAPI()

add_pagination(app)

@app.get("/", response_model=Page[TelemetryResponse])
def get_telemetry(device: str | None = None, after: datetime | None = None, before: datetime | None = None, db: Session = Depends(get_db)):
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
        
    return paginate(qs)

@app.get("/aggregates")
async def get_aggregates(request: Request):
    url = os.getenv("SCALA_URL", "http://scala-aggregation-service:8081/agg")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=request.query_params)
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError as exc:
        raise HTTPException(status_code=502, detail=f"Connect error: {repr(exc)}")
    except httpx.ReadTimeout as exc:
        raise HTTPException(status_code=502, detail=f"Timeout: {repr(exc)}")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Scala returned {exc.response.status_code}: {exc.response.text}"
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Request error: {repr(exc)}")