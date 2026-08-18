"""
Day 38 — FastAPI Server Scaffold

Creates the main FastAPI application, SQLite connection,
middleware, router registration, and health endpoint.
"""

from pathlib import Path
import sqlite3
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


# ---------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "nifty100.db"

API_VERSION = "1.0.0"


# ---------------------------------------------------------------------
# APPLICATION
# ---------------------------------------------------------------------

app = FastAPI(
    title="N100 Financial Intelligence API",
    description="REST API for the N100 Financial Intelligence Platform.",
    version=API_VERSION,
)


# ---------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------
# START TIME
# ---------------------------------------------------------------------

START_TIME = time.time()


# ---------------------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------------------

def get_db_connection():
    """Create and return a SQLite database connection."""

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


# ---------------------------------------------------------------------
# REQUEST LOGGING MIDDLEWARE
# ---------------------------------------------------------------------

@app.middleware("http")
async def request_logging_middleware(request, call_next):
    """Log request method, path, and response time."""

    start_time = time.perf_counter()

    response = await call_next(request)

    elapsed_time = time.perf_counter() - start_time

    print(
        f"{request.method} "
        f"{request.url.path} "
        f"{response.status_code} "
        f"{elapsed_time:.4f}s"
    )

    return response


# ---------------------------------------------------------------------
# HEALTH ENDPOINT
# ---------------------------------------------------------------------

@app.get("/api/v1/health")
def health_check():
    """Return API status and SQLite database row counts."""

    table_names = [
        "analysis",
        "balancesheet",
        "cashflow",
        "companies",
        "company_growth_metrics",
        "documents",
        "financial_ratios",
        "market_cap",
        "peer_groups",
        "peer_percentiles",
    ]

    connection = get_db_connection()

    try:
        db_row_counts = {}

        for table in table_names:
            row = connection.execute(
                f"SELECT COUNT(*) AS count FROM {table}"
            ).fetchone()

            db_row_counts[table] = row["count"]

    finally:
        connection.close()

    uptime_seconds = round(
        time.time() - START_TIME,
        2,
    )

    return JSONResponse(
        content={
            "status": "ok",
            "db_row_counts": db_row_counts,
            "uptime_seconds": uptime_seconds,
            "version": API_VERSION,
        }
    )


# ---------------------------------------------------------------------
# ROOT ENDPOINT
# ---------------------------------------------------------------------

@app.get("/")
def root():
    """Return basic API information."""

    return {
        "name": "N100 Financial Intelligence API",
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/api/v1/health",
    }


# ---------------------------------------------------------------------
# ROUTER REGISTRATION
# ---------------------------------------------------------------------

from src.api.routers import (companies,screener,sectors,peers,valuation,portfolio,documents,health,market_cap)

app.include_router(companies.router)
app.include_router(screener.router)
app.include_router(sectors.router)
app.include_router(peers.router)
app.include_router(valuation.router)
app.include_router(portfolio.router)
app.include_router(documents.router)
app.include_router(health.router)
app.include_router(market_cap.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )