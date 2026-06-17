from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

from backend.database import init_db
from backend.routers import auth, expenses, forecast, analytics

app = FastAPI(
    title="FinTrack AI API",
    description="AI-powered expense tracking and forecasting backend",
    version="1.0.0",
    docs_url=None,          # Disable default Swagger UI       
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/docs", include_in_schema=False)
async def custom_docs():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
      <title>FinTrack API Docs</title>

      <style>
        body {
          margin: 0;
          background: #121212;
        }

        #swagger-ui {
          filter: invert(0.92) hue-rotate(180deg);
        }
      </style>

      <link rel="stylesheet"
            href="https://unpkg.com/swagger-ui-dist/swagger-ui.css">
    </head>
    <body>
      <div id="swagger-ui"></div>

      <script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>

      <script>
        SwaggerUIBundle({
          url: "/openapi.json",
          dom_id: "#swagger-ui"
        });
      </script>
    </body>
    </html>
    """)

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