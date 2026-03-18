from fastapi import FastAPI, Depends
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