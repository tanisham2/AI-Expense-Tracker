from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routers import auth, expenses, forecast, analytics

app = FastAPI(
    title="FinTrack AI API",
    description="AI-powered expense tracking and forecasting backend",
    version="1.0.0",
    docs_url="/docs",       # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(forecast.router)
app.include_router(analytics.router)

@app.on_event("startup")
def startup():
    init_db()
    print("✅ Database initialized")

@app.get("/health")
def health():
    return {"status": "ok", "service": "FinTrack AI"}