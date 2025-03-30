from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from app.database.session import connect_to_mongo, close_mongo_connection
from app.api.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to MongoDB on startup
    await connect_to_mongo()
    yield
    # Close MongoDB connection on shutdown
    await close_mongo_connection()

app = FastAPI(
    title="SIGMA API",
    description="Backend API for SIGMA Mobile Application",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for mobile app connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your mobile app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Include API router
app.include_router(api_router)

@app.get("/")
def welcome():
    return {"message": "Welcome to SIGMA API BACKEND"}


