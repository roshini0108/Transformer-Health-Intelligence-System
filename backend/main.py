# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base

from models.transformer import Transformer
from models.reading import SensorReading
from models.prediction import HealthPrediction
from models.alert import Alert

Base.metadata.create_all(bind=engine)

from api.routes import transformers, readings, predictions, alerts

app = FastAPI(
    title="APEPDCL Transformer Health AI",
    description="AI-powered predictive maintenance for distribution transformers",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transformers.router, prefix="/api/v1")
app.include_router(readings.router,     prefix="/api/v1")
app.include_router(predictions.router,  prefix="/api/v1")
app.include_router(alerts.router,       prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "APEPDCL Transformer Health AI — Running ✓"}

@app.get("/health")
def health_check():
    return {"status": "ok", "database": "connected"}