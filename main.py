from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# Create directories if they don't exist
os.makedirs("static/images", exist_ok=True)
os.makedirs("static/uploads", exist_ok=True)

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Your other routes go here
